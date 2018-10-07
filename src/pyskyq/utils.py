"""Misc util functions."""

from urllib.parse import urlparse


def url_validator(x):
    """Validate a URL.

    Args:
        x (str): A string to validate.

    Returns:
        bool: True if the URL is valid.

    """
    try:
        result = urlparse(x)
        return result.scheme and result.netloc and result.path
    except: # pylint: disable=W0702
        return False
