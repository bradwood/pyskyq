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
        if isinstance(path, str):
            self._path = Path(path)
        else:
            self._path = path

        if not path.is_dir():
            path.mkdir()

        str_binary = str(self.__hash__()).encode('utf8')
        self._filename = self._path.joinpath(f'{hashlib.sha256(str_binary).hexdigest()}.xml')


    def __hash__(self) -> int:
        """Define hash function for a Hashable object."""
        return hash(self._url)


    def __eq__(self, other) -> bool:
        """Define equality test for a Hashable object."""
        # relying on lazy boolean evaluation here.
        return isinstance(other, Listing) and hash(other._url) == hash(self._url)  # pylint: disable=protected-access


    async def fetch(self,
                    *,
                    timeout: int = 60,
                    chunk_size: int = 1048576  # = 1 Mb
                    ) -> None:
        """Fetch the Listings XML file."""
        to_ = ClientTimeout(total=timeout)
        async with ClientSession(timeout=to_) as session:
            async with session.get(self._url) as resp:
                with open(self._filename, 'wb') as file_desc:
                    while True:
                        chunk = await resp.content.read(chunk_size)
                        if not chunk:
                            break
                        file_desc.write(chunk)


    def parse(self, parser) -> Dict:
        """Parse the Listings XML data."""
        pass
