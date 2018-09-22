import asyncio
import socket
import sys

import aiohttp
import pytest
from asynctest import CoroutineMock, MagicMock

from pyskyq import RCMD
from pyskyq.cli import run

from .asynccontextmanagermock import AsyncContextManagerMock
from .mock_constants import SERVICE_MOCK, REMOTE_TCP_MOCK


def test_cli(mocker):

    m = mocker.patch('socket.socket')
    m.return_value.recv.side_effect = REMOTE_TCP_MOCK

    a = mocker.patch('aiohttp.ClientSession.get', new_callable=AsyncContextManagerMock)
    a.return_value.__aenter__.return_value.json = CoroutineMock(side_effect=SERVICE_MOCK)

    mocker.patch.object(sys, 'argv', ['pyskyq', 'play'])

    run()

    m.assert_called_with(socket.AF_INET, socket.SOCK_STREAM)

    assert m.return_value.recv.call_count == 4
    m.return_value.send.assert_any_call(b'SKY 000.001\n')
    m.return_value.send.assert_any_call(b'\x01')
    m.return_value.send.assert_any_call(b'\x00')
    m.return_value.send.assert_any_call(bytearray(b'\x04\x00\x00\x00\x00\x00\xe4\x00'))

    # TODO test with --verbose
