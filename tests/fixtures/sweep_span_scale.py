"""Sweep the scale a span's bend is read at, over sliding stretches of the fixture tracks.

Run as `PYTHONPATH=tests uv run python tests/fixtures/sweep_span_scale.py --out PATH`.
For each of the Ambleside, Skye and Y Fenni fixtures it projects the committed track as the golden place
cards do (from a copy of the fixture, with a request budget of 0), cuts it into sliding
stretches by arc length, and judges each stretch once: which side is the outside of its
bend, and whether one side's mark keeps more than a quarter more of itself once cleared of
the route than the other's (the kept share). Then, for each scale swept, it counts the
stretches the bend votes on and how often the outside is the better mark, and applies the
decision rule to the 16-cap table.

Key names: `FIXTURES`, `fixture_route`, `report`, `main`; the scoring is
`fixtures.span_sweep_score`.

It does not change any constant, reads no environment, fetches nothing, and never writes
or logs a coordinate: only counts, scales and shares.
"""

import argparse
import logging
import shutil
import tempfile
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from fixtures.span_sweep_score import (
    CAP_PX,
    CASES,
    LENGTH_CAPS,
    MULTIPLE_TOL,
    SCALES,
    SECONDARY,
    STEP_CAPS,
    Decision,
    ScaleRow,
    Verdict,
    decide,
    judge,
    stretches,
    sweep,
)

from pyntpot.ink.polyline import Point
from pyntpot.maps import (
    Cache,
    FetchMargins,
    OpenTopoData,
    OverpassFeatures,
    Style,
    Track,
    fetch,
)
from pyntpot.maps.cache import LANDCOVER_MARGIN_M, MARGIN_M
from pyntpot.maps.lettering.label import Span
from pyntpot.maps.lettering.span_line import SPAN_OFFSET_CAPS
from pyntpot.maps.strands import merge_strands, strand_merge_px

log = logging.getLogger("sweep_span_scale")

REPO = Path(__file__).resolve().parents[2]

#: The fixtures: directory, theme and the margins `tests/golden/test_places.py` records.
FIXTURES = (
    ("ambleside", "examples/themes/ambleside.toml", FetchMargins(MARGIN_M, LANDCOVER_MARGIN_M)),
    ("skye", "examples/themes/skye.toml", FetchMargins(18000.0, 18000.0)),
    ("y-fenni", "examples/themes/y-fenni.toml", FetchMargins(MARGIN_M, LANDCOVER_MARGIN_M)),
)


def fixture_route(directory: str, theme: str, margins: FetchMargins) -> list[Point]:
    """A fixture's track in display pixels, pulled into strands, as the lettering sees it."""
    contact = "pyntpot-sweep@example.invalid"
    with tempfile.TemporaryDirectory() as tmp:
        cache_dir = Path(tmp) / "cache"
        shutil.copytree(REPO / "tests" / "fixtures" / directory, cache_dir)
        features = OverpassFeatures(contact, ("http://127.0.0.1:9/api/interpreter",), budget=0)
        elevation = OpenTopoData(contact, "http://127.0.0.1:9", budget=0)
        style = Style.from_toml(REPO / theme)
        track = Track.from_gpx(cache_dir / "track.gpx")
        basemap = fetch(track, Cache(cache_dir, margins), features, elevation, style)
    route = [basemap.card.xy(x, y) for x, y in basemap.track]
    return merge_strands(route, strand_merge_px(style))


def _judged(
    routes: dict[str, list[Point]], cap_px: float, length_caps: float
) -> dict[str, list[tuple[list[Point], Verdict]]]:
    """Every fixture's stretches at one length, each judged once."""
    out = {}
    for name, route in routes.items():
        out[name] = [
            (route[i0 : i1 + 1], judge(Span(name="stretch", i0=i0, i1=i1), route, cap_px))
            for i0, i1 in stretches(route, cap_px, length_caps, STEP_CAPS)
        ]
    return out


