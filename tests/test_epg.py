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
                             SERVICE_SUMMARY_MOCK, FUZZY_CHANNELS_MOCK)

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
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

    with pytest.raises(ValueError, match='No XMLTVListing file found.'):
        epg.apply_XMLTVListing(l)

    l._downloaded = True

    epg.load_skyq_channel_data()
    time.sleep(2)

    global json_data
    json_data = epg.as_json()   # save state here so we can use in the next test.

    # now test the xml loading.
    epg.apply_XMLTVListing(l)

    assert epg.get_channel_by_sid(2002).xmltv_id == 'f3932e75f691561adbe3b609369e487b'
    assert epg.get_channel_by_sid(2002).xmltv_display_name == 'BBC One Lon'
    assert epg.get_channel_by_sid(2002).xmltv_icon_url.human_repr() == 'http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png'


xmlfile_path = Path(__file__).resolve().parent.joinpath('parse_xmltv_data.xml')

def test_cronjob(mocker):
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
    with isolated_filesystem():
        l = XMLTVListing('http://host.com/some/feed')

        l2 = XMLTVListing('http://host.com/some/feed/2')


        with pytest.raises(ValueError, match='Bad cronspec passed.'):
            epg.add_XMLTV_listing_cronjob(l, "Arthur 'Two Sheds' Jackson", run_now=True)


        epg.add_XMLTV_listing_cronjob(l, "1 1 1 1 1", run_now=True)
        epg.add_XMLTV_listing_cronjob(l2, "1 1 1 1 1", run_now=False)


        time.sleep(3)
        assert epg.get_channel_by_sid(2002).xmltv_id == 'f3932e75f691561adbe3b609369e487b'
        assert epg.get_channel_by_sid(2002).xmltv_display_name == 'BBC One Lon'
        assert epg.get_channel_by_sid(2002).xmltv_icon_url.human_repr() == 'http://www.xmltv.co.uk/images/channels/f3932e75f691561adbe3b609369e487b.png'

        with pytest.raises(ValueError, match='XMLTVListing already added.'):
            epg.add_XMLTV_listing_cronjob(l, "1 1 1 1 1", run_now=True)

        time.sleep(2)

        cronjobs = epg.get_cronjobs()
        l, s = cronjobs[0]
        assert len(cronjobs) == 2
        assert isinstance(l, XMLTVListing)
        assert l.url.human_repr() == 'http://host.com/some/feed'
        assert s == "1 1 1 1 1"

        epg.delete_XMLTV_listing_cronjob(l)
        epg.delete_XMLTV_listing_cronjob(l2)



        epg2 = EPG('testing_cron')  # blank epg


        with pytest.raises(ValueError, match='No channels loaded.'):
            epg2.add_XMLTV_listing_cronjob(l, "1 1 1 1 1", run_now=True)

        with pytest.raises(ValueError, match='No cronjob found for the passed XMLTVListing.'):
            epg2.delete_XMLTV_listing_cronjob(l)

