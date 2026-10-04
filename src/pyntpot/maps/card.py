"""The card frame: where one map's card metres land on its pixel grids.

Key type: `Card`, the coordinate frame of one map: a box in card metres and
the display and render pixel grids it maps to. It converts a point in card
metres to display pixels (`xy`) and back (`metres`), and to render pixels
(`to_render`). Display pixels have their origin at the top left with y
running down; card metres have y running up, so the box's top edge is
display row 0.

It does not paint, hold a raster or read files: a canvas is the raster a
plate is painted on, and a card only says where things go on it. It is
built from a plates manifest's frame keys with `Card.from_manifest`.

Invariants: a card is immutable and compares by value; `xy` and `metres`
are inverse to floating-point rounding; `xy` computes in a fixed operation
order, so the same card and point always give the same pixels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True)
class Card:
    """The coordinate frame of one map.

    Attributes:
        box: The card in card metres, as x0, y0, x1, y1.
        display: The display pixel grid, width and height.
        render: The render pixel grid the plates are painted at, width and height.
        mpp: Metres per render pixel.
        mpp_display: Metres per display pixel.
    """

    box: tuple[float, float, float, float]
    display: tuple[int, int]
    render: tuple[int, int]
    mpp: float
    mpp_display: float

    @property
    def w(self) -> int:
        """The display width, in pixels."""
        return self.display[0]

    @property
    def h(self) -> int:
        """The display height, in pixels."""
        return self.display[1]

    @property
    def scale(self) -> float:
        """Display pixels per card metre."""
        x0, _y0, x1, _y1 = self.box
        return self.w / (x1 - x0)

    @property
    def render_scale(self) -> float:
        """Render pixels per display pixel."""
        return self.render[0] / max(self.display[0], 1)

    def xy(self, x: float, y: float) -> tuple[float, float]:
        """One point in card metres as display pixels.

        Args:
            x: Easting in card metres.
            y: Northing in card metres.

        Returns:
            The display pixel, x right and y down from the top left.
        """
        x0, _y0, _x1, y1 = self.box
        scale = self.scale
        return ((x - x0) * scale, (y1 - y) * scale)

    def metres(self, px: float, py: float) -> tuple[float, float]:
        """One display pixel as a point in card metres, the inverse of `xy`.

        Args:
            px: Display pixels right of the left edge.
            py: Display pixels down from the top edge.

        Returns:
            The point in card metres.
        """
        x0, _y0, _x1, y1 = self.box
        scale = self.scale
        return (px / scale + x0, y1 - py / scale)

    def to_render(self, x: float, y: float) -> tuple[float, float]:
        """One point in card metres as render pixels.

        Args:
            x: Easting in card metres.
            y: Northing in card metres.

        Returns:
            The render pixel, x right and y down from the top left.
        """
        px, py = self.xy(x, y)
        k = self.render_scale
        return (px * k, py * k)

    @classmethod
    def from_manifest(cls, manifest: Mapping[str, Any]) -> Card:
        """The card a plates manifest was painted on.

        Args:
            manifest: The plates manifest, read for its `card`, `display`,
                `render`, `mpp` and `mpp_display` keys. A manifest without
                `mpp_display` reads as one metre per display pixel.

        Returns:
            The card.
        """
        x0, y0, x1, y1 = manifest["card"]
        dw, dh = manifest["display"]
        rw, rh = manifest["render"]
        return cls(
            box=(x0, y0, x1, y1),
            display=(dw, dh),
            render=(rw, rh),
            mpp=manifest["mpp"],
            mpp_display=manifest.get("mpp_display", 1.0),
        )
