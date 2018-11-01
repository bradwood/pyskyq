import logging
import sys
from functools import partial
from pathlib import Path

import pytest
import trio

from pyskyq import EPG, XMLTVListing

from .http_server import http_server
from .mock_constants import (SERVICE_DETAIL_1, SERVICE_DETAIL_2,
                             SERVICE_SUMMARY_MOCK, EPG_JSON)

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

LOGGER = logging.getLogger(__name__)


json_data = ""


async def test_EPG_sky_channels():

    epg = EPG('localhost', rest_port=8000)

    with pytest.raises(ValueError, match='No channels loaded.'):
        epg.get_channel_by_sid(2002)

    with trio.move_on_after(5):
        async with trio.open_nursery() as server_nursery:
            LOGGER.debug('in nursery')
            responses = [
                {
                    'target': '/as/services',
                    'status_code': 200,
                    'content_type': "application/json; charset=utf-8",
                    'body': SERVICE_SUMMARY_MOCK.encode('utf-8'),
                    'headers': {
                        'Connection': 'close'
                    },
                },
                {
                    'target': '/as/services/details/2002',
                    'status_code': 200,
                    'content_type': "application/json; charset=utf-8",
                    'body': SERVICE_DETAIL_1.encode('utf-8'),
                    'headers': {
                        'Connection': 'close'
                    },
                },
                {
                    'target': '/as/services/details/2306',
                    'status_code': 200,
                    'content_type': "application/json; charset=utf-8",
                    'body': SERVICE_DETAIL_2.encode('utf-8'),
                    'headers': {
                        'Connection': 'close'
                    },
                },
            ]

            await server_nursery.start(trio.serve_tcp, partial(http_server, responses=responses), 8000)
            # await trio.serve_tcp(partial(http_server, responses=responses), 8000)
            LOGGER.debug('started server.')
            await epg.load_skyq_channel_data()

    assert isinstance(epg, EPG)
    assert len(epg._channels) == 2
    assert epg.get_channel_by_sid(2002).c == "101"
    assert epg.get_channel_by_sid(2002).t == "BBC One Lon"
    assert epg.get_channel_by_sid(2002).name == "BBC One Lon"
    assert epg.get_channel_by_sid('2002').c == "101"
    assert epg.get_channel_by_sid('2002').t == "BBC One Lon"
    assert epg.get_channel_by_sid('2002').name == "BBC One Lon"

    assert epg.get_channel_by_sid(2002).isbroadcasting is True
    assert "BBC ONE for Greater London and the surrounding area." in \
        epg.get_channel_by_sid(2002).upgradeMessage

    assert "Dave is the home of witty banter with quizcoms, cars and comedies." in \
        epg.get_channel_by_sid(2306).upgradeMessage

    with pytest.raises(ValueError, match='Sid:1234567 not found.'):
        epg.get_channel_by_sid(1234567)

    global json_data
    json_data = epg.as_json()   # save state here so we can use in the next test.


xmlfile_path = Path(__file__).resolve().parent.joinpath('parse_xmltv_data.xml')


def test_apply_EPG_XMLTV_listing():

    epg = EPG('localhost', rest_port=8000)

    global json_data

    epg.from_json(json_data)

    l = XMLTVListing('http://host.com/some/feed')
    l._full_path = xmlfile_path

    with pytest.raises(ValueError, match='No XMLTVListing file found.'):
        epg.apply_XMLTVListing(l)

    l._downloaded = True

    # now test the xml loading.
    epg.apply_XMLTVListing(l)

    assert epg.get_channel_by_sid(2002).xmltv_id == 'f3932e75f691561adbe3b609369e487b'
    assert epg.get_channel_by_sid(2002).xmltv_display_name == 'BBC One Lon'
    assert epg.get_channel_by_sid(2002).xmltv_icon_url.human_repr() == 'http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png'


def test_from_json():
    epg = EPG('localhost')
    epg.from_json(EPG_JSON)

    assert epg.get_channel_by_sid(2002).c == "101"
    assert epg.get_channel_by_sid(2002).t == "BBC One Lon"
    assert epg.get_channel_by_sid(2002).name == "BBC One Lon"
