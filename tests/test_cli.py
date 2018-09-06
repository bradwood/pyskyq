import pytest
import socket
import sys

from pyskyq.cli import run
from pyskyq import rcmd

def test_cli(mocker):

    m = mocker.patch('socket.socket')
    m.return_value.recv.side_effect = [  # set up the data to be returned on each successive call of socket.recv()
        b'SKY 000.001\n',
        b'\x01\x01',
        b'\x00\x00\x00\x00',
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
    ]

    mocker.patch.object(sys, 'argv', ['pyskyq', 'play'])
    
    run()

    m.assert_called_with(socket.AF_INET, socket.SOCK_STREAM)

    assert m.return_value.recv.call_count == 4
    m.return_value.send.assert_any_call(b'SKY 000.001\n')
    m.return_value.send.assert_any_call(b'\x01')
    m.return_value.send.assert_any_call(b'\x00')
    m.return_value.send.assert_any_call(bytearray(b'\x04\x00\x00\x00\x00\x00\xe4\x00'))

    # TODO test with --verbose
