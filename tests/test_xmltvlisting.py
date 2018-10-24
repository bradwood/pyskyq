import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import aiohttp
import pytest
from aiohttp import MultipartWriter
from dateutil import tz
from yarl import URL

from pyskyq import XMLTVListing

from .isloated_filesystem import isolated_filesystem

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

LOGGER = logging.getLogger(__name__)

def test_xmltvlisting_init():
    # used to set up and tear down a temp dir for these tests.
    with isolated_filesystem():
        with pytest.raises(TypeError, match='path must be a string or Path object.'):
            l = XMLTVListing('http://blah.com/feed/6715', 6)

        Path.cwd().joinpath('somedir').mkdir()  # test the case where the directory is already there.
        m = XMLTVListing('http://blah.com/feed/6715', 'somedir')
        assert m._url == URL('http://blah.com/feed/6715')
        assert isinstance(m._path, Path)
        assert str(m._path) == 'somedir'
        assert "<XMLTVListing: url='http://blah.com/feed/6715', path='somedir'" in m.__repr__()
        assert m._path.is_dir()
        assert m.url == URL('http://blah.com/feed/6715')

        n = XMLTVListing(URL('http://blah.com/feed/6715'), '.str_path')
        assert n._url == URL('http://blah.com/feed/6715')
        assert isinstance(n._path, Path)
        assert str(n._path) == '.str_path'

        assert m == n
        assert m._filename == n._filename
        assert m.__hash__() == n.__hash__()


xmlfile_path = Path(__file__).resolve().parent.joinpath('fetch_payload.txt')

@pytest.mark.asyncio
async def test_xmltvlisting_fetch_200(aresponses):

    async def get_handler_200(request):
        with open(xmlfile_path, 'r') as fd:
            data = fd.read()
            hdr = {'Last-Modified': 'Mon, 08 Oct 2018 01:50:19 GMT'}
            resp = aresponses.Response(status=200, reason='OK', body=data, headers=hdr)
        return resp


    aresponses.add('foo.com', '/feed/6715', 'get', response=get_handler_200)

    with isolated_filesystem():
        l = XMLTVListing('http://foo.com/feed/6715')
        assert not l._downloaded
        await l.fetch()
        assert l._downloaded
        assert l.file_path.is_file()
        assert l.last_modified == datetime(2018,10,8,1,50,19,0)

        with open(xmlfile_path, 'rb') as src, open(l.file_path, 'rb') as dest:
            assert src.read(-1) == dest.read(-1)


@pytest.mark.asyncio
async def test_xmltvlisting_fetch_206(aresponses):

    async def get_handler_206(request):
        LOGGER.debug(f'request headers = {request.headers}')
        rng = request.http_range
        LOGGER.debug(f'Range = {rng}. Start = {rng.start}. Stop = {rng.stop}. Diff = {rng.stop - rng.start}.')
        with open(xmlfile_path, 'rb') as f:
            f.seek(rng.start)
            data = f.read(rng.stop - rng.start)
            LOGGER.debug(f'data = {data}')
            hdr = {
                'Content-Range': f'bytes {rng.start}-{rng.stop - 1 }/{xmlfile_path.stat().st_size}',
            }
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
        l = XMLTVListing('http://foo.com/feed/6715')
        await l.fetch(range_size=100)
        assert l.file_path.is_file()

        with open(xmlfile_path, 'rb') as src, open(l.file_path, 'rb') as dest:
            assert src.read(-1) == dest.read(-1)

#TODO -- add bad xml file test here.
def test_channel_parse():
    l = XMLTVListing('http://foo.com/feed/6715')

    with pytest.raises(OSError, match='File not downloaded, or download is currently in flight.'):
        for chan in l.parse_channels():
            pass # should throw an error as file is not downloaded.

    l._full_path = Path(__file__).resolve().parent.joinpath('parse_xmltv_data.xml')
    l._downloaded = True

    for i,chan in enumerate(l.parse_channels()):

        LOGGER.debug(chan.xmltv_id)
        LOGGER.debug(chan.xmltv_icon_url)
        LOGGER.debug(chan.xmltv_display_name)

        if i == 0:
            assert chan.xmltv_id == 'f3932e75f691561adbe3b609369e487b'
            assert chan.xmltv_display_name == 'BBC One Lon'
            assert chan.xmltv_icon_url.human_repr() == 'http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png'
        elif i == 1:

            assert chan.xmltv_id == 'a3c70f4c25110a9ca84f7c604023ee6c'
            assert chan.xmltv_display_name == 'Dave'
            assert chan.xmltv_icon_url.human_repr() == 'http://www.xmltv.co.uk/images/channels/a3c70f4c25110a9ca84f7c604023ee6c.png'
        else:
            break
