"""This module implements the XMLTVListing listing class."""
#pylint: disable=line-too-long
import hashlib
import logging
import shutil
from collections.abc import Hashable
from datetime import datetime
from http.client import HTTPException
from pathlib import Path
from typing import Iterator, Optional

from aiohttp import ClientSession, ClientTimeout  # type: ignore
from yarl import URL

from .channel import Channel, channel_from_xmltv_list
from .utils import parse_http_date, xml_parse_and_remove

LOGGER = logging.getLogger(__name__)


class XMLTVListing(Hashable):  # pylint: disable=too-many-instance-attributes
    """Hold the data and functions required to obtain an XMLTVListing.

    Currently it only supports the XML TV Listings format which holds
    Channel and Programme scheduling information. See the dtd_ for details.

    .. _dtd: https://github.com/AlekSi/xmltv/blob/master/xmltv.dtd

    Note:

        The :class:`~.channel.Channel` class provides the **primary**
        interface to channel data through the :class:`~.epg.EPG` class.

        This class provides the means to download and parse XML data to do with
        channels, but more importantly, programming schedules. While it can be used
        stand-alone, it is designed to be injected into the
        :class:`~.epg.EPG` object using
        :meth:`.epg.EPG.add_XMLTV_listing_schedule`.

    """

    def __init__(self,
                 url: URL,
                 path: Path = Path('.epg_data'),
                 ) -> None:
        """Instantiate the object with the URL to fetch."""
        self._url: URL
        self._path: Path

        if not isinstance(url, URL):
            self._url = URL(url)
        else:
            self._url = url

        # Validate path
        if not isinstance(path, Path) and not isinstance(path, str):
            raise TypeError('path must be a string or Path object.')

        # coerce it to a Path if it's a string
        if isinstance(path, str):
            self._path = Path(path)
        else:
            self._path = path

        if not self._path.is_dir():
            self._path.mkdir()

        str_binary = str(self._url.human_repr()).encode('utf8')
        hashobj = hashlib.sha256(str_binary)
        self._hash = int.from_bytes(hashobj.digest(), 'big')
        self._filename = f'{hashobj.hexdigest()}.xml'
        self._full_path = self._path.joinpath(self._filename)
        self._last_modified: Optional[datetime] = None
        self._downloaded: bool = False
        self._downloading: bool = False

        LOGGER.debug(f'XMLTVListing initialised: {self}')

    def __hash__(self) -> int:
        """Define hash function for a Hashable object."""
        return self._hash

    def __eq__(self, other) -> bool:
        """Define equality test for a Hashable object."""
        # relying on lazy boolean evaluation here.
        return isinstance(other, XMLTVListing) and hash(other._url) == hash(self._url)  # pylint: disable=protected-access

    def __repr__(self):
        """Print a human-friendly representation of this object."""
        return f"<XMLTVListing: url='{self._url}', path='{self._path}', filename='{self._filename}'>"

    @property
    def last_modified(self):
        """Return the last modified date from the HTTP header of the last download.

        Returns the date and time when the data was last modified. Taken directly
        from the ``HTTP-Header``.

        Returns:
            datetime: A :py:class:`datetime.datetime` object


        """
        return self._last_modified

    @property
    def url(self) -> URL:
        """Return the url of this XMLTVListing.

        Returns:
            :py:class:`yarl.URL`

        """
        return self._url

    @property
    def downloaded(self) -> bool:
        """Return the status of XMLTV file download.

        Returns:
            bool: ``True`` if the file was downloaded successfully

        """
        return self._downloaded

    @property
    def downloading(self) -> bool:
        """Return the status of XMLTV file download.

        Returns:
            bool: ``True`` if the file is currently being downlaoded

        """
        return self._downloading

    @property
    def file_path(self) -> Path:
        """Return the full file path of this listing's XML file.

        Returns:
            :py:class:`pathlib.Path`: A `Path` to the location of the
            XML file (whether it has yet been :meth:`fetch`'ed or not).

        """
        return self._full_path

    # TODO - add aiofiles support HERE!
    # TODO -- add error handling for
    # -- HTTP headers missing
    # -- timeouts
    # -- etc
    # TODO -- add retry support

    async def fetch(self,  # pylint: disable=too-many-locals
                    *,
                    timeout: int = 60, # sec
                    range_size: int = 256*1024,   # bytes
                    ) -> None:
        """Fetch the XMLTVListing file.

        This async method will download the (XML) file specified by the URL passed
        at instantiation.

        As these files can be large, and because www.xmltv.co.uk, in particular,
        supports Range Requests (see rfc7233_) this method will attempt to download
        the file in parts using HTTP Range Requests, if the server supports them.
        This will limit the use of memory during the download process to that specified
        by the ``range_size`` parameter.

        If the server does not support Range Requests the method will will fall back
        to a more memory-intensive, vanilla HTTP download.

        .. _rfc7233 : https://tools.ietf.org/html/rfc7233

        Args:
            timeout (int): timeout in seconds for the HTTP session. Defaults to
                60 seconds.
            range_size (int): the size, in bytes, of each chunk. Defaults to
                256k (256*1024 bytes).

        Returns:
            None

        """
        LOGGER.debug(f'Fetch({self}) called started.')
        self._downloading = True
        to_ = ClientTimeout(total=timeout)
        async with ClientSession(timeout=to_) as session:
            LOGGER.debug(f'Client session created: {session}. About to fetch url={self._url}')
            byte_start = 0
            byte_stop = range_size - 1  # as we count from 0
            newfile = self._full_path.with_suffix('.tmp')
            with open(newfile, 'wb') as file_desc:  # TODO: use aiofile
                while True:
                    req_header = {"Range": f'bytes={byte_start}-{byte_stop}'}
                    resp = await session.get(self._url, headers=req_header)
                    #async with session.get(self._url, headers=req_header) as resp:
                    # -------
                    LOGGER.debug(f'Attempting byte range download. Range = {byte_start}-{byte_stop}')
                    LOGGER.info(f"Server responsed with status: {resp.status}.")
                    LOGGER.debug(f'Server response headers: {resp.headers}')

                    if 'Last-Modified' in resp.headers:
                        self._last_modified = parse_http_date(resp.headers['Last-Modified'])
                        LOGGER.debug(f'Content last modified on: {resp.headers["Last-Modified"]}.')

                    if resp.status == 416:
                        raise HTTPException("Server responsed with {resp.status}: {resp.message}")  # pragma: no cover

                    if resp.status == 206:  # partial content served.
                        # parse Content-Range header -- it looks like this: Content-Range: bytes 0-1023/16380313
                        content_range_from_total = resp.headers['Content-Range'].split()[1] # remove "bytes" from front of header
                        content_entire_payload_size = int(content_range_from_total.split('/')[1])  # grab the bit after  "/"

                    if resp.status == 200:  # full content served as HTTP server doesn't appear to handle range requests.
                        LOGGER.info("Server responsed with status 200 and not 206 so full download assumed.")

                    chunk = await resp.read()
                    file_desc.write(chunk)
                    if resp.status == 206:
                        if byte_stop + range_size + 1 > content_entire_payload_size: # type: ignore
                            byte_start = byte_stop + 1
                            byte_stop = content_entire_payload_size  # type: ignore
                            if byte_start >= byte_stop:
                                break
                        else:
                            byte_start = byte_stop + 1
                            byte_stop = byte_start + range_size
                        continue
                    break
                    # -------
            shutil.move(newfile, self._full_path)
            self._downloading = False
            self._downloaded = True
        LOGGER.debug(f'Fetch finished on {self}')

    def parse_channels(self) -> Iterator[Channel]:
        """Parse the XMLTVListing XML file and create an iterator over the channels in it."""
        if not self.downloaded and not self.downloading:
            raise OSError('File not downloaded, or download is currently in flight.')
        else:
            LOGGER.debug(f'in parse_channels. file = {self.file_path}')
            for xml_chan in xml_parse_and_remove(self.file_path, 'channel'):
                LOGGER.debug('yielding channel...')
                yield channel_from_xmltv_list(xml_chan)
