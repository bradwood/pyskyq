#!/usr/bin/env python
"""Example use of the Status API."""

import logging
import sys
import trio

from pyskyq import get_status

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

logging.getLogger().setLevel(logging.DEBUG)  # status changes are logged.

async def report_box_online():
    """Report whether the SkyQ is online or not."""
    # pylint: disable=not-async-context-manager
    async with get_status('skyq') as stat:
        while True:
            if stat.online:
                print('The SkyQ Box is Online ')
            else:
                print('The SkyQ Box is Offline')
            await trio.sleep(1)
try:
    print("Type Ctrl-C to exit.")
    trio.run(report_box_online)
except KeyboardInterrupt:
    raise SystemExit(0)
