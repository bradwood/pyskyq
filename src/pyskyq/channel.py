"""This module implements the Channel class"""
import logging
from typing import Dict, Optional, Any

from .constants import CHANNEL_FIELD_MAP

class Channel:
    """ This class holds channel data and methods for manipulating the channel.

        As the properties served from the SkyQ REST API are immutable, this class
        presents these as read-only attributes on the object. It will also dynamically
        set attributes based on the payload obtained from the API, which itself could vary
        from one channel to another. For example, channel's which are '+1' all carry the
        ``timeshifted`` property whereas regular channels do not.

        Finally, in order to present a more human-friendly API the
        :const:`~constants.CHANNEL_FIELD_MAP` dictionary is used to provide access to
        properties using more friendly names.

    """

    def __init__(self,
                 chan_dict: Dict,
                 logger: Optional[logging.Logger] = None,
                 ) -> None:
        """Initialise Channel Object.

        Args:
            chan_dict (Dict): String with resolvable hostname or IPv4 address to SkyQ box.
            logger (logging.Logger, optional): Standard Python logger object which if not
                passed will instantiate a local logger.
        Returns:
            None

        """
        self._chan_dict = chan_dict
        self.logger = logger
        if self.logger:
            self.logger.debug(f"Channel {self._chan_dict['t']} instantiated.")

    def __getattr__(self, name: str) -> Any:
        if name in self._chan_dict.keys():
            return self._chan_dict[name]
        if name in CHANNEL_FIELD_MAP.keys():
            return self._chan_dict.get(CHANNEL_FIELD_MAP[name], None)
        raise KeyError(name)


    def __setattr__(self, name: str, value: Any) -> None:
        if not name.startswith('_') and name != 'logger':
            raise AttributeError(f"Can't modify {name}")
        else:
            super().__setattr__(name,value)


    def __delattr__(self, name: str) -> None:
        if not name.startswith('_') and name != 'logger':
            raise AttributeError(f"Can't delete {name}")
        else:
            super().__delattr__(name)

    def add_detail_data(self, detail_dict: Dict) -> None:
        """Add additional properties obtained from the detail endpoint to the object.
        """
        self._chan_dict.update(detail_dict['details'])


# DETAIL payload looks like this -- note that we are not bothering mapping the streaming profiles yet.
# {
#     "details": {
#         "dvbtriplet": "2.2045.6301",
#         "isbroadcasting": true,
#         "upgradeMessage": "BBC ONE for Greater London and the surrounding area. Find out more about this and the other BBC English regions at www.bbc.co.uk/england."
#     },
#     "sid": "2002",
#     "streamingprofiles": [
#         {
#             "name": "AnExample",
#             "suri": "http://10.0.1.6:4730/trans_caption/CHAN%3Alocator%3A5%3A3%3A7D2/profileAnExample.ttml",
#             "uri": "http://10.0.1.6:4730/trans/CHAN%3Alocator%3A5%3A3%3A7D2/profileAnExample.ts"
#         }
#     ]
# }
