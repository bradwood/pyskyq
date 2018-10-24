# pylint: skip-file
import json
import xml.etree.ElementTree as ET

import pytest
from yarl import URL

from pyskyq import (CHANNELSOURCES, Channel, channel_from_skyq_service,
                    channel_from_xmltv_list, merge_channels, channel_from_json)

from .mock_constants import (MERGED_CHAN_JSON, SERVICE_DETAIL_1,
                             SERVICE_SUMMARY_MOCK, SKYQ_CHAN_JSON,
                             XML_CHAN_JSON, XML_CHANNEL_1, BAD_JSON)


def test_hashable_channels():

    blank_chan = Channel.__new__(Channel)
    another_blank_chan = Channel.__new__(Channel)

    # all blank channels are the same
    assert hash(blank_chan) == hash(another_blank_chan)

    skyq_chan1 = channel_from_skyq_service(json.loads(SERVICE_SUMMARY_MOCK)['services'][0])
    skyq_chan2 = channel_from_skyq_service(json.loads(SERVICE_SUMMARY_MOCK)['services'][0])

    # all sky channels from the same source are the same...
    assert hash(skyq_chan1) == hash(skyq_chan2)
    # but different to blank ones
    assert hash(blank_chan) != hash(skyq_chan1)

    skyq_chan1_detail = skyq_chan1.load_skyq_detail_data(json.loads(SERVICE_DETAIL_1))

    # a sky channel with detail is the same as one with only summary data.
    assert hash(skyq_chan1) == hash(skyq_chan1_detail)

    xml_chan = channel_from_xmltv_list(ET.XML(XML_CHANNEL_1))

    # channels with the same name, but diffenent sources are the same.
    assert skyq_chan1.name == xml_chan.xmltv_display_name
    assert hash(skyq_chan1) == hash(xml_chan)
    assert hash(skyq_chan1_detail) == hash(xml_chan)

    # a merging of 2 channels with the same name is the same as both of the sources.
    assert hash(merge_channels(skyq_chan1, xml_chan)) == \
        hash(skyq_chan1)

    assert hash(merge_channels(skyq_chan1_detail, xml_chan)) == \
        hash(skyq_chan1)

    assert hash(merge_channels(skyq_chan1, xml_chan)) == \
        hash(xml_chan)

    assert hash(merge_channels(skyq_chan1_detail, xml_chan)) == \
        hash(xml_chan)



def test_blank_channel():

    with pytest.raises(NotImplementedError,
                       match='This class cannot be instantiated directly. ' +
                       'Use a factory function to create an instance.'
                       ):
        blank_chan = Channel()

    blank_chan = Channel.__new__(Channel)


    assert blank_chan.sources == CHANNELSOURCES.no_source
    assert blank_chan.__repr__() == f'<Channel: sources={CHANNELSOURCES.no_source}, id=None, xmltv_id=None, number=None, name=None>'

    with pytest.raises(AttributeError, match="Can't modify sid"):
        blank_chan.sid = 232

    assert blank_chan.blah is None

    assert blank_chan.isbroadcasting is None

def test_channel_from_skyq_service():

    chan = channel_from_skyq_service(json.loads(SERVICE_SUMMARY_MOCK)['services'][0])

    assert isinstance(chan, Channel)
    assert chan.sources == CHANNELSOURCES.skyq_service_summary
    assert chan.__repr__() == f'<Channel: sources={CHANNELSOURCES.skyq_service_summary}, id=2002, xmltv_id=None, number=101, name=BBC One Lon>'
    assert chan.c == "101"
    assert chan.t == "BBC One Lon"
    assert chan.name == "BBC One Lon"

    with pytest.raises(AttributeError, match="Can't modify sid"):
        chan.sid = 232

    assert chan.isbroadcasting is None

    chan = chan.load_skyq_detail_data(json.loads(SERVICE_DETAIL_1))

    assert chan.isbroadcasting
    assert chan.sources == CHANNELSOURCES.skyq_service_summary | CHANNELSOURCES.skyq_service_detail
    assert chan.__repr__() == f'<Channel: sources={CHANNELSOURCES.skyq_service_detail | CHANNELSOURCES.skyq_service_summary}, id=2002, xmltv_id=None, number=101, name=BBC One Lon>'

    assert chan.upgradeMessage == "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england."
    assert chan.desc == "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england."


