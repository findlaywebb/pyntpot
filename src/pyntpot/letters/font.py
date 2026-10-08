"""The vendored typeface read as glyphs a pen can be run along.

`OutlineFont` opens one `.ttf`, flattens each glyph's contours, and hands back
`Glyph` records: paths in em units with the baseline at y zero and y up, and
the advance. It measures a line and lays one out in the caller's own pixels.
How a glyph becomes strokes is `letters.trace`; this module chooses the route
and caches the result a glyph.

The face is vendored under `fonts/`; its licence is `LICENSE-FONT` at the
repository root. It is Patrick Hand, SIL Open Font License 1.1: an upright,
unjoined print hand with even proportions and a large x-height. A looping
connected script is too scripty and ornate for a plate of names, however well it is
drawn. Patrick Hand is the opposite end of the same shelf.

It does not rasterise, thin or trace (`letters.skeleton`, `letters.trace`), and
it knows nothing of nibs, marks or placement.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from fontTools.pens.basePen import AbstractPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from pyntpot.letters.trace import CENTRELINE, _centrelines

if TYPE_CHECKING:
    from pyntpot.ink.polyline import Pt

#: The vendored face.
DEFAULT_FONT = Path(str(resources.files("pyntpot.letters") / "fonts" / "PatrickHand-Regular.ttf"))

#: A curve is flattened to this many straight pieces. A letter is read at about
#: 14 pixels and never measured, so the tolerance that matters is the eye's.
CURVE_STEPS = 8

#: A cubic arrives with three points; two is a quadratic in a pen's clothing.
QUAD_ARGS = 2

#: A closed contour made only of control points needs at least this many.
MIN_CONTROLS = 2

#: A contour of fewer points than this has no area and is not kept.
MIN_CONTOUR = 3


class _Flatten(AbstractPen):
    """A pen that records one glyph's contours as flattened polylines."""

    def __init__(self) -> None:
        """Start with nothing recorded."""
        self.contours: list[list[Pt]] = []
        self._cur: list[Pt] = []
        self._start: Pt = (0.0, 0.0)

    @override
    def moveTo(self, pt: Pt) -> None:
        """Start a contour."""
        self._flush()
        self._cur = [(float(pt[0]), float(pt[1]))]
        self._start = self._cur[0]

    @override
    def lineTo(self, pt: Pt) -> None:
        """A straight piece."""
        if not self._cur:
            return
        self._cur.append((float(pt[0]), float(pt[1])))

    @override
    def curveTo(self, *pts: Pt) -> None:
        """A cubic, or the higher-order form fontTools hands a pen."""
        if len(pts) == QUAD_ARGS:
            self.qCurveTo(*pts)
            return
        if not self._cur:
            return
        a = self._cur[-1]
        for i in range(0, len(pts) - 1, 2):
            b, c = pts[i], pts[i + 1]
            d = pts[i + 2] if i + 2 < len(pts) else pts[-1]
            self._cubic(a, b, c, d)
            a = self._cur[-1]

    @override
    def qCurveTo(self, *pts: Pt | None) -> None:
        """A quadratic run, with TrueType's implied on-curve points.

        A contour with no on-curve point at all is written as a run ending in
        None, and it arrives without a `moveTo` of its own, so it starts at the
        midpoint between its last control point and its first.
        """
        if pts and pts[-1] is None:
            self._all_off([(float(p[0]), float(p[1])) for p in pts[:-1] if p is not None])
            return
        if not self._cur:
            return
        a = self._cur[-1]
        run = tuple((float(p[0]), float(p[1])) for p in pts if p is not None) or (a,)
        for i in range(len(run) - 1):
            ctrl = run[i]
            nxt = run[i + 1]
            end = nxt if i == len(run) - 2 else ((ctrl[0] + nxt[0]) / 2, (ctrl[1] + nxt[1]) / 2)
            self._quad(a, ctrl, end)
            a = end

    @override
    def closePath(self) -> None:
        """Close the contour back onto its own first point."""
        if self._cur and self._cur[-1] != self._start:
            self._cur.append(self._start)
        self._flush()

    @override
    def endPath(self) -> None:
        """An open contour, which a glyph should not have but might."""
        self._flush()

    @override
    def addComponent(self, glyphName: str, transformation: Any) -> None:
        """Components are decomposed before the pen sees them."""

    def _all_off(self, ctrls: list[Pt]) -> None:
        """A closed contour made only of control points."""
        if len(ctrls) < MIN_CONTROLS:
            return
        self._flush()
        start = ((ctrls[-1][0] + ctrls[0][0]) / 2, (ctrls[-1][1] + ctrls[0][1]) / 2)
        self._cur = [start]
        self._start = start
        a = start
        for i, ctrl in enumerate(ctrls):
            nxt = ctrls[(i + 1) % len(ctrls)]
            end = start if i == len(ctrls) - 1 else ((ctrl[0] + nxt[0]) / 2, (ctrl[1] + nxt[1]) / 2)
            self._quad(a, ctrl, end)
            a = end
        self.closePath()

    def _quad(self, a: Pt, b: Pt, c: Pt) -> None:
        """One quadratic, flattened."""
        for i in range(1, CURVE_STEPS + 1):
            t = i / CURVE_STEPS
            u = 1.0 - t
            self._cur.append(
                (
                    u * u * a[0] + 2 * u * t * b[0] + t * t * c[0],
                    u * u * a[1] + 2 * u * t * b[1] + t * t * c[1],
                )
            )

    def _cubic(self, a: Pt, b: Pt, c: Pt, d: Pt) -> None:
        """One cubic, flattened."""
        for i in range(1, CURVE_STEPS + 1):
            t = i / CURVE_STEPS
            u = 1.0 - t
            self._cur.append(
                (
                    u**3 * a[0] + 3 * u * u * t * b[0] + 3 * u * t * t * c[0] + t**3 * d[0],
                    u**3 * a[1] + 3 * u * u * t * b[1] + 3 * u * t * t * c[1] + t**3 * d[1],
                )
            )

    def _flush(self) -> None:
        """Keep whatever contour is open."""
        if len(self._cur) >= MIN_CONTOUR:
            self.contours.append(self._cur)
        self._cur = []


