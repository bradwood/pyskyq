# pylint: skip-file

import asyncio
import logging
import sys
import time

import pytest
import websockets
from asynctest import CoroutineMock, MagicMock

from pyskyq import Status

from .asynccontextmanagermock import AsyncContextManagerMock
from .mock_constants import WS_STATUS_MOCK

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

logging.getLogger().setLevel(logging.DEBUG)

def serve_ws_json_with_detail():
    time.sleep(0.2)
    return WS_STATUS_MOCK


def test_status(mocker):
    a = mocker.patch('websockets.connect', new_callable=AsyncContextManagerMock)
    a.return_value.__aenter__.return_value.recv = \
        CoroutineMock(side_effect=serve_ws_json_with_detail)

    stat = Status('some_host')
    stat.create_event_listener()

    time.sleep(0.5) # allow time for awaiting, etc.
    assert stat.standby is True

    stat.shudown_event_listener()


timeout_test_call_count :int  # global var to could calls.

def server_then_close():
    global timeout_test_call_count
    timeout_test_call_count += 1
    print(timeout_test_call_count)
    time.sleep(0.2)
    if timeout_test_call_count > 5:
        raise websockets.exceptions.ConnectionClosed
    else:
        return WS_STATUS_MOCK


def test_status_timeout(mocker):
    global timeout_test_call_count
    timeout_test_call_count = 0
    a = mocker.patch('websockets.connect', new_callable=AsyncContextManagerMock)
    a.return_value.__aenter__.return_value.recv = \
        CoroutineMock(side_effect=server_then_close)

    stat = Status('timeout_host', ws_timeout=2)
    stat.create_event_listener()

    time.sleep(2)

    assert stat.standby is True

    stat.shudown_event_listener()


def test_status_shutdown_sentinel(mocker):
    global timeout_test_call_count
    timeout_test_call_count = 0
    a = mocker.patch('websockets.connect', new_callable=AsyncContextManagerMock)
    a.return_value.__aenter__.return_value.recv = \
        CoroutineMock(side_effect=server_then_close)

    stat = Status('shutdown_host')
    stat.create_event_listener()
    time.sleep(1)
    stat.shudown_event_listener()
    assert stat._shutdown_sentinel is True
    time.sleep(2)
    assert stat.standby is True
