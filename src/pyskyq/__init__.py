"""This package aims to provide APIs for all functions that are exposed over
the network by a SkyQ set top box, and a few additional things besides.

Current SkyQ Boxes expose the following functions (that I'm aware of):

    - a uPNP interface for getting and setting certain settings.
    - a TCP socket interface that provides a remote control API.
    - a HTTP REST interface, for miscellaneous channel, status and EPG data.
    - a WebSocket REST interface for subscribing to state changes, like Standby Mode.

Sky also provides some services to their SkyQ boxes over the internet, so
this API might tap into some of that stuff too.

As of October 2018, this is still very much a work in progress.
"""

import logging

from pyskyq.constants import RCMD
from pyskyq._version import __version__
from pyskyq.remote import press_remote
from pyskyq.epg import EPG
from pyskyq.status import Status
from pyskyq.listing import Listing

logging.getLogger(__name__).addHandler(logging.NullHandler())
