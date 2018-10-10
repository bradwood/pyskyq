"""Misc util functions."""

import logging
import email.utils as eut
from datetime import datetime
from xml.etree.ElementTree import iterparse
from typing import Iterator, Any

def parse_http_date(httpdatetime: str) -> datetime:
    """Turn an HTTP-formated date-time string into a native :py:class:`~datetime.datetime` object.

    Args:
        httpdatetime (str): A string like ``Mon, 08 Oct 2018 01:42:20 GMT``

    Returns:
        datetime: A datetime object.

    """
    return datetime(*eut.parsedate(httpdatetime)[:6])  # type: ignore


# todo: use  XMLPullParser instead of iterparse() as it's non-blocking...
def xml_parse_and_remove(filename, path) -> Iterator[Any]:
    """Incrementally load and parse an XML file.

    Stolen from Python Cookbook 3rd edition, section 6.4 with credit to the book's authors."""


    LOGGER = logging.getLogger(__name__)

    path_parts = path.split('/')
    doc = iterparse(filename, ('start', 'end'))
    # skip the root element
    next(doc)  # pylint: disable=stop-iteration-return
    tag_stack = []
    elem_stack = []
    for event, elem in doc:
        if event == 'start':
            tag_stack.append(elem.tag)
            elem_stack.append(elem)
            LOGGER.debug(f'START: tag stack = {tag_stack}')
            LOGGER.debug(f'START: elem stack = {elem_stack}')
        else: # event == 'end'
            LOGGER.debug(f'END: tag stack = {tag_stack}')
            LOGGER.debug(f'END: elem stack = {elem_stack}')
            if tag_stack == path_parts:
                LOGGER.debug(f'YEILD!!! ________________ {elem}')
                yield elem
                elem.clear()
            try:
                LOGGER.debug('POPPING both stacks')
                tag_stack.pop()
                elem_stack.pop()
            except IndexError:
                pass