@dataclass
class Glyph:
    """One character, ready to be drawn.

    `paths` are in em units with the baseline at y zero and the pen starting at
    x zero, y up. `advance` is in the same units, so a caller multiplies both
    by the type size and never thinks about the font again.
    """

    ch: str
    advance: float
    paths: list[list[Pt]]

    @property
    def ink(self) -> bool:
        """Whether this glyph puts anything on the paper."""
        return bool(self.paths)


class OutlineFont:
    """One typeface, as glyphs a pen can be run along.

    Args:
        path: The `.ttf` to read.
        route: `CENTRELINE` to thin the glyph to a written skeleton, `OUTLINE`
            to draw round its own contour.
    """

    def __init__(self, path: Path | str = DEFAULT_FONT, route: str = CENTRELINE) -> None:
        """Open the face and read its metrics."""
        self.path = Path(path)
        self.route = route
        self._font = TTFont(str(self.path), lazy=True)
        self._pen_cls = DecomposingRecordingPen
        self._glyphs = self._font.getGlyphSet()
        self._cmap = self._font.getBestCmap() or {}
        head: Any = self._font["head"]
        hhea: Any = self._font["hhea"]
        self.upem = int(head.unitsPerEm)
        self.ascender = float(hhea.ascent) / self.upem
        self.descender = float(hhea.descent) / self.upem
        self._cache: dict[str, Glyph] = {}

    @property
    def name(self) -> str:
        """The face's file name, for a note that says what lettered the plate."""
        return self.path.stem

    def _name_of(self, ch: str) -> str | None:
        """The glyph name for one character, or None when the face has none."""
        return self._cmap.get(ord(ch))

    def glyph(self, ch: str) -> Glyph:
        """One character as paths in em units, cached.

        Args:
            ch: The character.

        Returns:
            The glyph. A character the face has not got comes back with a
            fixed advance of 0.28 em and nothing to draw, which is what a
            missing glyph should look like on a plate and not a box.
        """
        got = self._cache.get(ch)
        if got is not None:
            return got
        name = self._name_of(ch)
        if name is None:
            self._cache[ch] = Glyph(ch, 0.28, [])
            return self._cache[ch]
        advance = self._font["hmtx"][name][0] / self.upem
        rec = self._pen_cls(self._glyphs)
        self._glyphs[name].draw(rec)
        flat = _Flatten()
        rec.replay(flat)
        contours = flat.contours
        if not contours:
            self._cache[ch] = Glyph(ch, advance, [])
            return self._cache[ch]
        if self.route == CENTRELINE:
            paths = _centrelines(contours, self.upem)
        else:
            paths = [[(x / self.upem, y / self.upem) for x, y in c] for c in contours]
        self._cache[ch] = Glyph(ch, advance, paths)
        return self._cache[ch]

    def advance(self, ch: str) -> float:
        """One character's advance in em units."""
        return self.glyph(ch).advance

    def measure(self, text: str, size: float, tracking: float = 0.0) -> tuple[float, float]:
        """How wide and how tall one line is, in the caller's own pixels.

        Args:
            text: The line.
            size: The type size in display pixels.
            tracking: Extra letter spacing, in em units.

        Returns:
            `(width, height)` in display pixels; an empty line is no width and
            `size` tall.
        """
        s = str(text)
        if not s:
            return 0.0, size
        width = sum(self.advance(c) + tracking for c in s) - tracking
        return width * size, (self.ascender - self.descender) * size * 0.86

    def run(
        self, text: str, size: float, tracking: float = 0.0
    ) -> list[tuple[str, float, float, list[list[Pt]]]]:
        """Every glyph of a line, at its pen position, scaled to the type size.

        Args:
            text: The line.
            size: The type size in display pixels.
            tracking: Extra letter spacing, in em units.

        Returns:
            One `(character, pen x, advance, paths)` a character, paths in
            display pixels with the baseline at y zero and y up, relative to
            that character's own pen position.
        """
        out = []
        pen = 0.0
        for ch in str(text):
            g = self.glyph(ch)
            paths = [[(x * size, y * size) for x, y in p] for p in g.paths]
            out.append((ch, pen, g.advance * size, paths))
            pen += (g.advance + tracking) * size
        return out


@functools.lru_cache(maxsize=8)
def load(path: str | None = None, route: str = CENTRELINE) -> OutlineFont:
    """A face, the vendored one by default, opened once a path and route and kept.

    Args:
        path: The font file, or None for the vendored one.
        route: `CENTRELINE` or `OUTLINE`.

    Returns:
        The face.
    """
    return OutlineFont(Path(path) if path else DEFAULT_FONT, route)
