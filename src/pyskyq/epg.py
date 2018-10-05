"""This module implements the EPG class"""

import asyncio
import logging
from typing import Any, List, Dict, Optional

from aiohttp import ClientSession, ClientTimeout  # type: ignore

from .channel import Channel
from .constants import (REST_PORT, REST_SERVICE_DETAIL_URL_PREFIX,
                        REST_SERVICES_URL)

LOGGER = logging.getLogger(__name__)

class EPG:
    """ The top-level class for all EPG data and functions.

    EPG implements access to any data and operations related to the SkyQ box's
    Electronic Programme Guide through a REST endpoint exposed on the box.
    Specifically, it fetches both summary and detail channel information from
    two different endpoints from the box and aggregates this data into a list of
    :class:`pyskyq.channel.Channel` objects.

    This channel data is then *augmented* with data from www.xmltv.co.uk which provides
    an XML file which follows the ``xmltv`` DTD.

    It also used the ``xmltv`` file to load **listings** data to enable the querying of
    programmes that are scheduled on the channels.

    Attributes:
        host (str): Hostname or IPv4 address of SkyQ Box.
        port (int): Port number to use to connect to the REST HTTP server.
            Defaults to the standard port used by SkyQ boxes which is 9006.

    """

    def __init__(self,
                 host: str,
                 *,
                 rest_port: int = REST_PORT,
                 ) -> None:
        """Initialise Sky EPG Object.

        This method instantiates the EPG object.

        Args:
            host (str): String with resolvable hostname or IPv4 address to SkyQ box.
            rest_port (int): Defaults to the SkyQ REST port which is 9006,

        Returns:
            None
        """

        self.host: str = host
        self.rest_port: int = rest_port
        self._xmltv_urls: set = set() # holds set of xmltv URLs for populatating listings data.

        self._channels: list = [] # holds list of Channel objects

        LOGGER.debug(f"Initialised EPG object using SkyQ box={self.host}")


    @staticmethod
    async def _fetch(session: ClientSession,
                     url: str
                     ) -> Dict:
        """Fetch data from URL asynchronously.

        This helper method fetches data from a URL asynchronously. It is used to fetch EPG
        data from the SkyQ box, including calling the detail endpoint for each channel.

        Args:
            session (aiohttp.ClientSession): Session to use when fetching the data.
            url (str): URL to fetch.

        Returns:
            dict: The body of data returned.

        """
        return await session.get(url)
        # async with session.get(url) as response:
        #     #TODO add validation etc.
        #     return await response

    async def _fetch_all_chan_details(self,
                                      session: ClientSession,
                                      sid_list: List[int]
                                      ) -> List[str]:
        """Fetch channel detail data from SkyQ box asynchronously.

        This method fetches the channel list from ``/as/services/detail/<sid>`` endpoint.

        Args:
            session (aiohttp.ClientSession): Session to use when fetching the data.
            sid_list (list): List of Channel SID's to fetch.

        Returns:
            List: List of JSON documents for each channel detail fetched.

        """

        urls = [f'http://{self.host}:{self.rest_port}{REST_SERVICE_DETAIL_URL_PREFIX}{sid}'
                for sid in sid_list]
        results = await asyncio.gather(*[asyncio.create_task(self._fetch(session, url))
                                         for url in urls])
        return results


    async def _load_channel_list(self) -> None:
        """Load channel data into channel property.

        This method fetches the channel list from ``/as/services`` endpoint and load
        :attr:`~pyskyq.epg.EPG._channels`

        Returns:
            None
        """
        LOGGER.debug('Fetching channel list')
        url = f'http://{self.host}:{self.rest_port}{REST_SERVICES_URL}'

        timeout = ClientTimeout(total=60)
        async with ClientSession(timeout=timeout) as session:
            chan_payload_json = await self._fetch(session, url)
            chan_payload = await chan_payload_json.json()

        for channel in chan_payload['services']:
            self._channels.append(Channel(channel))


    async def _load_channel_details(self) -> None:
        """Load channel details onto channel properties.

        This method is a wrapper which calls :meth:`~pyskyq.epg.EPG._fetch_all_chan_details`
        to get the details about each channel from it's detail endpoint
        ``/as/services/details/<sid>`` and then adds it to the list data
        on :attr:`~pyskyq.epg.EPG.channels`.

        Returns:
            None
        """
        sid_list = [chan.sid for chan in self._channels]
        timeout = ClientTimeout(total=60)
        async with ClientSession(timeout=timeout) as session:
            channels = await self._fetch_all_chan_details(session, sid_list)
            for channel, sid in zip(channels, sid_list):
                json_dict = await channel.json()
                self.get_channel(sid).add_detail_data(json_dict)


    def load_channel_data(self) -> None:
        """Load all channel data from the SkyQ REST Service

        This is the high-level method that fully loads all the channel detail.

        Returns:
            None
        """

        loop = asyncio.get_event_loop()

        loop.run_until_complete(self._load_channel_list())
        loop.run_until_complete(self._load_channel_details())

        loop.close()

    def get_channel(self,
                    sid: Any
                    ) -> Channel:
        """Get channel data.

        This method returns a :class:`pyskyq.channel.Channel` object when
        passed in a channel ``sid``.

        Args:
            sid: The sid (service id) of the channel
        Returns:
            :class:`pyskyq.channel.Channel`: The channel if found.

        Raises:
            AttributeError: If the channel is not found.
        """
        sid = str(sid)
        for chan in self._channels:
            if chan.sid == sid:
                return chan
        raise AttributeError(f"Channel not found. sid = {sid}. Did you call load_channel_data()?")
