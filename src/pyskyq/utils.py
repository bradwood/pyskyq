"""Misc util functions."""

import email.utils as eut
from datetime import datetime


def parse_http_date(httpdatetime: str) -> datetime:
    """Turn an HTTP-formated date-time string into a native datetime.datetime object.

    Args:
        httpdatetime (str): A string like 'Mon, 08 Oct 2018 01:42:20 GMT'

    Returns:
        dateime: A datetime object.

    """
    return datetime(*eut.parsedate(httpdatetime)[:6])  # type: ignore
