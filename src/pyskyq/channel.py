"""This module implements the Channel class and associated factory functions."""
import logging
from typing import Any, Dict
from xml.etree.ElementTree import Element

from yarl import URL

from pyskyq.constants import CHANNEL_FIELD_MAP, CSRC

LOGGER = logging.getLogger(__name__)


class Channel:
    """This class holds channel data and methods for manipulating the channel.

    Channel data can come form a variety of sources, including the SkyQ box itself (via)
    a number of endppints, or from a remote XML TV feed.

    The attributes are presented as read-only on the object.

    For SkyQ-sourced Data
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
        blank_chan_dict = {
            'sid': None,
            'c': None,
            't': None,
            'xmltv_id': None,
        }
        self._chan_dict: Dict[str, Any] = blank_chan_dict
        self._sources: CSRC = CSRC.no_source # type: ignore

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
        return f'<Channel: sources={self._sources}, id={self.id}, ' + \
        f'xmltv_id={self.xmltv_id}, number={self.number}, name={self.name}>'

    @property
    def sources(self):
        """Return the sources flag."""
        return self._sources

    def load_skyq_summary_data(self,
                               chan_dict: Dict[str, Any],
                               ) -> None:
        """Load summary data from SkyQ box into the Channel"""
        self._chan_dict.update(chan_dict)
        self._sources = self._sources | CSRC.skyq_service_summary # type: ignore
        LOGGER.debug(f"Channel SkyQ Summary Data Loaded  with {chan_dict}.")
        LOGGER.debug(f"Channel sources = {self._sources}.")

    def load_skyq_detail_data(self, detail_dict: Dict[str, Any]) -> None:
        """Add additional properties obtained from the SkqQ detail endpoint to the object.

        Args:
            detail_dict (dict): A detail dict that is passed in directly from the
                ``as/services/details/<sid>`` endpoint.

        Returns:
            None

        """
        self._chan_dict.update(detail_dict['details'])
        self._sources = self.sources | CSRC.skyq_service_detail

    def load_xmltv_data(self,
                        xml_chan: Element,
                        base_url: URL = URL('http://www.xmltv.co.uk/'),
                        ) -> None:
        """Take an XML TV Channel element and load it into the channel's data structure."""
        assert xml_chan.tag.lower() == 'channel'
        self._chan_dict['xmltv_id'] = xml_chan.attrib['id']
        for child in xml_chan:
            if child.tag.lower() == 'icon':
                self._chan_dict['xmltv_icon_url'] = base_url.join(URL(child.attrib['src']))
                continue
            if child.tag.lower() == 'display-name':
                self._chan_dict['xmltv_display_name'] = child.text
        self._sources = self.sources | CSRC.xml_tv


def channel_from_skyq_service(skyq_chan: Dict[str, Any]) -> Channel:
    """Create a Channel object from a SkyQ Service summary payload.

    Args:
        chan_dict (dict): This dictionary is the payload that comes directly from the
            SkyQ's ``as/services/`` endpoint.

    Returns:
        Channel: With SkyQ summary data loaded.

    """
    chan = Channel()
    chan.load_skyq_summary_data(skyq_chan)
    return chan

def channel_from_xmltv_list(xml_chan: Element) -> Channel:
    """Create a Channel object from an XMLTV channel element."""

    chan = Channel()
    chan.load_xmltv_data(xml_chan)
    return chan

def merge_channels(chan_a: Channel,
                   chan_b: Channel,
                   ) -> Channel:
    """Merge two channels together and returns a new one with the data combined.

    Warning:
        No checks are made to ensure these two channels represent the same real channel.
        You should check each first before merging, perhaps by matching on the ``name``
        or ``xmltv_display_name``.

        If there are any key clashes ``chan_b``'s keys will overrite ``chan_a``'s with
        the exception of the following:
            - if the ``sid`` or ``id`` attribute is ``None`` on one and not the other, the other
              will override regardless of the passed order.
            - if the ``c`` or ``number`` attribute is ``None`` on one and not the other, the other
              will override regardless of the passed order.
            - if the ``t`` or ``name`` attribute is ``None`` on one and not the other, the other
              will override regardless of the passed order.
            - if the ``xmltv_id`` attribute is ``None`` one one and not the other, the other will
              override, regardless of the passed order.

    """
    new_chan = Channel()
    new_chan._chan_dict = {**chan_a._chan_dict, **chan_b._chan_dict}  # pylint: disable=protected-access

    if chan_a.id is not None and chan_b.id is None:
        new_chan._chan_dict['sid'] = chan_a.id  # pylint: disable=protected-access

    if chan_b.id is not None and chan_a.id is None:
        new_chan._chan_dict['sid'] = chan_b.id  # pylint: disable=protected-access


    if chan_a.c is not None and chan_b.c is None:
        new_chan._chan_dict['c'] = chan_a.c  # pylint: disable=protected-access

    if chan_b.c is not None and chan_a.c is None:
        new_chan._chan_dict['c'] = chan_b.c  # pylint: disable=protected-access


    if chan_a.t is not None and chan_b.t is None:
        new_chan._chan_dict['t'] = chan_a.t  # pylint: disable=protected-access

    if chan_b.t is not None and chan_a.t is None:
        new_chan._chan_dict['t'] = chan_b.t  # pylint: disable=protected-access


    if chan_a.xmltv_id is not None and chan_b.xmltv_id is None:
        new_chan._chan_dict['xmltv_id'] = chan_a.xmltv_id  # pylint: disable=protected-access

    if chan_b.xmltv_id is not None and chan_a.xmltv_id is None:
        new_chan._chan_dict['sxmltv_id'] = chan_b.xmltv_id  # pylint: disable=protected-access

    new_chan._sources = chan_a._sources | chan_b._sources  # pylint: disable=protected-access
    return new_chan
