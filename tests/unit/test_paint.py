"""Tests for the painter, its brushes and the lettering hand.

Everything here paints a box a few dozen pixels across, so the suite stays fast.
"""

from __future__ import annotations

import dataclasses
import math
from typing import TYPE_CHECKING

import numpy as np
import pytest

from pyntpot.ink.brush import BRUSH_COLOURS
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.io import save_rgba
from pyntpot.ink.noise import edt
from pyntpot.ink.polyline import deform_line, length
from pyntpot.ink.sheet import Sheet, rgb
from pyntpot.maps.basemap import Basemap, Line, River, Road
from pyntpot.maps.card_geometry import journal_geometry
from pyntpot.maps.lettering.label import (
    WET_PX_DEFAULT,
    WET_SPREAD,
    Label,
    feature_px,
)
from pyntpot.maps.painter.plates import paint_plates
from pyntpot.maps.painter.ribbon import ribbon_alpha
from pyntpot.maps.style_groups import CardStyle, RibbonStyle

from support.basemaps import (
    PAINT_GROUPS,
    class_style,
    label_basemap,
    river_label,
    tiny_basemap,
    tiny_style,
    with_fields,
)
from support.lettering import open_hand

if TYPE_CHECKING:
    from pyntpot.maps.style import Style


def read(style: Style, name: str) -> object:
    """The value of the one field called `name`, whichever group of the style holds it."""
    for group in PAINT_GROUPS:
        values = dataclasses.asdict(getattr(style, group))
        if name in values:
            return values[name]
    raise KeyError(name)


def square(cx: float, cy: float, r: float) -> Line:
    """One closed square ring at a tenth of a metre, in metres."""
    pts = [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]
    return tuple((round(x, 1), round(y, 1)) for x, y in pts)


# --------------------------------------------------------------------------- painter


def test_a_tiny_box_paints_a_card_a_wash_and_a_manifest(tmp_path):
    """The painter writes two plates plus the pen, and says what it did."""
    style = tiny_style()
    plates = paint_plates(tiny_basemap(style=style), style, tmp_path)
    manifest = plates.manifest
    assert set(manifest.files) == {"paper", "wash", "pen"}
    for path in plates.paths.values():
        assert path.stat().st_size > 0
    assert (tmp_path / "plates.json").exists()
    assert manifest.card.display[0] == 80
    assert manifest.card.render[0] == 160
    assert manifest.dark.w == read(style, "dark_grid")[0]
    assert len(manifest.dark.values) == read(style, "dark_grid")[1]


def test_the_plates_are_webp_the_size_they_were_painted(tmp_path):
    """A plate is a WebP at the render size, not at the display size."""
    from PIL import Image

    style = tiny_style()
    plates = paint_plates(tiny_basemap(style=style), style, tmp_path)
    with Image.open(plates.paths["wash"]) as img:
        assert img.format == "WEBP"
        assert img.size == plates.card.render
    with Image.open(plates.paths["pen"]) as img:
        assert img.mode in ("RGBA", "P")


# ------------------------------------------------------- phase 1: the brush flags

#: The smoke box: a route, three roads and two watercourses, so every brush the
#: plate carries is stamped. Small enough to paint in a fraction of a second.
SMOKE_ROADS = (
    Road(((0.0, 200.0), (400.0, 180.0), (900.0, 240.0), (1390.0, 200.0)), "", "major", "", "", ""),
    Road(((40.0, 60.0), (600.0, 140.0), (1340.0, 90.0)), "", "minor", "", "", ""),
    Road(((30.0, 340.0), (700.0, 300.0), (1360.0, 360.0)), "", "path", "", "", ""),
)


SMOKE_RIVERS = (
    River(((20.0, 10.0), (400.0, 120.0), (900.0, 60.0), (1380.0, 150.0)), "major", "Lyn", 0.0, 0.0),
    River(((60.0, 300.0), (500.0, 250.0), (1100.0, 320.0)), "minor", "", 0.0, 0.0),
)


#: What HEAD's painter writes for that box at 120 display pixels. Every phase 1
#: field is off or inert by default, so these are what the working painter has
#: to keep writing, byte for byte.
#:
#: Moved twice, deliberately, both times by the stroke quality work. First when
#: `ink_ss` went on at 3 and `plate_lossless` on, because the marks on this
#: plate are three or four render pixels wide and the lossy encoder was
#: replacing their edge-to-centre ramp with two flats and a step. Then when the
#: bristle drift stopped being drawn independently per bristle: the tip was
#: folding over itself and landing as filaments with bare paper between them,
#: which shows as streaking. `paper` has not moved either time, because
#: neither change touches the card. The lock still holds: a change that moves
#: these hashes again is a change to what the reader sees and has to be argued
#: for.
SMOKE_SHA = {
    "paper": "014d13332900f01fd6653d9405e933aaec9efe2f17ce78f8fa523b1e6954e93e",
    "pen": "33614c92d30798b8ce823c5c1473115f46f7277ffe4b3345dc31f626c8fa03a6",
    "wash": "c45a643c36a9459cbefc748dce925222d410f537dede660db283284eea702c03",
}


