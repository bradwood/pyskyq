#!/usr/bin/env python
"""
Cli wrapper for the skyq API.

Example:
    You can invoke the cli client like this:

        ``$ python cli_epg.py pause``

"""

import argparse
import sys
from typing import List
from time import sleep
from pyskyq import EPG, XMLTVListing


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


def main(args: List[str]):
    """Run main routine, allowing arguments to be passed."""
    pargs = parse_args(args)
    epg = EPG('skyq')  # replace with hostname / IP of your Sky box
    epg.load_skyq_channel_data()  # load channel listing from Box.
    all_72_hour = XMLTVListing('http: // www.xmltv.co.uk/feed/6715')
    limited_7_day = XMLTVListing('http://www.xmltv.co.uk/feed/6784')

    sleep(5)


    epg.add_XMLTV_listing_cronjob(limited_7_day, '0 2 * * *', run_now=True)  # at At 02:00 every day
    epg.add_XMLTV_listing_cronjob(all_72_hour, '0 3 * * *', run_now=True)  # at At 03:00 every day


    sec = 0
    while True:
        print(f'Seconds = {sec}')
        print('Channel Description from the SkyQ Box:')
        print(epg.get_channel_by_sid(pargs.sid).desc)
        print('Channel XMLTV ID from the XMLTV Feed:')
        print(epg.get_channel_by_sid(pargs.sid).xmltv_id)
        sleep(1)
        sec += 1
    # for job in epg.get_cronjobs():
    #     epg.delete_XMLTV_listing_cronjob(job[0])

if __name__ == "__main__":
    main(sys.argv[1:])
