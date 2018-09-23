"""This module houses the main SKY Q class"""

import logging
from typing import Optional

from .constants import REMOTE_PORT, REST_PORT
from .skyremote import SkyRemote
from .epg import EPG

# pylint: disable=too-few-public-methods
class SkyQ:
    """Main Sky Q class definition.

    This is the main SkyQ Class definition which provides all available access
    to the SkyQ box that is currently implemented.

    Attributes:
        host (str): Hostname or IPv4 address of SkyQ Box.
        remote_port (int): Port number to use to connect to the Remote TCP socket.
            Defaults to the standard port used by SkyQ boxes which is 49160.
        rest_port (int, optional): Port number to use to connect to the Remote REST API.
            Defaults to the standard port used by SkyQ boxes which is 9006.
        logger (logging.Logger): Standard Python logger object which if not passed will
            instantiate a local logger.
        remote (SkyRemote): An instance of the SkyRemote class which can be used to
            call the lower-level remote API which essentially emulated button-presses on
            the SkyQ Remote.

    Todos:
        * Add interface to read EPG
        * Add higher level channel selector interface to pick channels by name, rather than number.
        * Add misc higher level interfaces to give "now and next" type responses.
    """


    def __init__(self,
                 host: str,
                 *,
                 remote_port: int = REMOTE_PORT,
                 rest_port: int = REST_PORT,
                 logger: Optional[logging.Logger] = None,
                 ) -> None:

        """Initialise SkyQ object.

        This method instantiates the SkyQ object, which will also instantiate a SkyRemote object.

        Args:
            host (str): String with resolvable hostname or IPv4 address to SkyQ box.
            remote_port (int, optional): Port number to use to connect to the Remote TCP socket.
                Defaults to the standard port used by SkyQ boxes which is 49160.
            rest_port (int, optional): Port number to use to connect to the Remote REST API.
                Defaults to the standard port used by SkyQ boxes which is 9006.
            logger (logging.Logger, optional): Standard Python logger object which if not passed
                will instantiate a local logger.
        Returns:
            None

        """
        self.host = host
        self.remote_port = remote_port
        self.rest_port = rest_port
        self.logger = logging.getLogger(__name__) if not logger else logger
        self.remote = SkyRemote(self.host, self.remote_port, self.logger)
        self.epg = EPG(self.host, self.rest_port, self.logger)

        self.logger.debug(f"Initialised SkyQ object with host={host}.")
