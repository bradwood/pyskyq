# This code stolen from https://h11.readthedocs.io/en/latest/examples.html
# and modified to suit my mocking needed.
# Credit to Nathaniel J. Smith for producting the original version.
# pylint: disable=no-member
import json
from itertools import count
from wsgiref.handlers import format_date_time

import trio
from trio_websocket import serve_websocket, ConnectionClosed
import h11
import logging

from functools import partial
import sys
MAX_RECV = 2 ** 16

TIMEOUT = 10

LOGGER = logging.getLogger(__name__)


class TrioHTTPWrapper:
    _next_id = count()

    def __init__(self, stream):
        self.stream = stream
        self.conn = h11.Connection(h11.SERVER)
        # Our Server: header
        self.ident = " ".join([
            "h11-example-trio-server/{}".format(h11.__version__),
            h11.PRODUCT_ID,
        ]).encode("ascii")
        # A unique id for this connection, to include in debugging output
        # (useful for understanding what's going on if there are multiple
        # simultaneous clients).
        self._obj_id = next(TrioHTTPWrapper._next_id)

    async def send(self, event):
        # The code below doesn't send ConnectionClosed, so we don't bother
        # handling it here either -- it would require that we do something
        # appropriate when 'data' is None.
        assert type(event) is not h11.ConnectionClosed
        data = self.conn.send(event)
        await self.stream.send_all(data)

    async def _read_from_peer(self):
        if self.conn.they_are_waiting_for_100_continue:
            LOGGER.debug("Sending 100 Continue")
            go_ahead = h11.InformationalResponse(
                status_code=100,
                headers=self.basic_headers())
            await self.send(go_ahead)
        try:
            data = await self.stream.receive_some(MAX_RECV)
        except ConnectionError:
            # They've stopped listening. Not much we can do about it here.
            data = b""
        self.conn.receive_data(data)

    async def next_event(self):
        while True:
            event = self.conn.next_event()
            if event is h11.NEED_DATA:
                await self._read_from_peer()
                continue
            return event

    async def shutdown_and_clean_up(self):
        # When this method is called, it's because we definitely want to kill
        # this connection, either as a clean shutdown or because of some kind
        # of error or loss-of-sync bug, and we no longer care if that violates
        # the protocol or not. So we ignore the state of self.conn, and just
        # go ahead and do the shutdown on the socket directly. (If you're
        # implementing a client you might prefer to send ConnectionClosed()
        # and let it raise an exception if that violates the protocol.)
        #
        try:
            await self.stream.send_eof()
        except trio.BrokenResourceError:
            # They're already gone, nothing to do
            return
        # Wait and read for a bit to give them a chance to see that we closed
        # things, but eventually give up and just close the socket.
        # XX FIXME: possibly we should set SO_LINGER to 0 here, so
        # that in the case where the client has ignored our shutdown and
        # declined to initiate the close themselves, we do a violent shutdown
        # (RST) and avoid the TIME_WAIT?
        # it looks like nginx never does this for keepalive timeouts, and only
        # does it for regular timeouts (slow clients I guess?) if explicitly
        # enabled ("Default: reset_timedout_connection off")
        with trio.move_on_after(TIMEOUT):
            try:
                while True:
                    # Attempt to read until EOF
                    got = await self.stream.receive_some(MAX_RECV)
                    if not got:
                        break
            finally:
                await self.stream.aclose()

    def basic_headers(self):
        # HTTP requires these headers in all responses (client would do
        # something different here)
        return [
            ("Date", format_date_time(None).encode("ascii")),
            ("Server", self.ident),
        ]


async def http_server(stream, responses):
    wrapper = TrioHTTPWrapper(stream)
    while True:
        assert wrapper.conn.states == {
            h11.CLIENT: h11.IDLE, h11.SERVER: h11.IDLE}

        try:
            with trio.fail_after(10):
                LOGGER.debug("Server main loop waiting for request")
                event = await wrapper.next_event()
                LOGGER.debug(f"Server main loop got event: {event}")
                if isinstance(event, h11.Request):
                    response = [response for response in responses if response['target'].encode('ascii') == event.target][0]
                    await send_mock_response(wrapper, event, response)
        except Exception as exc:
            LOGGER.debug(f"Error during response handler: {exc}")
            await maybe_send_error_response(wrapper, exc)

        if wrapper.conn.our_state is h11.MUST_CLOSE:
            LOGGER.debug("connection is not reusable, so shutting down")
            await wrapper.shutdown_and_clean_up()
            return
        else:
            try:
                LOGGER.debug("trying to re-use connection")
                wrapper.conn.start_next_cycle()
            except h11.ProtocolError:
                states = wrapper.conn.states
                LOGGER.debug(f"unexpected state: {states}, -- bailing out")
                await maybe_send_error_response(
                    wrapper,
                    RuntimeError("unexpected state {}".format(states)))
                await wrapper.shutdown_and_clean_up()
                return


################################################################
# Actual response handlers
################################################################

# Helper function


async def send_simple_response(wrapper, status_code, content_type, body, passed_headers):
    LOGGER.debug(f"Sending {status_code} response with {len(body)} bytes")
    headers = wrapper.basic_headers()
    headers.append(("Content-Type", content_type))
    headers.append(("Content-Length", str(len(body))))
    if passed_headers:
        for k, v in passed_headers.items():
            headers.append((k, v))
    LOGGER.debug(f'Final headers = {headers}')

    res = h11.Response(status_code=status_code, headers=headers)
    await wrapper.send(res)
    await wrapper.send(h11.Data(data=body))
    await wrapper.send(h11.EndOfMessage())


async def maybe_send_error_response(wrapper, exc):
    # If we can't send an error, oh well, nothing to be done
    LOGGER.debug("trying to send error response...")
    if wrapper.conn.our_state not in {h11.IDLE, h11.SEND_RESPONSE}:
        LOGGER.debug(f"...but I can't, because our state is: {wrapper.conn.our_state}")
        return
    try:
        if isinstance(exc, h11.RemoteProtocolError):
            status_code = exc.error_status_hint
        elif isinstance(exc, trio.TooSlowError):
            status_code = 408  # Request Timeout
        else:
            status_code = 500
        body = str(exc).encode("utf-8")
        await send_simple_response(wrapper,
                                   status_code,
                                   "text/plain; charset=utf-8",
                                   body,
                                   passed_headers=None) # no special headers needed.
    except Exception as exc:
        LOGGER.debug(f"error while sending error response: {exc}")


async def send_mock_response(wrapper, request, response):
    LOGGER.debug("Preparing mock response")
    if request.method not in {b"GET", b"POST"}:
        # Laziness: we should send a proper 405 Method Not Allowed with the
        # appropriate Accept: header, but we don't.
        raise RuntimeError("unsupported method")
    await send_simple_response(wrapper,
                               response['status_code'],
                               response['content_type'],
                               response['body'],
                               response['headers']
                               )


async def websocket_request_handler(request, *, responses):
    ws = await request.accept()
    for res in responses:
        try:
            await ws.send_message(res['body'])
            await trio.sleep(0.2)
        except ConnectionClosed:
            continue


async def websocket_server(ip_addr, port, responses):
    await serve_websocket(partial(websocket_request_handler, responses=responses), ip_addr, port, ssl_context=None)
