# pylint: skip-file

import socket

import pytest

from pyskyq import REMOTECOMMANDS as RCMD
from pyskyq import press_remote

from .mock_constants import REMOTE_TCP_MOCK


def test_sky_remote_send_command(mocker):

    m = mocker.patch('socket.socket')
    m.return_value.recv.side_effect = REMOTE_TCP_MOCK

    press_remote('some_host', RCMD.play)

    m.assert_called_with(socket.AF_INET, socket.SOCK_STREAM)

    assert m.return_value.recv.call_count == 4
    m.return_value.send.assert_any_call(b'SKY 000.001\n')
    m.return_value.send.assert_any_call(b'\x01')
    m.return_value.send.assert_any_call(b'\x00')
    m.return_value.send.assert_any_call(bytearray(b'\x04\x00\x00\x00\x00\x00\xe4\x00'))