def smoke_box(**over: object) -> tuple[Style, Basemap]:
    """The smoke box's style and basemap, with any style fields moved."""
    style = class_style(display_px=120, supersample=2, **over)
    return style, tiny_basemap(style=style, roads=SMOKE_ROADS, rivers=SMOKE_RIVERS)


def test_the_flags_off_still_paint_the_plates_that_were_approved(tmp_path):
    """The whole point of the flags: the same seed still writes the same bytes."""
    import hashlib

    style, basemap = smoke_box()
    manifest = paint_plates(basemap, style, tmp_path).manifest
    got = {
        name: hashlib.sha256((tmp_path / fn).read_bytes()).hexdigest()
        for name, fn in manifest.files.items()
    }
    assert got == SMOKE_SHA


def test_every_flag_on_together_still_paints_the_box(tmp_path):
    """And with all three on it is a different plate, not a broken one."""
    import hashlib

    style, basemap = smoke_box(ink_starve=True, dry_directional=True, pen_starve=True)
    manifest = paint_plates(basemap, style, tmp_path).manifest
    got = {
        name: hashlib.sha256((tmp_path / fn).read_bytes()).hexdigest()
        for name, fn in manifest.files.items()
    }
    assert got["paper"] == SMOKE_SHA["paper"]  # nothing here touches the card
    assert got["wash"] != SMOKE_SHA["wash"]
    assert got["pen"] != SMOKE_SHA["pen"]


# ---------------------------------------------------- phase 2: brush quality


def test_the_phase_2_brush_flags_on_together_still_paint_the_box(tmp_path):
    """All four on is a different plate, not a broken one, and not the card."""
    import hashlib

    style, basemap = smoke_box(brush_organic=True, ink_joins=True, stroke_smooth=True, ink_ss=2)
    manifest = paint_plates(basemap, style, tmp_path).manifest
    got = {
        name: hashlib.sha256((tmp_path / fn).read_bytes()).hexdigest()
        for name, fn in manifest.files.items()
    }
    assert got["paper"] == SMOKE_SHA["paper"]  # nothing here touches the card
    assert got["wash"] != SMOKE_SHA["wash"]
    assert got["pen"] != SMOKE_SHA["pen"]


# --------------------------------------------------------------------------- ribbon


def _loop_distance(size: int = 120) -> np.ndarray:
    """Distance to a square loop, so the inside of it is a hole."""
    mask = np.zeros((size, size), bool)
    mask[30, 30:90] = True
    mask[89, 30:90] = True
    mask[30:90, 30] = True
    mask[30:90, 89] = True
    return edt(mask)


def test_the_ribbon_fills_the_inside_of_a_loop():
    """A loop is a shape, not a band: what the outside cannot reach is painted."""
    sheet = Sheet(120, 120, gran_px=6.0, seed=4)
    d = _loop_distance()
    filled, _ = ribbon_alpha(d, 6.0, sheet, 1.0, fill=True)
    band, _ = ribbon_alpha(d, 6.0, sheet, 1.0, fill=False)
    assert filled[60, 60] > 0.9
    assert band[60, 60] < 0.1
    assert filled[5, 5] < 0.1  # and it still stops well short of the corner


def test_the_ribbon_radius_is_the_fitted_curve_times_the_slider():
    """7.15 times the root of the box plus 158 m, then the slider."""
    card, brush = CardStyle(), BrushStyle()
    route = [(0.0, 0.0), (3200.0, 0.0), (3200.0, 900.0)]
    fitted = journal_geometry(route, card, RibbonStyle(), brush)
    want = 7.15 * math.sqrt(3200.0) + 158.0
    assert fitted["ribbon_m"] == round(want)
    wider = journal_geometry(route, card, RibbonStyle(ribbon_mult=1.25), brush)
    assert wider["ribbon_m"] == round(want * 1.25)
    assert wider["card"] == fitted["card"]  # the card is framed the same either way


