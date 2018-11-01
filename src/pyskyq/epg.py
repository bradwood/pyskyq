"""This module implements the EPG class."""

import json
import logging
from typing import Any

import asks
import trio

# from .asyncthread import AsyncThread
from .channel import (Channel, _ChannelJSONEncoder, channel_from_json,
                      channel_from_skyq_service, merge_channels)
from .constants import (REST_PORT, REST_SERVICE_DETAIL_URL_PREFIX,
                        REST_SERVICES_URL)
from .xmltvlisting import XMLTVListing

LOGGER = logging.getLogger(__name__)

asks.init('trio')

class EPG:
    """The top-level class for all EPG data and functions.

    EPG implements access to any data and operations related to the SkyQ box's
    Electronic Programme Guide through a REST endpoint exposed on the box.
    Specifically, it fetches both summary and detail channel information from
    two different endpoints from the box and aggregates this data into a list of
    :class:`~.channel.Channel` objects.

    This channel data can then be *augmented* with data from an XMLTV feed site
    like http://www.xmltv.co.uk/ which provides an XML file which follows the ``xmltv``
    DTD.

    It also uses the ``xmltv`` file to load **listings** data to enable the
    querying of programmes that are scheduled on the channels.

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
        LOGGER.debug(f"Initialised EPG object using SkyQ box={self.host}")

    def __repr__(self):
        """Print a human-friendly representation of this object."""
        return f"<EPG: host={self.host}, rest_port={self.rest_port}, " + \
            f"len(_channels)={len(self._channels)}, len(_xmltv_urls)={len(self._channels)}>"

    def channels_loaded(self) -> bool:
        """Return whether channels have been loaded.

        Returns:
            bool: ``True`` if channels have been loaded.

        """
        return bool(self._channels)

    async def load_skyq_channel_data(self) -> None:
        """Load channel data into channel property.

        This method fetches the channel list from ``/as/services`` endpoint and
        loads the fetched channels into this ``EPG`` object. It then
        concurrently fetches each channel's detail info from
        ``/as/services/details/<sid>`` and adds that to the channels.

        Returns:
            None

        """
        async def _load_chan_detail(detail_url: str, channel: Channel) -> None:
            """Nursery async function to fetch the details of each channel."""
            LOGGER.debug(f'Fetching channel details from {detail_url}')
            detail_payload_json = await sess.get(detail_url)
            LOGGER.debug(f'Got channel details from {detail_url}')
            detail_payload = detail_payload_json.json()
            LOGGER.debug(f'Parsed JSON from {detail_url}')
            detailed_channel = channel.load_skyq_detail_data(detail_payload)
            LOGGER.debug(f'Merged {detail_url} into {channel}...')
            LOGGER.debug(f'...resulting in  {detailed_channel}')
            self._channels.append(detailed_channel)
            LOGGER.debug(f'Added {detailed_channel} to EPG')

        url = f'http://{self.host}:{self.rest_port}{REST_SERVICES_URL}'
        LOGGER.debug(f'Fetching channel list from {url}')
        sess = asks.Session(connections=50)
        LOGGER.debug(f'About to fetch channel list from sky box.')
        chan_payload_json = await sess.get(url)
        LOGGER.debug(f'Got channel list from sky box.')
        chan_payload = chan_payload_json.json()
        LOGGER.debug(f'Parsed channel list JSON payload.')

        with trio.move_on_after(90): # 90 sec timeout  #TODO parametrise this.
            async with trio.open_nursery() as nursery:
                LOGGER.debug('Started nursery to collect channel details.')
                for single_channel_payload in chan_payload['services']:
                    LOGGER.debug(f'Processing {single_channel_payload}')
                    channel = channel_from_skyq_service(single_channel_payload)
                    sid = channel.sid
                    detail_url = f'http://{self.host}:{self.rest_port}' + \
                        f'{REST_SERVICE_DETAIL_URL_PREFIX}{sid}'
                    nursery.start_soon(_load_chan_detail, detail_url, channel)


    def as_json(self) -> str:
        """Return the channel and programme data as JSON.

        Returns:
            str: A JSON representation of this EPG.

        """
        return json.dumps(self._channels, cls=_ChannelJSONEncoder, indent=4)

    def from_json(self, json_: str) -> None:
        """Load channel and programme data from JSON.

        Args:
            json_(str): A string of JSON text.

        """
        payload = json.loads(json_)
        new_chans: list = []

        for item in payload:
            if item['__type__'] == "__channel__":
                new_chans.append(channel_from_json(json.dumps(item)))
            # TODO: add jobs, programmes, etc
        self._channels = new_chans



    def get_channel_by_sid(self,
                           sid: Any
                           ) -> Channel:
        """Get channel data by SkyQ service id.

        This method returns a :class:`~.channel.Channel` object when
        passed in a channel ``sid``.

        Args:
            sid: The SkyQ service id of the channel
        Returns:
            :class:`~.channel.Channel`: The channel if found.

        Raises:
            ValueError: If the channel is not found or the channel
                list is empty.

        """
        sid = str(sid)
        if not self.channels_loaded():
            raise ValueError("No channels loaded.")

        for chan in self._channels:
            if chan.sid == sid:
                return chan
        raise ValueError(f"Sid:{sid} not found.")


    def apply_XMLTVListing(self, listing: XMLTVListing) -> None:
        """Merge listing data into the EPG channels data structure by channel name.

        This method takes an XMLTV listing object and, for every channel already loaded
        in the EPG it augments that channel's data with the data obtained from the XMLTV
        listing. This could provide additional descriptive channel data, the URL to the
        channel's logo and similar extra stuff.

        Args:
            listing(XMLTVListing): a :class:`~.xmltvlisting.XMLTVListing` object to
                merge to the EPG.

        Returns:
            None

        Raises:
            ValueError: Raised if the XMLTVListing file cannot be found.

        """
        if not listing.downloaded:
            raise ValueError("No XMLTVListing file found.")

        for xmltv_channel in listing.parse_channels():
            sky_channel_names = [chan.name.lower() for chan in self._channels]
            if xmltv_channel.xmltv_display_name.lower() in sky_channel_names:
                idx = sky_channel_names.index(xmltv_channel.xmltv_display_name.lower())
                new_chan = merge_channels(self._channels[idx], xmltv_channel)
                LOGGER.debug(f'New channel:{new_chan}.')
                self._channels.append(new_chan)
                LOGGER.debug(f'Replaced {self._channels[idx]} with {new_chan} in EPG.')
                del self._channels[idx]
