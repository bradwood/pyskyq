import pytest
import socket

from pyskyq import SkyQ, SkyRemote, rcmd


def test_sky_remote_init():
    skyq = SkyQ('blah')
    assert isinstance(skyq.remote, SkyRemote)
    assert skyq.remote.host == 'blah'

def test_sky_remote_send_command(mocker):
    
    #m.patch('SkyRemote.logger')

    # Mocket.register(MocketEntry(('localhost', 8080), b'SKY 000.001\n'))
    with mocker.patch('socket.socket') as mock_socket:
        skyrem = SkyRemote('blah')
        skyrem.send_command(rcmd.play)
        mock_socket.assert_called_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_socket.connect.return_value = None
        mock_socket.recv.return_value = b'SKY 000.001\n'

        #m.debug.assert_called_with("Received data=b'SKY 000.001\n'")


# def test_sky_remote_send_command():
#     skyrem = SkyRemote('localhost', 8080)
#     # for record in caplog.records:
#     #     assert record.levelname == 'DEBUG'
#     # assert 'SKY 000.001'  in caplog.text
#     assert False
