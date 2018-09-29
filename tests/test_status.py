import asyncio
import logging
import sys
import time

import pytest
import websockets
from asynctest import CoroutineMock, MagicMock

from pyskyq.status import Status

from .asynccontextmanagermock import AsyncContextManagerMock
from .mock_constants import WS_STATUS_MOCK

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"


def test_status(mocker):
    a = mocker.patch('websockets.connect', new_callable=AsyncContextManagerMock)
    a.return_value.__aenter__.return_value.recv = CoroutineMock(return_value=WS_STATUS_MOCK)
    b = a.start()


    stat = Status('some_host')
    stat.create_event_listener()

    time.sleep(1) # allow time for awaiting, etc.
    assert stat.standby is True

# def wait_beyond_timeout_then_serve_json():
#     time.sleep(3)
#     raise websockets.exceptions.ConnectionClosed
#     #return WS_STATUS_MOCK


# def test_status_timeout(mocker):
#     mocker.stopall()
#     b = mocker.patch('websockets.connect', new_callable=AsyncContextManagerMock)
#     b.return_value.__aenter__.return_value.recv = CoroutineMock(side_effect=wait_beyond_timeout_then_serve_json)
#     b.start()
#     stat = Status('timeout_host', ws_timeout=2)

#     logging.getLogger().setLevel(logging.DEBUG)

#     time.sleep(1)
#     with pytest.raises(asyncio.TimeoutError):
#         stat.create_event_listener()
#     b.stop()
