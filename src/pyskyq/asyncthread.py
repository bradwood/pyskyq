"""This module provides global management of asyncio-based tasked in a dedicated thread."""

import asyncio
import threading
import signal
import logging
import functools
from enum import Enum

LOGGER = logging.getLogger(__name__)


class _Singleton(type):
    """Metaclass for implementing a singleton."""
    def __init__(self, *args, **kwargs):
        self.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super().__call__(*args, **kwargs)
            return self.__instance
        else:
            return self.__instance


class AsyncThread(metaclass=_Singleton):
    """This class holds references to a separate thread which runs an asyncio event loop."""

    def __init__(self) -> None:
        """Create a thread and set up an asyncio event loop in it."""
        self._shutdown_sentinel = False

        def _start_event_loop_thread() -> None:
            """Run an asyncio event loop inside this thread."""
            asyncio.set_event_loop(self.loop)
            LOGGER.info(f'Starting asyncio loop in thread: {self.thread.name}.')
            self.loop.run_forever()


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
                                       daemon=False)
        LOGGER.debug(f'Started thread {self.thread.name}.')
        self.thread.start()
        asyncio.run_coroutine_threadsafe(self._loop_monitor(), self.loop)



    async def _loop_monitor(self) -> None:
        """Monitor the loop."""
        while not self._shutdown_sentinel:
            LOGGER.debug(f'Event loop still running in thread: {self.thread.name}')
            await asyncio.sleep(1)

    async def _cancel_all_tasks(self):
        """Cancel all running tasks in the loop."""
        tasks = [task for task in asyncio.Task.all_tasks() if task is not
                 asyncio.tasks.Task.current_task()]
        for task in tasks:
            task.cancel()
        LOGGER.info(f'Cancelled {len(tasks)} running tasks.')

    async def _shutdown_signal_handler(self, sig: Enum) -> None:
        """Shut down the event loop cleanly."""
        LOGGER.info(f'Caught signal: {sig.name}. Shutting down...')
        self._shutdown_sentinel = True
        await self._cancel_all_tasks()
        self.loop.stop()

    def shutdown_async_thread(self) -> None:
        """Shutdown the running asyncio thread."""
        LOGGER.info(f'Shutting down...')
        self._shutdown_sentinel = True
        fut = asyncio.run_coroutine_threadsafe(self._cancel_all_tasks(), self.loop)
        while fut.running():
            LOGGER.debug(f'Waiting for asyncio tasks to finish...')
            asyncio.sleep(.1)
        self.loop.stop()
