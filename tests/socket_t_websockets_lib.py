import asyncio
import websockets
import logging
import sys

LOGGER = logging.getLogger(__name__)
logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


async def hello():
    async with websockets.connect(
            'ws://skyq:9006/as/system/status') as websocket:

        payload = await websocket.recv()
        print(f"{payload}")

asyncio.get_event_loop().run_until_complete(hello())
