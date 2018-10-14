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

# LOGGER = logging.getLogger(__name__)


def test_asyncthread():

    at1 = AsyncThread()
    at2 = AsyncThread()

    assert at1.loop is at2.loop
    assert at1.thread is at2.thread
    assert at1.thread.is_alive()

    async def t1():
        await asyncio.sleep(1.2)
        return "He's not the Messiah..."

    async def t2():
        await asyncio.sleep(1.4)
        return "...he's very naughty boy."


    async def cancel_me():
        print('cancel_me(): before sleep')
        try:
            # Wait for 1 hour
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            print('cancel_me(): cancel sleep')
            await asyncio.sleep(5)
            raise
        finally:
            print('cancel_me(): after sleep')


    f1 = asyncio.run_coroutine_threadsafe(
        t1(),
        at1.loop
    )
    f2 = asyncio.run_coroutine_threadsafe(
        t2(),
        at1.loop
    )
    asyncio.run_coroutine_threadsafe(
        cancel_me(),
        at1.loop
    )

    while f1.running():
        time.sleep(.1)
    assert f1.result() == "He's not the Messiah..."

    while f1.running():
        time.sleep(.1)
    assert f2.result() == "...he's very naughty boy."

    at1.shutdown_async_thread()
