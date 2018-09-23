import pytest
import asyncio

from asynctest import CoroutineMock, MagicMock

from pyskyq import EPG

from .asynccontextmanagermock import AsyncContextManagerMock
from .mock_constants import REMOTE_TCP_MOCK, SERVICE_MOCK


def test_EPG(mocker):

    a = mocker.patch('aiohttp.ClientSession.get', new_callable=AsyncContextManagerMock)
    a.return_value.__aenter__.return_value.json = CoroutineMock(side_effect=SERVICE_MOCK)

    asyncio.set_event_loop(asyncio.new_event_loop())

    epg = EPG('host')

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
