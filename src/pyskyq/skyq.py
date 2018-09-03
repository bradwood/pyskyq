"""This module houses the main SKY Q class"""

import logging
from typing import Optional

from .constants import REMOTE_PORT
from .skyremote import SkyRemote

class SkyQ:
    """Main Sky Q class definition."""

    def __init__(self,
                 host: str,
                 remote_port: int = REMOTE_PORT,
                 logger: Optional[logging.Logger] = None,
                 ) -> None:
        
        """Initialise SkyQ object. """
        self.host = host
        self.remote_port = remote_port
        self.logger = logging.getLogger(__name__) if not logger else logger

        self.logger.debug(f"Initialised SkyQ object with host={host}, remote_port={remote_port}")
        self.remote = SkyRemote(self.host,self.remote_port, self.logger)
