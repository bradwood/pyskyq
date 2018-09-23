"""Constants for button codes, ports, and so on"""
from collections import namedtuple
from typing import Dict

REMOTE_LEGACY_PORT: int = 5900
"""int: Legacy port number for older Sky Boxes."""

REMOTE_PORT: int = 49160
"""int: Current port number for newer Sky Boxes."""

REMOTE_COMMANDS: Dict[str, int] = {
    'power': 0,
    'select': 1,
    'backup': 2,
    'dismiss': 2,
    'channelup': 6,
    'channeldown': 7,
    'interactive': 8,
    'sidebar': 8,
    'help': 9,
    'services': 10,
    'search': 10,
    'tvguide': 11,
    'home': 11,
    'i': 14,
    'text': 15,
    'up': 16,
    'down': 17,
    'left': 18,
    'right': 19,
    'red': 32,
    'green': 33,
    'yellow': 34,
    'blue': 35,
    'zero': 48,
    'one': 49,
    'two': 50,
    'three': 51,
    'four': 52,
    'five': 53,
    'six': 54,
    'seven': 55,
    'eight': 56,
    'nine': 57,
    'play': 64,
    'pause': 65,
    'stop': 66,
    'record': 67,
    'fastforward': 69,
    'rewind': 71,
    'boxoffice': 240,
    'sky': 241,
}
"""
Dictionary mapping strings of button names to their associated codes.
"""  # pylint: disable=W0105

# Silence mypy type errors on the below 2 commands.

RCMDTUPLE = namedtuple('RCMDTUPLE', sorted(REMOTE_COMMANDS))  # type: ignore

RCMD = RCMDTUPLE(**REMOTE_COMMANDS)  # type: ignore
"""
Named tuple object with attributes as button names and their values as the associated remote code.
"""  # pylint: disable=W0105

REST_PORT: int = 9006
"""int: Port number for the REST API."""

REST_SERVICES_URL: str = '/as/services'
"""str: REST endpoint for list of services (channels)."""

REST_SERVICE_DETAIL_URL_PREFIX: str = '/as/services/details/'
"""str: REST endpoint for service (channel) details."""

CHANNEL_FIELD_MAP = {
    "number": "c", # "101",
    "quality": "sf", # "sd",
    "id": "sid", # "2002",
    "name": "t",  # "BBC One Lon",
    "desc": "upgradeMessage",
}
"""Dict(str,str): Maps human-friendly names to Sky's terse field names (where understood)."""
