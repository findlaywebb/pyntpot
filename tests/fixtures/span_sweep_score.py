"""Score a span's two marks on a stretch, and sweep the scale the bend is read at.

The measuring half of `sweep_span_scale`. Key names: `stretches`, the sliding stretches
by arc length; `coverage` and `kept_share`, how much of its own mark a side keeps once
cleared of the route; `decisive`; `judge`, a stretch's case; `sweep`, the per-scale
counts; `decide`, the decision rule.

It reads no fixture and writes nothing; only the shipped `span_line`, `_convex_side` and
`bend_strength` are measured, never changed.
"""

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise

from pyntpot.ink.polyline import Pt
from pyntpot.maps.lettering.label import Span
from pyntpot.maps.lettering.span_line import SPAN_OFFSET_CAPS, span_line
from pyntpot.maps.lettering.span_sides import _convex_side, bend_strength

#: The scales swept, in cap heights: 0.6 to 2.5 in tenths.
SCALES = [i / 10 for i in range(6, 26)]

#: The stretch length the decision is made on, and the step, in cap heights.
LENGTH_CAPS = 16.0

STEP_CAPS = 2.0

#: The secondary lengths, reported only, each with the largest scale that still leaves
#: a stretch five resampled segments.
SECONDARY = {10.0: 2.0, 24.0: 2.5}

#: How much more of its own mark one side has to keep to be clearly the better: a quarter.
CLEARLY_BETTER_RATIO = 1.25

#: How near a scale over the offset has to come to a multiple of a half to be one.
MULTIPLE_TOL = 1e-9

#: The lettering's cap height in display pixels, as `place_spans` is called.
CAP_PX = 14.0

#: The fewest points a stretch needs before it has a middle one.
_FEWEST = 3

#: The cases a stretch falls into, in the order they are checked.
CASES = ("no-outside", "empty-mark", "ambiguous-feet", "even", "decisive")


def _cumulative(line: Sequence[Pt]) -> list[float]:
    """Arc length at every point of a polyline."""
    out: list[float] = [0.0]
    for a, b in pairwise(line):
        out.append(out[-1] + math.dist(a, b))
    return out


def stretches(
    route_px: Sequence[Pt], cap_px: float, length_caps: float, step_caps: float
) -> list[tuple[int, int]]:
    """Sliding stretches as `(i0, i1)`: each end the first index at or past its arc length.

    Starts are `k * step` for `k = 0, 1, ...` while a whole stretch still fits; a stretch
    of fewer than three points is skipped.
    """
    cum = _cumulative(route_px)
    run, step = length_caps * cap_px, step_caps * cap_px
    out: list[tuple[int, int]] = []
    k = 0
    while k * step + run <= cum[-1]:
        s = k * step
        i0 = next(i for i, c in enumerate(cum) if c >= s)
        i1 = next(i for i, c in enumerate(cum) if c >= s + run)
        if i1 - i0 + 1 >= _FEWEST:
            out.append((i0, i1))
        k += 1
    return out


def _position(p: Pt, sub: Sequence[Pt], cum: list[float]) -> float:
    """Arc length along `sub` of the foot of `p` on its nearest segment."""
    best, at = math.inf, 0.0
    for i, (a, b) in enumerate(pairwise(sub)):
        vx, vy = b[0] - a[0], b[1] - a[1]
        run = vx * vx + vy * vy
        t = 0.0 if run <= 0.0 else ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / run
        t = min(max(t, 0.0), 1.0)
        d = math.dist(p, (a[0] + t * vx, a[1] + t * vy))
        if d < best:
            best, at = d, cum[i] + t * math.sqrt(run)
    return at


def coverage(mark: Sequence[Pt], sub: Sequence[Pt]) -> float:
    """The signed share of the stretch between the feet of the mark's two ends.

    Negative when the last end's foot comes before the first's; not clamped; 0.0 for a
    mark under two points or a stretch of no length.
    """
    if len(mark) < 2 or len(sub) < 2:
        return 0.0
    cum = _cumulative(sub)
    if cum[-1] <= 0.0:
        return 0.0
    return (_position(mark[-1], sub, cum) - _position(mark[0], sub, cum)) / cum[-1]


def kept_share(drawn: Sequence[Pt], unclipped: Sequence[Pt], sub: Sequence[Pt]) -> float | None:
    """How much of its own unclipped mark a side keeps once cleared of the route.

    None, the ambiguous-feet case, when the unclipped coverage is not positive, the drawn
    one is negative, or the share is over `CLEARLY_BETTER_RATIO`: no clearance pass makes
    a mark keep a quarter more than it had, so a foot has landed on another limb.
    """
    whole, kept = coverage(unclipped, sub), coverage(drawn, sub)
    if whole <= 0.0 or kept < 0.0:
        return None
    share = kept / whole
    return None if share > CLEARLY_BETTER_RATIO else share


