""" This module implements the Status class.

It implements an :py:mod:`asyncio`-based event loop in a separate thread. It will then
schedule subscriptions/polling tasks that subscribe to various events in async
co-routines/tasks and add them to the event loop. Each of these will:

* await an event (e.g. on a websocket or uPNP subscription) and then invoke a callback
  before resuming awaiting.
* potentially asyncio.sleep() before resuming... (is this needed? 🤔)
* each callback should update the appropriate attribute on the class and log the event.

"""

import asyncio
import functools
import json
import logging
import signal
from threading import Thread
from typing import Dict

import websockets

from .constants import REST_PORT, REST_STATUS_URL

LOGGER = logging.getLogger(__name__)

class Status:
    """ This class implements the Status object, an internal :py:mod:`asyncio`-based
    event loop used to subscribe to various web-socket and/or uPNP based events, and
    methods/properties used to access the associated status attributes.

    It also logs all status changes.

    Attributes:
        host (str): Hostname or IPv4 address of SkyQ Box.
        port (int): Port number to use to connect to the REST HTTP server.
            Defaults to the standard port used by SkyQ boxes which is 9006.
        ws_url (str): ``ws://`` based URL to the SkyQ Box websocket.
        standby (bool): A Boolean indicator stating whether the box is in
            Standby Mode or not.

    Todo:
        * Generalise to handle different types of event suscriptions.

    """
    def __init__(self,
                 host: str,
                 *,
                 port: int = REST_PORT,
                 ws_url_path: str = REST_STATUS_URL,
                 ) -> None:
        """Initialise the Status object.

        Args:
            host (str): String with resolvable hostname or IPv4 address to SkyQ box.
            port (int, optional): Port number to use to connect to the Remote REST API.
                Defaults to the standard port used by SkyQ boxes which is ``9006``.
            ws_url_path (str, optional): Path stiring to append to the URL, defaults to
                ``/as/system/status``

        Returns:
            None

        """

        self.host: str = host
        self.port: int = port
        LOGGER.debug(f"Initialised Status object object with host={host}, port={port}")
        self.standby: bool = False
        # TODO turn into @property and make non-writeable.
        self.ws_url = f'ws://{self.host}:{self.port}{ws_url_path}'
        self._event_thread = None # the thread which runs the asyncio event loop
        self._event_loop = None  # the event loop which runs in the thread.
        self._shutdown_sentinel = False # used to trigger a clean shutdown.
        self.create_event_listener()


    async def _ws_subscribe(self) -> Dict:
        """ Fetch data from web socket asynchronously.

        This helper method fetches data from a web socket asynchronously. It is used to
        fetch subscribe to websockets of the SkyQ box.

        Returns:
            dict: The body of data returned.

        """
        LOGGER.debug(f'Setting up web socket listener on {self.ws_url}.')

        async with websockets.connect(self.ws_url) as ws:
            async for payload in ws:
                LOGGER.debug('Web-socket data received.')
                asyncio.create_task(self._handle(json.loads(payload)))

    def create_event_listener(self) -> None:
        """Create asyncio event loop thread for status event handling.

        Note:
            This method spawns a separate thread and in that thread it runs
            an :py:mod:`asyncio` based event loop. This event loop manages
            all subscriptions to various endpoints/services on the SkyQ box
            and invokes the appropriate callbacks when these events fire.

            This means that you will be able to simply refer to properties
            like :attr:`standby` and rely on them to report the __current__
            status from the SkyQ Box.

        """

        def _start_event_loop_thread() -> None:
            """Kick off a new asyncio eventloop in a dedicated thread.

            This method implements the thread. """
            LOGGER.debug(f"Asyncio event loop thread running...")
            self._shutdown_sentinel = False
            asyncio.set_event_loop(self._event_loop)
            self._event_loop.run_forever()

        # create a new loop
        self._event_loop = asyncio.new_event_loop()
        self._event_loop.add_signal_handler(signal.SIGTERM,
                                       functools.partial(asyncio.ensure_future,
                                                         self._shutdown_signal_handler(signal.SIGTERM)))

        # Assign the loop to another thread
        self._event_thread = Thread(target=_start_event_loop_thread)
        self._event_thread.start()

        asyncio.run_coroutine_threadsafe(
            self._ws_subscribe(),
            self._event_loop
        ).add_done_callback(lambda future: print(future.result()))

    async def _handle(self,
                      payload: Dict,
                      ) -> None:
        """Update status properties with payload"""
        self.standby = payload['hdmi']['state'] != 'available'
        LOGGER.info(f'standby =  {str(self.standby)}')



# TODO -- refactor the shutdown code to use a sentinel... It should
# shutdown the socket connection and then allow everything to finish up.
#

    async def _shutdown_signal_handler(self,
                                       sig: int,
                                       ) -> None:
        """Shut down event loop cleanly"""

        LOGGER.info(f'Caught {sig.name} signal')
        self._shutdown_sentinel = True  # trigger websocked to shutdown cleanly.
        tasks = [task for task in asyncio.Task.all_tasks() if task is not
                asyncio.tasks.Task.current_task()]
        results = await asyncio.gather(*tasks, return_exceptions=True).cancel()
        LOGGER.info(f'Finished awaiting cancelled tasks, results = {results}')
        self._event_loop.stop()
        self._event_loop.close()

    def shudown_event_listener(self) -> None:
        """Terminate the event listener thread and event loop."""
        self._shutdown_sentinel = True  # trigger websocked to shutdown cleanly.
        self._event_loop.create_task(self._shutdown_signal_handler(signal.SIGTERM))
        self._event_loop = None
        LOGGER.info(f'Event listener shut down...')
