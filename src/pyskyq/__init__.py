"""Import and merge all modules in this package."""
import logging

from .constants import RCMD
from ._version import __version__
from .remote import press_remote
from .epg import EPG
from .status import Status

logging.getLogger(__name__).addHandler(logging.NullHandler())
