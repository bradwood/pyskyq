"""This module implements the EPG listing class."""
#pylint: disable=line-too-long
import hashlib
import logging
from collections.abc import Hashable
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from http.client import HTTPException

from aiohttp import ClientSession, ClientTimeout  # type: ignore

from pyskyq.utils import parse_http_date, url_validator

LOGGER = logging.getLogger(__name__)


class Listing(Hashable):
    """Holds the data and functions required to obtain an EPG listing.

    Currently it only support the XML TV Listings format.

    """

    # TODO use yarl instead of str for URLs.
    def __init__(self,
                 url: str,
                 path: Path = Path('.epg_data'),
                 ) -> None:
        """Instantiate the object with the URL to fetch."""
        self._url: str
        self._path: Path

        # Validate URL
        if url_validator(url):
            self._url = url
        else:
            raise ValueError('Bad URL passed.')

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

        str_binary = str(self._url.lower()).encode('utf8')
        self._hashobj = hashlib.sha256(str_binary)
        self._filename = f'{self._hashobj.hexdigest()}.xml'
        self._full_path = self._path.joinpath(self._filename)
        self._last_modified: Optional[datetime] = None

        LOGGER.debug(f'Listing initialised: {self}')


    def __hash__(self) -> int:
        """Define hash function for a Hashable object."""
        return int.from_bytes(self._hashobj.digest(), 'big')


    def __eq__(self, other) -> bool:
        """Define equality test for a Hashable object."""
        # relying on lazy boolean evaluation here.
        return isinstance(other, Listing) and hash(other._url) == hash(self._url)  # pylint: disable=protected-access

    def __repr__(self):
        """Print a human-friendly representation of this object."""
        return f"<List: url='{self._url}', path='{self._path}', filename='{self._filename}'>"

    @property
    def last_modified(self):
        """Return the last modified date from the HTTP header of the last download."""
        return self._last_modified

    @property
    def url(self) -> str:
        """Return the url of this listing."""
        return self._url

    @property
    def file_path(self) -> Path:
        """Return the full file_path of this listing."""
        return self._full_path


    # TODO - add aiofiles support HERE!
    # TODO -- add error handling for
    # -- HTTP headers missing
    # -- timeouts
    # -- etc
    async def fetch(self,  # pylint: disable=too-many-locals
                    *,
                    timeout: int = 60, # sec
                    range_size: int = 256*1024,   # bytes
                    ) -> None:
        """Fetch the Listings XML file."""
        LOGGER.debug(f'Fetch({self}) called started.')
        to_ = ClientTimeout(total=timeout)
        async with ClientSession(timeout=to_) as session:
            LOGGER.debug(f'Client session created. About to fetch url={self._url}')
            byte_start = 0
            byte_stop = range_size - 1 # as we count from 0
            with open(self._full_path, 'wb') as file_desc:
                while True:
                    req_header = {"Range": f'bytes={byte_start}-{byte_stop}'}
                    async with session.get(self._url, headers=req_header) as resp:
                        LOGGER.debug(f'Attempting byte range download. Range = {byte_start}-{byte_stop}')
                        LOGGER.info(f"Server responsed with status: {resp.status}.")
                        LOGGER.debug(f'Server response headers: {resp.headers}')

                        if 'Last-Modified' in resp.headers:
                            self._last_modified = parse_http_date(resp.headers['Last-Modified'])
                            LOGGER.debug(f'Content last modified on: {resp.headers["Last-Modified"]}.')

                        if resp.status == 416:
                            raise HTTPException("Server responsed with {resp.status}: {resp.message}")

                        if resp.status == 206:  # partial content served.
                            # parse Content-Range header -- it looks like this: Content-Range: bytes 0-1023/16380313
                            content_range_from_total = resp.headers['Content-Range'].split()[1] # remove "bytes" from front of header
                            content_current_range = content_range_from_total.split('/')[0]  # grab the bit before the "/"
                            try:
                                content_entire_payload_size: Optional[int] = int(content_range_from_total.split('/')[1])  # grab the bit after  "/"" could be "*" if size is unknown
                            except ValueError:
                                content_entire_payload_size = None # not known.

                            # content_current_size = int(resp.headers['Content-Length'])  #length of this piece.
                            # content_start = int(content_current_range.split('-')[0])
                            content_end = int(content_current_range.split('-')[1])

                        if resp.status == 200:  # full content served as HTTP server doesn't appear to handle range requests.
                            LOGGER.info("Server responsed with status 200 and not 206 so full download assumed.")

                        chunk = await resp.read()
                        file_desc.write(chunk)
                        if resp.status == 206 and content_end + 1 == content_entire_payload_size:
                            # we have downloaded the entire file
                            break
                        if resp.status == 206:
                            # still have parts to go, update the range for the next cycle:
                            if byte_stop + range_size + 1 > content_entire_payload_size: # type: ignore
                                byte_start = byte_stop + 1
                                byte_stop = content_entire_payload_size  # type: ignore
                                if byte_start >= byte_stop:
                                    break
                            else:
                                byte_start = byte_stop + 1
                                byte_stop = byte_start + range_size
                            continue
                        # we've downloaded the whole file in one go
                        break

        LOGGER.debug(f'Fetch finished on {self}')


    def parse(self, parser) -> Dict:
        """Parse the Listings XML data."""
        pass
