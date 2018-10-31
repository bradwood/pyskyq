"""Monkey patch H11 to ensure that it sends headers the way the SkyQ box wants them to be."""

def write_headers_titlecase(headers, write):
    """Monkey-patch h11 header handling.

    See https://github.com/python-hyper/h11/issues/31 for the details. Essentially SkyQ box is
    not RFC compliant as regards case-insensitive headers, so this patch forces the headers to
    comply with SkyQ's braindead implementation.
    """
    # RFC says Host: header SHOULD be written out first.
    for name, value in headers:
        if name == b"host":
            write(b"%s: %s\r\n" % (name.title(), value))
    for name, value in headers:
        if name == b"upgrade":
            # SkyQ doesn't like 'WebSocket', it wants 'websocket'
            write(b"%s: %s\r\n" % (name.title(), value.lower()))
        elif name != b"host":
            write(b"%s: %s\r\n" % (name.title(), value))
    write(b"\r\n")
