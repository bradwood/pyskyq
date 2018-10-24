#!/usr/bin/env python
"""Cli wrapper for the Remote API.

Example:
    You can press a button on the SkyQ remote like this:

        ``$ python cli_remote.py pause``

        ``$ python cli_remote.py play``
"""

import argparse
import sys
from typing import List

from pyskyq import press_remote
from pyskyq import REMOTECOMMANDS as RCMD

def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command line parameters."""
    parser = argparse.ArgumentParser(
        description="Presses a button on the SkyQ remote")
    parser.add_argument(
        dest="cmd",
        help="command to send",
        type=str,
        metavar="CMD")
    return parser.parse_args(args)


def main(args: List[str]):
    """Provide main entry point."""
    pargs = parse_args(args)
    # replace 'skyq' with hostname / IP of your Sky box
    press_remote('skyq', getattr(RCMD, pargs.cmd))


if __name__ == "__main__":
    main(sys.argv[1:])
