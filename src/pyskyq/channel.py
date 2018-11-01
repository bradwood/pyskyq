"""This module implements the Channel class and associated factory functions."""
import copy
import json
import logging
from collections.abc import Hashable
from typing import Any, Dict
from xml.etree.ElementTree import Element

from yarl import URL

from .constants import CHANNEL_FIELD_MAP
from .constants import CHANNELSOURCES as CSRC

from .utils import skyq_json_decoder_hook

LOGGER = logging.getLogger(__name__)


class _ChannelJSONEncoder(json.JSONEncoder):
    """Encode Channel objects in JSON."""

    def default(self, obj):  # pylint: disable=arguments-differ,method-hidden,inconsistent-return-statements
        if isinstance(obj, Channel):
            type_ = '__channel__'
            chan_dict = obj._chan_dict # pylint: disable=protected-access
            sources = obj._sources  # pylint: disable=protected-access
            return {'__type__': type_,
                    'attributes': chan_dict,
                    'sources': sources
                    }
        if isinstance(obj, URL):
            return obj.human_repr()

        json.JSONEncoder.default(self, obj) # pragma: no cover


class Channel(Hashable):
    """This class holds channel data and methods for manipulating the channel.

    Channel data can come form a variety of sources, including the SkyQ box
    itself or from a remote XML TV feed.

    Warning:
        This class cannot be instantiated directly, but only via one of the factory methods.

        In order to be ``Hashable`` this class is **immutable**, and so its
        methods will return a new instance of the class with the effect of the
        method applied to returned class.

    Note:
        Attributes are dynamically set based on the data payload provided, so if
        the SkyQ box or XML TV feed is upgraded, new attributes *should*
        magically appear. Note that this also implies that not every channel has
        every field, e.g., the ``timeshifted`` and ``adult`` properties are only
        present if they are  ``True``. This Sky weirdness is managed by simply
        returing ``None`` if the attribute is not present, rather than raising a
        ``KeyError``.

    Note:
        Data from XML TV sources presents the following channel attributes.

    Attributes:
        xmltv_id (str): A hex string uniquely identifying this channel in the XML TV listing.
            It is needed to look up programme's on the channel.
        xmltv_icon_url (:py:class:`yarl.URL`): An internet URL to a graphic logo file.
        xmltv_display_name (str): The human-friendly name of the channel. Should be the same
            as ``name``.

    Note:
        The following attributes come from the SkyQ Box's various endpoints.

    Attributes:
        number (str): Human-friendly version of :attr:`c`.
        quality (str): Human-friendly version of :attr:`sf`.
        id (str): Human-friendly version of :attr:`sid`.
        name (str):Human-friendly version of :attr:`t`.
        desc (str): Human-friendly version of :attr:`upgradeMessage`.
        c (str): Channel number.
        dvbtriplet (str):  DVB Triplet (I have no idea what this is)
        schedule (bool): Is the channel "scheduled" or not?
        servicetype (str): Where is the channel coming from (e.g., ``DSAT``)
        sf (str): Quality of the channel (e.g., ``hd``, ``sd``, or ``au``)
        sg (int): No ideas what this is.
        sid (str): Channel id (aka ``sid``) in `str` form - the **primary key** for the channel.
        sk (int): Channel id (aka ``sid``) in `int` form.
        t (str): Channel name, eg, ``BBC One Lon``
        xsg (int): No idea what this is.
        timeshifted (bool): Is this a ``+1``-style channel?
        adult (bool): Is this an adult channel?
        upgradeMessage (str): A short description of the channel.
        isbroadcasting (boo): Is the channel broadcasting currently or not?

    """

    def __init__(self) -> None:
        """Raise exception to prevent this from being initatiated normally."""
        raise NotImplementedError('This class cannot be instantiated directly. ' +
                                  'Use a factory function to create an instance.')

    def __new__(cls, *args, **kwargs):
        """Initialise Channel Object."""
        blank_chan_dict = {
            'sid': None,
            'c': None,
            't': None,
            'xmltv_id': None,
        }
        # pylint: disable=attribute-defined-outside-init
        new_obj = super(Channel, cls).__new__(cls, *args, **kwargs)
        new_obj._chan_dict: Dict[str, Any] = blank_chan_dict
        new_obj._sources: CSRC = CSRC.no_source
        return new_obj

    def __getattr__(self, name: str) -> Any:
        """Handle attribute reads.

        Return ``None`` rather than a KeyError if the attriute not found.
        """
        if name in self._chan_dict.keys():
            return self._chan_dict[name]
        if name in CHANNEL_FIELD_MAP.keys():
            return self._chan_dict.get(CHANNEL_FIELD_MAP[name], None)
        return None


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

    def __hash__(self):
        """Return hash of this object."""
        # both sourced channel
        if (self._sources & CSRC.skyq_service_summary == CSRC.skyq_service_summary) and \
            (self._sources & CSRC.xml_tv == CSRC.xml_tv):
            assert self._chan_dict['t'] == self._chan_dict['xmltv_display_name']
            return hash(self._chan_dict['t'])

        # sky sourced channel
        if self._sources & CSRC.skyq_service_summary == CSRC.skyq_service_summary:
            return hash(self._chan_dict['t'])

        # xmltv sourced channel
        if self._sources & CSRC.xml_tv == CSRC.xml_tv:
            return hash(self._chan_dict['xmltv_display_name'])

        # empty channel
        return hash(CSRC.no_source)

    def __eq__(self, other):
        """Return True if self == other."""
        if not isinstance(other, Channel):
            return False
        return self._chan_dict == other._chan_dict and self._sources == other._sources # pylint: disable=protected-access


    def as_json(self) -> str:
        """Return a JSON string respenting this Channel."""
        return json.dumps(self, cls=_ChannelJSONEncoder, indent=4)

    @property
    def sources(self) -> CSRC:
        """Return the sources flag.

        Returns:
            CSRC: A flag of one or more
                :class:`~.constants.CHANNELSOURCES` ORed together to indicate
                which sources have been applied to this object.

        """
        return self._sources

    def load_skyq_summary_data(self,
                               chan_dict: Dict[str, Any]
                               ) -> 'Channel':
        """Load summary data from SkyQ box into a new Channel.

        Args:
            chan_dict (dict): A detail dict that is obtained from the
                ``as/services/`` endpoint.

        Returns:
            Channel: A new channel with the summary SkyQ data added.

        """
        # pylint: disable=attribute-defined-outside-init
        # pylint: disable=protected-access
        newchannel = Channel.__new__(Channel)
        newchannel._chan_dict = copy.deepcopy(self._chan_dict)
        newchannel._chan_dict.update(chan_dict)
        newchannel._sources = copy.copy(self._sources | CSRC.skyq_service_summary)
        return newchannel

    def load_skyq_detail_data(self, detail_dict: Dict[str, Any]) -> 'Channel':
        """Add additional properties obtained from the SkqQ box to a new object.

        Args:
            detail_dict (dict): A detail dict that is obtained from the
                ``as/services/details/<sid>`` endpoint.

        Returns:
            Channel: A new channel with the detailed SkyQ data added.

        """
        # pylint: disable=attribute-defined-outside-init
        # pylint: disable=protected-access
        newchannel = Channel.__new__(Channel)
        newchannel._chan_dict = copy.deepcopy(self._chan_dict)
        newchannel._chan_dict.update(detail_dict['details'])
        newchannel._sources = copy.copy(self._sources | CSRC.skyq_service_detail)
        return newchannel

    def load_xmltv_data(self,
                        xml_chan: Element,
                        base_url: URL = URL('http://www.xmltv.co.uk/'),
                        ) -> 'Channel':
        """Take an XML TV Channel element and load it into the channel's data structure.

        This method loads this object with data passed in from an XML TV channel element.

        Args:
            xml_chan (Element): A XML element of ``<channel>...</channel>`` tags.
            base_url (URL): A :py:class:`~yarl.URL` prefix which is used construct the full
                :attr:`~.channel.Channel.xmltv_icon_url` property.

        Returns:
            Channel: A new channel with the detailed XMLTV data added.

        """
        # pylint: disable=attribute-defined-outside-init
        # pylint: disable=protected-access

        newchannel = Channel.__new__(Channel)
        newchannel._chan_dict = copy.deepcopy(self._chan_dict)

        assert xml_chan.tag.lower() == 'channel'

        newchannel._chan_dict['xmltv_id'] = xml_chan.attrib['id']
        for child in xml_chan:
            if child.tag.lower() == 'icon':
                newchannel._chan_dict['xmltv_icon_url'] = base_url.join(URL(child.attrib['src']))
                continue
            if child.tag.lower() == 'display-name':
                newchannel._chan_dict['xmltv_display_name'] = child.text

        newchannel._sources = copy.copy(self._sources | CSRC.xml_tv)

        return newchannel

