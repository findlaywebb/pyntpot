"""`Annotations` and its parts validate what a caller asks a map to letter."""

import pydantic
import pytest

from pyntpot.maps.annotations import Annotations, Landmark, SpanRequest

#: Span ends that each state one end twice or not at all.
BAD_ENDS: tuple[dict[str, float], ...] = (
    {"from_i": 10, "from_km": 1.0, "to_i": 20},
    {"from_i": 10, "to_km": 2.0, "to_s": 600.0},
    {"to_i": 20},
    {"from_s": 60.0},
)
BAD_IDS: tuple[str, ...] = ("two-starts", "two-ends", "no-start", "no-end")

#: Span ends that each state one start and one end, mixing the three ways.
GOOD_ENDS: tuple[dict[str, float], ...] = (
    {"from_i": 10, "to_i": 20},
    {"from_km": 1.0, "to_s": 600.0},
    {"from_s": 60.0, "to_km": 2.5},
)
GOOD_IDS: tuple[str, ...] = ("indices", "km-to-seconds", "seconds-to-km")


class TestSpanRequest:
    """A span request states exactly one start and exactly one end."""

    def test_two_starts_raise(self) -> None:
        """A span request with both `from_i` and `from_km` raises `ValidationError`."""
        with pytest.raises(pydantic.ValidationError):
            SpanRequest(name="Dovedale", from_i=10, from_km=1.0, to_i=20)

    @pytest.mark.parametrize("ends", BAD_ENDS, ids=BAD_IDS)
    def test_an_end_stated_twice_or_never_raises(self, ends: dict[str, float]) -> None:
        """Any end stated twice or not at all raises `ValidationError`."""
        with pytest.raises(pydantic.ValidationError):
            SpanRequest.model_validate({"name": "Dovedale", **ends})

    @pytest.mark.parametrize("ends", GOOD_ENDS, ids=GOOD_IDS)
    def test_one_start_and_one_end_validate(self, ends: dict[str, float]) -> None:
        """One start and one end, stated in any of the three ways, validate."""
        span = SpanRequest.model_validate({"name": "Dovedale", **ends})
        assert span.kind == "climb"
        assert span.intent == "note"


class TestAnnotations:
    """`Annotations` takes landmarks as values or bare names and rejects unknown fields."""

    def test_a_bare_name_is_kept_as_a_name(self) -> None:
        """A bare string landmark is kept as the string, beside a full `Landmark`."""
        cove = Landmark(name="Malham Cove", lat=51.23, lng=-3.83)
        notes = Annotations(landmarks=(cove, "Watersmeet"))
        assert notes.landmarks == (cove, "Watersmeet")

    def test_an_unknown_field_raises(self) -> None:
        """An unknown field on `Annotations` raises `ValidationError`."""
        with pytest.raises(pydantic.ValidationError):
            Annotations.model_validate({"rivers": ["Severn"]})