def test_the_coast_is_a_hard_edge_the_ribbon_never_crosses():
    """The torn edge stops at the surveyed line; the sea takes over there."""
    sheet = Sheet(120, 120, gran_px=6.0, seed=4)
    d = _loop_distance()
    land = np.ones((120, 120), np.float32)
    land[:, 70:] = 0.0
    free, _ = ribbon_alpha(d, 6.0, sheet, 1.0, fill=True)
    masked, rim = ribbon_alpha(d, 6.0, sheet, 1.0, fill=True, land=land)
    assert free[60, 80] > 0.5
    assert masked[:, 70:].max() == 0.0
    assert rim[:, 70:].max() == 0.0
    assert masked[60, 60] == pytest.approx(free[60, 60])


# --------------------------------------------------------------------------- land cover


def test_land_cover_is_one_class_per_pixel_with_the_wood_on_top(tmp_path):
    """Two pigments never stack: the later class in the order replaces the earlier."""
    style = tiny_style()
    basemap = tiny_basemap(style=style)
    cx0, cy0, cx1, cy1 = basemap.card.box
    mid = ((cx0 + cx1) / 2, (cy0 + cy1) / 2)
    basemap = with_fields(
        basemap,
        cover={
            "farmland": (square(mid[0], mid[1], 400),),
            "wood": (square(mid[0], mid[1], 300),),
        },
        cover_order=("farmland", "wood"),
    )
    manifest = paint_plates(basemap, style, tmp_path).manifest
    from PIL import Image

    with Image.open(tmp_path / manifest.files["wash"]) as img:
        arr = np.asarray(img.convert("RGB"), np.float32) / 255
    h, w, _ = arr.shape
    centre = arr[h // 2, w // 2]
    wood = rgb(read(style, "pigments")["wood"])
    farmland = rgb(read(style, "pigments")["farmland"])
    assert abs(centre[1] - centre[2]) > abs(farmland[1] - farmland[2]) * 0.5
    # The wood alone, never the two multiplied together.
    assert centre[2] > (wood * farmland)[2] + 0.02


# ------------------------------------------------- phase 1: compositing and paper
#
# Every option below is off by default, and the first two tests are what keeps
# the approved plates reproducible: nothing here may move a pixel until a theme
# asks for it. After that, one test a flag, stating what the flag is for.


def test_every_phase_one_option_is_off_by_default():
    """The default plates paint as before until a theme turns one on."""
    style = class_style()
    assert not read(style, "km_glazing")
    assert not read(style, "paper_fibre")
    assert not read(style, "wet_bleed")
    assert not read(style, "flow_rim")
    assert not read(style, "blooms")


# ------------------------------------------------------- phase 2: the wash flags
#
# The wash half of phase 2: deformed silhouettes, two-pigment washes and the
# bounded shallow-water pass. Same rule as phase 1 - off by default, one test a
# flag, and the flag has to be shown doing the thing it is named for.

#: The smoke box with land cover in it, because the phase 2 wash flags all need
#: a class to work on. Two blocks either side of the route, one of them the
#: wood, in the box's own metres.
COVER_BOX = {
    "wood": (((200.0, -140.0), (640.0, -140.0), (640.0, 220.0), (200.0, 220.0)),),
    "farmland": (((720.0, -140.0), (1320.0, -140.0), (1320.0, 220.0), (720.0, 220.0)),),
}


def cover_box(**over: object) -> tuple[Style, Basemap]:
    """The smoke box with two land classes in it, and any style fields moved."""
    style, basemap = smoke_box(**over)
    return style, with_fields(basemap, cover=dict(COVER_BOX), cover_order=("farmland", "wood"))


def painted(tmp_path, **over: object) -> dict[str, str]:
    """The cover box's plates, as a digest a name."""
    import hashlib

    style, basemap = cover_box(**over)
    out = tmp_path / ("on" if over else "off")
    manifest = paint_plates(basemap, style, out).manifest
    return {
        name: hashlib.sha256((out / fn).read_bytes()).hexdigest()
        for name, fn in manifest.files.items()
    }


def test_every_phase_two_wash_option_is_off_by_default():
    """The default plates paint as before until a theme turns one on."""
    style = class_style()
    assert not read(style, "silhouette_deform")
    assert not read(style, "pigment_separation")
    assert not read(style, "fluid_pass")


def test_the_wash_flags_off_still_paint_the_plates_that_were_approved(tmp_path):
    """Three more fields on the style, and the same seed writes the same bytes."""
    import hashlib

    style, basemap = smoke_box()
    manifest = paint_plates(basemap, style, tmp_path).manifest
    got = {
        name: hashlib.sha256((tmp_path / fn).read_bytes()).hexdigest()
        for name, fn in manifest.files.items()
    }
    assert got == SMOKE_SHA


def test_each_wash_flag_moves_the_plate_and_none_of_them_moves_the_card(tmp_path):
    """One flag at a time on a box that has cover in it, against the same box."""
    off = painted(tmp_path)
    for i, flag in enumerate(("silhouette_deform", "pigment_separation", "fluid_pass")):
        on = painted(tmp_path / str(i), **{flag: True})
        assert on["wash"] != off["wash"], flag
        assert on["paper"] == off["paper"], flag  # nothing here touches the card
        assert on["pen"] == off["pen"], flag  # nor the route's own plate


def test_the_surveyed_coast_is_not_deformed(tmp_path):
    """The coast is a fact. Only the land cover's own outlines are pushed about."""
    import hashlib

    def sea_only(**over: object) -> str:
        style, basemap = smoke_box(**over)
        basemap = with_fields(
            basemap,
            sea=(((-400.0, -400.0), (600.0, -400.0), (600.0, -160.0), (-400.0, -160.0)),),
            lakes=(((800.0, 20.0), (1000.0, 20.0), (1000.0, 120.0), (800.0, 120.0)),),
        )
        out = tmp_path / ("on" if over else "off")
        manifest = paint_plates(basemap, style, out).manifest
        return hashlib.sha256((out / manifest.files["wash"]).read_bytes()).hexdigest()

    assert sea_only(silhouette_deform=True) == sea_only()


# ------------------------------------------------------------------ phase 2: tuning and sea


def test_every_phase_two_tuning_field_is_inert_by_default():
    """A field added here must not move a plate until a theme asks for it."""
    style = class_style()
    assert read(style, "bloom_strength") == 1.0
    assert read(style, "wet_close_px") == 0.0
    assert not read(style, "sea_variation")


# --------------------------------------------------------------------------- labels


def test_the_named_lines_keep_what_a_name_can_be_set_along():
    """Named roads and watercourses become named lines; unnamed ones do not.

    The geo payload is transient and re-deriving it at label time costs seven
    seconds and a network the renderer must not need, so the centrelines a
    curved baseline is taken from are read from the basemap the plates came from.
    """
    basemap = tiny_basemap(
        roads=(
            Road(((0.0, 0.0), (300.0, 4.0), (600.0, 0.0)), "major", "major", "primary", "A39", ""),
            Road(((0.0, 90.0), (600.0, 90.0)), "minor", "minor", "unclassified", "", ""),
        ),
        rivers=(
            River(((0.0, 40.0), (400.0, 44.0), (800.0, 40.0)), "major", "River Lyn", 0.0, 0.0),
        ),
        coastline=(((0.0, 10.0), (900.0, 12.0)),),
    )
    from pyntpot._port import labels as lb

    geom = lb.named_lines(basemap, tiny_style().lettering.label_geom_tol_px)
    assert [r["n"] for r in geom["roads"]] == ["A39"]
    assert [r["n"] for r in geom["rivers"]] == ["River Lyn"]
    assert len(geom["coast"]) == 1
    assert all(len(line["d"]) >= 2 for line in geom["roads"] + geom["rivers"])


def _labelled_card(**basemap_over):
    """A tiny basemap and the card that projects into it, for the label rules."""
    basemap = tiny_basemap(**basemap_over)
    card = basemap.card
    route = [(float(x), 40.0 + 30.0 * math.sin(x / 260.0)) for x in range(0, 1400, 40)]
    return basemap, card, [card.xy(x, y) for x, y in route]


def _place_node(name, kind, x, y, off):
    """One settlement as `journal_candidates` writes it into the basemap."""
    return {
        "name": name,
        "class": "place",
        "lat": 0.0,
        "lng": 0.0,
        "x": x,
        "y": y,
        "distance_m": off,
        "tags": {"place": kind},
    }


def test_upper_and_lower_are_one_place_under_their_shared_stem():
    """A reader says Grasmere; OSM has two nodes and neither is called that."""
    from pyntpot._port import labels as lb

    basemap, card, route_px = _labelled_card(
        candidates=[
            _place_node("Upper Grasmere", "village", 200.0, 44.0, 241),
            _place_node("Lower Grasmere", "village", 340.0, 40.0, 70),
        ],
    )
    found = lb.settlements(basemap)
    assert [e["name"] for e in found] == ["Grasmere"]
    # Positioned on the member the route actually came nearest.
    assert found[0]["off_route_m"] == 70


def test_the_settlements_are_chosen_by_rank_and_by_route_not_by_distance():
    """A distance sort spends every slot inside one town. This one does not."""
    from pyntpot._port import labels as lb

    basemap, card, route_px = _labelled_card(
        candidates=[
            _place_node("Little Combes", "hamlet", 100.0, 42.0, 4),
            _place_node("Tarns Bridge", "hamlet", 180.0, 44.0, 18),
            _place_node("Abergavenny", "town", 600.0, 45.0, 3),
            _place_node("Monmouth", "town", 1100.0, 20.0, 441),
            _place_node("Faraway", "village", 700.0, 60.0, 4000),
        ],
    )
    picked = [lb.name for lb in lb.pick_settlements(basemap, card, route_px)]
    assert "Abergavenny" in picked and "Monmouth" in picked
    assert "Faraway" not in picked, "over 1.5 km off the route is not this ride"
    assert len(picked) <= lb.settlement_budget(card.w)


def test_a_hamlet_alone_in_empty_country_is_not_worth_a_name():
    """A floor, so a run through nowhere gets one label or none, not three."""
    from pyntpot._port import labels as lb

    basemap, card, route_px = _labelled_card(
        candidates=[
            _place_node("Brendon", "hamlet", 300.0, 44.0, 700),
        ],
    )
    assert lb.pick_settlements(basemap, card, route_px) == []


def test_the_river_the_route_crossed_beats_the_one_it_did_not():
    """Run length alone cannot separate two tributaries; the route can."""
    from pyntpot._port import labels as lb

    crossed = [[float(x), 40.0 + 30.0 * math.sin(x / 260.0)] for x in range(0, 1400, 40)]
    away = [[float(x), 900.0] for x in range(0, 1400, 40)]
    basemap, card, route_px = _labelled_card()
    lines = {
        "roads": [],
        "coast": [],
        "rivers": [
            {"n": "River Heddon", "c": "medium", "d": crossed},
            {"n": "River Medway", "c": "medium", "d": away},
            {"n": "Hebden Beck", "c": "minor", "d": crossed},
        ],
    }
    named = [x.name for x in lb.pick_rivers(basemap, lines, card, route_px)]
    assert named[0] == "Heddon", "the name loses its 'River', the water says it"
    assert "Hebden Beck" not in named, "a beck is noise at this scale"


def test_an_open_line_deforms_without_moving_its_ends(tmp_path):
    """A leader that misses its pin is not hand-drawn, it is wrong."""
    rng = np.random.default_rng(3)
    line = [(0.0, 0.0), (40.0, 0.0), (80.0, 0.0)]
    out = deform_line(line, (rng, 0.06, 4, 0.62, 6.0, 1.0))
    assert len(out) > len(line)
    assert tuple(out[0]) == (0.0, 0.0)
    assert tuple(out[-1]) == (80.0, 0.0)
    assert abs(out[:, 1]).max() > 0.0, "the line did not move at all"
    assert abs(out[:, 1]).max() <= 6.0
    # Seeded, so the same leader is the same curve on every render.
    again = deform_line(line, (np.random.default_rng(3), 0.06, 4, 0.62, 6.0, 1.0))
    assert np.allclose(out, again)


# ----------------------------------------------------------------- letterforms


def test_the_face_measures_a_name_instead_of_counting_its_characters():
    """The flat eight pixels a character is what every placement fault came from.

    A real face knows that `Abergavenny` and `Wllllllllll` are not the same
    width, and the default cannot: it counts characters. This is the change
    that moves every label on the sheet.
    """
    from pyntpot.letters.font import OutlineFont

    hand = open_hand()
    assert isinstance(hand.font, OutlineFont)
    narrow = hand.measure("iiiiiiiiiii", 20.0)[0]
    wide = hand.measure("WWWWWWWWWWW", 20.0)[0]
    assert wide > narrow * 1.8, "the face is not measuring, it is counting"


def test_the_label_plate_carries_its_own_colour_and_its_own_alpha(tmp_path):
    """The plate is composited normally, so it can lighten as well as darken.

    A backing wash in the paper's own colour is the whole reason it is not on
    the wash plate: multiply can only darken, and a white wash multiplied over
    the card does nothing at all.
    """
    from PIL import Image

    from pyntpot._port import labels as lb

    plates = paint_plates(tiny_basemap(), tiny_style(), tmp_path)
    placed = [
        Label(
            name="Aviemore",
            kind="settlement",
            px=30.0,
            py=25.0,
            size=14.0,
            tx=30.0,
            ty=25.0,
            anchor="middle",
            box=(10.0, 15.0, 60.0, 30.0),
        )
    ]
    plate = lb.draw_plate(plates, placed, [], [(10.0, 10.0), (70.0, 40.0)], tiny_style())
    assert plate is not None and plate.exists()
    img = Image.open(plate)
    assert img.mode == "RGBA"
    assert img.size == plates.card.render
    assert img.getchannel("A").getextrema()[1] > 0, "nothing was written"
    # And it is cached on what is lettered, so a second call writes nothing new.
    stamp = plate.stat().st_mtime_ns
    assert lb.draw_plate(plates, placed, [], [(10.0, 10.0), (70.0, 40.0)], tiny_style()) == plate
    assert plate.stat().st_mtime_ns == stamp


# ------------------------------------------------------ the encoder and the ramp


def test_the_style_decides_how_the_plates_are_written(tmp_path):
    """Lossless is the default, and turning it off is the old encoder back."""
    from PIL import Image

    assert read(class_style(), "plate_lossless")

    style, basemap = smoke_box(plate_lossless=False)
    lossy = paint_plates(basemap, style, tmp_path / "lossy")
    style, basemap = smoke_box()
    clean = paint_plates(basemap, style, tmp_path / "clean")
    assert clean.manifest.bytes > lossy.manifest.bytes

    # The pen plate is alpha, which WebP already stored losslessly, so the flag
    # only tidies the flat white beside it and the plate does not grow.
    assert clean.manifest.sizes["pen"] <= lossy.manifest.sizes["pen"]
    for name in ("paper", "wash"):
        assert clean.manifest.sizes[name] > lossy.manifest.sizes[name] * 4

    with Image.open(tmp_path / "clean" / clean.manifest.files["wash"]) as got:
        assert got.size == basemap.card.render


# ------------------------------------------------------------------- the V5 rules


def test_the_label_plate_is_written_losslessly_like_the_others(tmp_path):
    """Thin glyphs are the encoder's worst case, not a marginal one.

    A thinned stroke is one to three pixels wide against a 4 by 4 transform
    block on a half resolution chroma plane, and a name is what a reader looks
    at closest on the card.
    """
    import numpy as np
    from PIL import Image

    rng = np.random.default_rng(5)
    rgb = np.clip(rng.random((40, 40, 3)).astype(np.float32), 0.0, 1.0)
    alpha = np.zeros((40, 40), np.float32)
    alpha[18:21, 4:36] = 0.85  # one thin stroke, which is what a glyph is

    clean = tmp_path / "clean.webp"
    lossy = tmp_path / "lossy.webp"
    save_rgba(rgb, alpha, clean)
    save_rgba(rgb, alpha, lossy, lossless=False)
    ref = np.clip(rgb * 255.0 + 0.5, 0, 255).astype(np.uint8)
    want_a = np.clip(alpha * 255.0 + 0.5, 0, 255).astype(np.uint8)
    back = np.asarray(Image.open(clean).convert("RGBA"), np.uint8)
    got = np.asarray(Image.open(lossy).convert("RGBA"), np.uint8)
    # WebP zeroes the colour under a fully transparent pixel either way, so the
    # comparison is over the stroke, which is the only part anybody sees.
    ink = alpha > 0
    assert np.array_equal(back[..., :3][ink], ref[ink]), "the plate was not exact"
    assert np.array_equal(back[..., 3], want_a)
    assert not np.array_equal(got[..., :3][ink], ref[ink])


def test_a_road_is_lettered_by_its_number_and_falls_back_to_its_name():
    """The rule: "A361" where OSM has a number, the name where it does not.

    A number places a climb for a rider reading the card. A name like "Aviemore
    Road" is longer, eats a corner and says nothing at 26 m a pixel.
    """
    from pyntpot._port import labels as lb

    numbered = [[round(float(x), 1), 0.0] for x in range(0, 4000, 25)]
    unnumbered = [[round(float(x), 1), 200.0] for x in range(0, 4000, 25)]
    lines = {
        "roads": [
            {"n": "Lyn Valley Road", "c": "major", "r": "A361", "d": numbered},
            {"n": "Aviemore Road", "c": "major", "r": "", "d": unnumbered},
        ]
    }

    class FlatCard:
        w, h, scale = 400.0, 300.0, 0.1

        @staticmethod
        def xy(x, y):
            """Metres to card pixels, at a tenth of a pixel a metre."""
            return (x * 0.1, y * 0.1 + 40.0)

    route = [(float(x), 45.0) for x in range(0, 400, 10)]
    got = lb.pick_roads(label_basemap(), lines, FlatCard(), route, budget=2)
    names = {label.name for label in got}
    assert "A361" in names, "the numbered road is lettered by its number"
    assert "Lyn Valley Road" not in names
    assert "Aviemore Road" in names, "an unnumbered road keeps its name"


def test_a_concurrent_road_number_is_written_once():
    """OSM joins two numbers on one carriageway; the card has room for one."""
    from pyntpot._port import labels as lb

    assert lb.road_ref("A5;A470") == "A5"
    assert lb.road_ref(" B4231 ") == "B4231"
    assert lb.road_ref(None) == ""
    # A walking route's code is not a road number, and this box carries three.
    assert lb.road_ref("EXE") == ""
    assert lb.road_ref("CFG") == ""


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


# ------------------------------------------------- a name on its own water


def _contrast(a: str, b: str) -> float:
    """WCAG contrast between two hex colours."""

    def lum(hexed):
        v = hexed.lstrip("#")
        out = []
        for i in (0, 2, 4):
            c = int(v[i : i + 2], 16) / 255
            out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]

    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_a_name_on_the_water_takes_its_own_ink():
    """The water ink is the colour of the thing the name is now written on."""
    from pyntpot.maps.lettering_marks import _ink

    assert _ink(river_label(40.0)) == "in_water"
    assert _ink(river_label(11.0)) == "water"


