import asyncio
import aiohttp
import logging
import sys
from pathlib import Path
import pytest
from aiohttp import MultipartWriter

from pyskyq import Listing

from .isloated_filesystem import isolated_filesystem

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

LOGGER = logging.getLogger(__name__)

def test_listing_init():
    # used to set up and tear down a temp dir for these tests.
    with isolated_filesystem():
        with pytest.raises(ValueError, match='Bad URL passed.'):
            l = Listing('blah')

        with pytest.raises(TypeError, match='path must be a string or Path object.'):
            l = Listing('http://blah.com/feed/6715', 6)

        m = Listing('http://blah.com/feed/6715')
        assert m._url == 'http://blah.com/feed/6715'
        assert isinstance(m._path, Path)
        assert str(m._path) == '.epg_data'
        assert "<List: url='http://blah.com/feed/6715', path='.epg_data'" in m.__repr__()
        assert m._path.is_dir()

        n = Listing('http://blah.com/feed/6715', '.str_path')
        assert n._url == 'http://blah.com/feed/6715'
        assert isinstance(n._path, Path)
        assert str(n._path) == '.str_path'

        assert m == n
        assert m._filename == n._filename
        assert m.__hash__() == n.__hash__()


@pytest.mark.asyncio
async def test_listing_fetch_200(aresponses):

    async def get_handler_200(request):
        xmlfile_path = Path(__file__).resolve().parent.joinpath('fetch_payload.xml')
        LOGGER.debug(f'xml file path = {xmlfile_path}')
        with open(xmlfile_path, 'r') as fd:
            data = fd.read()
            resp = aresponses.Response(status=200, reason='OK', body=data)
        return resp


    aresponses.add('foo.com', '/feed/6715', 'get', response=get_handler_200)

    with isolated_filesystem():
        l = Listing('http://foo.com/feed/6715')
        await l.fetch()
        assert l._path.joinpath(l._filename).is_file()


@pytest.mark.asyncio
async def test_listing_fetch_206(aresponses):

    async def get_handler_206(request):
        xmlfile_path = Path(__file__).resolve().parent.joinpath('fetch_payload.xml')
        LOGGER.debug(f'xml file path = {xmlfile_path}')
        LOGGER.debug(f'request headers = {request.headers}')

        rng = request.http_range
        LOGGER.debug(f'Range = {rng}. Start = {rng.start}. Stop = {rng.stop}. Diff = {rng.stop - rng.start}.')
        with open(xmlfile_path, 'rb') as f:
            f.seek(rng.start)
            data = f.read(rng.stop - rng.start)
            LOGGER.debug(f'data = {data}')
            hdr = {'Content-Range': f'bytes {rng.start}-{rng.stop - 1 }/{xmlfile_path.stat().st_size}'}
            if rng.stop - 1 > xmlfile_path.stat().st_size:
                LOGGER.debug('Range request went too far...')
                resp = aresponses.Response(status=416, reason='Range Not Satisfiable', body=data)
            else:
                LOGGER.debug('Range request OK.')
                resp = aresponses.Response(status=206, reason='OK', body=data, headers=hdr)
            LOGGER.debug(f'resp header = {hdr}')
        return resp

    for _ in range(1000):
        aresponses.add('foo.com', '/feed/6715', 'get', response=get_handler_206)


    with isolated_filesystem():
        l = Listing('http://foo.com/feed/6715')
        await l.fetch(range_size=100)
        assert l._path.joinpath(l._filename).is_file()
