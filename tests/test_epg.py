import asyncio
import json
import logging
import sys

import pytest
from asynctest import CoroutineMock, MagicMock

from pyskyq import EPG

from .asynccontextmanagermock import AsyncContextManagerMock
from .mock_constants import (REMOTE_TCP_MOCK, SERVICE_DETAIL_1,
                             SERVICE_DETAIL_2, SERVICE_SUMMARY_MOCK)

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

def test_load_channel_list(mocker):

    a = mocker.patch('aiohttp.ClientSession.get', new_callable=AsyncContextManagerMock)

    class jsonmock:
        @staticmethod
        async def json():
            return json.loads(SERVICE_SUMMARY_MOCK)

    client_response = asyncio.Future()
    client_response.set_result(jsonmock)

    a.return_value = client_response

    loop = asyncio.get_event_loop()
    epg = EPG('test_load_channel_list_fake_host')
    loop.run_until_complete(epg._load_channel_list())


    assert isinstance(epg, EPG)
    assert len(epg._channels) == 2
    assert epg.get_channel(2002).c == "101"
    assert epg.get_channel(2002).t == "BBC One Lon"
    assert epg.get_channel(2002).name == "BBC One Lon"
    assert epg.get_channel('2002').c == "101"
    assert epg.get_channel('2002').t == "BBC One Lon"
    assert epg.get_channel('2002').name == "BBC One Lon"





def tdest_EPG(mocker):

    # SERVICE_MOCK = [json.loads(SERVICE_SUMMARY_MOCK), json.loads(SERVICE_DETAIL_1), json.loads(SERVICE_DETAIL_2)]

    # SERVICE_MOCK = [1, 2, 3]

    a = mocker.patch('aiohttp.ClientSession.get', new_callable=AsyncContextManagerMock)

    jsonmock_invocation_count = 0
    class jsonmock:
        @staticmethod
        async def json():
            nonlocal jsonmock_invocation_count
            jsonmock_invocation_count += 1
            print(jsonmock_invocation_count)

            if jsonmock_invocation_count == 1:
                return json.loads(SERVICE_SUMMARY_MOCK)
            if jsonmock_invocation_count == 2:
                return json.loads(SERVICE_DETAIL_1)
            if jsonmock_invocation_count == 3:
                return json.loads(SERVICE_DETAIL_2)


    client_response = asyncio.Future()
    client_response.set_result(jsonmock)

    a.return_value = client_response

    loop = asyncio.get_event_loop()
    epg = EPG('test_load_channel_list_fake_host')
    epg.load_channel_data()

    assert isinstance(epg, EPG)
    assert len(epg._channels) == 2
    assert epg.get_channel(2002).c == "101"
    assert epg.get_channel(2002).t == "BBC One Lon"
    assert epg.get_channel(2002).name == "BBC One Lon"
    assert epg.get_channel('2002').c == "101"
    assert epg.get_channel('2002').t == "BBC One Lon"
    assert epg.get_channel('2002').name == "BBC One Lon"

    with pytest.raises(AttributeError, match='Channel not found. sid = 1234567.'):
        epg.get_channel(1234567)
