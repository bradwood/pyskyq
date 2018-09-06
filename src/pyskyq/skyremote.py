"""This module implements the SkyRemote class"""

import logging
import socket
import math
from typing import Optional, Callable

from .constants import REMOTE_PORT


class SkyRemote:
    """Main SkyRemote implementation"""

    def __init__(self,
                 host: str,
                 port: int = REMOTE_PORT,
                 logger: Optional[logging.Logger] = None,
                 ) -> None:
        """Initial Sky Remote Object."""
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__) if not logger else logger
        self.logger.debug(f"Initialised SkyRemote object with host={host}, port={port}")

    def send_command(self, code: int) -> None:
        """Send a command to the Sky Q box using the Remote interface."""
        self.logger.debug(f'Sending command code={code}')
        command_bytes = bytearray([4, 1, 0, 0, 0, 0, math.floor(224 + (code/16)), code % 16])
        self.logger.debug(f'command_bytes={command_bytes}')

        # TODO try/except         
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
