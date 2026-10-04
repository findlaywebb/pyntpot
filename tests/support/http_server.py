"""A real HTTP server on the loopback interface that answers from a script.

`serve` starts a `ThreadingHTTPServer` on `127.0.0.1` at a free port and answers the
n-th request with the n-th scripted `(status, body)`, repeating the last one. It records
every request as a `Request`, with header names lower-cased. It is a real server, not a
mock: provider tests point a real HTTP client at `Server.url`. It never reaches the
network beyond the loopback interface.
"""

import threading
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import MappingProxyType


@dataclass(frozen=True)
class Request:
    """One request the server received.

    Attributes:
        method: The HTTP method, such as `GET` or `POST`.
        path: The request target, with its query string.
        headers: The request headers, names lower-cased.
        body: The request body, empty when none was sent.
    """

    method: str
    path: str
    headers: Mapping[str, str]
    body: bytes


@dataclass
class Server:
    """A running scripted server.

    Attributes:
        url: The server's base URL, `http://127.0.0.1:<port>`.
        requests: Every request received so far, in arrival order.
    """

    url: str
    requests: list[Request] = field(default_factory=list)


def _handler(
    responses: Sequence[tuple[int, str]], requests: list[Request], lock: threading.Lock
) -> type[BaseHTTPRequestHandler]:
    """Return a handler class that records each request and answers from the script."""

    def answer(handler: BaseHTTPRequestHandler) -> None:
        """Record the request, then send the scripted reply for its position."""
        length = int(handler.headers.get("Content-Length", "0"))
        body = handler.rfile.read(length) if length else b""
        headers = MappingProxyType({k.lower(): v for k, v in handler.headers.items()})
        with lock:
            requests.append(Request(handler.command, handler.path, headers, body))
            status, text = responses[min(len(requests), len(responses)) - 1]
        payload = text.encode()
        handler.send_response(status)
        handler.send_header("Content-Type", "text/plain; charset=utf-8")
        handler.send_header("Content-Length", str(len(payload)))
        handler.end_headers()
        handler.wfile.write(payload)

    # http.server dispatches to `do_GET`/`do_POST`, names ruff's N802 rejects in a `def`.
    methods = {f"do_{method}": answer for method in ("GET", "POST")}
    return type("ScriptedHandler", (BaseHTTPRequestHandler,), methods)


@contextmanager
def serve(responses: Sequence[tuple[int, str]]) -> Iterator[Server]:
    """Run a scripted server for the duration of the block, then shut it down and join it.

    Args:
        responses: `(status, body)` per request, in order; the last repeats.

    Raises:
        ValueError: When `responses` is empty.
    """
    if not responses:
        raise ValueError("serve needs at least one scripted response")
    requests: list[Request] = []
    handler = _handler(tuple(responses), requests, threading.Lock())
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    httpd.daemon_threads = True
    host, port = httpd.server_address[:2]
    host_name = host.decode() if isinstance(host, bytes) else host
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield Server(url=f"http://{host_name}:{port}", requests=requests)
    finally:
        httpd.shutdown()
        thread.join()
        httpd.server_close()
