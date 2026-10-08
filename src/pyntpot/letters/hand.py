"""The hand: it writes a setting in a real face, a little differently each time.

Key types: `Hand`, which opens the face a `FaceStyle` names and writes a
`Setting` as `Mark`s, and measures text in that face; the `Setting` and `Mark`
it trades in live in `letters.setting`.

The face gives the proportions, which is the whole reason for taking one: a
stroke font is a skeleton somebody plotted and a handwriting face is a hand
somebody drew. What the hand adds is everything a designed face has no way to
say, because a font is by construction the same shape every time: a letter
leans a shade differently in every word, a baseline drifts, and the pen is
never held at quite the same angle twice. Every one of those draws comes from
the generator the caller passes to `write`, so the caller decides what an
instance is seeded by and may carry the same generator on into whatever else it
draws beside the text: `generator` makes one, `stroke` wanders a line the
caller drew along it with the same hand.

It does not choose where a name sits, which way along a line it reads, how far
it is lifted off a feature or which ink a class of feature takes: those arrive
in the setting. It draws no furniture and it never reverses or lifts a path.

Invariants: the draw order of one `write` is fixed (the pen's tilt, then for a
flat block the block's tilt, then each glyph's drift, and for each of its
strokes the lean, scale, rotation, nudge and wobble), so the same setting and a
generator in the same state write the same marks; `measure` is the face's own
width, with no padding.
"""

import math

import numpy as np

from pyntpot.ink.polyline import Pt, cumulative_length, deform_line
from pyntpot.letters.font import load as load_font
from pyntpot.letters.setting import Mark, Setting
from pyntpot.letters.style import FaceStyle, HandStyle

#: The mask a seed is cut to, so it is a non-negative 31-bit number.
_SEED_MASK = 0x7FFFFFFF

#: The fewest points a line can be wandered along: it needs two ends.
_LINE_ENDS = 2

#: How far a flat block's rows sit apart, as a share of the type size.
_ROW_LEADING = 1.06


