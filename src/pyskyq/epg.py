"""This module implements the EPG class."""

import asyncio
import logging
from typing import Any, List, Tuple

from aiohttp import ClientSession, ClientTimeout  # type: ignore

from pyskyq.channel import Channel, channel_from_skyq_service
from pyskyq.constants import (REST_PORT, REST_SERVICE_DETAIL_URL_PREFIX,
                              REST_SERVICES_URL)
from pyskyq.xmltvlisting import XMLTVListing

LOGGER = logging.getLogger(__name__)

class EPG:
    """The top-level class for all EPG data and functions.

    EPG implements access to any data and operations related to the SkyQ box's
    Electronic Programme Guide through a REST endpoint exposed on the box.
    Specifically, it fetches both summary and detail channel information from
    two different endpoints from the box and aggregates this data into a list of
    :class:`pyskyq.channel.Channel` objects.

    This channel data is then *augmented* with data from www.xmltv.co.uk which provides
    an XML file which follows the ``xmltv`` DTD.

    It also used the ``xmltv`` file to load **listings** data to enable the querying of
    programmes that are scheduled on the channels.

    Args:
        host (str): String with resolvable hostname or IPv4 address to SkyQ box.
        rest_port (int): Defaults to the SkyQ REST port which is 9006.

    Attributes:
        host (str): Hostname or IPv4 address of SkyQ Box.
        rest_port (int): Port number to use to connect to the REST HTTP server.
            Defaults to the standard port used by SkyQ boxes which is 9006.

    """

    def __init__(self,
                 host: str,
                 *,
                 rest_port: int = REST_PORT,
                 ) -> None:
        """Initialise Sky EPG Object."""
        self.host: str = host
        self.rest_port: int = rest_port
        self._channels: list = []
        self._listings: list = []
        LOGGER.debug(f"Initialised EPG object using SkyQ box={self.host}")

        # TODO:
        # - set up eventloop
        # - pass it into a separate thread
        # - loop through listings and call fetch when scheduled.

    def __repr__(self):
        """Print a human-friendly representation of this object."""
        return f"<EPG: host={self.host}, rest_port={self.rest_port}, " + \
            f"len(_channels)={len(self._channels)}, len(_xmltv_urls)={len(self._channels)}>"


    async def _load_channel_list(self) -> None:
        """Load channel data into channel property.

        This method fetches the channel list from ``/as/services`` endpoint and load
        :attr:`~pyskyq.epg.EPG._channels`

        Returns:
            None

        """
        url = f'http://{self.host}:{self.rest_port}{REST_SERVICES_URL}'
        LOGGER.debug('Fetching channel list from {url}')

        timeout = ClientTimeout(total=60)
        async with ClientSession(timeout=timeout) as session:
            chan_payload_json = await session.get(url)
            chan_payload = await chan_payload_json.json()

        for channel in chan_payload['services']:
            self._channels.append(channel_from_skyq_service(channel))


    async def _fetch_all_chan_details(self,
                                      session: ClientSession,
                                      sid_list: List[int]
                                      ) -> Tuple:
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
        results = await asyncio.gather(*[session.get(url) for url in urls])

        return results


    async def _load_channel_details(self) -> None:
        """Load channel details onto channel properties.

        This method is a wrapper which calls :meth:`~pyskyq.epg.EPG._fetch_all_chan_details`
        to get the details about each channel from it's detail endpoint
        ``/as/services/details/<sid>`` and then adds it to the list data
        on :attr:`~pyskyq.epg.EPG._channels`.

        Returns:
            None

        """
        sid_list = [chan.sid for chan in self._channels]
        timeout = ClientTimeout(total=60)
        async with ClientSession(timeout=timeout) as session:
            channels = await self._fetch_all_chan_details(session, sid_list)
            for channel, sid in zip(channels, sid_list):
                json_dict = await channel.json()
                self.get_channel(sid).load_skyq_detail_data(json_dict)


    def load_channel_data(self) -> None:
        """Load all channel data from the SkyQ REST Service.

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
        """Get a specific channel's data.

        This method returns a :class:`~pyskyq.channel.Channel` object when
        passed in a channel ``sid``.

        Args:
            sid: The sid (service id) of the channel

        Returns:
            :class:`~pyskyq.channel.Channel`: The channel if found.

        Raises:
            AttributeError: If the channel is not found.

        """
        sid = str(sid)
        for chan in self._channels:
            if chan.sid == sid:
                return chan
        raise AttributeError(f"Sid:{sid} not found.")

    def add_XMLTV_listing_schedule(self,
                                   *,
                                   listing: XMLTVListing,
                                   # schedule=None,
                                   ) -> None:
        """Add an  XML TV listing schedule to the EPG.

        This method will add a :class:`~pyskyq.xmltvlisting.XMLTVListing` to the EPG object,
        which will then takecare of downloading the XML TV listing data and updating the EPG
        object with it according to the passed download shedule.

        Args:
            listing (XMLTVListing): a :class:`~pyskyq.xmltvlisting.XMLTVListing` object to
                add to the EPG.

        Returns:
            None

        Raises:
            ValueError: Raised if this XMLTV listing is already added to the EPG.

        """
        if listing not in self._listings:
            self._listings.append(listing)
        else:
            raise ValueError('XMLTVListing already added.')
