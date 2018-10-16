"""This module implements the EPG class."""

import asyncio
import logging
from typing import List, Optional, Tuple, Union, Any
import time

from aiohttp import ClientSession, ClientTimeout  # type: ignore
from croniter.croniter import croniter
from fuzzywuzzy import process

from dataclasses import dataclass
from .channel import Channel, channel_from_skyq_service, merge_channels
from .constants import QUALITY as Q
from .constants import (REST_PORT, REST_SERVICE_DETAIL_URL_PREFIX,
                              REST_SERVICES_URL)
from .cronthread import CronThread
from .asyncthread import AsyncThread
from .xmltvlisting import XMLTVListing

LOGGER = logging.getLogger(__name__)

at = AsyncThread()

class EPG:
    """The top-level class for all EPG data and functions.

    EPG implements access to any data and operations related to the SkyQ box's
    Electronic Programme Guide through a REST endpoint exposed on the box.
    Specifically, it fetches both summary and detail channel information from
    two different endpoints from the box and aggregates this data into a list of
    :class:`~.channel.Channel` objects.

    This channel data is then *augmented* with data from www.xmltv.co.uk which provides
    an XML file which follows the ``xmltv`` DTD.

    It also uses the ``xmltv`` file to load **listings** data to enable the querying of
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
        self._jobs: list = []

        #self._loop = loop if loop else asyncio.get_event_loop()

        #assert not self._loop.is_closed()

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

    async def _load_channels_from_skyq(self) -> None:
        """Load channel data into channel property.

        This method fetches the channel list from ``/as/services`` endpoint and loads
        :attr:`~.epg.EPG._channels`

        Returns:
            None

        """
        url = f'http://{self.host}:{self.rest_port}{REST_SERVICES_URL}'
        LOGGER.debug(f'Fetching channel list from {url}')

        timeout = ClientTimeout(total=60)
        async with ClientSession(timeout=timeout) as session:
            chan_payload_json = await session.get(url)
            chan_payload = await chan_payload_json.json()

            for single_channel_payload in chan_payload['services']:
                channel = channel_from_skyq_service(single_channel_payload)
                sid = channel.sid
                detail_url =f'http://{self.host}:{self.rest_port}{REST_SERVICE_DETAIL_URL_PREFIX}{sid}'
                detail_payload_json = await session.get(detail_url)
                detail_payload = await detail_payload_json.json()
                detailed_channel = channel.load_skyq_detail_data(detail_payload)
                self._channels.append(detailed_channel)


    def load_skyq_channel_data(self) -> None:
        """Load all channel data from the SkyQ REST Service.

        This method loads all channel data from the SkyQ box into the
        :class:`~.epg.EPG` object.

        Warning:
            This method is non-blocking. You may need to wait a few seconds before
            the channels are all fully loaded..

        Returns:
            None

        """
        asyncio.run_coroutine_threadsafe(
            self._load_channels_from_skyq(),
            at.loop
        )

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
            raise ValueError(f"No channels loaded.")

        for chan in self._channels:
            if chan.sid == sid:
                return chan
        raise ValueError(f"Sid:{sid} not found.")


    def get_channel(self,
                    name: str,
                    fuzzy_match: bool = True,
                    include_timeshift: bool = True,
                    quality_flag: Optional[Q] = None,
                    limit: int = 1
                    ) -> List[Channel]:
        """Get a channel or list of channels based on various input.

        This method returns a :class:`~.channel.Channel` object or
        a list of them based on the various parameters passed.

        Args:
            name (str): The name of the channel being searched for
                (wildcards are not supported).
            fuzzy_match (bool): Use exact or fuzzy string matching.
            include_timeshift (bool): Include ``+1`` channels.
            quality_flag (Q): One of :class:`~.constants.QUALITY`
                `None` means any.
            limit (int): Maximum (not exact) number of matches to return.

        Returns:
            List[Channel]: Returns a list of matches ordered with closest
                match first.

        Raises:
            ValueError: If a match is not found, the channel list is
                empty or a bad limit is passed.

        """
        if limit < 1:
            raise ValueError('Limit must be 1 or higher.')
        if not self._channels:
            raise ValueError(f"No channels loaded.")

        if not include_timeshift:
            channels = [chan for chan in self._channels if not chan.timeshifted]
        if quality_flag:
            channels = [chan for chan in channels if chan.quality == quality_flag]

        choices = [chan.name for chan in channels]
        matches = process.extract(name, choices, limit=limit) # returns a list of tuples (name, score)
        matched_names = [item[0] for item in matches]
        return [chan for chan in channels if chan.name in matched_names]

    @dataclass
    class _CronJob:
        listing: XMLTVListing
        schedule: str
        thread: Optional[CronThread] = None

    def delete_XMLTV_listing_cronjob(self,
                                     listing: XMLTVListing,
                                     ) -> None:
        """Delete an XML TV listing cronjob from the EPG."""
        try:
            cronjob = [job for job in self._jobs if job.listing == listing][0]
        except ValueError as ve:
            raise ValueError('No cronjob found for the passed XMLTVListing.') from ve

        cronjob.thread.stop()
        del self._jobs[cronjob]


    def add_XMLTV_listing_cronjob(self,
                                  listing: XMLTVListing,
                                  cronspec: str,
                                  *,
                                  run_now: bool = False
                                  ) -> None:
        """Add an XML TV listing cronjob to the EPG.

        This method will add a :class:`~.xmltvlisting.XMLTVListing` to the EPG object
        and immediately schedule it as a cronjob.

        The processing of the XMLTV download and load into memory will be immedately triggered
        if ``run_now`` is ``True``.

        Args:
            listing (XMLTVListing): a :class:`~.xmltvlisting.XMLTVListing` object to
                add to the EPG.
            cronspec (str): cronspec string, e.g.: ``0 9,10 * * * mon,fri``.
            run_now (bool): If ``True`` **runs** the XMLTV job immediately in addition to
                scheduling the cronjob.

        Returns:
            None

        Raises:
            ValueError: Raised if this XMLTV listing is already added to the EPG, the
                cronspec passes is invalid, or the channel list is empty.

        """
        if not self._channels:
            raise ValueError(f"No channels loaded.")

        if listing not in [job.listing for job in self._jobs]:
            if cronspec and croniter.is_valid(cronspec):
                cron_t = CronThread()
                cron_t.crontab(cronspec,
                               func=self.download_and_apply_XMLTVListing(listing),
                               start=True
                               )
                cronjob = self._CronJob(listing=listing, schedule=cronspec, thread=cron_t)
                self._jobs.append(cronjob)
            else:
                raise ValueError('Bad cronspec passed.')
        else:
            raise ValueError('XMLTVListing already added.')

        if run_now:
            # no thread required, just run it async in this thread.
            asyncio.run(self.download_and_apply_XMLTVListing(listing))


    async def download_and_apply_XMLTVListing(self, listing: XMLTVListing) -> None:
        """Download a listing and merge its data into the EPG channels data structure.

        This method is intended primarily for use in EPG cronjobs. If you wish to manually
        download and apply an XMLTVListing, you might prefer to call
        :meth:`.xmltvlisting.XMLTVListing.fetch` manually first, followed by
        :meth:`apply_XMLTVListing`.

        Args:
            listing (XMLTVListing): a :class:`~.xmltvlisting.XMLTVListing` object to
                download and apply to the EPG.

        Returns:
            None

        Raises:
            ValueError: Raised if the channel list is empty.

        """
        if not self._channels:
            raise ValueError(f"No channels loaded.")

        await listing.fetch()  # do the download
        self.apply_XMLTVListing(listing)


    def apply_XMLTVListing(self, listing: XMLTVListing) -> None:
        """Merge listing data into the EPG channels data structure.

        Args:
            listing(XMLTVListing): a: class: `~.xmltvlisting.XMLTVListing` object to
            merge to the EPG.

        Returns:
            None

        Raises:
            ValueError: Raised if the channel list is empty.

        """
        if not self._channels:
            raise ValueError(f"No channels loaded.")

        # TODO: optimise this, maybe with some kind of sorted list?
        for skyq_channel in self._channels:
            for xmltv_channel in listing.parse_channels():  # load the channels
                if skyq_channel.name.lower() == xmltv_channel.xmltv_display_name.lower():
                    skyq_channel = merge_channels(skyq_channel, xmltv_channel)

    def get_cronjobs(self) -> List[Tuple[XMLTVListing, str]]:
        """Return currently loaded XML TV Listings and associated cronjobs.

        This returns a list of tuples containing
        :class:`~.xmltvlisting.XMLTVListing` objects and associated cronspec
        strings.

        Returns:
            List[Tuple[XMLTVListing, str]]: Returns a list of tuples where each
                tuple is as follows::

                    (XMLTVListing, cronspec)

                where:

                - listing is an :class:`~.xmltvlisting.XMLTVListing` object
                - cronspec is a string like ``0 9,10 * * * mon,fri``

        """
        return [(j.listing, j.cronspec) for j in self._jobs]