def _table(rows: Sequence[ScaleRow]) -> list[str]:
    """A sweep as markdown rows."""
    out = [
        "| scale | voted | empty-mark | ambiguous-feet | even | decisive | right | % right |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        pct = "" if r.percent_right is None else f"{r.percent_right:.1f}"
        out.append(
            f"| {r.scale:.1f} | {r.voted} | {r.empty_mark} | {r.ambiguous_feet} | {r.even} "
            f"| {r.decisive} | {r.right} | {pct} |"
        )
    return out


def _cases_table(judged: dict[str, list[tuple[list[Point], Verdict]]]) -> list[str]:
    """Each fixture's stretches by case, before the vote."""
    out = ["| fixture | stretches | " + " | ".join(CASES) + " |", "|---" * (len(CASES) + 2) + "|"]
    for name, cases in judged.items():
        tally = Counter(v.case for _, v in cases)
        out.append(f"| {name} | {len(cases)} | " + " | ".join(str(tally[c]) for c in CASES) + " |")
    return out


def report(routes: dict[str, list[Point]], cap_px: float) -> tuple[str, Decision]:
    """The whole sweep as markdown, and the decision on the primary length."""
    judged = _judged(routes, cap_px, LENGTH_CAPS)
    cases = [case for per in judged.values() for case in per]
    rows = sweep([(sub, v) for sub, v in cases], cap_px, SCALES)
    decision = decide(rows, LENGTH_CAPS, STEP_CAPS)
    pool = Counter(name for name, per in judged.items() for _, v in per if v.case == "decisive")
    total = sum(pool.values())
    split = ", ".join(f"{name} {pool[name]}" for name in routes)
    lines = [
        "# 004 — sweep",
        "",
        (
            "Written by `tests/fixtures/sweep_span_scale.py`. Cap height "
            f"{cap_px:g} px; offset `SPAN_OFFSET_CAPS` = {SPAN_OFFSET_CAPS:g} caps; "
            f"stretches every {STEP_CAPS:g} caps."
        ),
        "",
        f"## Stretches by case, {LENGTH_CAPS:g}-cap length, before the vote",
        "",
        *_cases_table(judged),
        "",
        (
            f"The decisive pool before the vote is {total} stretches: {split}. "
            f"{100.0 * pool['skye'] / total if total else 0.0:.0f}% of it is Skye's."
        ),
        "",
        f"## Sweep, {LENGTH_CAPS:g}-cap length (decides)",
        "",
        *_table(rows),
        "",
        "## Decision",
        "",
        f"- `n` at 1.5: {decision.n_current}.",
        f"- {decision.reason}.",
    ]
    if decision.best is not None:
        lines.append(
            f"- Best eligible scale {decision.best:.1f}; Agresti-Coull 95% interval on "
            f"`n_eff = n / {LENGTH_CAPS / STEP_CAPS:g}`: {decision.lower:.3f} to "
            f"{decision.upper:.3f}."
        )
    lines.append(f"- Scale: {decision.scale:.1f} ({'changed' if decision.changed else 'kept'}).")
    for run, top in SECONDARY.items():
        extra = [case for per in _judged(routes, cap_px, run).values() for case in per]
        lines += [
            "",
            f"## Sweep, {run:g}-cap length (reported only; scales to {top:.1f})",
            "",
            f"{len(extra)} stretches.",
            "",
            *_table(sweep(extra, cap_px, [k for k in SCALES if k <= top + MULTIPLE_TOL])),
        ]
    for r in rows:
        log.info("scale %.1f: %d decisive, %d right", r.scale, r.decisive, r.right)
    log.info("decision: %s (%s)", decision.scale, decision.reason)
    return "\n".join(lines) + "\n", decision


def main(argv: Sequence[str] | None = None) -> None:
    """Project the three fixtures, sweep, and write the tables to `--out`."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True, help="the sweep.md to write")
    parser.add_argument("--cap-px", type=float, default=CAP_PX, help="cap height, px")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    routes = {name: fixture_route(name, theme, margins) for name, theme, margins in FIXTURES}
    text, _ = report(routes, args.cap_px)
    args.out.write_text(text, encoding="utf-8")
    log.info("wrote %s", args.out)


if __name__ == "__main__":
    main()
