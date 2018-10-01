""" This module implements the Status class.

It implements an :py:mod:`asyncio`-based event loop in a separate thread. It will then
schedule subscriptions/polling tasks that subscribe to various events in async
co-routines/tasks and add them to the event loop. Each of these will await an event
(e.g. on a websocket or uPNP subscription) and then respond when neccessary.

"""

import asyncio
import functools
import json
import logging
import signal
import socket
from threading import Thread
from typing import Dict

import websockets

from .constants import REST_PORT, REST_STATUS_URL

LOGGER = logging.getLogger(__name__)

# pylint: disable=too-many-instance-attributes
# For now this will do until standby gets refactored into a dict of items.

class Status:
    """ This class implements the Status object, an internal :py:mod:`asyncio`-based
    event loop used to subscribe to various web-socket and/or uPNP based events.

    It also logs all status changes.

    Attributes:
        host (str): Hostname or IPv4 address of SkyQ Box.
        port (int): Port number to use to connect to the REST HTTP server.
            Defaults to the standard port used by SkyQ boxes which is 9006.
        ws_url (str): ``ws://`` based URL to the SkyQ Box websocket.
        standby (bool): A Boolean indicator stating whether the box is in
            Standby Mode or not.


    """
    def __init__(self,
                 host: str,
                 *,
                 port: int = REST_PORT,
                 ws_url_path: str = REST_STATUS_URL,
                 ws_timeout: int = 20,
                 ping_timeout: int = 10,
                 ) -> None:
        """Initialise the Status object.

        Args:
            host (str): String with resolvable hostname or IPv4 address to SkyQ box.
            port (int, optional): Port number to use to connect to the Remote REST API.
                Defaults to the standard port used by SkyQ boxes which is ``9006``.
            ws_url_path (str, optional): Path stiring to append to the URL, defaults to
                ``/as/system/status``
            ws_timeout (int, optional): Web socket connection timeout. Defaults is 20 sec.
            ping_timeout (int, optional): Web socket ping timeout. Defaults is 10 sec.

        Returns:
            None

        """

        self.host: str = host
        self.port: int = port
        self.standby: bool = False
        # TODO turn into @property and make non-writeable.
        self.ws_url: str = f'ws://{self.host}:{self.port}{ws_url_path}'
        self._event_thread: Thread  # the thread which runs the asyncio event loop
        self._event_loop: asyncio.AbstractEventLoop   # the event loop which runs in the thread.
        self._shutdown_sentinel: bool = False # used to trigger a clean shutdown.
        self._ws_timeout: int = ws_timeout
        self._ping_timeout: int = ping_timeout
        LOGGER.debug(f"Initialised Status object object with host={host}, port={port}")


    async def _ws_subscribe(self) -> None:
        """ Fetch data from web socket asynchronously.

        This  method fetches data from a web socket asynchronously. It is used to
        fetch subscribe to websockets of the SkyQ box.

        """
        LOGGER.debug(f'Setting up web socket listener on {self.ws_url}.')

        while not self._shutdown_sentinel:  # while not being told to shut down
        # outer loop that will restart every time the connection fails (if sentinel says its okay)
            LOGGER.debug('No shutdown sentinel set, so (re)-starting websocket connection.')
            try:
                async with websockets.connect(self.ws_url) as ws:

                    while not self._shutdown_sentinel:
                        # listener loop
                        LOGGER.debug('Starting websocket listener loop iteration...')
                        try:
                            LOGGER.debug('Waiting for data...')
                            payload = await asyncio.wait_for(ws.recv(), timeout=self._ws_timeout)
                            LOGGER.debug(f'Web-socket data received. size = {len(payload)}')
                        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed) as err:  # pylint: disable=line-too-long
                            LOGGER.debug(f'Websocket timed out or was closed. Error = {err}')
                            try:
                                if self._shutdown_sentinel:
                                    LOGGER.debug(f'Shutdown triggered. Shutting down...')
                                    break # inner listening loop.
                                else:
                                    LOGGER.debug(f'Trying ping message...')
                                    pong = await ws.ping()
                                    await asyncio.wait_for(pong, timeout=self._ping_timeout)
                                    LOGGER.debug(f'Ping OK, keeping connection alive.')
                            except:  # pylint: disable=bare-except
                                LOGGER.debug(f'Ping timeout - retrying...')
                                break # inner listener loop
                        # process payload
                        LOGGER.debug(f'Invoking payload handler on received message...')
                        asyncio.create_task(self._handle(json.loads(payload)))

            except (socket.gaierror, ConnectionRefusedError) as sc_err:
                await asyncio.sleep(1)
                LOGGER.debug(f'Could not connect to web socket. Error={sc_err}. Retrying...')
                # sleep a bit, log it, then try again
                continue



    def create_event_listener(self) -> None:
        """Create asyncio event loop thread for status event handling.

        Note:
            This method spawns a separate thread and in that thread it runs
            an :py:mod:`asyncio` based event loop. This event loop manages
            all subscriptions to various endpoints/services on the SkyQ box
            and takes the appropriate update actions when these events fire.

            This means that you will be able to simply refer to properties
            like :attr:`standby` and rely on them to report the _current_
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
                                            functools.partial(asyncio.ensure_future,  # pylint: disable=line-too-long
                                                              self._shutdown_signal_handler(signal.SIGTERM)))  # pylint: disable=line-too-long

        # Assign the loop to another thread
        self._event_thread = Thread(target=_start_event_loop_thread, daemon=True)
        self._event_thread.start()

        asyncio.run_coroutine_threadsafe(
            self._ws_subscribe(),
            self._event_loop
        )


    async def _handle(self,
                      payload: Dict,
                      ) -> None:
        """Update status properties with payload."""
        self.standby = payload['hdmi']['state'] != 'available'
        LOGGER.info(f'standby =  {str(self.standby)}')


    async def _shutdown_signal_handler(self,
                                       sig: int,
                                       ) -> None:
        """Shut down event loop cleanly."""


        # mypy gets confused wit IntEnums
        LOGGER.info(f'Caught {sig.name} signal')  # type: ignore
        self._shutdown_sentinel = True  # trigger websocked to shutdown cleanly.
        tasks = [task for task in asyncio.Task.all_tasks() if task is not
                 asyncio.tasks.Task.current_task()]
        results = await asyncio.gather(*tasks, return_exceptions=True).cancel()  # type: ignore
        LOGGER.info(f'Finished awaiting cancelled tasks, results = {results}')
        self._event_loop.stop()
        self._event_loop.close()

    def shudown_event_listener(self) -> None:
        """Terminate the event listener thread and event loop."""
        self._shutdown_sentinel = True
