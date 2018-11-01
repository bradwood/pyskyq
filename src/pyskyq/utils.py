"""Misc util functions."""

import email.utils as eut
from datetime import datetime

from yarl import URL


def parse_http_date(httpdatetime: str) -> datetime:
    """Turn an HTTP-formated date-time string into a native :py:class:`~datetime.datetime` object.

    Args:
        httpdatetime (str): A string like ``Mon, 08 Oct 2018 01:42:20 GMT``

    Returns:
        datetime: A datetime object.

    """
    return datetime(*eut.parsedate(httpdatetime)[:6])  # type: ignore


#TODO: this is ugly, fix at some point.
def skyq_json_decoder_hook(obj):
    """Decode JSON into appropriate types used in this library."""
    if "xmltv_icon_url" in obj.keys():
        obj['xmltv_icon_url'] = URL(obj['xmltv_icon_url'])
    return obj