def test_the_in_water_ink_beats_a_dark_one_on_the_river():
    """The water is a mid-tone: a dark ink fights it from the wrong side.

    Measured against the major watercourse's own pigment, which is what the
    letters are written over.
    """
    style = class_style()
    river = BRUSH_COLOURS["RIV"]["a"]
    assert _contrast(read(style, "label_in_water_ink"), river) > _contrast("#0f1216", river)
    assert _contrast(read(style, "label_in_water_ink"), river) > 4.5


def test_a_name_on_the_water_asks_for_no_backing_wash():
    """A pale blob on a river reads as a hole in the water."""
    from pyntpot.maps.lettering_marks import label_marks

    hand = open_hand()
    wet = label_marks(hand, river_label(40.0))
    dry = label_marks(hand, river_label(11.0))
    assert wet and not any(m.wash for m in wet)
    assert dry and all(m.wash for m in dry)


def test_the_second_river_name_is_earned_by_the_run():
    """A river that clips a corner is read in one piece and named once.

    The second name exists because a river crossing the whole sheet is read in
    pieces. The Severn has 295 px of water on a 900 px card and taking both
    allowances wrote the second name in open paper past the end of the river.
    """
    from pyntpot._port import labels as lb

    class FlatCard:
        w = 900
        h = 671
        scale = 1.0

        @staticmethod
        def xy(x, y):
            return (float(x), float(y))

    def rivers(x1):
        lines = {"rivers": [{"n": "Severn", "c": "major", "w": 30.0, "d": [[100, 400], [x1, 400]]}]}
        basemap = label_basemap(wet_px={"major": 11.0})
        return lb.pick_rivers(basemap, lines, FlatCard(), [(100.0, 100.0), (800.0, 100.0)])

    short = [lb.name for lb in rivers(395)]  # 295 px of water
    assert short == ["Severn"], "a corner of river was lettered twice"
    long = [lb.name for lb in rivers(800)]  # 700 px of water
    assert long == ["Severn", "Severn"], "a river across the sheet lost its second name"


