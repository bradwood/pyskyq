# pylint: skip-file
import pytest
import json
from pyskyq.channel import Channel, channel_from_skyq_service, channel_from_xmltv_list, merge_channels
from pyskyq.constants import CHANNELSOURCES
import xml.etree.ElementTree as ET
from yarl import URL
from .mock_constants import SERVICE_DETAIL_1, SERVICE_SUMMARY_MOCK, XML_CHANNEL_1


def test_blank_channel():

    with pytest.raises(NotImplementedError,
                       match='This class cannot be instantiated directly. ' +
                       'Use a factory function to create an instance.'
                       ):
        blank_chan = Channel()

    blank_chan = Channel.__new__(Channel)

    assert blank_chan.sources == CHANNELSOURCES.no_source
    assert blank_chan.__repr__() == '<Channel: sources=CHANNELSOURCES.no_source, id=None, xmltv_id=None, number=None, name=None>'

    with pytest.raises(AttributeError, match="Can't modify sid"):
        blank_chan.sid = 232

    with pytest.raises(KeyError, match="blah"):
        blank_chan.blah

    with pytest.raises(KeyError, match="isbroadcasting"):
        blank_chan.isbroadcasting

def test_channel_from_skyq_service():

    chan = channel_from_skyq_service(json.loads(SERVICE_SUMMARY_MOCK)['services'][0])

    assert isinstance(chan, Channel)
    assert chan.sources == CHANNELSOURCES.skyq_service_summary
    assert chan.__repr__() == '<Channel: sources=CHANNELSOURCES.skyq_service_summary, id=2002, xmltv_id=None, number=101, name=BBC One Lon>'
    assert chan.c == "101"
    assert chan.t == "BBC One Lon"
    assert chan.name == "BBC One Lon"

    with pytest.raises(AttributeError, match="Can't modify sid"):
        chan.sid = 232

    with pytest.raises(KeyError, match="blah"):
        chan.blah

    with pytest.raises(KeyError, match="isbroadcasting"):
        chan.isbroadcasting

    chan = chan.load_skyq_detail_data(json.loads(SERVICE_DETAIL_1))

    assert chan.isbroadcasting
    assert chan.sources == CHANNELSOURCES.skyq_service_summary | CHANNELSOURCES.skyq_service_detail
    assert chan.__repr__() == '<Channel: sources=CHANNELSOURCES.skyq_service_detail|skyq_service_summary, id=2002, xmltv_id=None, number=101, name=BBC One Lon>'

    assert chan.upgradeMessage == "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england."
    assert chan.desc == "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england."


def test_channel_from_xmltv_data():

    chan = channel_from_xmltv_list(ET.XML(XML_CHANNEL_1))

    assert isinstance(chan, Channel)
    assert chan.sources == CHANNELSOURCES.xml_tv
    assert chan.__repr__() == '<Channel: sources=CHANNELSOURCES.xml_tv, id=None, xmltv_id=015ac32387fbc90e1e920d780d43787c, number=None, name=None>'
    assert chan.xmltv_id == "015ac32387fbc90e1e920d780d43787c"
    assert isinstance(chan.xmltv_icon_url, URL)
    assert chan.xmltv_icon_url.human_repr() == "http://www.xmltv.co.uk/images/channels/015ac32387fbc90e1e920d780d43787c.png"
    assert chan.xmltv_display_name == "Zee Cinema"


def test_channel_from_both_sources():
    chan_x = channel_from_xmltv_list(ET.XML(XML_CHANNEL_1))
    chan_q = channel_from_skyq_service(json.loads(SERVICE_SUMMARY_MOCK)['services'][0])

    # first way round
    chan = merge_channels(chan_q, chan_x) # note, chan_x overwrites chan_q

    assert isinstance(chan, Channel)
    assert chan.sources == CHANNELSOURCES.xml_tv | CHANNELSOURCES.skyq_service_summary
    assert chan.__repr__() == '<Channel: sources=CHANNELSOURCES.xml_tv|skyq_service_summary, id=2002, xmltv_id=015ac32387fbc90e1e920d780d43787c, number=101, name=BBC One Lon>'
    assert chan.c == "101"
    assert chan.t == "BBC One Lon"
    assert chan.name == "BBC One Lon"
    assert chan.xmltv_id == "015ac32387fbc90e1e920d780d43787c"
    assert isinstance(chan.xmltv_icon_url, URL)
    assert chan.xmltv_icon_url.human_repr() == "http://www.xmltv.co.uk/images/channels/015ac32387fbc90e1e920d780d43787c.png"
    assert chan.xmltv_display_name == "Zee Cinema"

    # other way round
    chan = merge_channels(chan_x, chan_q)  # note, chan_q overwrites chan_x

    assert isinstance(chan, Channel)
    assert chan.sources == CHANNELSOURCES.xml_tv | CHANNELSOURCES.skyq_service_summary
    assert chan.__repr__() == '<Channel: sources=CHANNELSOURCES.xml_tv|skyq_service_summary, id=2002, xmltv_id=015ac32387fbc90e1e920d780d43787c, number=101, name=BBC One Lon>'
    assert chan.c == "101"
    assert chan.t == "BBC One Lon"
    assert chan.name == "BBC One Lon"
    assert chan.xmltv_id == "015ac32387fbc90e1e920d780d43787c"
    assert isinstance(chan.xmltv_icon_url, URL)
    assert chan.xmltv_icon_url.human_repr() == "http://www.xmltv.co.uk/images/channels/015ac32387fbc90e1e920d780d43787c.png"
    assert chan.xmltv_display_name == "Zee Cinema"
