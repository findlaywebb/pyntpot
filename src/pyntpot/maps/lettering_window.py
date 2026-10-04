"""The run of a feature's line a name is set along, for a name the placer skipped.

Key names: `baseline`, which returns the line a label is set along, or None to
set it flat.

The placer chooses a window against everything already on the sheet and leaves
it on the label; this is the fallback for a label that never went through it,
and it is what the old placer did. A label anchored to a line is set along that
line and a label anchored to a point is set horizontally beside it. Rivers,
roads and spans curve; settlements, landmarks and route markers do not, and a
name the reader would have to work at is never curved whatever it is anchored
to: past about sixty degrees of turning the run is rejected and the name is set
flat instead.

It does not lift the line and it never writes: the hand is handed the line.

Invariants: a returned run is never upside down, a run whose text would read
right to left is returned the other way along the same line.
"""

import math

from pyntpot._port import labels as placer
from pyntpot.ink.polyline import Pt, length
from pyntpot.maps.lettering.label import Label
from pyntpot.maps.lettering.span_line import _resample

#: How much longer than the name a window is cut, so the last letter is not
#: clipped at the window's end.
_WINDOW_SLACK = 1.02


def baseline(lb: Label, width: float) -> list[Pt] | None:
    """The run of line this name is set along, or None to set it flat.

    Args:
        lb: The label; its placed window wins when it has one.
        width: The set width of the name, in card pixels.

    Returns:
        The window read left to right, or None when the name is flat, short, or
        has no run of its line that is straight enough.
    """
    if lb.window:
        return lb.window
    if lb.flat or not lb.baseline or len(lb.name) < placer.MIN_CURVED_CHARS:
        return None
    want = width * _WINDOW_SLACK
    line = _resample(lb.baseline, max(want / 24.0, 2.0))
    if length(line) < want:
        return None
    at = _best_window(line, want, (lb.px, lb.py))
    if at is None:
        return None
    # Never upside down: a run whose text would read right to left is written
    # along the same line the other way.
    return at[::-1] if at[-1][0] < at[0][0] else at


def _best_window(line: list[Pt], want: float, near: Pt) -> list[Pt] | None:
    """The readable run of a line that sits closest to a point, or None."""
    best: float | None = None
    at: list[Pt] | None = None
    step = max(len(line) // 40, 1)
    for i in range(0, len(line), step):
        window = placer._window(line, i, want)
        if window is None:
            break
        turn = placer._turning(window)
        if turn > placer.MAX_TURN_DEG:
            continue
        chord = math.dist(window[0], window[-1]) or 1.0
        if placer._bow(window) / chord > placer.MAX_BOW_FRAC:
            continue
        cost = math.dist(window[len(window) // 2], near) + turn * 1.5
        if best is None or cost < best:
            best, at = cost, window
    return at