# pylint: disable=attribute-defined-outside-init
# pylint: disable=protected-access
def channel_from_json(json_) -> Channel:
    """Create a channel from JSON data.

    Args:
        str: A string of JSON data.

    Returns:
        Channel: A channel object.

    """
    chan = Channel.__new__(Channel)
    data = json.loads(json_, object_hook=skyq_json_decoder_hook)
    if not data.get('__type__') == '__channel__':
        raise ValueError('Incorrect type metadata in JSON payload.')
    chan._chan_dict = data['attributes']
    chan._sources = data['sources']
    return chan



def channel_from_skyq_service(skyq_chan: Dict[str, Any]) -> Channel:
    """Create a Channel object from a SkyQ Service summary payload.

    Args:
        skyq_chan (Dict[str, Any]): This dictionary is the payload that comes directly from the
            SkyQ's ``as/services/`` endpoint.

    Returns:
        Channel: A channel object with the  SkyQ summary data loaded.

    """
    chan = Channel.__new__(Channel)
    return chan.load_skyq_summary_data(skyq_chan)

def channel_from_xmltv_list(xml_chan: Element) -> Channel:
    """Create a Channel object from an XMLTV channel element.

    This function is a Channel factory. It will generate a Channel object given a XML
    channel element from an XML TV file.

    Args:
        xml_chan (Element): A XML element of ``<channel>...</channel>`` tags.

    Returns:
        Channel: A channel object with the XML TV data loaded.

    """
    chan = Channel.__new__(Channel)
    return chan.load_xmltv_data(xml_chan)

