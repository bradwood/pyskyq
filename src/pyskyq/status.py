"""This module implements the Status class.

It schedules subscriptions/polling tasks that monitor various events emitted
from the SkyQ box. Each of these will await an event (e.g. on a websocket or
uPNP subscription) and then update object attributes when neccessary.
"""
import asyncio
import json
import logging
import socket
from typing import Dict

import websockets

from .constants import REST_PORT, REST_STATUS_URL
# from .asyncthread import AsyncThread
LOGGER = logging.getLogger(__name__)

# at = AsyncThread()
class Status:
    """This class provides real-time access to the status of the SkyQ box.

    It uses an internal :py:mod:`asyncio`-based concurrency object used to
    subscribe to various web-socket and/or uPNP based events.

    It also logs all status changes.

    Args:
        host (str): String with resolvable hostname or IPv4 address to SkyQ box.
        port (int, optional): Port number to use to connect to the Remote REST API.
            Defaults to the standard port used by SkyQ boxes which is ``9006``.
        ws_url_path (str, optional): Path string to append to the URL, defaults to
            ``/as/system/status``
        ws_timeout (int, optional): Web socket connection timeout. Defaults is 20 sec.
        ping_timeout (int, optional): Web socket ping timeout. Defaults is 10 sec.

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
        """Initialise the Status object."""
        self.host: str = host
        self.port: int = port
        self.standby: bool = False
        self.ws_url: str = f'ws://{self.host}:{self.port}{ws_url_path}'

        self._shutdown_sentinel: bool = False # used to trigger a clean shutdown.

        self._ws_timeout: int = ws_timeout
        self._ping_timeout: int = ping_timeout
        LOGGER.debug(f"Initialised Status object object with host={host}, port={port}")


    async def _ws_subscribe(self) -> None:
        """Fetch data from web socket asynchronously.

        This  method fetches data from a web socket asynchronously. It is used to
        subscribe to websockets of the SkyQ box.

        """
        LOGGER.debug(f'Setting up web socket listener on {self.ws_url}.')

        while not at.shutdown_sentinel and not self._shutdown_sentinel:
        # outer loop that will restart every time the connection fails (if sentinel says its okay)
            LOGGER.debug('No shutdown sentinel set, so (re)-starting websocket connection.')
            try:
                async with websockets.connect(self.ws_url) as ws:

                    while not at.shutdown_sentinel and not self._shutdown_sentinel:
                        # listener loop
                        LOGGER.debug('Starting websocket listener loop iteration...')
                        try:
                            LOGGER.debug('Waiting for data...')
                            payload = await asyncio.wait_for(ws.recv(), timeout=self._ws_timeout)
                            LOGGER.debug(f'Web-socket data received. size = {len(payload)}')
                        except (asyncio.TimeoutError,
                                websockets.exceptions.ConnectionClosed) as err:
                            LOGGER.debug(f'Websocket timed out or was closed. Error = {err}')
                            try:
                                if at.shutdown_sentinel or self._shutdown_sentinel:
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
                await asyncio.sleep(.1)
                LOGGER.debug(f'Could not connect to web socket. Error={sc_err}. Retrying...')
                # sleep a bit, log it, then try again
                continue


    def create_event_listener(self) -> None:
        """Create status event listener coroutine and schedule it.

        This method spawns a coroutine that runs using the facility provided by
        :class:`.asyncthread.AsyncThread`. The coroutine manages all
        subscriptions to various endpoints/services on the SkyQ box and takes
        the appropriate update actions when these events fire.

        This means that you will be able to simply refer to properties like
        :attr:`standby` and rely on them to report the _current_ status from the
        SkyQ Box.

        """
        at.run(self._ws_subscribe())


    async def _handle(self,
                      payload: Dict,
                      ) -> None:
        """Update status properties with payload."""
        self.standby = payload['hdmi']['state'] != 'available'
        LOGGER.info(f'standby =  {str(self.standby)}')


    def shudown_event_listener(self) -> None:
        """Terminate the event listener thread and event loop."""
        self._shutdown_sentinel = True
