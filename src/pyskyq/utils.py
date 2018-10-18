"""Misc util functions."""

import email.utils as eut
import logging
from datetime import datetime
from typing import Any, Iterator
from xml.etree.ElementTree import iterparse

from yarl import URL


def parse_http_date(httpdatetime: str) -> datetime:
    """Turn an HTTP-formated date-time string into a native :py:class:`~datetime.datetime` object.

    Args:
        httpdatetime (str): A string like ``Mon, 08 Oct 2018 01:42:20 GMT``

    Returns:
        datetime: A datetime object.

    """
    return datetime(*eut.parsedate(httpdatetime)[:6])  # type: ignore


# TODO: use  XMLPullParser instead of iterparse() as it's non-blocking...
# TODO: add error checking for XML errors
def xml_parse_and_remove(filename, path) -> Iterator[Any]:
    """Incrementally load and parse an XML file.

    Stolen from Python Cookbook 3rd edition, section 6.4 with credit to the book's authors.
    """
    LOGGER = logging.getLogger(__name__)

    path_parts = path.split('/')
    doc = iterparse(filename, ('start', 'end')) #TODO: see if we can use aiofiles here.
    # skip the root element
    next(doc)  # pylint: disable=stop-iteration-return
    tag_stack = []
    elem_stack = []
    for event, elem in doc:
        if event == 'start':
            LOGGER.debug(f'Parsing XML element: {elem.tag}')
            tag_stack.append(elem.tag)
            elem_stack.append(elem)
        else: # event == 'end'
            if tag_stack == path_parts:
                yield elem
                elem.clear()
            try:
                tag_stack.pop()
                elem_stack.pop()
            except IndexError:
                pass

#TODO: this is ugly, fix at some point.
def skyq_json_decoder_hook(obj):
    """Decode JSON into appropriate types used in the project."""
    if "xmltv_icon_url" in obj.keys():
        obj['xmltv_icon_url'] = URL(obj['xmltv_icon_url'])
    return obj