def decisive(a: float, b: float) -> int:
    """The better side, +1 for `a` and -1 for `b`, when it keeps over 1.25 times the other."""
    hi, lo = max(a, b), min(a, b)
    if hi > CLEARLY_BETTER_RATIO * lo:
        return 1 if a > b else -1
    return 0


@dataclass(frozen=True)
class Verdict:
    """One stretch, judged once: its case, its outside and its better side (0 unless decisive)."""

    case: str
    outside: int
    better: int

    @property
    def right(self) -> bool:
        """Whether the outside is the better mark."""
        return self.case == "decisive" and self.outside == self.better


def judge(span: Span, route_px: list[Pt], cap_px: float) -> Verdict:
    """Which case a stretch is, by the marks the shipped code draws for rung 0."""
    outside, marks = _convex_side(span, route_px, cap_px)
    if outside == 0:
        return Verdict("no-outside", 0, 0)
    if any(len(marks[side]) < 2 for side in (1, -1)):
        return Verdict("empty-mark", outside, 0)
    sub = route_px[span.i0 : span.i1 + 1]
    offset = cap_px * SPAN_OFFSET_CAPS
    shares = {}
    for side in (1, -1):
        unclipped = span_line(route_px, span.i0, span.i1, side, offset, clear_px=0.0)
        shares[side] = kept_share(marks[side], unclipped, sub)
    plus, minus = shares[1], shares[-1]
    if plus is None or minus is None:
        return Verdict("ambiguous-feet", outside, 0)
    better = decisive(plus, minus)
    return Verdict("decisive" if better else "even", outside, better)


@dataclass(frozen=True)
class ScaleRow:
    """One scale's counts over the voted stretches."""

    scale: float
    voted: int
    empty_mark: int
    ambiguous_feet: int
    even: int
    decisive: int
    right: int

    @property
    def percent_right(self) -> float | None:
        """The outside's share right of the decisive stretches, in percent, or None."""
        return 100.0 * self.right / self.decisive if self.decisive else None


def sweep(
    cases: Sequence[tuple[Sequence[Pt], Verdict]], cap_px: float, scales: Sequence[float]
) -> list[ScaleRow]:
    """Per scale, the voted stretches by case; only the bend's vote is read again."""
    rows = []
    for k in scales:
        tally: Counter[str] = Counter()
        right = 0
        for sub, verdict in cases:
            if bend_strength(list(sub), cap_px * k) <= 0.0:
                continue
            tally["voted"] += 1
            tally[verdict.case] += 1
            right += verdict.right
        rows.append(
            ScaleRow(
                k,
                tally["voted"],
                tally["empty-mark"],
                tally["ambiguous-feet"],
                tally["even"],
                tally["decisive"],
                right,
            )
        )
    return rows


@dataclass(frozen=True)
class Decision:
    """What the decision rule chose, and the numbers it chose on."""

    scale: float
    changed: bool
    reason: str
    n_current: int
    best: float | None = None
    lower: float | None = None
    upper: float | None = None
    multiple: float | None = None


def _multiple(scale: float) -> float | None:
    """`m` when the scale is `m * SPAN_OFFSET_CAPS` for `m` a multiple of a half."""
    m = round(scale / SPAN_OFFSET_CAPS * 2.0) / 2.0
    return m if abs(scale / SPAN_OFFSET_CAPS - m) < MULTIPLE_TOL else None


def decide(
    rows: Sequence[ScaleRow],
    length_caps: float,
    step_caps: float,
    current: float = 1.5,
    n_min: int = 30,
) -> Decision:
    """The decision rule: keep `current` unless a scale is clearly better on enough data."""
    now = next(r for r in rows if abs(r.scale - current) < MULTIPLE_TOL)
    if now.decisive < n_min:
        reason = f"{now.decisive} decisive stretches at {current} are too few to compare"
        return Decision(current, False, reason, now.decisive)
    eligible = [r for r in rows if r.decisive >= n_min]
    best = max(eligible, key=lambda r: (round(r.percent_right or 0.0, 1), r.decisive, -r.scale))
    n_eff = best.decisive * step_caps / length_caps
    p = best.right / best.decisive
    tilde = (p * n_eff + 2.0) / (n_eff + 4.0)
    half = 1.96 * math.sqrt(tilde * (1.0 - tilde) / (n_eff + 4.0))
    lower, upper = tilde - half, tilde + half
    share_now = now.right / now.decisive
    changed = share_now < lower and abs(best.scale - current) > MULTIPLE_TOL
    reason = (
        f"{current} at {share_now:.3f} lies below the best's lower bound {lower:.3f}"
        if changed
        else f"{current} at {share_now:.3f} is not below the best's lower bound {lower:.3f}"
    )
    return Decision(
        best.scale if changed else current,
        changed,
        reason,
        now.decisive,
        best.scale,
        lower,
        upper,
        _multiple(best.scale) if changed else None,
    )
