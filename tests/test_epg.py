import asyncio
import json
import logging
import sys
import time
from pathlib import Path

import pytest
from asynctest import CoroutineMock, MagicMock

from pyskyq import EPG, Channel, XMLTVListing, channel_from_skyq_service

from .asynccontextmanagermock import AsyncContextManagerMock
from .isloated_filesystem import isolated_filesystem
from .mock_constants import (SERVICE_DETAIL_1, SERVICE_DETAIL_2,
                             SERVICE_SUMMARY_MOCK)

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format=logformat)  # datefmt="%Y-%m-%d %H:%M:%S"

json_data = ""

def test_EPG_sky_channels(mocker):

    jsonmock_invocation_count = 0

    class jsonmock:

        @staticmethod
        async def json():
            nonlocal jsonmock_invocation_count
            jsonmock_invocation_count += 1
            if jsonmock_invocation_count == 1:
                return json.loads(SERVICE_SUMMARY_MOCK)
            if jsonmock_invocation_count == 2:
                return json.loads(SERVICE_DETAIL_1)
            if jsonmock_invocation_count == 3:
                return json.loads(SERVICE_DETAIL_2)


    client_response = asyncio.Future()
    client_response.set_result(jsonmock)

    a = mocker.patch('aiohttp.ClientSession.get', new_callable=AsyncContextManagerMock)
    a.return_value = client_response

    epg = EPG('test_load_channel_list_fake_host')

    with pytest.raises(ValueError, match='No channels loaded.'):
        epg.get_channel_by_sid(2002)

    epg.load_skyq_channel_data()

    time.sleep(2)
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

def test_apply_EPG_XMLTV_listing(mocker):

    # set up the epg object with sky data.
    jsonmock_invocation_count = 0

    class jsonmock:
        @staticmethod
        async def json():
            nonlocal jsonmock_invocation_count
            jsonmock_invocation_count += 1
            if jsonmock_invocation_count == 1:
                return json.loads(SERVICE_SUMMARY_MOCK)
            if jsonmock_invocation_count == 2:
                return json.loads(SERVICE_DETAIL_1)
            if jsonmock_invocation_count == 3:
                return json.loads(SERVICE_DETAIL_2)

    client_response = asyncio.Future()
    client_response.set_result(jsonmock)

    a = mocker.patch('aiohttp.ClientSession.get', new_callable=AsyncContextManagerMock)
    a.return_value = client_response

    epg = EPG('test_load_channel_list_fake_host')

    l = XMLTVListing('http://host.com/some/feed')
    l._full_path = Path(__file__).resolve().parent.joinpath('parse_xmltv_data.xml')
    l._downloaded = True

    epg.load_skyq_channel_data()
    time.sleep(2)

    global json_data
    json_data = epg.as_json()
    # now test the xml loading.
    epg.apply_XMLTVListing(l)

    assert epg.get_channel_by_sid(2002).xmltv_id == 'f3932e75f691561adbe3b609369e487b'
    assert epg.get_channel_by_sid(2002).xmltv_display_name == 'BBC One Lon'
    assert epg.get_channel_by_sid(2002).xmltv_icon_url.human_repr() == 'http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png'


xmlfile_path = Path(__file__).resolve().parent.joinpath('parse_xmltv_data.xml')

def test_add_cronjob(mocker):
    # set up the epg object with sky data.
    epg = EPG('testing_cron')

    global json_data
    epg.from_json(json_data)

    assert epg.get_channel_by_sid(2002).name == "BBC One Lon"

    # now mock the xml server
    class xmlmock:
        status = 200
        headers = {'Last-Modified': 'Mon, 08 Oct 2018 01:50:19 GMT'}


        @staticmethod
        async def read(*args, **kwargs):
            with open(xmlfile_path, 'rb') as fil:
                return fil.read()


    xmlresponse = asyncio.Future()
    xmlresponse.set_result(xmlmock)

    b = mocker.patch('aiohttp.ClientSession.get', new_callable=AsyncContextManagerMock)
    b.return_value = xmlresponse

    # and finally test the cronjob.
    # with isolated_filesystem():

    l = XMLTVListing('http://host.com/some/feed')
    epg.add_XMLTV_listing_cronjob(l, "1 1 1 1 1", run_now=True)

    time.sleep(3)
    assert epg.get_channel_by_sid(2002).xmltv_id == 'f3932e75f691561adbe3b609369e487b'
    assert epg.get_channel_by_sid(2002).xmltv_display_name == 'BBC One Lon'
    assert epg.get_channel_by_sid(2002).xmltv_icon_url.human_repr() == 'http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png'

    time.sleep(2)
    epg.delete_XMLTV_listing_cronjob(l)


@pytest.mark.asyncio
async def tesst_add_cronjob(aresponses):
    # mock out the XMLTV server.
    # xmlfile_path = Path(__file__).resolve().parent.joinpath('fetch_payload.txt')
    # async def get_XML_handler_200(request):
    #     with open(xmlfile_path, 'r') as fd:
    #         data = fd.read()
    #         hdr = {'Last-Modified': 'Mon, 08 Oct 2018 01:50:19 GMT'}
    #         resp = aresponses.Response(status=200, reason='OK', body=data, headers=hdr)
    #     return resp

    # # mock out the SkyQ box.
    # async def get_skyq_service_summary(request):
    #     data = SERVICE_SUMMARY_MOCK
    #     #hdr = {'Last-Modified': 'Mon, 08 Oct 2018 01:50:19 GMT'}
    #     resp = aresponses.Response(status=200, reason='OK', body=data)
    #     return resp

    # async def get_skyq_detail_1(request):
    #     data = SERVICE_DETAIL_1
    #     hdr = {'Last-Modified': 'Mon, 08 Oct 2018 01:50:19 GMT'}
    #     resp = aresponses.Response(status=200, reason='OK', body=data, headers=hdr)
    #     return resp

    # async def get_skyq_detail_2(request):
    #     data = SERVICE_DETAIL_2
    #     hdr = {'Last-Modified': 'Mon, 08 Oct 2018 01:50:19 GMT'}
    #     resp = aresponses.Response(status=200, reason='OK', body=data, headers=hdr)
    #     return resp

    aresponses.add(aresponses.ANY, '/as/services', 'get', response=SERVICE_SUMMARY_MOCK)
    aresponses.add(aresponses.ANY, '/as/services/details/2002', 'get', response=SERVICE_DETAIL_1)
    aresponses.add(aresponses.ANY, '/as/services/details/2306', 'get', response=SERVICE_DETAIL_2)


    # aresponses.add('foo.com', '/feed/6715', 'get', response=get_XML_handler_200)

    # now run the test
    with isolated_filesystem():

        epg = EPG('skybox', rest_port=80)

        epg.load_skyq_channel_data()
        await asyncio.sleep(10)
        assert epg.get_channel_by_sid(2002).name == "BBC One Lon"


        l = XMLTVListing('http://foo.com/feed/6715')
        epg.add_XMLTV_listing_cronjob(l, "* * * * * *", run_now=True)

        await asyncio.sleep(3)
        assert epg.get_channel_by_sid(2002).xmltv_id == 'f3932e75f691561adbe3b609369e487b'
        assert epg.get_channel_by_sid(2002).xmltv_display_name == 'BBC One Lon'
        assert epg.get_channel_by_sid(2002).xmltv_icon_url.human_repr() == 'http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png'
