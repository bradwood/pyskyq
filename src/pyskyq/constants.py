"""Constants for button codes, ports, and so on"""
from collections import namedtuple

REMOTE_LEGACY_PORT: int = 5900
REMOTE_PORT: int = 49160

REMOTE_COMMANDS = {
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

RCmdTuple = namedtuple('RCmdTuple', sorted(REMOTE_COMMANDS))

rcmd = RCmdTuple(**REMOTE_COMMANDS)
