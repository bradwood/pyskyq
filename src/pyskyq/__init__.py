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

from .constants import REMOTECOMMANDS, CHANNELSOURCES, QUALITY
from ._version import __version__
from .remote import press_remote
from .epg import EPG
from .status import Status
from .xmltvlisting import XMLTVListing
from .channel import (Channel, channel_from_skyq_service,
                      channel_from_xmltv_list, merge_channels,
                      channel_from_json)
from .cronthread import CronThread
from .asyncthread import AsyncThread

logging.getLogger(__name__).addHandler(logging.NullHandler())
