"""Builders the lettering tests share: a tiny style, a tiny basemap, and a river laid on a wide card."""

import dataclasses
import math

from pyntpot.maps.basemap import Basemap, Layers
from pyntpot.maps.card import Card
from pyntpot.maps.card_geometry import journal_geometry
from pyntpot.maps.lettering.label import Label
from pyntpot.maps.lettering.picks_rivers import pick_rivers
from pyntpot.maps.projection import track_projection
from pyntpot.maps.style import Style

#: The `Style` groups the painter and the lettering read, which `class_style` builds.
PAINT_GROUPS: tuple[str, ...] = (
    "paper",
    "wash",
    "brush",
    "face",
    "nib",
    "hand",
    "card",
    "ribbon",
    "cover",
    "route",
    "lettering",
)


#: A short synthetic track inside the Lynmouth box.
LATS = [51.2250 + 2e-5 * i for i in range(60)]


LNGS = [-3.8400 + 0.00040 * i for i in range(60)]


def class_style(**over: object) -> Style:
    """The packaged style with every painted group at its class defaults and `over` moved.

    Each override is named by the field it moves and goes to the group that holds it.
    """
    base = Style.default()
    left = dict(over)
    groups = {}
    for name in PAINT_GROUPS:
        group = type(getattr(base, name))
        mine = {f.name: left.pop(f.name) for f in dataclasses.fields(group) if f.name in left}
        groups[name] = group(**mine)
    assert not left, f"no group holds {sorted(left)}"
    return base.model_copy(update=groups)


def tiny_style(**over: object) -> Style:
    """The approved style, painted small enough to be a unit test."""
    return class_style(display_px=80, supersample=2, **over)


def with_fields(basemap: Basemap, **over: object) -> Basemap:
    """The basemap with any of its own or its layers' fields replaced."""
    names = {f.name for f in dataclasses.fields(Layers)}
    layers = dataclasses.replace(basemap.layers, **{k: v for k, v in over.items() if k in names})
    rest = {k: v for k, v in over.items() if k not in names}
    return dataclasses.replace(basemap, layers=layers, **rest)


def tiny_basemap(style: Style | None = None, **over: object) -> Basemap:
    """A whole basemap for a small box, with nothing in it but the route."""
    style = style or tiny_style()
    route = [(float(x), 40.0 + 30.0 * math.sin(x / 260.0)) for x in range(0, 1400, 40)]
    full = style
    geometry = journal_geometry(route, full.card, full.ribbon, full.brush)
    layers = Layers(
        route=tuple((round(x, 1), round(y, 1)) for x, y in route),
        cover={},
        cover_order=(),
        lakes=(),
        sea=(),
        coastline=(),
        roads=(),
        rivers=(),
        elevation=None,
        ribbon_m=geometry["ribbon_m"],
        wet_px=geometry["wet_px"],
        minor_roads=geometry["minor_roads"],
        blotch_m=geometry["blotch_m"],
        dab_spacing_m=geometry["dab_spacing_m"],
        gran_m=geometry["gran_m"],
    )
    bx0, by0, bx1, by1 = geometry["bounds"]
    basemap = Basemap(
        projection=track_projection(LATS, LNGS)[0],
        card=Card.from_manifest(geometry),
        layers=layers,
        bounds=(bx0, by0, bx1, by1),
        span_m=geometry["span_m"],
        ribbon_fitted_m=geometry["ribbon_fitted_m"],
        track=tuple(route),
    )
    return with_fields(basemap, **over)


def label_basemap(**over: object) -> Basemap:
    """A tiny basemap whose layers carry no painted widths, for the label readers."""
    return with_fields(tiny_basemap(), **{"wet_px": {}, **over})


def wide_card() -> Card:
    """A real card 900 by 671 display pixels at one pixel a metre, for placing a river's name."""
    return Card(
        box=(0.0, 0.0, 900.0, 671.0),
        display=(900, 671),
        render=(900, 671),
        mpp=1.0,
        mpp_display=1.0,
    )


def hung_card(w: int, h: int, mpp: float, top: float = 0.0) -> Card:
    """A real card `w` by `h` display pixels at `mpp` metres a pixel, its top edge at northing `top`.

    A card's pixel rows run down while northing runs up, so a point `d` metres below the top
    edge is written with a northing of `top - d`, and lands `d / mpp` pixels down the card.
    """
    return Card(
        box=(0.0, top - h * mpp, w * mpp, top),
        display=(w, h),
        render=(w, h),
        mpp=mpp,
        mpp_display=mpp,
    )


def river_label(width_px: float) -> Label:
    """One river of a given painted width, placed, 400 pixels down a card that is 671 high."""
    lines = {
        "rivers": [
            {
                "n": "Severn",
                "c": "major",
                "w": width_px,
                "wn": width_px,
                "d": [[100, 271], [800, 271]],
            }
        ]
    }
    basemap = label_basemap(wet_px={"major": 11.0})
    return pick_rivers(basemap, lines, wide_card(), [(100.0, 100.0), (800.0, 100.0)])[0]
