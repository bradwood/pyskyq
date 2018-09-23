"""This module implements the SkyRemote class"""

import logging
import socket
import math
from typing import Optional

from .constants import REMOTE_PORT

# pylint: disable=too-few-public-methods
class SkyRemote:
    """Main SkyRemote implementation.

    SkyRemote is a lower level interface to the SkyQ box that seeks to emulate most of the the
    button presses available on the SkyQ remote. There are some buttons which are not (currently)
    supported, however.

    Attributes:
        host (str): Hostname or IPv4 address of SkyQ Box.
        port (int): Port number to use to connect to the Remote TCP socket.
            Defaults to the standard port used by SkyQ boxes which is 49160.
        logger (logging.Logger): Standard Python logger object which if not passed will
            instantiate a local logger.
    Todos:
        * Research some of the missing button codes to see if it's possible to also include them.
    """

    def __init__(self,
                 host: str,
                 port: int = REMOTE_PORT,
                 logger: Optional[logging.Logger] = None,
                 ) -> None:
        """Initialise Sky Remote Object

        This method instantiates the SkyRemote object.

        Args:
            host (str): String with resolvable hostname or IPv4 address to SkyQ box.
            port (int, optional): Port number to use to connect to the Remote TCP socket.
                Defaults to the standard port used by SkyQ boxes which is 49160.
            logger (logging.Logger, optional): Standard Python logger object which if not
                passed will instantiate a local logger.
        Returns:
            None
        """

        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__) if not logger else logger
        self.logger.debug(f"Initialised SkyRemote object with host={host}, port={port}")

    def send_command(self, code: int) -> None:
        """Send a command to the Sky Q box using the Remote interface.

        This method sends a button press to the SkyQ box via a TCP socket connection. The
        encoding and handshake required was extracted by looking at the following sources:

        - https://github.com/dalhundal/sky-remote
        - https://gladdy.uk/blog/2017/03/13/skyq-upnp-rest-and-websocket-api-interfaces/

        Args:
            code (int): A code passed which represents the button to press. See
                :py:mod:`pyskyq.constants` for a human-friendly list of the currently
                supported buttons and their associated codes.

        Returns:
            None

        """


        self.logger.debug(f'Sending command code={code}')
        command_bytes = bytearray([4, 1, 0, 0, 0, 0, math.floor(224 + (code/16)), code % 16])
        self.logger.debug(f'command_bytes={command_bytes}')

        # TODO try/except socket.gaierror
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.host, self.port))

        # Wait until ready for data
        length = 12
        while True:
            data = client.recv(24)
            self.logger.debug(f'Received data={data}')
            if len(data) < 24: # box sends 24 x \x00 to signal end of hand-shake.
                client.send(data[0:length])
                self.logger.debug(f'Sent data={data[0:length]}')
                length = 1
            else:
                break

        client.send(command_bytes)
        self.logger.debug(f'Send command part 1 data={command_bytes}')
        command_bytes[1] = 0
        client.send(command_bytes)
        self.logger.debug(f'Send command part 2 data={command_bytes}')
        client.close()
