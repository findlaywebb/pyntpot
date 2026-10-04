"""The Overpass provider's requests, usage limits and query templates."""

from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from importlib.metadata import version
from urllib.parse import parse_qs

import httpx
import pytest

from pyntpot.maps.providers.base import Features, ProviderBudgetExceededError, ProviderError
from pyntpot.maps.providers.overpass import OverpassFeatures
from pyntpot.maps.track import BoundingBox

from support.http_server import Request, Server, serve

#: A box around Lynmouth, inside the fixture box.
LYNMOUTH = BoundingBox(51.2, -3.86, 51.24, -3.82)


@contextmanager
def _client() -> Iterator[httpx.Client]:
    """Yield a client that ignores proxy settings, so it reaches the loopback server."""
    with httpx.Client(trust_env=False) as client:
        yield client


def _sent_query(request: Request) -> str:
    """Return the Overpass query a recorded form post carried."""
    return parse_qs(request.body.decode())["data"][0]


@contextmanager
def _servers(*scripts: list[tuple[int, str]]) -> Iterator[list[Server]]:
    """Run one scripted server per script, all shut down on exit."""
    with ExitStack() as stack:
        yield [stack.enter_context(serve(script)) for script in scripts]


def test_overpass_features_is_a_features_provider() -> None:
    """`OverpassFeatures` satisfies `Features` and carries the id the cache keys on."""
    provider: Features = OverpassFeatures("walker@example.org")
    assert provider.id == "overpass"
    assert provider.credit.url == "https://www.openstreetmap.org/copyright"


@pytest.mark.parametrize("contact", ["", "  "], ids=["empty", "blank"])
def test_contact_is_required(contact: str) -> None:
    """An empty or blank contact string is refused at construction."""
    with pytest.raises(ValueError, match="contact"):
        OverpassFeatures(contact)


def test_user_agent_carries_the_contact() -> None:
    """Every request names the package version and the caller's contact."""
    with serve([(200, "{}")]) as server, _client() as client:
        OverpassFeatures("walker@example.org", (server.url,), client=client).features(LYNMOUTH)
    expected = f"pyntpot/{version('pyntpot')} (walker@example.org)"
    assert server.requests[0].headers["user-agent"] == expected


def test_too_many_requests_backs_off_then_tries_the_next_endpoint() -> None:
    """A 429 sleeps 30 s once and the second endpoint's body is returned."""
    slept: list[float] = []
    with _servers([(429, "")], [(200, '{"elements": []}')]) as (busy, free), _client() as client:
        provider = OverpassFeatures(
            "walker@example.org", (busy.url, free.url), client=client, sleep=slept.append
        )
        text = provider.landcover(LYNMOUTH)
    assert text == '{"elements": []}'
    assert slept == [30.0]
    assert (len(busy.requests), len(free.requests)) == (1, 1)


def test_every_endpoint_failing_raises_provider_error() -> None:
    """When every endpoint errors, `ProviderError` is raised from the last HTTP error."""
    slept: list[float] = []
    with _servers([(504, "")], [(502, "")]) as (first, second), _client() as client:
        provider = OverpassFeatures(
            "walker@example.org", (first.url, second.url), client=client, sleep=slept.append
        )
        with pytest.raises(ProviderError) as caught:
            provider.features(LYNMOUTH)
    assert isinstance(caught.value.__cause__, httpx.HTTPStatusError)
    assert caught.value.__cause__.response.status_code == 502
    assert slept == []


def test_budget_refuses_the_query_past_it_before_any_request() -> None:
    """With a budget of one, the second query raises and only one request is sent."""
    with serve([(200, "{}")]) as server, _client() as client:
        provider = OverpassFeatures("walker@example.org", (server.url,), budget=1, client=client)
        provider.features(LYNMOUTH)
        with pytest.raises(ProviderBudgetExceededError):
            provider.landcover(LYNMOUTH)
    assert len(server.requests) == 1


def test_feature_query_carries_the_size_bound_and_the_box() -> None:
    """The posted query starts with the size bound and holds the box as six-decimal text."""
    with serve([(200, "{}")]) as server, _client() as client:
        OverpassFeatures("walker@example.org", (server.url,), client=client).features(LYNMOUTH)
    query = _sent_query(server.requests[0])
    assert query.startswith("[out:json][maxsize:67108864][timeout:240];\n")
    assert 'way["natural"="wood"](51.200000,-3.860000,51.240000,-3.820000);' in query


def test_landcover_query_carries_the_size_bound() -> None:
    """The posted land cover query starts with the size bound and its own timeout."""
    with serve([(200, "{}")]) as server, _client() as client:
        OverpassFeatures("walker@example.org", (server.url,), client=client).landcover(LYNMOUTH)
    assert _sent_query(server.requests[0]).startswith("[out:json][maxsize:67108864][timeout:300];")


def test_the_query_asks_for_the_things_a_runner_would_pick() -> None:
    """Buildings, bridges and zoos are in the box's own question to OSM."""
    with serve([(200, "{}")]) as server, _client() as client:
        OverpassFeatures("walker@example.org", (server.url,), client=client).features(LYNMOUTH)
    query = _sent_query(server.requests[0])
    assert "zoo" in query
    assert '"bridge"' in query
    assert "cathedral" in query
    assert "place_of_worship" in query
