# pylint: skip-file
import pytest
import json
from pyskyq.channel import Channel, channel_from_skyq_service, CSRC

from .mock_constants import SERVICE_DETAIL_1, SERVICE_SUMMARY_MOCK


def test_channel_from_skyq_service():

    chan = channel_from_skyq_service(json.loads(SERVICE_SUMMARY_MOCK)['services'][0])

    assert isinstance(chan, Channel)
    assert chan.sources == CSRC.skyq_service
    assert chan.__repr__() == '<Channel: sources=1>'
    assert chan.c == "101"
    assert chan.t == "BBC One Lon"
    assert chan.name == "BBC One Lon"

    with pytest.raises(AttributeError, match="Can't modify sid"):
        chan.sid = 232

    with pytest.raises(KeyError, match="blah"):
        chan.blah

    with pytest.raises(KeyError, match="isbroadcasting"):
        chan.isbroadcasting


    chan.add_detail_data(json.loads(SERVICE_DETAIL_1))

    assert chan.isbroadcasting

    assert chan.upgradeMessage == "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england."
    assert chan.desc == "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england."
