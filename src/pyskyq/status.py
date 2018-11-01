"""This module implements the Status class.

It schedules subscriptions/polling tasks that monitor various events emitted
from the SkyQ box. Each of these will await an event (e.g. on a websocket or
uPNP subscription) and then update object attributes when neccessary.
"""
import json
import logging
from contextlib import asynccontextmanager

import h11  # this import needed for the monkey-patch
import trio
from trio_websocket import open_websocket_url, WebSocketConnection

from dataclasses import dataclass, field

from ._h11_header_monkey_patch import write_headers_titlecase
from .constants import REST_PORT, REST_STATUS_URL

LOGGER = logging.getLogger(__name__)

# Monkey patch h11 HTTP header writing to override case. SkyQ needs this to be happy.
h11._writers.write_headers = write_headers_titlecase # pylint: disable=protected-access

@dataclass
class Status:
    """This dataclass provides real-time access to the status of the SkyQ box.

    Example:

        It should be access via an asynchronous context manager like so::

            async def report_box_online():
                async with get_status('skyq') as stat:
                    while True:
                        if stat.standby:
                            print('The SkyQ Box is in Standby Mode')
                        else:
                            print('The SkyQ Box is in Online Mode')
                        await trio.sleep(1)

            try:
                print("Type Ctrl-C to exit.")
                trio.run(report_box_online)
            except KeyboardInterrupt:
                raise SystemExit(0)

    Attributes:
        online (bool): Is the box in online?

    Todo:
        Add more attributes once the JSON has been figured out.

    """

    online: bool = field(init=False, default=False)


@asynccontextmanager
async def get_status(host: str,
                     *,
                     port: int = REST_PORT,
                     ws_url_path: str = REST_STATUS_URL,
                     ):
    """Yield a Status object through an asynchronous context manager.

    This async function yields a :class:`Status` object asynchronously to enable
    the calling code to interact with is while it is updated via a websocket connection
    to the SkyQ box.

    Args:
        host (str): Hostname/IP address of the SkyQ Box
        port (int): Port number to connect to. Defaults to
            :data:`~pyskyq.constants.REST_PORT`.
        w_url_path (str): URL path to the websocket. Defaults to
            :data:`~pyskyq.constants.REST_STATUS_URL`

    Yields:
        status (Status): A :class:`Status` object.

    """
    ws_url: str = f'ws://{host}:{port}{ws_url_path}'
    LOGGER.debug(f'About to connect to: {ws_url}')
    status = Status()

    # no try/except as we want the exception thown up the stack if the socket's closed.
    async with open_websocket_url(ws_url) as conn:
        LOGGER.debug(f'Created connection to socket: {ws_url}')
        async with trio.open_nursery() as ws_nursery:
            LOGGER.debug('In ws_nursery yielding loop...')
            LOGGER.debug('Backgrounding connection_handler...')
            ws_nursery.start_soon(_handle_connection, status, conn)
            LOGGER.debug(f'Handler backgrounded. Yielding...')
            yield status


async def _handle_connection(s: Status, conn: WebSocketConnection):
    LOGGER.debug(f'Entered connection handler...{conn}')
    async with trio.open_nursery() as handler_nursery:
        LOGGER.debug('Created handler_nursery...')
        LOGGER.debug('Backgrounded _process_messages...')
        handler_nursery.start_soon(_process_messages, s, conn)

# TODO parse the entire payload and load it into Status.
async def _process_messages(s: Status, conn: WebSocketConnection):
    LOGGER.debug('Inside _process_messages...')
    while True:
        LOGGER.debug(f'conn: {conn}')
        data_json = await conn.get_message()
        LOGGER.debug('Got data from websocket...')
        data = json.loads(data_json)
        LOGGER.debug(f'Parsed JSON data from websocket.')
        s.online = data['hdmi']['state'] == 'available'
