"""The OpenTopoData provider: lattice, batching, pauses, budget and User-Agent."""

import json
from importlib.metadata import version

import pytest

from pyntpot.maps.providers.base import (
    ProviderBudgetExceededError,
    ProviderError,
)
from pyntpot.maps.providers.opentopodata import OpenTopoData
from pyntpot.maps.track import BoundingBox

from support.http_server import serve

BOX = BoundingBox(51.21, -3.85, 51.24, -3.82)


def _reply(values: list[float | None], status: str = "OK") -> tuple[int, str]:
    """Return a scripted OpenTopoData answer carrying the values in order."""
    results = [{"elevation": v, "location": {"lat": 0.0, "lng": 0.0}} for v in values]
    return 200, json.dumps({"status": status, "results": results})


class TestGrid:
    """What `grid` samples, asks for and returns."""

    def test_three_by_three_is_one_call_in_order(self) -> None:
        """A 3 by 3 grid makes one call and returns the served values in order."""
        served = [10.0, 11.0, 12.0, 13.0, None, 15.0, 16.0, 17.0, 18.0]
        pauses: list[float] = []
        with serve([_reply(served)]) as server:
            provider = OpenTopoData("test", server.url, sleep=pauses.append)
            grid = provider.grid(BOX, 3)
        assert len(server.requests) == 1
        assert grid.elev == (10.0, 11.0, 12.0, 13.0, 0.0, 15.0, 16.0, 17.0, 18.0)
        assert grid.lats == pytest.approx((51.21, 51.225, 51.24))
        assert grid.lons == pytest.approx((-3.85, -3.835, -3.82))
        assert pauses == [1.1]

    def test_request_path_names_the_dataset_and_locations(self) -> None:
        """The request goes to the dataset path with south-west first, six places."""
        with serve([_reply([0.0] * 4)]) as server:
            OpenTopoData("test", server.url, "eudem25m", sleep=lambda _: None).grid(BOX, 2)
        path = server.requests[0].path
        assert path.startswith("/eudem25m?locations=51.210000%2C-3.850000%7C")

    def test_eleven_by_eleven_is_two_calls_and_two_pauses(self) -> None:
        """121 points make two calls of 100 and 21 points and sleep twice."""
        pauses: list[float] = []
        first = _reply([float(i) for i in range(100)])
        second = _reply([float(i) for i in range(100, 121)])
        with serve([first, second]) as server:
            grid = OpenTopoData("test", server.url, sleep=pauses.append).grid(BOX, 11)
        assert len(server.requests) == 2
        assert pauses == [1.1, 1.1]
        assert grid.elev == tuple(float(i) for i in range(121))

    def test_status_other_than_ok_raises(self) -> None:
        """A reply whose status is not `OK` raises `ProviderError`."""
        with serve([_reply([], status="INVALID_REQUEST")]) as server:
            provider = OpenTopoData("test", server.url, sleep=lambda _: None)
            with pytest.raises(ProviderError, match="INVALID_REQUEST"):
                provider.grid(BOX, 3)

    def test_http_error_raises_provider_error(self) -> None:
        """An HTTP error status raises `ProviderError`."""
        with serve([(500, "")]) as server:
            provider = OpenTopoData("test", server.url, sleep=lambda _: None)
            with pytest.raises(ProviderError):
                provider.grid(BOX, 3)

    def test_unreadable_reply_raises(self) -> None:
        """A reply that is not the expected JSON raises `ProviderError`."""
        with serve([(200, "not json")]) as server:
            provider = OpenTopoData("test", server.url, sleep=lambda _: None)
            with pytest.raises(ProviderError):
                provider.grid(BOX, 3)


class TestBudget:
    """The call counter."""

    def test_budget_of_one_stops_a_two_call_grid_after_one_call(self) -> None:
        """`budget=1` with `n = 11` raises after one call has been made."""
        with serve([_reply([1.0] * 100)]) as server:
            provider = OpenTopoData("test", server.url, budget=1, sleep=lambda _: None)
            with pytest.raises(ProviderBudgetExceededError):
                provider.grid(BOX, 11)
        assert len(server.requests) == 1

    def test_budget_is_per_instance(self) -> None:
        """A second instance has its own budget."""
        with serve([_reply([1.0] * 4)]) as server:
            for _ in range(2):
                provider = OpenTopoData("test", server.url, budget=1, sleep=lambda _: None)
                provider.grid(BOX, 2)
        assert len(server.requests) == 2


class TestIdentity:
    """Contact, User-Agent, id and credit."""

    def test_user_agent_carries_the_contact(self) -> None:
        """The User-Agent is `pyntpot/<version> (<contact>)`."""
        with serve([_reply([0.0] * 4)]) as server:
            OpenTopoData("walker@example.org", server.url, sleep=lambda _: None).grid(BOX, 2)
        expected = f"pyntpot/{version('pyntpot')} (walker@example.org)"
        assert server.requests[0].headers["user-agent"] == expected

    @pytest.mark.parametrize("contact", ["", "  "], ids=["empty", "blank"])
    def test_empty_contact_raises(self, contact: str) -> None:
        """An empty contact raises `ValueError`."""
        with pytest.raises(ValueError, match="contact"):
            OpenTopoData(contact)

    def test_id_names_the_dataset(self) -> None:
        """The id is `opentopodata-` plus the dataset, `srtm30m` by default."""
        assert OpenTopoData("test").id == "opentopodata-srtm30m"
        assert OpenTopoData("test", dataset="eudem25m").id == "opentopodata-eudem25m"
