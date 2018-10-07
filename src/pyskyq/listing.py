"""This module implements the EPG listing class."""

import logging
from collections.abc import Hashable
from typing import Dict
from pathlib import Path
import hashlib

from aiohttp import ClientSession, ClientTimeout  # type: ignore

from .utils import url_validator

LOGGER = logging.getLogger(__name__)


class Listing(Hashable):
    """Holds the data and functions required to obtain an EPG listing.

    Currently it only support the XML TV Listings format.

    """

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

    # TODO - add aiofiles support HERE!
    async def fetch(self,
                    *,
                    timeout: int = 60, # sec
                    chunk_size: int = 1048576 # = 1 Mb
                    ) -> None:
        """Fetch the Listings XML file."""
        LOGGER.debug(f'Fetch({self}) called started.')
        to_ = ClientTimeout(total=timeout)
        async with ClientSession(timeout=to_) as session:
            LOGGER.debug(f'Fetch: Inside ClientSession()')
            LOGGER.debug(f'Fetch: About to fetch url={self._url}')
            async with session.get(self._url) as resp:
                LOGGER.debug(f'Fetch: Inside session.get(url={self._url})')
                with open(self._full_path, 'wb') as file_desc:
                    while True:
                        LOGGER.debug(f'Fetch: Inside file writing loop. filename={self._full_path}')
                        chunk = await resp.content.read(chunk_size)
                        if not chunk:
                            break
                        LOGGER.debug('Fetch: Got a chunk')
                        file_desc.write(chunk)
                        LOGGER.debug('Fetch: Wrote the chunk')

        LOGGER.debug(f'Fetch() call finished on {self}')


    def parse(self, parser) -> Dict:
        """Parse the Listings XML data."""
        pass