def test_channel_from_xmltv_data():

    chan = channel_from_xmltv_list(ET.XML(XML_CHANNEL_1))

    assert isinstance(chan, Channel)
    assert chan.sources == CHANNELSOURCES.xml_tv
    assert chan.__repr__() == f'<Channel: sources={CHANNELSOURCES.xml_tv}, id=None, xmltv_id=f3932e75f691561adbe3b609369e487b, number=None, name=None>'
    assert chan.xmltv_id == "f3932e75f691561adbe3b609369e487b"
    assert isinstance(chan.xmltv_icon_url, URL)
    assert chan.xmltv_icon_url.human_repr() == "http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png"
    assert chan.xmltv_display_name == "BBC One Lon"


def test_channel_from_both_sources():
    chan_x = channel_from_xmltv_list(ET.XML(XML_CHANNEL_1))
    chan_q = channel_from_skyq_service(json.loads(SERVICE_SUMMARY_MOCK)['services'][0])

    # first way round
    chan = merge_channels(chan_q, chan_x) # note, chan_x overwrites chan_q

    assert isinstance(chan, Channel)
    assert chan.sources == CHANNELSOURCES.xml_tv | CHANNELSOURCES.skyq_service_summary
    assert chan.__repr__() == f'<Channel: sources={CHANNELSOURCES.xml_tv | CHANNELSOURCES.skyq_service_summary}, id=2002, xmltv_id=f3932e75f691561adbe3b609369e487b, number=101, name=BBC One Lon>'
    assert chan.c == "101"
    assert chan.t == "BBC One Lon"
    assert chan.name == "BBC One Lon"
    assert chan.xmltv_id == "f3932e75f691561adbe3b609369e487b"
    assert isinstance(chan.xmltv_icon_url, URL)
    assert chan.xmltv_icon_url.human_repr() == "http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png"
    assert chan.xmltv_display_name == "BBC One Lon"

    # other way round
    chan = merge_channels(chan_x, chan_q)  # note, chan_q overwrites chan_x

    assert isinstance(chan, Channel)
    assert chan.sources == CHANNELSOURCES.xml_tv | CHANNELSOURCES.skyq_service_summary
    assert chan.__repr__() == f'<Channel: sources={CHANNELSOURCES.xml_tv | CHANNELSOURCES.skyq_service_summary}, id=2002, xmltv_id=f3932e75f691561adbe3b609369e487b, number=101, name=BBC One Lon>'
    assert chan.c == "101"
    assert chan.t == "BBC One Lon"
    assert chan.name == "BBC One Lon"
    assert chan.xmltv_id == "f3932e75f691561adbe3b609369e487b"
    assert isinstance(chan.xmltv_icon_url, URL)
    assert chan.xmltv_icon_url.human_repr() == "http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png"
    assert chan.xmltv_display_name == "BBC One Lon"


def test_channel_json():
    chan_x = channel_from_xmltv_list(ET.XML(XML_CHANNEL_1))
    chan_q = channel_from_skyq_service(json.loads(SERVICE_SUMMARY_MOCK)['services'][0])
    chan_q = chan_q.load_skyq_detail_data(json.loads(SERVICE_DETAIL_1))

    mergechan = merge_channels(chan_q, chan_x)  # note, chan_x overwrites chan_q

    assert json.loads(chan_x.as_json()) == json.loads(XML_CHAN_JSON)
    assert json.loads(chan_q.as_json()) == json.loads(SKYQ_CHAN_JSON)
    assert json.loads(mergechan.as_json()) == json.loads(MERGED_CHAN_JSON)

    assert chan_x == channel_from_json(XML_CHAN_JSON)
    assert chan_q == channel_from_json(SKYQ_CHAN_JSON)
    assert mergechan == channel_from_json(MERGED_CHAN_JSON)

    assert chan_x != chan_q

    assert chan_x != "blah"

    with pytest.raises(ValueError, match="Incorrect type metadata in JSON payload."):
        channel_from_json(BAD_JSON)


