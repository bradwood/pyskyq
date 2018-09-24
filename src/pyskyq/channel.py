"""This module implements the Channel class"""
import logging
from typing import Dict, Any

from .constants import CHANNEL_FIELD_MAP

LOGGER = logging.getLogger(__name__)

class Channel:
    """ This class holds channel data and methods for manipulating the channel.

        As the properties served from the SkyQ REST API are immutable, this class
        presents these as read-only attributes on the object. It will also dynamically
        set attributes based on the payload obtained from the API, which itself could vary
        from one channel to another. For example, channel's which are '+1' all carry the
        ``timeshifted`` property whereas regular channels do not.

        Finally, in order to present a more human-friendly API the
        :const:`~pyskyq.constants.CHANNEL_FIELD_MAP` dictionary is used to provide access to
        properties using more friendly names.

        Note:
            These channel attributes could change at any time with a box upgrade. The API will
            attempt to adapt to ensure the new fields are presented.

        Attributes:
            c (str): Channel number.
            dvbtriplet (str):  DVB Triplet (I have no idea what this is)
            schedule (bool): Is the channel "scheduled" or not?
            servicetype (str): Where is the channel coming from (e.g., ``DSAT``)
            sf (str): Quality of the channel (e.g., ``hd``)
            sg (int): No ideas what this is.
            sid (str): Channel id (aka ``sid``) in `str` form - the **primary key** for the channel.
            sk (int): Channel id (aka ``sid``) in `str` form.
            t (str): Channel name, eg, ``BBC One Lon``
            xsg (int): No idea what this is.
            timeshifted (bool): Is this a ``+1``-style channel?
            upgradeMessage (str): A short description of the channel.
            isbroadcasting (boo): Is the channel broadcasting currently or not?

        Note:
            The below are the human-friendly mappings of some of Sky's terser-named
            attributes.

        Attributes:
            number (str): Human-friendly version of :attr:`c`.
            quality (str): Human-friendly version of :attr:`sf`.
            id (str): Human-friendly version of :attr:`sid`.
            name (str):Human-friendly version of :attr:`t`.
            desc (str): Human-friendly version of :attr:`upgradeMessage`.


    """

    def __init__(self,
                 chan_dict: Dict,
                 ) -> None:
        """Initialise Channel Object.

        Args:
            chan_dict (dict): This dictionary is the payload that comes directly from the
                ``as/services/`` endpoint.
        Returns:
            None

        """
        self._chan_dict = chan_dict
        LOGGER.debug(f"Channel {self._chan_dict['t']} instantiated.")

    def __getattr__(self, name: str) -> Any:
        if name in self._chan_dict.keys():
            return self._chan_dict[name]
        if name in CHANNEL_FIELD_MAP.keys():
            return self._chan_dict.get(CHANNEL_FIELD_MAP[name], None)
        raise KeyError(name)


    def __setattr__(self, name: str, value: Any) -> None:
        if not name.startswith('_'):
            raise AttributeError(f"Can't modify {name}")
        else:
            super().__setattr__(name, value)


    def add_detail_data(self, detail_dict: Dict) -> None:
        """ Add additional properties obtained from the detail endpoint to the object.

            Args:
                detail_dict (dict): A detail dict that is passed in directly from the
                    ``as/services/details/<sid>`` endpoint.
            Returns:
                None

        """
        self._chan_dict.update(detail_dict['details'])
