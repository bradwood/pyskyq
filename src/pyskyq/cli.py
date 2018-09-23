#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cli wrapper for the skyq API.

This module implements a cli client which can be used to interact with the SkyQ Box.

Example:
    You can invoke the cli client like this:

        ``$ pyskyq pause``

        ``$ pyskyq play``
Note:
    The main purpose of this package is to provide the API, so the CLI implementation is really
    more just for my own testing. A much better cli client should probably be built using this
    libary, but that is not the scope of this project.

"""

import argparse
import sys
import logging
from typing import List

from pyskyq import __version__, SkyQ, REMOTE_COMMANDS

__author__ = "Bradley Wood"
__copyright__ = "Bradley Wood"
__license__ = "mit"

LOGGER = logging.getLogger(__name__)


def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command line parameters

    Args:
      args ([str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace.
    """
    parser = argparse.ArgumentParser(
        description="Sends a command to a SkyQ box")
    parser.add_argument(
        '--version',
        action='version',
        version='pyskyq {ver}'.format(ver=__version__))
    parser.add_argument(
        dest="cmd",
        help="command to send",
        type=str,
        metavar="CMD")
    parser.add_argument(
        '-v',
        '--verbose',
        dest="loglevel",
        help="set loglevel to INFO",
        action='store_const',
        const=logging.INFO)
    parser.add_argument(
        '-vv',
        '--very-verbose',
        dest="loglevel",
        help="set loglevel to DEBUG",
        action='store_const',
        const=logging.DEBUG)
    return parser.parse_args(args)


def setup_logging(loglevel: int):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages.
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def main(args: List[str]):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    pargs = parse_args(args)
    setup_logging(pargs.loglevel)
    LOGGER.debug("Starting SkyQ...")
    skyq = SkyQ('skyq')
    skyq.remote.send_command(REMOTE_COMMANDS[pargs.cmd])
    print(skyq.epg.get_channel(2002).desc)
    LOGGER.info("Script ends here")


def run():
    """Entry point for console_scripts.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
