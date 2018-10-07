import asyncio
import logging
import sys
from pathlib import Path
import pytest
from aiohttp import MultipartWriter

from pyskyq.listing import Listing

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
async def test_listing_fetch(aresponses):

    # custom handler to respond with chunks
    async def my_handler(request):
        LOGGER.debug('in handler')
        my_boundary = 'boundary'
        xmlfile_path = Path(__file__).resolve().parent.joinpath('6729.xml')
        LOGGER.debug('xml file path = {xmlfile_path}')
        hdr = {
            "Content-Type": "application/xml"
        }
        resp = aresponses.Response(status=200,
                                   reason='OK',
                                   headers=hdr,
                                   )
        resp.enable_chunked_encoding()
        await resp.prepare(request)

        xmlfile = open(xmlfile_path, 'rb')

        LOGGER.debug('opened xml file for serving')
        with MultipartWriter('application/xml', boundary=my_boundary) as mpwriter:
            mpwriter.append(xmlfile, hdr)
            LOGGER.debug('appended chunk')
            await mpwriter.write(resp, close_boundary=True)
            LOGGER.debug('wrote chunk')

        xmlfile.close()
        return resp

    aresponses.add('foo.com', '/feed/6715', 'get', response=my_handler)

    # with isolated_filesystem():
    l = Listing('http://foo.com/feed/6715')

    await l.fetch()

    assert l._path.joinpath(l._filename).is_file()
