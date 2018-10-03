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

from pyskyq import EPG


def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command line parameters"""
    parser = argparse.ArgumentParser(
        description="Query Channel Description from SkyQ EPG")
    parser.add_argument(
        dest="sid",
        help="channel sid, try 2002 as an example",
        type=str,
        metavar="SID")
    return parser.parse_args(args)


def main(args: List[str]):
    """Main entry point allowing external calls"""
    pargs = parse_args(args)
    epg = EPG('skyq')  # replace with hostname / IP of your Sky box
    epg.load_channel_data() # load channel listing from Box.

    print(epg.get_channel(pargs.sid).desc)


if __name__ == "__main__":
    main(sys.argv[1:])
