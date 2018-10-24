"""This module implements the ``press_remote()`` function.

Remote is a lower level interface to the SkyQ box that seeks to emulate most of the the
button presses available on the SkyQ remote. There are some buttons which are not (currently)
supported, however.

Todos:
    * Research some of the missing button codes to see if it's possible to also include them.
"""

import logging
import socket
import math

from .constants import REMOTE_PORT

LOGGER = logging.getLogger(__name__)

def press_remote(host: str, code: int, *, port: int = REMOTE_PORT) -> None:
    """Send a command to the Sky Q box using the Remote interface.

    This function sends a button press to the SkyQ box via a TCP socket connection. The
    encoding and handshake required was extracted by looking at the following sources:

    - https://github.com/dalhundal/sky-remote
    - https://gladdy.uk/blog/2017/03/13/skyq-upnp-rest-and-websocket-api-interfaces/

    Args:
        host (str): String with resolvable hostname or IPv4 address to SkyQ box.
        code (int): A code passed which represents the button to press. See
            :py:mod:`.constants` for a human-friendly list of the currently
            supported buttons and their associated codes.
        port (int, optional): Port number to use to connect to the Remote TCP socket.
            Defaults to the standard port used by SkyQ boxes which is 49160.

    Returns:
        None

    """
    LOGGER.debug(f'Sending command code={code}')
    command_bytes = bytearray([4, 1, 0, 0, 0, 0, math.floor(224 + (code/16)), code % 16])
    LOGGER.debug(f'command_bytes={command_bytes}')

    # TODO try/except socket.gaierror
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))

    # Wait until ready for data
    length = 12
    while True:
        data = client.recv(24)
        LOGGER.debug(f'Received data={data}')
        if len(data) < 24: # box sends 24 x \x00 to signal end of hand-shake.
            client.send(data[0:length])
            LOGGER.debug(f'Sent data={data[0:length]}')
            length = 1
        else:
            break

    client.send(command_bytes)
    LOGGER.debug(f'Send command part 1 data={command_bytes}')
    command_bytes[1] = 0
    client.send(command_bytes)
    LOGGER.debug(f'Send command part 2 data={command_bytes}')
    client.close()
