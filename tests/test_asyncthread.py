import asyncio
import logging
import sys
import time
import signal
import os

import pytest

from pyskyq.asyncthread import AsyncThread

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

LOGGER = logging.getLogger(__name__)


def test_asyncthread():

    at1 = AsyncThread()
    at2 = AsyncThread()

    # test singleton.
    assert at1.loop is at2.loop
    assert at1.thread is at2.thread

    assert at1.shutdown_sentinel is False
    assert at1.thread.is_alive()

    async def t1():
        await asyncio.sleep(1.2)
        return "He's not the Messiah..."

    async def t2():
        await asyncio.sleep(1.4)
        return "...he's very naughty boy."


    async def cancel_me():
        try:
            # Wait for 1 hour
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            await asyncio.sleep(5)
            raise

    f1 = at1.run(t1())
    f2 = at1.run(t2())
    at1.run(cancel_me())

    while f1.running():
        time.sleep(.1)
    assert f1.result() == "He's not the Messiah..."

    while f1.running():
        time.sleep(.1)
    assert f2.result() == "...he's very naughty boy."

    at1.shutdown()
    assert at1.shutdown_sentinel is True

    time.sleep(0.1)
    assert not at1.loop.is_running()

    at3 = AsyncThread()  #create a new one to test re-initing...
    assert at3.shutdown_sentinel is False
    assert at3.thread.is_alive()