# ------------------------------------------------- one name, and one for a place


# ------------------------------------------------- the clearance a name keeps


def test_a_road_number_needs_a_run_of_road_measured_against_its_own_type():
    """How much road is enough is a question about the name, not about a card.

    It was a flat 110 display pixels, which is over three times the widest road
    number, and it was that only because the card it was tuned on carried a
    235 px run of the A3052.
    """
    from pyntpot._port import labels as lb

    assert lb.road_min_px(28.0) == pytest.approx(2 * lb.road_min_px(14.0))
    assert lb.road_min_px(lb.DEFAULT_LINE_PX * 0.7) < 110.0


def test_a_numbered_road_is_gathered_by_its_number_not_by_its_street_name():
    """A street name changes at every parish and the road does not.

    The A3052 crosses a card as Hollow Lane, Coastguard Road and New Road,
    none of them long enough to letter, so the card carried no road number at
    all while the same code could number another card twice.
    """
    from pyntpot._port import labels as lb

    def leg(x0, x1, y):
        return [[round(float(x), 1), float(y)] for x in range(x0, x1 + 1, 25)]

    lines = {
        "roads": [
            {"n": "Hollow Lane", "c": "major", "r": "A3052", "d": leg(0, 500, 0)},
            {"n": "Coastguard Road", "c": "major", "r": "A3052", "d": leg(500, 1000, 0)},
            {"n": "New Road", "c": "major", "r": "A3052", "d": leg(1000, 1500, 0)},
        ]
    }

    class FlatCard:
        w, h, scale = 400.0, 300.0, 0.1

        @staticmethod
        def xy(x, y):
            """Metres to card pixels, at a tenth of a pixel a metre."""
            return (x * 0.1, y * 0.1 + 40.0)

    route = [(float(x), 41.0) for x in range(0, 150, 5)]
    got = lb.pick_roads(label_basemap(), lines, FlatCard(), route, budget=2)
    assert [label.name for label in got] == ["A3052"]
    # No one leg is long enough on its own; the number is what gathers them.
    assert length(got[0].baseline) > lb.road_min_px(got[0].size)