def merge_channels(chan_a: Channel,
                   chan_b: Channel,
                   ) -> Channel:
    """Merge two channels together and returns a new one with the data combined.

    Args:
        chan_a (Channel): First channel to merge.
        chan_b (Channel): Second channel to merge.

    Returns:
        Channel: Merged channel, although see warning for gotchas.

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
    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=protected-access

    new_chan = Channel.__new__(Channel)

    new_chan._chan_dict = {**chan_a._chan_dict, **chan_b._chan_dict}

    if chan_a.id is not None and chan_b.id is None:
        new_chan._chan_dict['sid'] = chan_a.id

    if chan_b.id is not None and chan_a.id is None:
        new_chan._chan_dict['sid'] = chan_b.id


    if chan_a.c is not None and chan_b.c is None:
        new_chan._chan_dict['c'] = chan_a.c

    if chan_b.c is not None and chan_a.c is None:
        new_chan._chan_dict['c'] = chan_b.c


    if chan_a.t is not None and chan_b.t is None:
        new_chan._chan_dict['t'] = chan_a.t

    if chan_b.t is not None and chan_a.t is None:
        new_chan._chan_dict['t'] = chan_b.t


    if chan_a.xmltv_id is not None and chan_b.xmltv_id is None:
        new_chan._chan_dict['xmltv_id'] = chan_a.xmltv_id

    if chan_b.xmltv_id is not None and chan_a.xmltv_id is None:
        new_chan._chan_dict['xmltv_id'] = chan_b.xmltv_id

    new_chan._sources = chan_a._sources | chan_b._sources
    return new_chan
