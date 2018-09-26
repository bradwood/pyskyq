import asyncio
import logging
import sys

import aiohttp

LOGGER = logging.getLogger(__name__)
logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://skyq:9006/as/system/status') as ws:
            payload = await ws.receive()
            print(payload.text)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
