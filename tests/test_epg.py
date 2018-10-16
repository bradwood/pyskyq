import asyncio
import json
import logging
import sys
from pathlib import Path
import time
import pytest
from asynctest import CoroutineMock, MagicMock

from pyskyq import EPG, Channel, channel_from_skyq_service, XMLTVListing

from .asynccontextmanagermock import AsyncContextManagerMock
from .mock_constants import (REMOTE_TCP_MOCK, SERVICE_DETAIL_1,
                             SERVICE_DETAIL_2, SERVICE_SUMMARY_MOCK)


logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

def test_EPG_sky_channels(mocker):

    jsonmock_invocation_count = 0

    class jsonmock:
        @staticmethod
        async def json():
            nonlocal jsonmock_invocation_count
            jsonmock_invocation_count += 1
            if jsonmock_invocation_count == 1:
                return json.loads(SERVICE_SUMMARY_MOCK)
            if jsonmock_invocation_count == 2:
                return json.loads(SERVICE_DETAIL_1)
            if jsonmock_invocation_count == 3:
                return json.loads(SERVICE_DETAIL_2)


    client_response = asyncio.Future()
    client_response.set_result(jsonmock)

    a = mocker.patch('aiohttp.ClientSession.get', new_callable=AsyncContextManagerMock)
    a.return_value = client_response

    epg = EPG('test_load_channel_list_fake_host')

    with pytest.raises(ValueError, match='No channels loaded.'):
        epg.get_channel_by_sid(2002)

    epg.load_skyq_channel_data()

    time.sleep(1)
    assert isinstance(epg, EPG)
    assert len(epg._channels) == 2
    assert epg.get_channel_by_sid(2002).c == "101"
    assert epg.get_channel_by_sid(2002).t == "BBC One Lon"
    assert epg.get_channel_by_sid(2002).name == "BBC One Lon"
    assert epg.get_channel_by_sid('2002').c == "101"
    assert epg.get_channel_by_sid('2002').t == "BBC One Lon"
    assert epg.get_channel_by_sid('2002').name == "BBC One Lon"

    assert epg.get_channel_by_sid(2002).isbroadcasting is True
    assert "BBC ONE for Greater London and the surrounding area." in \
        epg.get_channel_by_sid(2002).upgradeMessage

    assert "Dave is the home of witty banter with quizcoms, cars and comedies." in \
        epg.get_channel_by_sid(2306).upgradeMessage

    with pytest.raises(ValueError, match='Sid:1234567 not found.'):
        epg.get_channel_by_sid(1234567)

def test_apply_EPG_XMLTV_listing(mocker, event_loop):
    asyncio.set_event_loop(event_loop)

    # set up the epg object with sky data.
    jsonmock_invocation_count = 0

    class jsonmock:
        @staticmethod
        async def json():
            nonlocal jsonmock_invocation_count
            jsonmock_invocation_count += 1
            if jsonmock_invocation_count == 1:
                return json.loads(SERVICE_SUMMARY_MOCK)
            if jsonmock_invocation_count == 2:
                return json.loads(SERVICE_DETAIL_1)
            if jsonmock_invocation_count == 3:
                return json.loads(SERVICE_DETAIL_2)

    client_response = asyncio.Future()
    client_response.set_result(jsonmock)

    a = mocker.patch('aiohttp.ClientSession.get', new_callable=AsyncContextManagerMock)
    a.return_value = client_response

    epg = EPG('test_load_channel_list_fake_host')
    epg.load_skyq_channel_data()

    # now test the xml loading.

    l = XMLTVListing('http://host.com/some/feed')
    l._full_path = Path(__file__).resolve().parent.joinpath('parse_xmltv_data.xml')
    l._downloaded_okay = True

    epg.apply_XMLTVListing(l)  # apply EPG listing to an empty EPG.

    #assert True
