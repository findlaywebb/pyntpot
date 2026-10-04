"""The label types and the rules that size and wrap a name."""

import math

import pytest

from pyntpot.maps.lettering.label import (
    MAX_LINES,
    SPAN_EFFORT,
    SPAN_GROUND,
    TIER_ROAD,
    TIER_SPAN,
    WET_PX_DEFAULT,
    WET_SPREAD,
    WRAP_LEADING,
    WRAP_MIN_CHARS,
    WRAP_MIN_SHARE,
    Label,
    block_size,
    feature_px,
    wrap_forms,
)
from pyntpot.maps.lettering_marks import label_marks
from pyntpot.maps.lettering_window import baseline

from support.basemaps import label_basemap
from support.lettering import open_hand
from support.measure import flat_measure


def test_a_name_is_never_set_along_a_line_that_turns_too_far():
    """Curved baselines for linear things, and only where they stay readable.

    Total turning across the run is the test that matters, not curvature at a
    point: a river bend reads, a switchback does not, and the difference
    between elegant and unreadable is this one rule.
    """
    hand = open_hand()
    straight = [(float(x), 100.0 + 4.0 * math.sin(x / 90.0)) for x in range(0, 400, 8)]
    hairpin = [
        (100.0 + 40.0 * math.cos(a / 9.0), 100.0 + 40.0 * math.sin(a / 9.0)) for a in range(0, 80)
    ]
    gentle = Label(name="Heddon", kind="river", px=200.0, py=100.0, size=14.0, baseline=straight)
    tight = Label(name="Heddon", kind="river", px=100.0, py=100.0, size=14.0, baseline=hairpin)
    assert baseline(gentle, hand.font.measure("Heddon", 14.0)[0])
    assert baseline(tight, hand.font.measure("Heddon", 14.0)[0]) is None


def test_a_long_span_name_breaks_over_two_lines_and_reserves_the_block():
    """The root cause of every awkward span placement: one line and only one.

    A break is offered, never forced: it costs `WRAP_COST` and is taken only
    where it buys a materially better position. What it must never do is claim
    a one-line box and then write two lines in it.
    """
    forms = wrap_forms("the long climb out of Aviemore", "span")
    assert forms[0] == ["the long climb out of Aviemore"]
    assert all(len(form) <= MAX_LINES for form in forms)
    assert any(len(form) == 2 for form in forms)
    assert all(" ".join(form) == "the long climb out of Aviemore" for form in forms)
    # Balanced first, and never a one-word orphan. Three characters of a
    # thirty-character phrase is an orphan whatever the character floor says,
    # and the card drew "the" over "long climb out of Aviemore" until the share
    # was added: a stub first line makes the widest possible second line.
    assert forms[1][0] == "the long climb"
    floor = max(WRAP_MIN_CHARS, WRAP_MIN_SHARE * len("the long climb out of Aviemore"))
    for form in forms[1:]:
        assert min(len(part) for part in form) >= floor
    assert ["the", "long climb out of Aviemore"] not in forms

    wide, tall = block_size(["the long climb", "out of Aviemore"], 14.0, flat_measure)
    one_wide, one_tall = block_size(["the long climb out of Aviemore"], 14.0, flat_measure)
    assert wide < one_wide, "the block is not narrower than the single line"
    assert tall > one_tall, "the block did not reserve the second line"


def test_a_settlement_name_is_never_broken():
    """A place name is one thing a reader looks up; two lines read as two places."""
    assert wrap_forms("Monmouth Castle", "settlement") == [["Monmouth Castle"]]
    assert wrap_forms("Lyn Valley Road", "road") == [["Lyn Valley Road"]]
    assert wrap_forms("Heddon", "span") == [["Heddon"]], "nothing to break at"
    # A span carries its own vocabulary as its kind, so every one of them has
    # to be wrappable without being named here.
    for kind in SPAN_GROUND + SPAN_EFFORT:
        got = wrap_forms("the long climb out of Aviemore", kind, TIER_SPAN)
        assert len(got) > 1, kind
    # And the same word as a ground kind still does not wrap.
    assert len(wrap_forms("Lyn Valley Road", "road", TIER_ROAD)) == 1


def test_the_hand_writes_both_lines_of_a_wrapped_name():
    """The placer reserving two lines is only half of it; the hand has to write them."""
    try:
        hand = open_hand()
    except (ImportError, OSError):  # no fonttools or no face on disk
        pytest.skip("no face to letter with")
    one = Label(
        name="the long climb out of Aviemore",
        kind="climb",
        tier=TIER_SPAN,
        px=200.0,
        py=150.0,
        size=14.0,
        tx=200.0,
        ty=150.0,
        anchor="middle",
        flat=True,
    )
    two = Label(
        name="the long climb out of Aviemore",
        kind="climb",
        tier=TIER_SPAN,
        px=200.0,
        py=150.0,
        size=14.0,
        tx=200.0,
        ty=150.0,
        anchor="middle",
        flat=True,
        lines=["the long climb", "out of Aviemore"],
    )
    marks_one = [m for m in label_marks(hand, one) if m.role == "glyph"]
    marks_two = [m for m in label_marks(hand, two) if m.role == "glyph"]
    assert marks_one and marks_two
    wide_one = max(x for m in marks_one for x, _y in m.pts) - min(
        x for m in marks_one for x, _y in m.pts
    )
    wide_two = max(x for m in marks_two for x, _y in m.pts) - min(
        x for m in marks_two for x, _y in m.pts
    )
    assert wide_two < wide_one * 0.7, "the wrapped name is not narrower"
    tall_two = max(y for m in marks_two for _x, y in m.pts) - min(
        y for m in marks_two for _x, y in m.pts
    )
    assert tall_two > WRAP_LEADING * two.size, "only one line was written"


def test_the_painted_width_of_a_watercourse_reaches_the_label_layer():
    """The label layer sees a centreline; the layers tell it the brush."""
    fresh = label_basemap(wet_px={"major": 9.5, "medium": 6.0, "minor": 2.4})
    # The layers carry the brush's nominal width and the brush lays down
    # more than that, so what reaches the label layer is the footprint.
    assert feature_px(fresh, "river", "major") == pytest.approx(9.5 * WET_SPREAD)
    # Layers with no width for the class fall back to the painter's defaults
    # rather than to nothing, so such a map letters its rivers where any
    # other does.
    assert feature_px(label_basemap(), "river", "major") == pytest.approx(
        WET_PX_DEFAULT["major"] * WET_SPREAD
    )
