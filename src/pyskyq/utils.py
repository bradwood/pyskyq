"""Misc util functions."""

import email.utils as eut
from datetime import datetime
from xml.etree.ElementTree import iterparse

def parse_http_date(httpdatetime: str) -> datetime:
    """Turn an HTTP-formated date-time string into a native :py:class:`~datetime.datetime` object.

    Args:
        httpdatetime (str): A string like ``Mon, 08 Oct 2018 01:42:20 GMT``

    Returns:
        datetime: A datetime object.

    """
    return datetime(*eut.parsedate(httpdatetime)[:6])  # type: ignore

def xml_parse_and_remove(filename, path):
    """Incrementally load and parse an XML file.

    Stolen from Python Cookbook 3rd edition, section 6.4 with credit to the book's authors."""

    path_parts = path.split('/')
    doc = iterparse(filename, ('start', 'end'))
    next(doc)  # skip the root element
    tag_stack = []
    elem_stack = []
    for event, elem in doc:
        if event == 'start':
            tag_stack.append(elem.tag)
            elem_stack.append(elem)
        elif event == 'end':
            if tag_stack == path_parts:
                yield elem
                elem_stack[-2].remove(elem)
            try:
                tag_stack.pop()
                elem_stack.pop()
            except IndexError:
                pass
