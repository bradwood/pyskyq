#!/usr/bin/env python
"""
Cli wrapper for the skyq API.

Example:
    You can invoke the cli client like this:

        ``$ python cli_epg.py pause``

"""
import logging
import argparse
import sys
from typing import List

import trio

from pyskyq import EPG, XMLTVListing

logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                    format=logformat)



def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command line parameters."""
    parser = argparse.ArgumentParser(
        description="Query Channel Description from SkyQ EPG")
    parser.add_argument(
        dest="sid",
        help="channel sid, try 2002 as an example",
        type=str,
        metavar="SID")
    return parser.parse_args(args)


async def main(args: List[str]):
    """Run main routine, allowing arguments to be passed."""
    pargs = parse_args(args)
    epg = EPG('10.0.1.6')  # replace with hostname / IP of your Sky box
    await epg.load_skyq_channel_data()  # load channel listing from Box.
    all_72_hour = XMLTVListing('http://www.xmltv.co.uk/feed/6715')
    #limited_7_day = XMLTVListing('http://www.xmltv.co.uk/feed/6784')

    async with trio.open_nursery() as nursery:
        # fetch 2 separate XMLTV listing concurrently.
        nursery.start_soon(all_72_hour.fetch)

    assert all_72_hour.downloaded
    print("Downloaded XMLTV Listing: {all_72_hour}")

    # assert limited_7_day.downloaded
    # print("Downloaded XMLTV Listing: {limited_7_day}")

    epg.apply_XMLTVListing(all_72_hour)

    #epg.apply_XMLTVListing(limited_7_day)

    print('Channel Description from the SkyQ Box:')
    print(epg.get_channel_by_sid(pargs.sid).desc)
    print('Channel XMLTV ID from the XMLTV Feed:')
    print(epg.get_channel_by_sid(pargs.sid).xmltv_id)
    print('Channel Logo URL from the XMLTV Feed:')
    print(epg.get_channel_by_sid(pargs.sid).xmltv_icon_url)

if __name__ == "__main__":
    trio.run(main, sys.argv[1:])
