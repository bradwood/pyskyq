"""This module provides global management of asyncio-based tasks in a dedicated thread.

It provides the :class:`AsyncThread` class which is a singleton with some specical quirks.
When instantiated it will figure out if it has been instantiated before. If this is the first
instantiation, it will create an internal thread and run an event loop in it. If it's being
instantiated again, it will check the state of the thead and the event loop within it and restart
those if needed.

It also provides signal handlers that cleanly cancel and await the completion of any tasks upon
receipt of a ``SIGINT`` or ``SIGTERM`` interrupt.

Example:
    This can be used as follows::

        at = AsyncThread()

        future = at.run(my_coro())

        # do some other stuff

        at.shutdown()

Warning:
    Remember that you **must** always used thread-safe asyncio invocation methods with this
    class.

"""
# pylint: disable=no-member
import asyncio
import threading
import signal
import logging
import functools
from concurrent.futures import Future
from enum import Enum
from typing import Coroutine

LOGGER = logging.getLogger(__name__)

class AsyncThread():
    """This class holds references to a separate thread which runs an asyncio event loop.

    It is a Singleton.
    Attributes:
        loop (asyncio.AbstractEventLoop): The associated event loop.
        thread (threading.Thread): The thread that the event loop is running in.
    """
    _instance = None
    # pylint: disable=protected-access
    def __new__(cls, *args, **kwargs):
        """Implement the Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._state = 'new'
        else:
            cls._instance._state = 'exists'
        if not hasattr(cls._instance, 'thread'):
            cls._instance.thread = None

        if not hasattr(cls._instance, 'loop'):
            cls._instance.loop = None

        return cls._instance

    def __init__(self) -> None:
        """Create/reinitialise a thread and set up an asyncio event loop in it.

        If the thread/loop already exist, this will make sure that they are running,
        otherwise it will create new ones.

        """
        self.thread: threading.Thread
        self.loop: asyncio.AbstractEventLoop

        def _start_event_loop_thread() -> None:
            """Run an asyncio event loop inside this thread."""
            asyncio.set_event_loop(self.loop)
            LOGGER.info(f'Starting asyncio loop in thread: {self.thread.name}.')
            self.loop.run_forever()

        # pylint: disable=access-member-before-definition
        if self._state == 'new':  # type: ignore
            # set up everything as this is the first invocation.
            self.loop = asyncio.new_event_loop()
            LOGGER.info('Created new event loop.')
            for sig in (signal.SIGINT, signal.SIGTERM):
                self.loop.add_signal_handler(sig,
                                             functools.partial(asyncio.create_task,
                                                               self._shutdown_signal_handler(sig)
                                                               )
                                             )
            LOGGER.debug('Added signal handlers...')
            self.thread = threading.Thread(target=_start_event_loop_thread,
                                           name=__name__,
                                           daemon=True)
            LOGGER.debug(f'Started thread {self.thread.name}.')
            self.thread.start()
            self._state = 'exists'

        else:
            LOGGER.info('Loop already exists, so not creating a new one.')
            if not self.thread or not self.thread.is_alive():
                self.thread = threading.Thread(target=_start_event_loop_thread,
                                               name=__name__,
                                               daemon=True)
                LOGGER.debug(f'Started thread {self.thread.name}.')
                self.thread.start()

        self._shutdown_sentinel = False
        asyncio.run_coroutine_threadsafe(self._loop_monitor(), self.loop)

    def run(self, coro: Coroutine) -> Future:
        """Run a coroutine in the async thread.

        Warning:
            This is a non-blocking method.

        Returns:
            concurrent.futures.Future: a Future holding any results returned from the call.

        """
        return asyncio.run_coroutine_threadsafe(
            coro, self.loop)


    # def __enter__(self):
    #     """Open the context block."""
    #     AsyncThread._context_count += 1
    #     LOGGER.debug(f'Started context block. Nest level = {AsyncThread._context_count}.')
    #     return self

    # def __exit__(self, ex_type, ex_val, traceback):
    #     """Close the context block and shutdown the thread if this is outmost block."""
    #     AsyncThread._context_count -= 1
    #     LOGGER.debug(f'Exited context block. Nest level = {AsyncThread._context_count}.')
    #     if AsyncThread._context_count == 0:
    #         LOGGER.debug(f'Nest level = {AsyncThread._context_count}. Shutting down.')
    #         self.shutdown()


    @property
    def shutdown_sentinel(self):
        """Flag imminent shutdown of the event loop and its thread.

        This sentinel can be used in coroutines that want to loop ``while
        True``. Instead of doing that do::

             while not at.shutdown_sentinel:
                 ...

        Returns:
            shutdown_sentinel (bool): If ``True`` then the event loop has been i
            nstructed to shut down.

        """
        return self._shutdown_sentinel


    async def _loop_monitor(self) -> None:
        """Monitor the loop."""
        while not self._shutdown_sentinel:
            LOGGER.debug(f'Event loop still running in thread: {self.thread.name}')
            await asyncio.sleep(1)

    async def _cancel_all_tasks(self):
        """Cancel all running tasks in the loop."""
        tasks = [task for task in asyncio.all_tasks(loop=self.loop) if task is not
                 asyncio.current_task(loop=self.loop)]
        for task in tasks:
            task.cancel()
        LOGGER.info(f'Cancelled {len(tasks)} running tasks.')

    # no unit test for the below, but tested manually... Honestly... :)
    async def _shutdown_signal_handler(self, sig: Enum) -> None:  # pragma: no cover
        """Shut down the event loop cleanly."""
        LOGGER.info(f'Caught signal: {sig.name}. Shutting down...')
        self._shutdown_sentinel = True
        await self._cancel_all_tasks()
        self.loop.stop()

    def shutdown(self) -> None:
        """Shutdown the running asyncio thread."""
        LOGGER.info(f'Shutting down...')
        self._shutdown_sentinel = True
        def stop_callback(_):
            self.loop.stop()

        fut = asyncio.run_coroutine_threadsafe(self._cancel_all_tasks(), self.loop)
        fut.add_done_callback(stop_callback)
