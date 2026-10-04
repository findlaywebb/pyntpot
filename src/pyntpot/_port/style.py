"""Route ink and the cream page tokens."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: The route ink, for every sport: a burnt maroon
#: on the pinker side, blended from the original rose (#e01c64) toward maroon,
#: and lifted back toward it.
#:
#: The maroon read as one more dark mark on a sheet already carrying dark
#: washes: against cream it had the contrast (6.5:1) and against a wood or a
#: built-up wash it had almost none, and the route is the one line on the card
#: the reader is looking for. This is about 40% more luminous and carries more
#: chroma with it, which is what actually separates it from a green or a grey
#: wash, and it still holds 5:1 on the paper. It is not the rose: that was
#: too hot, and this sits between the two.
ROUTE_INK = "#c22050"
#: Everything `basemap_route_effect` understands, all of it off. A theme names
#: only the keys it wants and the rest are filled in from here, so a block that
#: asks for a glow is not also silently asking for a shadow.
ROUTE_EFFECT_OFF: dict[str, Any] = {
    "glow_px": 0.0,
    "glow_opacity": 0.0,
    "casing_colour": "cream",
    "casing_px": 0.0,
    "adaptive_pct": 0.0,
    "shadow_px": 0.0,
    "shadow_blur_px": 0.0,
    "blend": "normal",
}
#: The three casings the lab offered. Anything else is taken as a colour.
CASING_COLOURS = {"cream": "#f2e9d4", "dark": "#241c14", "white": "#ffffff"}
#: The drop shadow's pigment, from the lab: a brown black, not a grey.
ROUTE_SHADOW = "#120d07"


@dataclass(frozen=True)
class RouteInk:
    """One sport's route treatment, with every effect key already filled in."""

    style: str
    px: float
    colour: str
    effect: dict[str, Any]

    @property
    def casing(self) -> str:
        """The casing's colour: one of the three names, or a colour as given."""
        named = str(self.effect["casing_colour"])
        return CASING_COLOURS.get(named, named)


#: The pigments of the cream notebook page. A card is its own object with its
#: own ground, so it carries its own colours rather than the theme's tokens.
CREAM_PIGMENTS = {
    "map_sea": "#93b5c6",
    "map_water": "#5b86a4",
    "map_wood": "#6f8f5a",
    "map_park": "#a9ba8b",
    "map_road": "#8a7f6d",
    "map_relief": "#b09b78",
    "map_ink": "#5f574a",
    "bg1": "#efe9dc",
    "fg0": "#2b2620",
    "fg1": "#3d372e",
    "fg2": "#6b6355",
    "actual": "#2b2620",
}
CREAM_PAPER = "#efe9dc"
