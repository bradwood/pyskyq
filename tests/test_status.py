import logging
import sys
import trio
import pytest
from trio_websocket import ConnectionClosed, WebSocketConnection
from contextlib import asynccontextmanager
from functools import partial
from asynctest import CoroutineMock, MagicMock
from pyskyq import get_status
from .http_server import http_server, websocket_server

from .asynccontextmanagermock import AsyncContextManagerMock
from .mock_constants import WS_STATUS_MOCK

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

LOGGER = logging.getLogger(__name__)


async def test_get_status():

    with trio.move_on_after(1):
        async with trio.open_nursery() as server_nursery:
            responses = []
            response = {
                'target': '/as/system/status',
                'body': WS_STATUS_MOCK.encode('utf-8'),
                }

            for _ in range(10):
                responses.append(response)  # add 10 of them for good measure.
            server_nursery.start_soon(websocket_server, '127.0.0.1', 9006, responses)
            # await trio.serve_tcp(partial(http_server, responses=responses), 8000)
            LOGGER.debug('started websocket server.')
            await trio.sleep(0.3)
            # pylint: disable=not-async-context-manager

            async with get_status('localhost') as stat:
                await trio.sleep(0.1)
                assert stat.online is True  #object initialises this to False, JSON payload sets to True.

