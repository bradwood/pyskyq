import asyncio
import logging
import sys
import time
import signal
import os

import pytest

from pyskyq.asyncthread import AsyncThread

def test_asyncthread():

    at1 = AsyncThread()
    at2 = AsyncThread()

    assert at1.loop is at2.loop
    assert at1.thread is at2.thread
    assert at1.thread.is_alive()

    async def t1():
        await asyncio.sleep(.2)
        return "He's not the Messiah..."

    async def t2():
        await asyncio.sleep(.4)
        return "...he's very naughty boy."

    async def t3():
        while True:
            await asyncio.sleep(.1)

    f1 = asyncio.run_coroutine_threadsafe(
        t1(),
        at1.loop
    )
    f2 = asyncio.run_coroutine_threadsafe(
        t2(),
        at1.loop
    )
    asyncio.run_coroutine_threadsafe(
        t3(),
        at1.loop
    )

    time.sleep(.21)
    assert f1.result() == "He's not the Messiah..."
    time.sleep(.21)
    assert f2.result() == "...he's very naughty boy."
    at1.shutdown_async_thread()
