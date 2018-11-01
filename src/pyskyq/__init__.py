"""This package aims to provide APIs for the SkyQ set-top box.

It aims to provide access to all functions that are exposed over the network by
a SkyQ box, and a few additional things besides.

Current SkyQ Boxes expose the following functions (that I'm aware of):

    - a uPNP interface for getting and setting certain settings.
    - a TCP socket interface that provides a remote control API.
    - a HTTP REST interface, for miscellaneous channel, status and EPG data.
    - a WebSocket JSON interface for subscribing to state changes, like Standby Mode.

Sky also provides some services to their SkyQ boxes over the internet, so
this API might tap into some of that stuff too. It also is capable of fetching
data from 3rd party XMLTV sources.

As of November 2018, this is still very much a work in progress.
"""

import logging

from .constants import REMOTECOMMANDS, CHANNELSOURCES, QUALITY
from ._version import __version__
from .remote import press_remote
from .epg import EPG
from .status import get_status
from .xmltvlisting import XMLTVListing
from .channel import (Channel, channel_from_skyq_service,
                      channel_from_xmltv_list, merge_channels,
                      channel_from_json)

logging.getLogger(__name__).addHandler(logging.NullHandler())
