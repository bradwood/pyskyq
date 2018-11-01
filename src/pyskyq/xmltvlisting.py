"""This module implements the XMLTVListing listing class."""
#pylint: disable=line-too-long
import hashlib
import logging
import shutil
import zlib
from collections.abc import Hashable
from datetime import datetime
from functools import partial
from os import PathLike
from pathlib import Path
from typing import IO, Any, Iterator, Optional, Union
from xml.etree.ElementTree import Element, iterparse

import asks
import trio
from yarl import URL

from .channel import Channel, channel_from_xmltv_list
from .utils import parse_http_date

LOGGER = logging.getLogger(__name__)
asks.init('trio')


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
        stand-alone, it is most effective when injected into the
        :class:`~.epg.EPG` object using
        :meth:`.epg.EPG.apply_XMLTVListing()`.

    """

    def __init__(self,
                 url: URL,
                 path: PathLike = Path('.epg_data'),
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

        If the header was not provided, it returns ``None``.

        Returns:
            datetime: A :py:class:`datetime.datetime` object or ``None``.

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

    # TODO -- add error handling for
    # -- HTTP headers missing
    # -- timeouts
    # -- badURL, etc, etc.
    # TODO -- add retry support

    async def fetch(self) -> None:
        """Fetch the XMLTVListing file.

        This async method will download the (XML) file specified by the URL passed
        at instantiation.

        If the server does not support streaming downloads the method will will
        fall back to a more memory-intensive, vanilla HTTP download.

        Args:
            timeout (int): timeout in seconds for the HTTP session. Defaults to
                60 seconds.
            range_size (int): the size, in bytes, of each chunk. Defaults to
                256k (256*1024 bytes).

        Returns:
            None

        """
        LOGGER.debug(f'Fetch({self}) call started.')
        self._downloading = True
        newfile = self._full_path.with_suffix('.tmp')


        # We support gzip encoding as www.xmltv.co.uk sends stuff gzipped.
        # the zlib decompressiion object supports streaming decompression which
        # why we use it.

        # We should probably support more encoding algorithms at some point.

        decompression_obj = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)
        compressed_payload = True  # assume payload is compressed first.

        async def chunk_processor(decomp_obj, bytechunk):
            nonlocal compressed_payload
            async with await trio.open_file(newfile, 'ab') as output_file:
                if compressed_payload:
                    try:
                        LOGGER.debug(f'Got zipped chunk. size = {len(bytechunk)}. Unzipping...')
                        await output_file.write(decomp_obj.decompress(bytechunk))
                        LOGGER.debug(f'Wrote unzipped chunk. size = {len(bytechunk)}')
                    except zlib.error:
                        await output_file.write(bytechunk)
                        LOGGER.debug(f'Wrote chunk. size = {len(bytechunk)}')
                        compressed_payload = False  # it wasn't compressed, so fall back
                else:
                    await output_file.write(bytechunk)
                    LOGGER.debug(f'Wrote chunk. size = {len(bytechunk)}')


        resp = await asks.get(str(self._url),
                              headers={'Accept-Encoding': 'gzip'},
                              # callback takes bytes only
                              callback=partial(chunk_processor, decompression_obj)
                              )

        LOGGER.debug(f'Got headers = {resp.headers}')

        # h11 makes header keys lowercase so we can reply on this
        if resp.headers.get("last-modified"):
            self._last_modified = parse_http_date(resp.headers.get("last-modified"))
            LOGGER.debug(f'Content last modified on: {resp.headers.get("last-modified")}.')

        shutil.move(newfile, self._full_path)
        self._downloading = False
        self._downloaded = True
        LOGGER.debug(f'Fetch finished on {self}')


    def parse_channels(self) -> Iterator[Channel]:
        """Parse the XMLTVListing XML file and create an iterator over the channels in it.

        Yield:
            :class:`~pyskyq.channel.Channel`
        """
        if not self.downloaded and not self.downloading:
            raise OSError('File not downloaded, or download is currently in flight.')
        else:
            LOGGER.debug(f'in parse_channels. file = {self.file_path}')
            for xml_chan in _xml_parse_and_remove(self._full_path, 'channel'): # type: ignore
                LOGGER.debug('yielding channel...')
                yield channel_from_xmltv_list(xml_chan)


# TODO: add error checking for XML errors
# TODO: see if this can be made async.
def _xml_parse_and_remove(filename: Union[str, bytes, int, IO[Any]],
                          path: str
                          ) -> Iterator[Element]:
    """Incrementally load and parse an XML file.

    Stolen from Python Cookbook 3rd edition, section 6.4 with credit to the book's authors.

    Args:
        filename(Union[str, bytes, int, IO[Any]]): a file-like object.
        path(str): The XML element to parse

    Yields:
        Element: A Parsed XML element.

    """
    path_parts = path.split('/')
    doc = iterparse(filename, ('start', 'end'))
    # skip the root element
    next(doc)  # pylint: disable=stop-iteration-return
    tag_stack = []
    elem_stack = []
    for event, elem in doc:
        if event == 'start':
            LOGGER.debug(f'Parsing XML element: {elem.tag}')
            tag_stack.append(elem.tag)
            elem_stack.append(elem)
        else:  # event == 'end'
            if tag_stack == path_parts:
                yield elem
                elem.clear()
            try:
                tag_stack.pop()
                elem_stack.pop()
            except IndexError:
                pass
