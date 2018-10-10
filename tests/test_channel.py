# pylint: skip-file
import pytest
import json
from pyskyq.channel import Channel, channel_from_skyq_service
from pyskyq.constants import CSRC

from .mock_constants import SERVICE_DETAIL_1, SERVICE_SUMMARY_MOCK


def test_blank_channel():

    blank_chan = Channel()
    assert blank_chan.sources == CSRC.no_source
    assert blank_chan.__repr__() == '<Channel: sources=CSRC.no_source, id=None, number=None, name=None>'

    with pytest.raises(AttributeError, match="Can't modify sid"):
        blank_chan.sid = 232

    with pytest.raises(KeyError, match="blah"):
        blank_chan.blah

    with pytest.raises(KeyError, match="isbroadcasting"):
        blank_chan.isbroadcasting

def test_channel_from_skyq_service():

    chan = channel_from_skyq_service(json.loads(SERVICE_SUMMARY_MOCK)['services'][0])

    assert isinstance(chan, Channel)
    assert chan.sources == CSRC.skyq_service_summary
    print(chan.__repr__())
    assert chan.__repr__() == '<Channel: sources=CSRC.skyq_service_summary, id=2002, number=101, name=BBC One Lon>'
    assert chan.c == "101"
    assert chan.t == "BBC One Lon"
    assert chan.name == "BBC One Lon"

    with pytest.raises(AttributeError, match="Can't modify sid"):
        chan.sid = 232

    with pytest.raises(KeyError, match="blah"):
        chan.blah

    with pytest.raises(KeyError, match="isbroadcasting"):
        chan.isbroadcasting

    chan.load_skyq_detail_data(json.loads(SERVICE_DETAIL_1))
    print(chan.__repr__())

    assert chan.isbroadcasting
    assert chan.sources == CSRC.skyq_service_summary | CSRC.skyq_service_detail
    assert chan.__repr__() == '<Channel: sources=CSRC.skyq_service_detail|skyq_service_summary, id=2002, number=101, name=BBC One Lon>'

    assert chan.upgradeMessage == "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england."
    assert chan.desc == "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england."
