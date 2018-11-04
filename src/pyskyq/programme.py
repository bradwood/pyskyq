"""This module implements the Programme class."""

from datetime import datetime
from typing import Optional
from xml.etree.ElementTree import Element

from dateutil.parser import parse

from dataclasses import dataclass, field


# This object needs a few special attributes:
# - The ability to be hashable so that it can reside in a Sorted set
#   reflecting the programs in order on a channel.
# - The ability to support greater than, less than or equal to comparisons using
#   ony the start time.
#
# We should bear in mind that the detail of a particular programme as provided
# by the XMLTV file might improve in quality as XMLTV files come in various
# flavours (e.g., long forward range but limited data, or shorter forward
# ranges, but with richer data). We want to be able to update a Programme with
# richer data as its show time nears without making it appear as if it's a new
# programme, so we want its hash to remain the same as long as the Title,
# Channel and Start Time are the same.
#
# A Sorted Set maintains both deduplication and ordering simultaneously and so
# it should be a good structure to allow us to add newer entries of the same
# programme as the data gets richer, while preserving order via the programme's
# hash.


@dataclass(order=True)  # pylint: disable=too-few-public-methods
class Programme:
    """This dataclass represents a TV Programme.

    Attributes:
        title (str): Title of the Programme.
        title_lang (str): Language that the Title is in.
        desc (str): Description of the Programme.
        desc_lang (str): Language that the Description is in.
        start (datetime): Start datetime.
        start_raw (str): Start datetime in raw string format.
        stop (datetime): End datetime.
        stop_raw (str):  End datetime in raw string format.
        channel_xml_id (str): Channel key. Maps to :attr:`pyskyq.channel.Channel.xmltv_id`
        episode_num (str): Optional series and episode information.
        episode_num_system (str): Numbering scheme used for episode data.

    """

    title: str = field(init=True,
                       repr=True,
                       compare=False,
                       )
    title_lang: str = field(init=True,
                            repr=False,
                            compare=False,
                            )
    desc: str = field(init=True,
                      repr=False,
                      compare=False,
                      )
    desc_lang: str = field(init=True,
                           repr=False,
                           compare=False,
                           )
    start: datetime = field(init=False,  # computed value
                            repr=True,
                            compare=True,
                            )
    start_raw: str = field(init=True,
                           repr=False,
                           compare=False,
                           )
    stop: datetime = field(init=False,  # computed value
                           repr=True,
                           compare=False,
                           )
    stop_raw: str = field(init=True,
                          repr=False,
                          compare=False,
                          )
    channel_xml_id: str = field(init=True,
                                repr=True,
                                compare=False,
                                )
    episode_num: Optional[str] = field(init=True,
                                       repr=True,
                                       compare=False,
                                       )
    episode_num_system: Optional[str] = field(init=True,
                                              repr=False,
                                              compare=False,
                                              )

    def __post_init__(self):
        """Process the start and stop strings into datetime objects."""
        self.start = parse(self.start_raw)
        self.stop = parse(self.stop_raw)

    def __hash__(self):
        """Calculate the hash of this object."""
        return hash(self.title + self.channel_xml_id + str(self.start))

def programme_from_xmltv_list(xml_prog: Element) -> Programme:
    """Create a Programme object from an XMLTV programme element.

    This function is a Programme factory. It will generate a Programme object
    given a XML channel element from an XML TV file.

    Args:
        xml_prog (Element): A XML element of ``<programme>...</programme>`` tags.

    Returns:
        Programme: A channel object with the XML TV data loaded.

    """
    assert xml_prog.tag.lower() == 'programme'

    start = xml_prog.attrib['start']
    stop = xml_prog.attrib['stop']
    chan_id = xml_prog.attrib['channel']
    episode_num_system = None
    episode_num = None

    for child in xml_prog:
        if child.tag.lower() == 'title':
            title_lang = child.attrib.get('lang', None)
            title = child.text
            continue
        if child.tag.lower() == 'desc':
            desc_lang = child.attrib.get('lang', None)
            desc = child.text
            continue
        if child.tag.lower() == 'episode-num':
            episode_num_system = child.attrib.get('system', None)
            episode_num = child.text
            continue

    return Programme(title=title,     # type: ignore
                     title_lang=title_lang,
                     desc=desc,
                     desc_lang=desc_lang,
                     start_raw=start,
                     stop_raw=stop,
                     channel_xml_id=chan_id,
                     episode_num=episode_num,
                     episode_num_system=episode_num_system
                     )
