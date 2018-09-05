#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cli wrapper for the skyq API
"""

import argparse
import sys
import logging

from pyskyq import __version__, SkyQ, REMOTE_COMMANDS

__author__ = "Bradley Wood"
__copyright__ = "Bradley Wood"
__license__ = "mit"

_logger = logging.getLogger(__name__)


def parse_args(args):
    """Parse command line parameters

    Args:
      args ([str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
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


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    _logger.debug("Starting SkyQ...")
    skyq = SkyQ('skyq')
    skyq.remote.send_command(REMOTE_COMMANDS[args.cmd])
    _logger.info("Script ends here")


def run():
    """Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
