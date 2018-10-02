#!/usr/bin/env python
"""
Example use of the Status API.

"""

import logging
import sys

from pyskyq import Status

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

logging.getLogger().setLevel(logging.DEBUG)  # status changes are logged.

stat = Status('skyq')  # replace with hostname / IP of your Sky box
stat.create_event_listener()  # set up listener thread.

# do other stuff.

# standby property will be updated asynchronously when the box is turned on or off.
if stat.standby:
    print('The SkyQ Box is in Standby Mode')
else:
    print('The SkyQ Box is in Online Mode')

stat.shudown_event_listener()  # shut down listener thread.
