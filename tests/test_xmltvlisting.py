import logging
import sys
from datetime import datetime
from functools import partial
from pathlib import Path

import pytest
import trio
from yarl import URL

from pyskyq import XMLTVListing

from .http_server import http_server
from .isloated_filesystem import isolated_filesystem

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
                    format=logformat)

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


xmlfile_path = Path(__file__).resolve().parent.joinpath('parse_xmltv_data.xml')


async def test_download():
    with isolated_filesystem():
        with trio.move_on_after(5):
            async with trio.open_nursery() as server_nursery:
                LOGGER.debug('in nursery')
                async with await trio.open_file(xmlfile_path, 'r') as fd:
                    data = await fd.read()
                responses = [
                    {
                        'target': '/feed/6715',
                        'status_code': 200,
                        'content_type': "application/xml",
                        'body': bytearray(data.encode('utf-8')),
                        'headers': {
                            'Last-Modified': 'Mon, 08 Oct 2018 01:50:19 GMT',
                            'Connection': 'close',
                        },

                    },
                ]

                await server_nursery.start(trio.serve_tcp, partial(http_server, responses=responses), 8000)
                LOGGER.debug('started server.')


                l = XMLTVListing('http://localhost:8000/feed/6715')
                assert not l._downloaded
                await l.fetch()
                assert l._downloaded
                assert l.file_path.is_file()
                assert l.last_modified == datetime(2018, 10, 8, 1, 50, 19, 0)

                with open(xmlfile_path, 'rb') as src, open(l.file_path, 'rb') as dest:
                    assert src.read(-1) == dest.read(-1)


async def test_download_no_last_modified():
    with isolated_filesystem():
        with trio.move_on_after(5):
            async with trio.open_nursery() as server_nursery:
                LOGGER.debug('in nursery')
                async with await trio.open_file(xmlfile_path, 'r') as fd:
                    data = await fd.read()
                responses = [
                    {
                        'target': '/feed/6715',
                        'status_code': 200,
                        'content_type': "application/xml",
                        'body': bytearray(data.encode('utf-8')),
                        'headers': {
                            'Connection': 'close',
                        },

                    },
                ]

                await server_nursery.start(trio.serve_tcp, partial(http_server, responses=responses), 8000)
                LOGGER.debug('started server.')

                l = XMLTVListing('http://localhost:8000/feed/6715')
                assert not l._downloaded
                await l.fetch()
                assert l._downloaded
                assert l.file_path.is_file()
                assert l.last_modified is None

                with open(xmlfile_path, 'rb') as src, open(l.file_path, 'rb') as dest:
                    assert src.read(-1) == dest.read(-1)


xmlfile_path_gz = Path(__file__).resolve().parent.joinpath('parse_xmltv_data.xml.gz')


async def test_download_gzipped():
    with isolated_filesystem():
        with trio.move_on_after(5):
            async with trio.open_nursery() as server_nursery:
                LOGGER.debug('in nursery')
                async with await trio.open_file(xmlfile_path_gz, 'rb') as fd:
                    data = await fd.read()
                responses = [
                    {
                        'target': '/feed/6715',
                        'status_code': 200,
                        'content_type': "application/xml",
                        'body': data,
                        'headers': {
                            'Last-Modified': 'Mon, 08 Oct 2018 01:50:19 GMT',
                            'Connection': 'close',
                            'Content-Encoding': 'gzip',
                        },

                    },
                ]

                await server_nursery.start(trio.serve_tcp, partial(http_server, responses=responses), 8000)
                LOGGER.debug('started server.')

                l = XMLTVListing('http://localhost:8000/feed/6715')
                assert not l._downloaded
                await l.fetch()
                assert l._downloaded
                assert l.file_path.is_file()
                assert l.last_modified == datetime(2018, 10, 8, 1, 50, 19, 0)

                # note, we assert equivalence with the unzipped file to verify uncompression worked.
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
