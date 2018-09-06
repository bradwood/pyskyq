import pytest
import socket

from pyskyq import SkyQ, SkyRemote, rcmd


def test_sky_remote_init():
    skyq = SkyQ('blah')
    assert isinstance(skyq.remote, SkyRemote)
    assert skyq.remote.host == 'blah'

def test_sky_remote_send_command(mocker):
    
    m = mocker.patch('socket.socket')
    m.return_value.recv.side_effect = [  # set up the data to be returned on each successive call of socket.recv()
        b'SKY 000.001\n',
        b'\x01\x01',
        b'\x00\x00\x00\x00',
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
    ]

    skyrem = SkyRemote('blah')

    skyrem.send_command(rcmd.play)

    m.assert_called_with(socket.AF_INET, socket.SOCK_STREAM)
    
    assert m.return_value.recv.call_count == 4
    m.return_value.send.assert_any_call(b'SKY 000.001\n')
    m.return_value.send.assert_any_call(b'\x01')
    m.return_value.send.assert_any_call(b'\x00')
    m.return_value.send.assert_any_call(bytearray(b'\x04\x00\x00\x00\x00\x00\xe4\x00'))