class Hand:
    """The writer: a real face, per-instance variation, and marks to stroke.

    Args:
        face: Which face to open and how a glyph becomes a pen path.
        hand: The style whose `label_seed` every generator is mixed with.
        route: `centreline` or `outline`; the face style's when not given.
    """

    def __init__(self, face: FaceStyle, hand: HandStyle, route: str | None = None) -> None:
        """Open the face the style names."""
        self.route = route or face.label_route
        self.font = load_font(face.label_face or None, self.route)
        self.seed = int(hand.label_seed)

    def measure(self, text: str, size: float, tracking: float = 0.0) -> tuple[float, float]:
        """How wide and how tall a text is set, from the face's own metrics.

        Args:
            text: What is set.
            size: The type size, in display pixels.
            tracking: Extra letter spacing, in em units.

        Returns:
            The set width and the height, with no room added around them.
        """
        return self.font.measure(text, size, tracking)

    def generator(self, seed: int) -> np.random.Generator:
        """This instance's own generator: the style's seed mixed with the caller's.

        Every draw a name makes comes from here, so an unchanged set of names letters
        identically on every render and a deliberate reshuffle is one number in
        the style.
        """
        return np.random.default_rng((self.seed ^ int(seed)) & _SEED_MASK)

    def stroke(self, points: list[Pt], rng: np.random.Generator, amount: float) -> list[Pt]:
        """A hand's own wander along a line the caller drew, a different curve every instance.

        Args:
            points: The line, in display pixels; its ends stay where they were.
            rng: The generator the wander is drawn from.
            amount: How far it wanders; nothing is drawn when it is not positive.

        Returns:
            The wandered line, or a copy of it when `amount` is not positive or
            the line has fewer than two points.
        """
        if amount <= 0 or len(points) < _LINE_ENDS:
            return list(points)
        got = deform_line(points, (rng, amount * 0.14, 2, 0.55, amount * 1.3, 1.4))
        return [(float(x), float(y)) for x, y in got]

    def write(self, setting: Setting, rng: np.random.Generator) -> list[Mark]:
        """A setting as one mark a glyph stroke, in display pixels.

        Args:
            setting: What to write and how it is set.
            rng: The generator every draw comes from; left positioned after the
                last glyph.

        Returns:
            The glyph marks, in the order the pen lays them down.
        """
        pen = float(rng.normal(0.0, 0.09))
        if setting.path is not None:
            strokes = self._along(setting, setting.path, rng)
        elif setting.anchor is not None:
            strokes = self._flat(setting, setting.anchor, rng)
        else:  # unreachable: a setting is built with one of the two
            strokes = []
        return [
            Mark(
                pts=pts,
                role="glyph",
                ink=setting.ink,
                size=setting.size,
                pen=pen,
                wash=setting.wash,
            )
            for pts in strokes
        ]

    def _along(
        self, setting: Setting, walk: tuple[Pt, ...], rng: np.random.Generator
    ) -> list[list[Pt]]:
        """The text set along a line, each glyph on its own tangent."""
        line = list(walk)
        cum = cumulative_length(line)
        out: list[list[Pt]] = []
        for _ch, pen_x, adv, paths in self.font.run(setting.text, setting.size, setting.tracking):
            if not paths:
                continue
            (ox, oy), theta = _on_line(line, cum, pen_x + adv * 0.5)
            cos_t, sin_t = math.cos(theta), math.sin(theta)
            drift = float(rng.normal(0.0, setting.size * 0.02))
            for path in paths:
                pts = []
                for gx, gy in self._vary(path, setting, rng):
                    x, y = gx - adv * 0.5, gy + drift
                    pts.append((ox + x * cos_t + y * sin_t, oy + x * sin_t - y * cos_t))
                out.append(self.stroke(pts, rng, 0.14))
        return out

    def _flat(self, setting: Setting, anchor: Pt, rng: np.random.Generator) -> list[list[Pt]]:
        """The text set horizontally from its anchor, one row at a time.

        Each row is aligned on the block, not on itself, so a `start` block
        stays flush left and a `middle` block stays centred.
        """
        ax, ay = anchor
        rows = setting.lines or (setting.text,)
        size, track = setting.size, setting.tracking
        width = max(self.font.measure(row, size, track)[0] for row in rows)
        tilt = float(rng.normal(0.0, 0.012))
        cos_t, sin_t = math.cos(tilt), math.sin(tilt)
        out: list[list[Pt]] = []
        for index, text in enumerate(rows):
            run = self.font.measure(text, size, track)[0]
            x0 = ax - _held_back(setting.align, width) + _row_pad(setting.align, width, run)
            baseline = ay + index * size * _ROW_LEADING
            for _ch, pen_x, _adv, paths in self.font.run(text, size, track):
                if not paths:
                    continue
                drift = float(rng.normal(0.0, size * 0.022))
                for path in paths:
                    pts = []
                    for gx, gy in self._vary(path, setting, rng):
                        x, y = pen_x + gx, gy + drift
                        pts.append((x0 + x * cos_t + y * sin_t, baseline + x * sin_t - y * cos_t))
                    out.append(self.stroke(pts, rng, 0.14))
        return out

    def _vary(self, path: list[Pt], setting: Setting, rng: np.random.Generator) -> list[Pt]:
        """One stroke of a glyph, this time: leaned, scaled, turned and nudged a little."""
        lean = setting.slant + float(rng.normal(0.0, 0.03))
        sx = 1.0 + float(rng.normal(0.0, 0.022))
        sy = 1.0 + float(rng.normal(0.0, 0.028))
        rot = float(rng.normal(0.0, 0.024))
        dx = float(rng.normal(0.0, setting.size * 0.012))
        cos_r, sin_r = math.cos(rot), math.sin(rot)
        out = []
        for x, y in path:
            gx, gy = x * sx, y * sy
            gx += lean * gy
            out.append((gx * cos_r - gy * sin_r + dx, gx * sin_r + gy * cos_r))
        return out


def _held_back(align: str, width: float) -> float:
    """How far left of its anchor a block of this width starts."""
    if align == "end":
        return width
    return width / 2 if align == "middle" else 0.0


def _row_pad(align: str, width: float, run: float) -> float:
    """How far a row is moved in from its block's left edge."""
    if align == "start":
        return 0.0
    return width - run if align == "end" else (width - run) / 2


def _on_line(line: list[Pt], cum: list[float], at: float) -> tuple[Pt, float]:
    """The point at an arc length along a line, and the tangent's angle there."""
    at = min(max(at, 0.0), cum[-1])
    i = min(_segment(cum, at), len(line) - 2)
    run = max(cum[i + 1] - cum[i], 1e-9)
    t = (at - cum[i]) / run
    (ax, ay), (bx, by) = line[i], line[i + 1]
    return ((ax + (bx - ax) * t, ay + (by - ay) * t), math.atan2(by - ay, bx - ax))


def _segment(cum: list[float], at: float) -> int:
    """The segment an arc length falls in."""
    lo, hi = 0, len(cum) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if cum[mid] <= at:
            lo = mid
        else:
            hi = mid
    return lo
