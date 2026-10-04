"""The sheet and the canvas: the paper's noise fields and the pixel grid a plate is painted on.

Key types: `Sheet`, the paper's own noise fields, seeded, shared by every wash and every
mark; `Canvas`, a box in the card's metres and the pixel grid it is painted on, which
projects metre points into render pixels. `rgb` reads a hex colour as floats and `PAPER`
is the card's own cream.

It paints nothing: it is the surface painting is done on.

Invariants: a sheet is a pure function of its size, grain and seed; a sheet with no
fibre is the sheet it always was, because the fibre field is drawn last; a canvas
projects with north up.
"""

from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt

from pyntpot.ink.noise import F32, fbm, fbm_aniso

#: The card's own cream, before anything is laid on it.
PAPER = "#f3ead6"


def rgb(hex_s: str) -> np.ndarray:
    """One hex colour as three floats in 0 to 1."""
    h = hex_s.lstrip("#")
    return np.array([int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)], F32)


@dataclass
class Canvas:
    """The card's metre box and the pixel grid it is painted on."""

    x0: float
    y0: float
    x1: float
    y1: float
    w: int
    h: int

    @property
    def scale(self) -> float:
        """Render pixels per metre."""
        return self.w / (self.x1 - self.x0)

    def px(self, pts: npt.ArrayLike) -> np.ndarray:
        """Project metre points into render pixels, north up."""
        a = np.asarray(pts, dtype=np.float64)
        s = self.scale
        out = np.empty_like(a)
        out[:, 0] = (a[:, 0] - self.x0) * s
        out[:, 1] = (self.y1 - a[:, 1]) * s
        return out


@dataclass
class Sheet:
    """The paper's own noise fields, shared by every wash and every mark."""

    h: int
    w: int
    gran_px: float
    seed: int = 11
    #: Cold press. Above 0 a second noise field, stretched along one sheet-wide
    #: axis, is mixed into the tooth at this weight, so the paper reads as a
    #: laid fibre rather than as concrete. 0 is the isotropic sheet.
    fibre: float = 0.0
    fibre_stretch: float = 3.0
    fibre_angle: float = 0.42
    fibre_cell: float = 4.2
    paper: np.ndarray = field(init=False)
    coarse: np.ndarray = field(init=False)
    fine: np.ndarray = field(init=False)
    wet: np.ndarray = field(init=False)
    gran: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        """Build the five fields from one seeded generator."""
        rng = np.random.default_rng(self.seed)
        self.paper = np.clip(
            0.5 * fbm(self.h, self.w, 3.6, 3, rng) + 0.5 * fbm(self.h, self.w, 92.0, 3, rng), 0, 1
        )
        self.coarse = fbm(self.h, self.w, 74.0, 3, rng)
        self.fine = fbm(self.h, self.w, 5.0, 2, rng)
        self.wet = fbm(self.h, self.w, 130.0, 2, rng)
        self.gran = fbm(self.h, self.w, self.gran_px, 2, rng)
        if self.fibre > 0:
            # Drawn last, so a sheet with no fibre is the sheet it always was:
            # the five fields above have already taken their draws.
            grain = fbm_aniso(
                (self.h, self.w), self.fibre_cell, 3, rng, self.fibre_stretch, self.fibre_angle
            )
            self.paper = np.clip((1.0 - self.fibre) * self.paper + self.fibre * grain, 0, 1)
        self._rng = rng

    def pits(self, gamma: float) -> np.ndarray:
        """How readily pigment settles, from the paper's own height.

        Granulation on real paper is deposition following the tooth: the
        hollows take the heavy pigment, and they are the same hollows a dry
        brush skips over. Taking it from `paper` rather than from an unrelated
        field is what ties the two together.

        Args:
            gamma: How sharply it follows. Above 1 a pigment has to reach a
                real hollow before it settles.

        Returns:
            A field about 0 to 1, high in the pits.
        """
        return np.clip(1.0 - self.paper, 0.0, 1.0) ** F32(max(gamma, 0.05))

    def noise(self, cell: float, octaves: int = 2) -> np.ndarray:
        """One more noise field at this scale."""
        return fbm(self.h, self.w, cell, octaves, self._rng)
