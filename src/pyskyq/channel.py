"""This module implements the Channel class and associated factory functions."""
import logging
from typing import Dict, Any
from enum import IntEnum

from pyskyq.constants import CHANNEL_FIELD_MAP

LOGGER = logging.getLogger(__name__)


class CSRC(IntEnum):
    """Enumeration of Channel Sources."""
    no_source = 0
    skyq_service = 1
    skyq_service_detail = 2
    xml_tv_summary = 4
    xml_tv_detail = 8

class Channel:
    """This class holds channel data and methods for manipulating the channel.

    Channel data can come form a variety of sources, including the SkyQ box itself (via)
    a number of endppints, or from a remote XML TV feed.

    The attributes are presented as read-only on the object.

    For SkyQ-Sourced Data
    ---------------------
    It will also dynamically
    set attributes based on the payload obtained from the API, which itself could vary
    from one channel to another. For example, channel's which are '+1' all carry the
    ``timeshifted`` property whereas regular channels do not.


    In order to present a more human-friendly API the
    :const:`~pyskyq.constants.CHANNEL_FIELD_MAP` dictionary is used to provide access to
    properties using more friendly names.

    For XMLTV-sourced Data
    ----------------------
    TBC

    Note:
        These channel attributes could change at any time with a box upgrade. The API will
        attempt to adapt to ensure the new fields are presented.

    Attributes:
        c (str): Channel number.
        dvbtriplet (str):  DVB Triplet (I have no idea what this is)
        schedule (bool): Is the channel "scheduled" or not?
        servicetype (str): Where is the channel coming from (e.g., ``DSAT``)
        sf (str): Quality of the channel (e.g., ``hd``)
        sg (int): No ideas what this is.
        sid (str): Channel id (aka ``sid``) in `str` form - the **primary key** for the channel.
        sk (int): Channel id (aka ``sid``) in `str` form.
        t (str): Channel name, eg, ``BBC One Lon``
        xsg (int): No idea what this is.
        timeshifted (bool): Is this a ``+1``-style channel?
        upgradeMessage (str): A short description of the channel.
        isbroadcasting (boo): Is the channel broadcasting currently or not?

    Note:
        The below are the human-friendly mappings of some of Sky's terser-named
        attributes.

    Attributes:
        number (str): Human-friendly version of :attr:`c`.
        quality (str): Human-friendly version of :attr:`sf`.
        id (str): Human-friendly version of :attr:`sid`.
        name (str):Human-friendly version of :attr:`t`.
        desc (str): Human-friendly version of :attr:`upgradeMessage`.

    """

    def __init__(self,) -> None:
        """Initialise Channel Object."""
        self._chan_dict: Dict[str, Any] = {}
        self._sources: CSRC = CSRC.no_source

    def __getattr__(self, name: str) -> Any:
        """Handle attribute reads."""
        if name in self._chan_dict.keys():
            return self._chan_dict[name]
        if name in CHANNEL_FIELD_MAP.keys():
            return self._chan_dict.get(CHANNEL_FIELD_MAP[name], None)
        raise KeyError(name)


    def __setattr__(self, name: str, value: Any) -> None:
        """Handle attribute assignments."""
        if not name.startswith('_'):
            raise AttributeError(f"Can't modify {name}")
        else:
            super().__setattr__(name, value)

    def __repr__(self):
        """Give human-friendly representation."""
        return f'<Channel: sources={self._sources}>'

    @property
    def sources(self):
        return self._sources

    def load_skyq_summary_data(self,
                               chan_dict: Dict[str, Any],
                               ) -> None:
        """Load summary data from SkyQ box into the Channel"""
        self._chan_dict.update(chan_dict)
        self._sources = self._sources | CSRC.skyq_service # type: ignore
        LOGGER.debug(f"Channel SkyQ Summary Data Loaded  with {chan_dict}.")
        LOGGER.debug(f"Channel sources = {self._sources}.")


    def add_detail_data(self, detail_dict: Dict[str, Any]) -> None:
        """Add additional properties obtained from the detail endpoint to the object.

        Args:
            detail_dict (dict): A detail dict that is passed in directly from the
                ``as/services/details/<sid>`` endpoint.

        Returns:
            None

        """
        self._chan_dict.update(detail_dict['details'])

def channel_from_skyq_service(skyq_chan: Dict[str, Any]) -> Channel:
    """Create a channel from a SkyQ Service payload.

    Args:
        chan_dict (dict): This dictionary is the payload that comes directly from the
            SkyQ's ``as/services/`` endpoint.

    Returns:
        Channel: Will the SkyQ Data loaded.

    """
    chan = Channel()
    chan.load_skyq_summary_data(skyq_chan)
    return chan

