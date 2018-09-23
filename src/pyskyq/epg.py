"""This module implements the EPG class"""

import asyncio
import logging
from typing import Any, List, Optional

from aiohttp import ClientSession, ClientTimeout  # type: ignore

from .channel import Channel
from .constants import (REST_PORT, REST_SERVICE_DETAIL_URL_PREFIX,
                        REST_SERVICES_URL)


class EPG:
    """ The top-level class for all EPG data and functions.

    EPG implements access to any data and operations related to the SkyQ box's
    Electronic Programme Guide. Currently, this means that both summary and detail
    channel information is aggregated into a :class:`pyskyq.channel.Channel` object.

    Attributes:
        host (str): Hostname or IPv4 address of SkyQ Box.
        port (int): Port number to use to connect to the REST HTTP server.
            Defaults to the standard port used by SkyQ boxes which is 9006.
        logger (logging.Logger): Standard Python logger object which if not passed will
            instantiate a local logger.

    """

    def __init__(self,
                 host: str,
                 port: int = REST_PORT,
                 logger: Optional[logging.Logger] = None,
                 ) -> None:
        """Initialise Sky EPG Object.

        This method instantiates the EPG object and populates it with:

        - Channel data

        Args:
            host (str): String with resolvable hostname or IPv4 address to SkyQ box.
            port (int, optional): Port number to use to connect to the Remote REST API.
                Defaults to the standard port used by SkyQ boxes which is 9006.
            logger (logging.Logger, optional): Standard Python logger object which if not
                passed will instantiate a local logger.
        Returns:
            None
        """

        self.host: str = host
        self.port: int = port
        self.logger: logging.Logger = logging.getLogger(__name__) if not logger else logger
        self._channels: list = []
        self.logger.debug(f"Initialised EPG object object with host={host}, port={port}")

        self.load_channels()


        # get list of channels from channel URL
        # get detail's metadata for channels URL
        # create channel's list (in panda's)

    @staticmethod
    async def _fetch(session: ClientSession,
                     url: str
                     ) -> Any:
        """Fetch data from URL asynchronously.

        This helper method fetches data from a URL asynchronously. It is used to fetch EPG
        data from the SkyQ box, including calling the detail endpoint for each channel.

        Args:
            session (aiohttp.ClientSession): Session to use when fetching the data.
            url (str): URL to fetch.

        Returns:
            any: The body of data returned.

        """

        async with session.get(url) as response:
            #TODO add validation etc.
            return await response.json()

    async def _fetch_all_chan_details(self,
                                      session: ClientSession,
                                      sid_list: List[int]
                                      ) -> List:
        """Fetch channel detail data from SkyQ box asynchronously.

        This method fetches the channel list from ``/as/services/detail/<sid>`` endpoint.

        Args:
            session (aiohttp.ClientSession): Session to use when fetching the data.
            sid_list (list): List of Channel SID's to fetch.

        Returns:
            List: List of JSON documents for each channel detail fetched.

        """

        urls = [f'http://{self.host}:{self.port}{REST_SERVICE_DETAIL_URL_PREFIX}{sid}'
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
        self.logger.debug('Fetching channel list')
        url = f'http://{self.host}:{self.port}{REST_SERVICES_URL}'

        timeout = ClientTimeout(total=60)
        async with ClientSession(timeout=timeout) as session:
            chan_payload = await self._fetch(session, url)

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
                self.get_channel(sid).add_detail_data(channel)


    def load_channels(self) -> None:
        """Load all channel data.

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
        raise AttributeError(f"Channel not found. sid = {sid}.")