# ------------------------------------------------- two strands of one route


def test_a_doubled_back_stretch_is_drawn_as_two_strands():
    """An out-and-back on one path is two lines with paper between them.

    Drawn on its own true line the second pass lands in the first one's gaps
    and the reader cannot tell an out-and-back from a single pass, which is
    what happened along a shared path.
    """
    from pyntpot._port.card import separate_strands

    out = [(float(x), 100.0) for x in range(0, 400, 4)]
    back = [(float(x), 100.0) for x in range(400, 0, -4)]
    moved = separate_strands(out + back, 12.0)
    assert len(moved) == len(out + back)
    # The middle of each limb, well clear of the ends where the two rejoin.
    a = moved[len(out) // 2]
    b = moved[len(out) + len(back) // 2]
    assert abs(a[1] - b[1]) > 8.0, "the two limbs are still on one line"
    # And neither has wandered further off the ground than half the gap.
    assert all(abs(y - 100.0) <= 6.01 for _x, y in moved)


def test_a_route_that_never_doubles_back_is_left_where_it_is():
    """Nothing is displaced on a route with no second pass on any of it."""
    from pyntpot._port.card import separate_strands

    line = [(float(x), 100.0) for x in range(0, 400, 4)]
    assert separate_strands(line, 12.0) == line


def test_a_bend_is_not_mistaken_for_a_second_strand():
    """A hairpin comes back to itself within a few of its own widths.

    The two sides of one corner are the same pass, and pushing them apart
    would straighten a real bend.
    """
    from pyntpot._port.card import separate_strands

    corner = [(0.0, 0.0), (20.0, 0.0), (24.0, 4.0), (20.0, 8.0), (0.0, 8.0)]
    assert separate_strands(corner, 12.0) == corner


def test_the_strands_part_and_rejoin_as_a_curve():
    """No step where the displacement starts: a kink is a fault in the line."""
    from pyntpot._port.card import separate_strands

    out = [(float(x), 100.0) for x in range(0, 600, 4)]
    back = [(float(x), 100.0) for x in range(600, 300, -4)]
    moved = separate_strands(out + back, 12.0)
    steps = [abs(b[1] - a[1]) for a, b in zip(moved, moved[1:], strict=False)]
    assert max(steps) < 1.0, "the displacement comes on as a step, not a ramp"


# ------------------------------------------------- leaders that cross


def test_a_lettering_only_style_change_leaves_the_base_key_and_the_plates_alone(tmp_path):
    """Changing the hand's seed keeps `base_key`, and `paint` repaints nothing."""
    from pyntpot.maps import pipeline
    from pyntpot.maps.cache import Cache

    style = tiny_style()
    basemap = tiny_basemap()
    first = pipeline.paint(basemap, style, tmp_path)
    stamps = {name: path.stat().st_mtime_ns for name, path in first.paths.items()}
    reseeded = tiny_style(label_seed=2)
    assert reseeded.lettering_digest() != style.lettering_digest()
    assert Cache.base_key(basemap, reseeded) == Cache.base_key(basemap, style)
    again = pipeline.paint(basemap, reseeded, tmp_path)
    assert {name: path.stat().st_mtime_ns for name, path in again.paths.items()} == stamps
    assert again.hash == first.hash


def test_a_base_plate_style_change_changes_the_base_key_and_the_lettering_key():
    """A paper change moves `base_key`, and with it the key of a plate drawn against it."""
    from pyntpot.letters.setting import Mark
    from pyntpot.maps.cache import Cache

    style = tiny_style()
    other = tiny_style(paper_fibre=not read(tiny_style(), "paper_fibre"))
    basemap = tiny_basemap()
    marks = [Mark(pts=[(1.0, 2.0), (3.0, 4.0)])]
    one, two = Cache.base_key(basemap, style), Cache.base_key(basemap, other)
    assert one != two
    assert Cache.lettering_key(marks, one, style) != Cache.lettering_key(marks, two, style)
