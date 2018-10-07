import logging
import sys
from pathlib import Path
import pytest

from pyskyq.listing import Listing

from .isloated_filesystem import isolated_filesystem

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

def test_listing_init():
    # used to set up and tear down a temp dir for these tests.
    with isolated_filesystem():
        with pytest.raises(ValueError, match='Bad URL passed.'):
            l = Listing('blah')

        with pytest.raises(TypeError, match='path must be a string or Path object.'):
            l = Listing('http://blah.com/', 6)

        m = Listing('http://blah.com/')
        assert m._url == 'http://blah.com/'
        assert isinstance(m._path, Path)
        assert str(m._path) == '.epg_data'
        assert m.__repr__() == "<List: url='http://blah.com/', path='.epg_data', filename='1a69413b99ac80f93df562fcc3e2e0646708789a1cf80f5c0494813c9cc5b2d4.xml'>"
        assert m._path.is_dir()

        n = Listing('http://blah.com/', '.str_path')
        assert n._url == 'http://blah.com/'
        assert isinstance(n._path, Path)
        assert str(n._path) == '.str_path'

        assert m == n
        assert m._filename == n._filename
        assert m.__hash__() == n.__hash__()

def test_listing_fetch(mocker):
    # mocking class
    pass
    # see https://github.com/CircleUp/aresponses

    # class jsonmock:
    #     @staticmethod
    #     async def json():
    #         return json.loads(SERVICE_SUMMARY_MOCK)

    # client_response = asyncio.Future()
    # client_response.set_result(jsonmock)

    # a = mocker.patch('aiohttp.ClientSession.get', new_callable=AsyncContextManagerMock)
    # a.return_value = client_response

    # loop = asyncio.get_event_loop()
    # epg = EPG('test_load_channel_list_fake_host')
    # loop.run_until_complete(epg._load_channel_list())

    # assert isinstance(epg, EPG)
    # assert len(epg._channels) == 2
    # assert epg.get_channel(2002).c == "101"
    # assert epg.get_channel(2002).t == "BBC One Lon"
    # assert epg.get_channel(2002).name == "BBC One Lon"
    # assert epg.get_channel('2002').c == "101"
    # assert epg.get_channel('2002').t == "BBC One Lon"
    # assert epg.get_channel('2002').name == "BBC One Lon"
