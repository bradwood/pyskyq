import asyncio
import pytest
from asynctest import CoroutineMock

from pyskyq.constants import REMOTE_PORT, REST_PORT
from pyskyq.skyq import SkyQ

from .asynccontextmanagermock import AsyncContextManagerMock
from .mock_constants import SERVICE_MOCK

@pytest.mark.parametrize("host,remote_port,rest_port", [
    ("hostname", REMOTE_PORT, REST_PORT),
    ("hostname", 2342, 3243),
])
def test_SkyQ_init(mocker, host, remote_port, rest_port):

    a = mocker.patch('aiohttp.ClientSession.get', new_callable=AsyncContextManagerMock)
    a.return_value.__aenter__.return_value.json = CoroutineMock(side_effect=SERVICE_MOCK)

    asyncio.set_event_loop(asyncio.new_event_loop())

    skybox = SkyQ(host, remote_port=remote_port, rest_port=rest_port)

    assert skybox.host == host
    assert skybox.remote_port == remote_port

