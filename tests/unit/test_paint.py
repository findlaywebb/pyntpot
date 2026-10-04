"""Tests for the painter, its brushes and the lettering hand.

Everything here paints a box a few dozen pixels across, so the suite stays fast.
"""

from __future__ import annotations

import dataclasses
import json
import math

import numpy as np
import pytest

from pyntpot._port import geo, paint
from pyntpot.ink.brush import BRUSH_COLOURS
from pyntpot.ink.io import save_rgba
from pyntpot.ink.noise import edt
from pyntpot.ink.polyline import deform_line, foot_on, length, meet, simplify
from pyntpot.ink.sheet import Sheet, rgb
from pyntpot.maps.basemap import Basemap, Layers, Line, River, Road
from pyntpot.maps.card import Card
from pyntpot.maps.projection import Projection, track_projection
from pyntpot.maps.style import PAINT_GROUPS, Style

from support.measure import flat_measure
from support.paths import FIXTURE_DIR, KEY

FIXTURE_GPX = FIXTURE_DIR / "track.gpx"

#: A short synthetic track inside the Lynmouth box.
LATS = [51.2250 + 2e-5 * i for i in range(60)]


LNGS = [-3.8400 + 0.00040 * i for i in range(60)]


def tiny_style(**over: object) -> paint.PaintStyle:
    """The approved style, painted small enough to be a unit test."""
    return paint.PaintStyle(display_px=80, supersample=2, **over)


def as_style(pstyle: paint.PaintStyle) -> Style:
    """The packaged style with every painter field read from a flat painter style."""
    base = Style.default()
    groups = {
        name: type(getattr(base, name))(
            **{f.name: getattr(pstyle, f.name) for f in dataclasses.fields(getattr(base, name))}
        )
        for name in PAINT_GROUPS
    }
    return base.model_copy(update=groups)


def square(cx: float, cy: float, r: float) -> Line:
    """One closed square ring at a tenth of a metre, in metres."""
    pts = [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]
    return tuple((round(x, 1), round(y, 1)) for x, y in pts)


def with_fields(basemap: Basemap, **over: object) -> Basemap:
    """The basemap with any of its own or its layers' fields replaced."""
    names = {f.name for f in dataclasses.fields(Layers)}
    layers = dataclasses.replace(basemap.layers, **{k: v for k, v in over.items() if k in names})
    rest = {k: v for k, v in over.items() if k not in names}
    return dataclasses.replace(basemap, layers=layers, **rest)


def tiny_basemap(style: paint.PaintStyle | None = None, **over: object) -> Basemap:
    """A whole basemap for a small box, with nothing in it but the route."""
    style = style or tiny_style()
    route = [(float(x), 40.0 + 30.0 * math.sin(x / 260.0)) for x in range(0, 1400, 40)]
    geometry = geo.journal_geometry(route, style)
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


# --------------------------------------------------------------------------- painter


def test_a_tiny_box_paints_a_card_a_wash_and_a_manifest(tmp_path):
    """The painter writes two plates plus the pen, and says what it did."""
    style = tiny_style()
    plates = paint.paint(tiny_basemap(style=style), as_style(style), tmp_path)
    manifest = plates.manifest
    assert set(manifest.files) == {"paper", "wash", "pen"}
    for path in plates.paths.values():
        assert path.stat().st_size > 0
    assert (tmp_path / "plates.json").exists()
    assert manifest.card.display[0] == 80
    assert manifest.card.render[0] == 160
    assert manifest.dark.w == style.dark_grid[0]
    assert len(manifest.dark.values) == style.dark_grid[1]


def test_the_plates_are_webp_the_size_they_were_painted(tmp_path):
    """A plate is a WebP at the render size, not at the display size."""
    from PIL import Image

    style = tiny_style()
    plates = paint.paint(tiny_basemap(style=style), as_style(style), tmp_path)
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


def smoke_box(**over: object) -> tuple[paint.PaintStyle, Basemap]:
    """The smoke box's style and basemap, with any style fields moved."""
    style = paint.PaintStyle(display_px=120, supersample=2, **over)
    return style, tiny_basemap(style=style, roads=SMOKE_ROADS, rivers=SMOKE_RIVERS)


def test_the_flags_off_still_paint_the_plates_that_were_approved(tmp_path):
    """The whole point of the flags: the same seed still writes the same bytes."""
    import hashlib

    style, basemap = smoke_box()
    manifest = paint.paint(basemap, as_style(style), tmp_path).manifest
    got = {
        name: hashlib.sha256((tmp_path / fn).read_bytes()).hexdigest()
        for name, fn in manifest.files.items()
    }
    assert got == SMOKE_SHA


def test_every_flag_on_together_still_paints_the_box(tmp_path):
    """And with all three on it is a different plate, not a broken one."""
    import hashlib

    style, basemap = smoke_box(ink_starve=True, dry_directional=True, pen_starve=True)
    manifest = paint.paint(basemap, as_style(style), tmp_path).manifest
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
    manifest = paint.paint(basemap, as_style(style), tmp_path).manifest
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
    filled, _ = paint.ribbon_alpha(d, 6.0, sheet, True, 1.0)
    band, _ = paint.ribbon_alpha(d, 6.0, sheet, False, 1.0)
    assert filled[60, 60] > 0.9
    assert band[60, 60] < 0.1
    assert filled[5, 5] < 0.1  # and it still stops well short of the corner


def test_the_ribbon_radius_is_the_fitted_curve_times_the_slider():
    """7.15 times the root of the box plus 158 m, then the slider."""
    style = paint.PaintStyle()
    route = [(0.0, 0.0), (3200.0, 0.0), (3200.0, 900.0)]
    fitted = geo.journal_geometry(route, style)
    want = 7.15 * math.sqrt(3200.0) + 158.0
    assert fitted["ribbon_m"] == round(want)
    wider = geo.journal_geometry(route, paint.PaintStyle(ribbon_mult=1.25))
    assert wider["ribbon_m"] == round(want * 1.25)
    assert wider["card"] == fitted["card"]  # the card is framed the same either way


def test_the_coast_is_a_hard_edge_the_ribbon_never_crosses():
    """The torn edge stops at the surveyed line; the sea takes over there."""
    sheet = Sheet(120, 120, gran_px=6.0, seed=4)
    d = _loop_distance()
    land = np.ones((120, 120), np.float32)
    land[:, 70:] = 0.0
    free, _ = paint.ribbon_alpha(d, 6.0, sheet, True, 1.0)
    masked, rim = paint.ribbon_alpha(d, 6.0, sheet, True, 1.0, land)
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
    manifest = paint.paint(basemap, as_style(style), tmp_path).manifest
    from PIL import Image

    with Image.open(tmp_path / manifest.files["wash"]) as img:
        arr = np.asarray(img.convert("RGB"), np.float32) / 255
    h, w, _ = arr.shape
    centre = arr[h // 2, w // 2]
    wood = rgb(style.pigments["wood"])
    farmland = rgb(style.pigments["farmland"])
    assert abs(centre[1] - centre[2]) > abs(farmland[1] - farmland[2]) * 0.5
    # The wood alone, never the two multiplied together.
    assert centre[2] > (wood * farmland)[2] + 0.02


def test_the_tag_lookup_takes_the_last_class_that_matches(tmp_path):
    """A way tagged both ways is the one further down the table, which is the wood."""
    way = {
        "type": "way",
        "tags": {"landuse": "meadow", "natural": "wood"},
        "geometry": [
            {"lat": 51.2250, "lon": -3.8400},
            {"lat": 51.2250, "lon": -3.8380},
            {"lat": 51.2270, "lon": -3.8380},
            {"lat": 51.2270, "lon": -3.8400},
            {"lat": 51.2250, "lon": -3.8400},
        ],
    }
    (tmp_path / "landcover-iTAGS.json").write_text(json.dumps({"elements": [way]}))
    proj, _ = track_projection(LATS, LNGS)
    rings = geo.cover_rings("iTAGS", proj, (-9000.0, -9000.0, 9000.0, 9000.0), 2.0, tmp_path)
    assert list(rings) == ["wood"]


def test_a_box_with_no_land_cover_cached_is_bare_paper(tmp_path):
    """Where nobody has drawn a field the ground stays paper, and that is honest."""
    proj, _ = track_projection(LATS, LNGS)
    assert geo.cover_rings("iNONE", proj, (-100.0, -100.0, 100.0, 100.0), 2.0, tmp_path) == {}


# --------------------------------------------------------------------------- climbs


def test_a_climb_is_a_rise_that_never_gives_back():
    """Sixty metres up, with no fifteen-metre drop on the way, is a climb."""
    lat = [51.225 + 4e-4 * i for i in range(40)]
    lng = [-3.840] * 40
    ele = [100.0 + 4.0 * i for i in range(20)] + [180.0 - 4.0 * i for i in range(20)]
    found = geo.climbs(lat, lng, ele)
    assert len(found) == 1
    assert found[0]["gain_m"] == 80
    assert found[0]["start_km"] < found[0]["end_km"]


def test_a_bumpy_flat_is_not_a_climb():
    """Noise is not terrain: nothing under the threshold is offered as a climb."""
    lat = [51.225 + 4e-4 * i for i in range(40)]
    lng = [-3.840] * 40
    ele = [100.0 + (i % 4) for i in range(40)]
    assert geo.climbs(lat, lng, ele) == []


def test_a_flat_run_in_is_not_part_of_the_climb():
    """A climb starts where the pitch does, not where the valley last ticked up.

    Twenty samples of valley floor drifting up a metre, then a real pitch. The
    detector's own span begins on the floor; what is reported must not, because
    the start point is where the label is pinned on the map.
    """
    lat = [51.225 + 4e-4 * i for i in range(50)]
    lng = [-3.840] * 50
    ele = [100.0 + 0.05 * i for i in range(20)] + [101.0 + 5.0 * i for i in range(30)]
    found = geo.climbs(lat, lng, ele)
    assert len(found) == 1
    climb = found[0]
    assert climb["approach_trimmed_km"] > 0.8, "the flat run-in was kept"
    assert climb["start_km"] > 0.8
    assert climb["bottom_ele_m"] == 101
    assert climb["avg_grade_pct"] > 10  # the pitch's own gradient, not the span's
    assert climb["start_lat"] > lat[10], "the pin is still down on the valley floor"


def test_a_plaque_is_not_a_monument():
    """A blue plaque carries the name of the wall it is on, so it names nothing.

    OpenStreetMap tags one `historic=memorial` with the building's own name, and
    that is how a Forest of Bowland climb came to be named after a war memorial 112 m
    from its foot. Classed apart, it stays readable and stops being a landmark.
    """
    assert geo.classify({"historic": "memorial", "memorial": "plaque"}) == "plaque"
    assert geo.classify({"historic": "memorial", "memorial": "blue_plaque"}) == "plaque"
    assert geo.classify({"historic": "memorial", "memorial": "war_memorial"}) == "monument"
    assert geo.classify({"historic": "memorial"}) == "monument"
    assert geo.LANDMARK_CLASSES["plaque"] is False


# --------------------------------------------------------------------------- real data


def test_the_real_box_assembles_the_layers_the_painter_needs():
    """The Lynmouth box: land cover, roads by brush, and the fitted ribbon."""
    lat, lng = geo.read_gpx(FIXTURE_GPX)
    basemap = geo.journal_layers(
        KEY,
        lat,
        lng,
        paint.PaintStyle(),
        cache_dir=FIXTURE_DIR,
        places=[],
        basemap_style=Style.default().basemap,
    )
    assert basemap is not None
    layers = basemap.layers
    assert layers.ribbon_m == 553
    assert basemap.card.display == (900, 728)
    assert "wood" in layers.cover
    assert layers.cover_order[-1] == "wood"
    assert {r.band for r in layers.roads} <= {"major", "minor", "path"}
    assert layers.minor_roads is True


def test_the_real_box_offers_candidates_and_no_climb_without_elevation():
    """What the label step reads: named things and how far off; no climbs without elevation."""
    lat, lng = geo.read_gpx(FIXTURE_GPX)
    export = geo.landmark_export(
        KEY,
        lat,
        lng,
        geo.read_gpx_elevation(FIXTURE_GPX),
        cache_dir=FIXTURE_DIR,
        places=[],
    )
    names = {c["name"] for c in export["candidates"]}
    assert {"Lynmouth", "Lynton", "Countisbury"} <= names
    assert all(c["distance_m"] is not None for c in export["candidates"])
    assert export["climbs"] == [], "the fixture track carries no elevation"


# ------------------------------------------------- phase 1: compositing and paper
#
# Every option below is off by default, and the first two tests are what keeps
# the approved plates reproducible: nothing here may move a pixel until a theme
# asks for it. After that, one test a flag, stating what the flag is for.


def test_every_phase_one_option_is_off_by_default():
    """The default plates paint as before until a theme turns one on."""
    style = paint.PaintStyle()
    assert not style.km_glazing
    assert not style.paper_fibre
    assert not style.wet_bleed
    assert not style.flow_rim
    assert not style.blooms


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


def cover_box(**over: object) -> tuple[paint.PaintStyle, Basemap]:
    """The smoke box with two land classes in it, and any style fields moved."""
    style, basemap = smoke_box(**over)
    return style, with_fields(basemap, cover=dict(COVER_BOX), cover_order=("farmland", "wood"))


def painted(tmp_path, **over: object) -> dict[str, str]:
    """The cover box's plates, as a digest a name."""
    import hashlib

    style, basemap = cover_box(**over)
    out = tmp_path / ("on" if over else "off")
    manifest = paint.paint(basemap, as_style(style), out).manifest
    return {
        name: hashlib.sha256((out / fn).read_bytes()).hexdigest()
        for name, fn in manifest.files.items()
    }


def test_every_phase_two_wash_option_is_off_by_default():
    """The default plates paint as before until a theme turns one on."""
    style = paint.PaintStyle()
    assert not style.silhouette_deform
    assert not style.pigment_separation
    assert not style.fluid_pass


def test_the_wash_flags_off_still_paint_the_plates_that_were_approved(tmp_path):
    """Three more fields on the style, and the same seed writes the same bytes."""
    import hashlib

    style, basemap = smoke_box()
    manifest = paint.paint(basemap, as_style(style), tmp_path).manifest
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
        manifest = paint.paint(basemap, as_style(style), out).manifest
        return hashlib.sha256((out / manifest.files["wash"]).read_bytes()).hexdigest()

    assert sea_only(silhouette_deform=True) == sea_only()


# ------------------------------------------------------------------ phase 2: tuning and sea


def test_every_phase_two_tuning_field_is_inert_by_default():
    """A field added here must not move a plate until a theme asks for it."""
    style = paint.PaintStyle()
    assert style.bloom_strength == 1.0
    assert style.wet_close_px == 0.0
    assert not style.sea_variation


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

    geom = lb.named_lines(basemap, tiny_style().label_geom_tol_px)
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


def label_basemap(**over: object) -> Basemap:
    """A tiny basemap whose layers carry no painted widths, for the label readers."""
    return tiny_basemap(**{"wet_px": {}, **over})


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


def test_home_is_untouched_by_the_new_keys():
    """`Home` has a symbol, no kind and no always_label, and draws as it always did."""
    entries = [{"name": "Home", "symbol": "house", "lat": 51.2255, "lng": -3.835}]
    assert entries[0]["name"] == "Home"
    marks = geo._place_marks(
        entries,
        Projection(
            lat0=51.225,
            lat_ref=51.225,
            lng_ref=-3.840,
        ),
        (-9e9, -9e9, 9e9, 9e9),
    )
    assert marks[0]["sym"] == "house"
    assert marks[0]["kind"] == "marker"
    assert marks[0]["always"] is False


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


def _open_hand():
    """The default hand, as the style's face and seed open it."""
    from pyntpot.letters.hand import Hand
    from pyntpot.letters.style import FaceStyle, HandStyle

    return Hand(FaceStyle(), HandStyle())


def test_the_face_measures_a_name_instead_of_counting_its_characters():
    """The flat eight pixels a character is what every placement fault came from.

    A real face knows that `Abergavenny` and `Wllllllllll` are not the same
    width, and the default cannot: it counts characters. This is the change
    that moves every label on the sheet.
    """
    from pyntpot.letters.font import OutlineFont

    hand = _open_hand()
    assert isinstance(hand.font, OutlineFont)
    narrow = hand.measure("iiiiiiiiiii", 20.0)[0]
    wide = hand.measure("WWWWWWWWWWW", 20.0)[0]
    assert wide > narrow * 1.8, "the face is not measuring, it is counting"


def test_a_name_is_never_set_along_a_line_that_turns_too_far():
    """Curved baselines for linear things, and only where they stay readable.

    Total turning across the run is the test that matters, not curvature at a
    point: a river bend reads, a switchback does not, and the difference
    between elegant and unreadable is this one rule.
    """
    import math

    from pyntpot._port import labels as lb
    from pyntpot.maps.lettering_window import baseline

    hand = _open_hand()
    straight = [(float(x), 100.0 + 4.0 * math.sin(x / 90.0)) for x in range(0, 400, 8)]
    hairpin = [
        (100.0 + 40.0 * math.cos(a / 9.0), 100.0 + 40.0 * math.sin(a / 9.0)) for a in range(0, 80)
    ]
    gentle = lb.Label(name="Heddon", kind="river", px=200.0, py=100.0, size=14.0, baseline=straight)
    tight = lb.Label(name="Heddon", kind="river", px=100.0, py=100.0, size=14.0, baseline=hairpin)
    assert baseline(gentle, hand.font.measure("Heddon", 14.0)[0])
    assert baseline(tight, hand.font.measure("Heddon", 14.0)[0]) is None


def test_the_label_plate_carries_its_own_colour_and_its_own_alpha(tmp_path):
    """The plate is composited normally, so it can lighten as well as darken.

    A backing wash in the paper's own colour is the whole reason it is not on
    the wash plate: multiply can only darken, and a white wash multiplied over
    the card does nothing at all.
    """
    from PIL import Image

    from pyntpot._port import labels as lb
    from pyntpot._port import paint

    plates = paint.paint(tiny_basemap(), as_style(tiny_style()), tmp_path)
    placed = [
        lb.Label(
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
    plate = lb.draw_plate(plates, placed, [], [(10.0, 10.0), (70.0, 40.0)], as_style(tiny_style()))
    assert plate is not None and plate.exists()
    img = Image.open(plate)
    assert img.mode == "RGBA"
    assert img.size == plates.card.render
    assert img.getchannel("A").getextrema()[1] > 0, "nothing was written"
    # And it is cached on what is lettered, so a second call writes nothing new.
    stamp = plate.stat().st_mtime_ns
    assert (
        lb.draw_plate(plates, placed, [], [(10.0, 10.0), (70.0, 40.0)], as_style(tiny_style()))
        == plate
    )
    assert plate.stat().st_mtime_ns == stamp


# ------------------------------------------------------ the encoder and the ramp


def test_the_style_decides_how_the_plates_are_written(tmp_path):
    """Lossless is the default, and turning it off is the old encoder back."""
    from PIL import Image

    assert paint.PaintStyle().plate_lossless

    style, basemap = smoke_box(plate_lossless=False)
    lossy = paint.paint(basemap, as_style(style), tmp_path / "lossy")
    style, basemap = smoke_box()
    clean = paint.paint(basemap, as_style(style), tmp_path / "clean")
    assert clean.manifest.bytes > lossy.manifest.bytes

    # The pen plate is alpha, which WebP already stored losslessly, so the flag
    # only tidies the flat white beside it and the plate does not grow.
    assert clean.manifest.sizes["pen"] <= lossy.manifest.sizes["pen"]
    for name in ("paper", "wash"):
        assert clean.manifest.sizes[name] > lossy.manifest.sizes[name] * 4

    with Image.open(tmp_path / "clean" / clean.manifest.files["wash"]) as got:
        assert got.size == basemap.card.render


# ------------------------------------------------------------------- the V5 rules


class _Sheet:
    """The smallest thing the placer will accept as a card."""

    w = 400.0
    h = 300.0
    scale = 1.0


def _flat_dark(w: int = 8, h: int = 8, v: float = 0.2) -> dict:
    """A darkness grid with nothing dark in it, so it decides nothing."""
    return {"w": w, "h": h, "v": [[v] * w for _ in range(h)]}


def test_a_span_takes_its_name_along_it_only_when_it_runs_across_the_sheet():
    """The bearing rule, on three cases.

    The A39 drag and the climb out of Aviemore run across the card and read
    well with the name along them; the A361 climb runs down it and does not,
    because the letters stack and the reader has to tilt their head. The
    threshold is `SPAN_ALONG_MAX_BEARING_DEG` and it is a tunable, so the test
    is written against the tunable rather than against the number.
    """
    from pyntpot._port import labels as lb

    across = [(float(x), 100.0 + x * 0.15) for x in range(0, 300, 10)]  # ~9 deg
    slanted = [(float(x), 100.0 + x * 0.9) for x in range(0, 300, 10)]  # ~42 deg
    down = [(100.0 + y * 0.06, float(y)) for y in range(0, 300, 10)]  # ~87 deg
    assert lb.span_bearing(across) < lb.SPAN_ALONG_MAX_BEARING_DEG
    assert lb.span_bearing(slanted) > lb.SPAN_ALONG_MAX_BEARING_DEG
    assert lb.span_bearing(down) > lb.SPAN_ALONG_MAX_BEARING_DEG
    # And the label follows the rule rather than restating it.
    for line, along in ((across, True), (down, False)):
        span = lb.Span(name="the long drag up the valley", kind="drag", i0=0, i1=2)
        span.line = list(line)
        label = lb._span_label(span, [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)], 14.0, flat_measure)
        assert bool(label.baseline) is along
        # Never a leader, either way: a name beside its own bracket needs none.
        assert label.tier == lb.TIER_SPAN


def test_the_card_carries_no_more_spans_than_the_cap():
    """Four brackets made the sheet cluttered, so three is the cap.

    Dropped in the payload's own order, because the agent is asked for its best
    first and that ordering is the only judgement available here.
    """
    from pyntpot._port import labels as lb

    class _Picks:
        spans = [
            type(
                "S",
                (),
                {
                    "name": f"span {i}",
                    "kind": "climb",
                    "intent": "note",
                    "why": "",
                    "from_km": float(i),
                    "to_km": float(i) + 0.5,
                    "from_s": None,
                    "to_s": None,
                    "from_i": None,
                    "to_i": None,
                },
            )()
            for i in range(6)
        ]

    dist = [float(m) for m in range(0, 6000, 10)]
    got = lb.resolve_spans(_Picks(), [], dist)
    assert len(got) == lb.SPAN_MAX == 3
    assert {s.name for s in got} == {"span 0", "span 1", "span 2"}


def test_a_curved_label_reserves_the_room_it_actually_takes():
    """The fault every variant shared: a curved name defended the wrong box.

    A river used to claim the box its anchor fell in and then be set along a
    window chosen afterwards, so nothing placed later avoided the pixels the
    reader saw. The window is chosen in the placer now and contributes a run of
    small boxes, and this asserts both: that the boxes follow the water, and
    that a name placed afterwards is pushed off them.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    water = [(float(x), 150.0 + 18.0 * math.sin(x / 70.0)) for x in range(20, 380, 6)]
    river = lb.Label(
        name="Heddon",
        kind="river",
        px=200.0,
        py=150.0,
        tier=lb.TIER_RIVER,
        size=14.0,
        baseline=water,
    )
    later = lb.Label(
        name="Monmouth Castle",
        kind="monument",
        px=200.0,
        py=150.0,
        tier=lb.TIER_LANDMARK,
        size=14.0,
    )
    got = lb.place(
        [river, later], [], card, [(0.0, 290.0), (400.0, 290.0)], _flat_dark(), [], flat_measure
    )
    assert river.window, "the river was not set along its own water"
    assert not river.flat
    # A box that follows the water, rather than one drawn round the anchor.
    assert river.box is not None
    assert river.box[2] - river.box[0] > 20.0
    # And the name that came after it is not sitting on top of it.
    x0, y0, x1, y1 = later.box
    for bx0, by0, bx1, by1 in [river.box]:
        assert not (min(x1, bx1) > max(x0, bx0) and min(y1, by1) > max(y0, by0)), (
            "the later name was placed on top of the curved one"
        )
    assert got == [river, later]


def test_a_road_crossing_costs_and_a_longer_leader_is_the_cheaper_answer():
    """The rule: shift the name and spend leader instead.

    Not a constraint. Sometimes there is nowhere else and a name that vanished
    would be worse than one that crosses a lane, so it is priced, and priced
    against the leader so the two are directly comparable. That ordering is the
    rule: a crossing has to cost more than the placer could ever spend on
    leader, or the cheap answer stays the one on the tarmac.
    """
    from pyntpot._port import labels as lb

    assert lb.ROAD_CROSS_COST > max(lb.LEADER_RUNGS) * lb.LEADER_COST_PX

    card = _Sheet()
    route = [(0.0, 290.0), (400.0, 290.0)]
    free = lb.Label(name="Castle", kind="monument", px=200.0, py=150.0, size=14.0)
    lb.place([free], [], card, route, _flat_dark(), [], flat_measure, [])
    # A road laid straight down the middle of the box the placer just chose.
    x0, y0, x1, y1 = free.box
    road = [[((x0 + x1) / 2, 0.0), ((x0 + x1) / 2, 300.0)]]
    assert lb._crossings(free.box, road) > 0

    moved = lb.Label(name="Castle", kind="monument", px=200.0, py=150.0, size=14.0)
    lb.place([moved], [], card, route, _flat_dark(), [], flat_measure, road)
    assert lb._crossings(moved.box, road) == 0, "the road was not avoided"
    assert moved.box != free.box


def test_the_major_river_carries_its_name_twice_and_the_others_once():
    """A long feature is met in pieces, so it is named in pieces.

    Only the major one: a tributary that runs a third of the card twice-named is
    repetition rather than help. And the two have to be far apart, or they read
    as one name written twice.
    """
    from pyntpot._port import labels as lb

    big = [[round(float(x), 1), 0.0] for x in range(0, 4000, 25)]
    small = [[500.0, round(float(y), 1)] for y in range(0, 900, 25)]
    lines = {
        "rivers": [
            {"n": "River Lyn", "c": "major", "d": big},
            {"n": "Heddon", "c": "medium", "d": small},
        ]
    }

    class FlatCard:
        w, h, scale = 400.0, 300.0, 0.1

        @staticmethod
        def xy(x, y):
            """Metres to card pixels, at a tenth of a pixel a metre."""
            return (x * 0.1, y * 0.1 + 40.0)

    route = [(float(x), 60.0) for x in range(0, 400, 10)]
    got = lb.pick_rivers(label_basemap(), lines, FlatCard(), route)
    names = [label.name for label in got]
    assert names.count("Lyn") == lb.MAJOR_RIVER_LABELS == 2
    assert names.count("Heddon") == 1
    a, b = [label for label in got if label.name == "Lyn"]
    apart = math.dist((a.px, a.py), (b.px, b.py))
    assert apart > length(a.baseline) * lb.RIVER_REPEAT_FRAC * 0.9


def test_a_span_that_doubles_back_is_still_one_open_gesture():
    """The iso-contour cannot self-intersect, but it can enclose.

    An out-and-back on the same lane comes back as one closed ring round both
    strands, and read by side alone every point of it qualifies: that is how
    the Aviemore bracket came to be drawn as a ring round its own climb. The
    contour is read along the route now, from the span's start to its end, with
    the caps trimmed and the run broken wherever it jumps to the other strand,
    so what comes back is one open flank whatever the route did.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    out = [(100.0 + i * 4.0, 150.0) for i in range(30)]
    back = [(x, y + 1.0) for x, y in reversed(out)]
    doubled = out + back
    line = lb.span_line(doubled, 0, len(doubled) - 1, 1, 14.0, card)
    assert line, "a doubled-back span drew nothing at all"
    # Not a ring: it does not come back to where it started.
    assert math.dist(line[0], line[-1]) > 0.33 * length(line)
    # And it stands off the stretch it belongs to rather than wrapping it.
    assert min(min(math.dist(p, q) for q in doubled) for p in line) > 8.0


def _arc(
    turn_deg: float, n: int = 60, r: float = 100.0, start: float = 180.0
) -> list[tuple[float, float]]:
    """One circular arc turning `turn_deg`, centred so it sits on the sheet.

    Positive `turn_deg` turns towards side +1, which in card pixels is the
    normal `(-dy, dx)`, so the centre of the arc is on side +1 and side -1 is
    the outside of the bend.
    """
    out = []
    for i in range(n):
        a = math.radians(start + turn_deg * i / (n - 1))
        out.append((200.0 + r * math.cos(a), 150.0 + r * math.sin(a)))
    return out


def test_the_outside_of_a_bend_is_the_side_the_mark_stands_off_the_chord():
    """ "The outside" is defined on the drawn mark, and this pins which one it is.

    The module signs a side two ways that disagree: `_bracket` pushes off the
    chord's own normal, the contour filters a ring with `_side_at`, and on the
    same arc the two land on opposite flanks. So nothing about the outside is
    read off a normal. It is read off the two brackets, by how far each stands
    out of the bend, and the one that does is the convex one.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    centre = (200.0, 150.0)
    for radius in (80.0, 110.0, 150.0):
        for turn in (45.0, -45.0):
            route = _arc(turn, r=radius)
            span = lb.Span(name="the bend", kind="climb", i0=0, i1=len(route) - 1)
            side, marks = lb._convex_side(span, route, 14.0, card)
            assert side in (1, -1)
            assert set(marks) == {1, -1}
            line = lb.span_line(route, 0, len(route) - 1, side, 14.0 * lb.SPAN_OFFSET_CAPS, card)
            far = sum(math.dist(p, centre) for p in line) / len(line)
            assert far > radius, (
                f"the {turn:+.0f} degree bend of radius {radius:.0f} put its "
                f"bracket inside, at {far:.0f}"
            )


def test_a_straight_or_an_s_bend_has_no_outside_and_the_bend_does_not_vote():
    """The two ways "the outside" names nothing, and both fall through.

    The rule is "the outside of the curve **where there is one**". A
    straight stretch has no outside because it has no curve, and an S-bend has
    no one outside because it has two: whichever side were chosen, half the
    stretch would be written on the inside of it. Both withhold the vote and
    leave the free-paper rule to decide, which is the fall-through.
    """
    from pyntpot._port import labels as lb

    straight = [(60.0 + i * 4.0, 150.0) for i in range(60)]
    assert lb.bend_strength(straight, 21.0) == 0.0
    # Turning, but not enough of it to be a bend.
    assert lb.bend_strength(_arc(lb.SPAN_CURVE_MIN_TURN_DEG * 0.7), 21.0) == 0.0
    # And a bend is a strength, not a flag: gentle votes softly, hard votes 1.
    assert 0.0 < lb.bend_strength(_arc(55.0), 21.0) < 1.0
    assert lb.bend_strength(_arc(120.0), 21.0) == 1.0
    # An S: one arc one way, the same arc back. It turns plenty and nets zero.
    first = _arc(100.0, r=140.0)
    dx, dy = first[-1][0] - first[-2][0], first[-1][1] - first[-2][1]
    back = _arc(-100.0, r=140.0)
    ox, oy = back[0]
    ess = first + [(x - ox + first[-1][0] + dx, y - oy + first[-1][1] + dy) for x, y in back]
    net, gross = lb.route_turn(lb._resample(ess, 21.0))
    assert gross > lb.SPAN_CURVE_MIN_TURN_DEG * 2, "the S does turn"
    assert abs(net) / gross < lb.SPAN_CURVE_MIN_COHERENCE
    assert lb.bend_strength(ess, 21.0) == 0.0


def test_the_bend_is_a_weighted_term_and_a_clearer_side_still_wins():
    """ "Where there is one", not "always": the vote can be outvoted.

    A bracket goes on the outside when the free-paper rule was close to a tie,
    and stays where the paper put it when the other side is properly clearer.
    The switch turns the whole term off and the free-paper answer comes back
    unchanged, which is what makes the A/B honest.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    route = _arc(-80.0, r=110.0)
    span = lb.Span(name="the bend", kind="climb", i0=0, i1=len(route) - 1)
    outside = lb._convex_side(span, route, 14.0, card)[0]
    inside = -outside
    # A near tie: the bend turns the side round.
    assert lb._curved_side(span, route, inside, 0.01, 14.0, card) == outside
    # A margin past what the vote is worth: the free paper keeps it.
    assert lb._curved_side(span, route, inside, lb.SPAN_CURVE_WEIGHT * 2, 14.0, card) == inside
    # Already on the outside: nothing to do either way.
    assert lb._curved_side(span, route, outside, 0.01, 14.0, card) == outside
    # And with the term off, the free-paper answer stands whatever the bend.
    lb.SPAN_CURVE_SIDE = False
    try:
        assert lb._curved_side(span, route, inside, 0.01, 14.0, card) == inside
    finally:
        lb.SPAN_CURVE_SIDE = True


def test_a_span_on_a_bend_is_drawn_on_the_convex_side_of_the_route():
    """The whole term, through `place_spans`, on a sheet with nothing dark on it.

    With the darkness grid flat the free-paper rule is a coin toss decided by a
    tie-break, so this is exactly the near-tie the bend is meant to settle. The
    bracket lands outboard of the arc, further from its centre than the route
    is, which is the intended geometry. With the term off it is a
    coin toss again and the assertion below is not guaranteed, which is the
    point of the switch.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    centre = (200.0, 150.0)
    for turn, radius in ((45.0, 110.0), (-45.0, 110.0), (-80.0, 110.0)):
        route = _arc(turn, r=radius)
        span = lb.Span(name="the bend", kind="climb", i0=0, i1=len(route) - 1)
        assert lb.place_spans([span], card, route, _flat_dark(), flat_measure, cap_px=14.0)
        assert sum(math.dist(p, centre) for p in span.line) / len(span.line) > radius, (
            f"the {turn:+.0f} degree bend drew its bracket on the inside"
        )


def test_a_span_mark_never_crosses_any_piece_of_the_route():
    """Rule seven, mechanically, on every shape the sheet has a case for.

    Span marks are never drawn over any other piece of route. Any piece, so the whole track is
    tested and not the stretch alone, and the ticks are tested with the line
    because a tick is part of the mark. Each of these routes carries the strand
    that used to be crossed: the returning leg of an out-and-back, the far side
    of a loop, the second limb of an S, and a lane that cuts across the corner
    the span ends in.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    for name, route in _shapes().items():
        span = lb.Span(name=name, kind="climb", i0=0, i1=len(route) - 1)
        placed = lb.place_spans([span], card, route, _flat_dark(), flat_measure, cap_px=14.0)
        if not placed:  # a shape with no room for a mark says so, and stops
            continue
        for part in (span.line, *span.ticks):
            assert not _crosses(part, route), f"{name}: the mark crosses the route"
            assert lb.clear_of_route(part, route, 14.0 * lb.SPAN_CLEAR_CAPS), (
                f"{name}: the mark comes nearer the route than the clearance"
            )


def test_a_doubled_back_stretch_is_enclosed_rather_than_cut_across():
    """Rule four, which withdrew the rule before it.

    A mark round a stretch that comes back on itself encloses both strands.
    That used to be forbidden and the straight fallback was what enforced it,
    by drawing a rule across the middle of the loop, and that line crossed the
    route on both sides of the span. The mark goes round the outside of both
    strands now.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    out = [(80.0 + i * 4.0, 150.0) for i in range(40)]
    back = [(x, y + 26.0) for x, y in reversed(out)]
    route = out + back
    line = lb.span_line(route, 0, len(route) - 1, 1, 20.0, card)
    assert length(line) > 2.0 * 20.0, "the doubled-back stretch drew no mark"
    assert not _crosses(line, route), "the mark cuts across the loop"
    # Corners, because the loop's own turns are corners: a route that turns
    # right round in a few pixels is not drawn as an arc. So the mark is a few
    # long strokes rather than a hundred short ones.
    assert _corners(line) <= 4
    # Round the outside of both strands: the mark reaches past the turn at the
    # east end, and past both strands north and south.
    assert max(x for x, _ in line) > max(x for x, _ in route)
    assert min(y for _, y in line) < 150.0
    assert max(y for _, y in line) > 176.0


def test_a_hairpin_takes_the_short_way_over_its_own_mouth():
    """Rule three's limit: the short mark over the open end wins.

    Both strands of an out-and-back are the same piece of ground, so the two
    ways round the envelope are a short mark over the open end and a long one
    all the way out to the turn and back. The short one is taken.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    out = [(60.0 + i * 4.0, 150.0) for i in range(50)]
    back = [(x, y + 6.0) for x, y in reversed(out)]
    route = out + back
    line = lb.span_line(route, 0, len(route) - 1, 1, 20.0, card)
    assert line, "the hairpin drew no mark"
    assert not _crosses(line, route)
    # Over the mouth, which is the west end where the two ends of the span are,
    # and nothing like the length of the stretch itself.
    assert length(line) < 0.4 * length(route)
    assert sum(x for x, _ in line) / len(line) < 100.0


def test_the_mark_follows_the_shape_in_a_few_strokes_and_does_not_hold_its_gap():
    """Rules one, two and three together, which replace the held offset.

    The mark does not keep a constant distance from the path. It approximates
    the angle of the path and, at a bend, goes out and around the bendiest
    part of the route. A mark that smooths all of that away is too straight
    and mechanical: it should be a smooth curve that follows the shape and
    could be drawn by hand in a few strokes.

    So there are two failures to keep away from, not one. The mark has to have
    the road's turns in it, and it has to have only a few of them.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    route = [(60.0 + i * 3.0, 120.0) for i in range(30)]
    route += [(150.0 + i * 2.1, 120.0 + i * 2.1) for i in range(1, 25)]
    route += [(202.0 + i * 3.0, 172.0) for i in range(1, 30)]
    span = lb.Span(name="the corner", kind="climb", i0=0, i1=len(route) - 1)
    assert lb.place_spans([span], card, route, _flat_dark(), flat_measure, cap_px=14.0)
    gaps = [foot_on(p, route)[0] for p in span.line]
    # It stands off the route the whole way, and it does not hold one distance.
    assert min(gaps) >= 14.0 * lb.SPAN_CLEAR_CAPS
    assert max(gaps) - min(gaps) > 0.25 * span.offset_px, (
        f"the mark holds its distance: {min(gaps):.1f} to {max(gaps):.1f}"
    )
    # It has the corner in it, and it has only a few turns in all.
    assert 1 <= _corners(span.line) <= 6, f"{_corners(span.line)} turns is not a few strokes"
    assert _corners(span.line) >= _corners(simplify(route, 3.0)) - 2


def test_the_mark_stops_short_of_a_tangle_rather_than_pushing_through_it():
    """Where the ends run into other road, the mark is cut back, not forced.

    On a tight bend the mark ends well before the end of the stretch when the
    end of the stretch is a junction. Cutting back is allowed; crossing is not.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    route = [(60.0 + i * 4.0, 150.0) for i in range(60)]
    # A lane across the far end of the stretch, on both sides of it.
    route += [(300.0, 150.0 + i * 4.0) for i in range(1, 12)]
    span = lb.Span(name="the lane", kind="climb", i0=0, i1=59)
    assert lb.place_spans([span], card, route, _flat_dark(), flat_measure, cap_px=14.0)
    assert not _crosses(span.line, route)
    assert max(x for x, _ in span.line) < 300.0, (
        "the mark ran through the lane at the end of the stretch"
    )


def test_a_span_with_nowhere_to_go_is_dropped_and_says_so(caplog):
    """The answer when rule seven cannot be met is no mark, not a bad one."""
    import logging

    from pyntpot._port import labels as lb

    card = _Sheet()
    # Ground the route hatches from end to end, ten pixels between strands.
    # There is nowhere on it a mark can stand a cap height clear of a road,
    # and no direction to push one that reaches open paper.
    route: list[tuple[float, float]] = []
    for row in range(30):
        y = 10.0 + row * 10.0
        legs = [(20.0 + i * 4.0, y) for i in range(90)]
        route += legs if row % 2 == 0 else list(reversed(legs))
    span = lb.Span(name="the tangle", kind="climb", i0=900, i1=989)
    with caplog.at_level(logging.INFO, logger="pyntpot._port.labels"):
        placed = lb.place_spans([span], card, route, _flat_dark(), flat_measure, cap_px=14.0)
    assert placed == [], "a mark was drawn where none can clear the route"
    assert any("clears the route" in r.message for r in caplog.records)


def test_a_mark_prefers_clear_paper_to_lying_along_a_river():
    """Clear paper is preferred, and given up rather than cross the route.

    A mark would rather not sit tight against a river or a road, and it
    gives that up rather than cross the route. It is a cost weighed against
    how much mark each side yields, not a rule: with the water on one side of
    a straight lane and clear paper on the other, the mark takes the paper.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    route = [(60.0 + i * 4.0, 150.0) for i in range(60)]
    river = [[(60.0 + i * 4.0, 150.0 - 20.0) for i in range(60)]]
    north, south = [], []
    for lines, out in ((None, north), (river, south)):
        span = lb.Span(name="the lane", kind="climb", i0=0, i1=59)
        assert lb.place_spans(
            [span], card, route, _flat_dark(), flat_measure, cap_px=14.0, lines=lines
        )
        out.append(sum(y for _, y in span.line) / len(span.line))
    assert south[0] > 150.0, "the mark stayed on the water"
    # And the river only tips a choice: it is not allowed to lose the mark.
    span = lb.Span(name="the lane", kind="climb", i0=0, i1=59)
    both = [[(60.0 + i * 4.0, 150.0 + s) for i in range(60)] for s in (-20.0, 20.0)]
    assert lb.place_spans(
        [span], card, route, _flat_dark(), flat_measure, cap_px=14.0, lines=both
    ), "water on both sides lost the mark"


def test_the_module_signs_a_side_one_way_and_the_mark_lands_on_it():
    """The sign bug: `_bracket` and `_side_at` disagreed, and one of them went.

    `_bracket` pushed off the chord's own normal and `_side_at` filtered the
    contour by a cross product with the opposite sense, so the two paths landed
    on opposite flanks of the same arc and anything reasoning about `side` from
    a normal was wrong on whichever half of the card took the fallback. There
    is one convention now, `_side_at`'s, and the drawn mark obeys it.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    route = [(60.0 + i * 4.0, 150.0) for i in range(60)]
    for side in (1, -1):
        line = lb.span_line(route, 0, len(route) - 1, side, 20.0, card)
        assert line, f"side {side} drew nothing"
        votes = [lb._side_at(route, lb._nearest_on(route, p), p) for p in line]
        assert sum(votes) / len(votes) == side, (
            f"the mark asked for side {side} landed on the other one"
        )
    # And the two sides are the two sides: one above the lane, one below.
    left = lb.span_line(route, 0, len(route) - 1, 1, 20.0, card)
    right = lb.span_line(route, 0, len(route) - 1, -1, 20.0, card)
    assert (sum(y for _, y in left) < 150.0 * len(left)) != (
        sum(y for _, y in right) < 150.0 * len(right)
    )


def test_an_end_tick_stops_short_of_the_route_rather_than_touching_it():
    """A tick is part of the mark, so rule seven binds it too.

    The tick points at the road, because what it says is where on the road the
    span starts. On ground where the mark sits close, the leg that points at
    the road is shortened until its tip clears it.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    route = [(60.0 + i * 4.0, 150.0) for i in range(60)]
    span = lb.Span(name="the lane", kind="climb", i0=0, i1=59)
    assert lb.place_spans([span], card, route, _flat_dark(), flat_measure, cap_px=14.0)
    assert len(span.ticks) == 2
    clear = 14.0 * lb.SPAN_CLEAR_CAPS
    for tick in span.ticks:
        assert lb.clear_of_route(tick, route, clear)
        assert length(tick) > 0.0


def _shapes() -> dict[str, list[tuple[float, float]]]:
    """One route a case: the shapes a hand-drawn set of marks is made of."""
    straight = [(60.0 + i * 4.0, 150.0) for i in range(60)]
    bend = [(60.0 + i * 3.0, 120.0) for i in range(30)]
    bend += [(150.0 + i * 2.1, 120.0 + i * 2.1) for i in range(1, 25)]
    ess = [(80.0 + i * 3.0, 150.0 + 30.0 * math.sin(i / 9.0)) for i in range(60)]
    out = [(80.0 + i * 4.0, 150.0) for i in range(40)]
    return {
        "straight": straight,
        "bend": bend,
        "s-bend": ess,
        "hairpin": out + [(x, y + 6.0) for x, y in reversed(out)],
        "loop": out + [(x, y + 26.0) for x, y in reversed(out)],
        "crossed": straight + [(200.0, 90.0 + i * 4.0) for i in range(1, 30)],
    }


def _crosses(line: list[tuple[float, float]], route: list[tuple[float, float]]) -> bool:
    """Whether a drawn line properly crosses a route polyline anywhere."""

    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    for a, b in zip(line, line[1:], strict=False):
        for c, d in zip(route, route[1:], strict=False):
            d1, d2 = side(c, d, a), side(c, d, b)
            d3, d4 = side(a, b, c), side(a, b, d)
            if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
                return True
    return False


def _corners(pts: list[tuple[float, float]], tol: float = 3.0) -> int:
    """How many turns a drawn line has, at the tolerance a reader sees.

    A spline is a hundred points that each turn a degree; what a person counts
    is the corners left when the line is simplified to what it looks like.
    """
    return max(len(simplify(pts, tol)) - 2, 0)


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


def test_a_river_follows_its_bend_even_when_the_bend_runs_down_the_sheet():
    """The rule that overrules the tilt test for rivers only.

    A river name says which water it is by sitting on that water. A steep
    window used to be refused outright, which put the Heddon and the lower Lyn
    in clear paper beside their own bends; a name read sideways is better than
    one that could be about anything.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    water = [(200.0 + 12.0 * math.sin(y / 60.0), float(y)) for y in range(20, 280, 5)]
    river = lb.Label(
        name="Heddon",
        kind="river",
        px=200.0,
        py=150.0,
        tier=lb.TIER_RIVER,
        size=14.0,
        baseline=water,
    )
    lb.place([river], [], card, [(0.0, 295.0), (400.0, 295.0)], _flat_dark(), [], flat_measure)
    assert river.window, "a vertical river was not set along its own water"
    assert not river.flat
    assert lb._tilt(river.window) > lb.MAX_TILT_DEG, "this window is a steep one"
    assert "river" in lb.TILT_EXEMPT_KINDS


def test_the_tilt_test_still_holds_for_everything_that_is_not_a_river():
    """A road is not exempt: the rule that was overruled was about water."""
    from pyntpot._port import labels as lb

    card = _Sheet()
    tarmac = [(200.0 + 12.0 * math.sin(y / 60.0), float(y)) for y in range(20, 280, 5)]
    road = lb.Label(
        name="A361", kind="road", px=200.0, py=150.0, tier=lb.TIER_ROAD, size=14.0, baseline=tarmac
    )
    lb.place([road], [], card, [(0.0, 295.0), (400.0, 295.0)], _flat_dark(), [], flat_measure)
    assert road.flat, "a steep road window was accepted"


def test_a_name_on_a_line_that_runs_upwards_is_turned_to_read_downwards():
    """Turning a window round is not rejecting it, which is the whole rule."""
    from pyntpot._port import labels as lb

    up = [(100.0, float(y)) for y in range(300, 100, -5)]
    assert lb._reading(up)[-1][1] > lb._reading(up)[0][1]
    leftwards = [(float(x), 100.0) for x in range(300, 100, -5)]
    assert lb._reading(leftwards)[-1][0] > lb._reading(leftwards)[0][0]
    assert len(lb._reading(up)) == len(up), "a window was dropped, not turned"


def test_a_road_name_stays_near_the_road_it_names():
    """ "Aviemore Road" sat far enough off its tarmac to be a guess.

    With no leader drawn, the only thing joining a road name to its road is
    that they are near each other, so distance from its own centreline is a
    cost in its own right.
    """
    from pyntpot._port import labels as lb

    tarmac = [(float(x), 150.0) for x in range(20, 380, 5)]
    near = lb.Label(
        name="A361", kind="road", px=200.0, py=150.0, tier=lb.TIER_ROAD, size=14.0, baseline=tarmac
    )
    far = lb.Label(
        name="A361", kind="road", px=200.0, py=150.0, tier=lb.TIER_ROAD, size=14.0, baseline=tarmac
    )
    close = (0.0, 0.0, 40.0, 40.0)
    assert lb._off_own_feature(close, far) > 0.0
    assert lb._off_own_feature((190.0, 140.0, 230.0, 160.0), near) == 0.0


def test_a_long_span_name_breaks_over_two_lines_and_reserves_the_block():
    """The root cause of every awkward span placement: one line and only one.

    A break is offered, never forced: it costs `WRAP_COST` and is taken only
    where it buys a materially better position. What it must never do is claim
    a one-line box and then write two lines in it.
    """
    from pyntpot._port import labels as lb

    forms = lb.wrap_forms("the long climb out of Aviemore", "span")
    assert forms[0] == ["the long climb out of Aviemore"]
    assert all(len(form) <= lb.MAX_LINES for form in forms)
    assert any(len(form) == 2 for form in forms)
    assert all(" ".join(form) == "the long climb out of Aviemore" for form in forms)
    # Balanced first, and never a one-word orphan. Three characters of a
    # thirty-character phrase is an orphan whatever the character floor says,
    # and the card drew "the" over "long climb out of Aviemore" until the share
    # was added: a stub first line makes the widest possible second line.
    assert forms[1][0] == "the long climb"
    floor = max(lb.WRAP_MIN_CHARS, lb.WRAP_MIN_SHARE * len("the long climb out of Aviemore"))
    for form in forms[1:]:
        assert min(len(part) for part in form) >= floor
    assert ["the", "long climb out of Aviemore"] not in forms

    wide, tall = lb.block_size(["the long climb", "out of Aviemore"], 14.0, flat_measure)
    one_wide, one_tall = lb.block_size(["the long climb out of Aviemore"], 14.0, flat_measure)
    assert wide < one_wide, "the block is not narrower than the single line"
    assert tall > one_tall, "the block did not reserve the second line"


def test_a_span_name_is_charged_for_every_corner_of_its_block():
    """A short bracket's name read as detached, and the cost could not see it.

    The gap a leaderless name pays for is the clear space between its anchor
    and the near edge of its block, which says nothing at all about where the
    rest of the block went. Off the end of a short bracket a long single line
    clears the anchor by one rung and then runs on for its own width: near by
    that measure, and belonging to nothing by eye. A span is measured over its
    whole block against its whole bracket instead.
    """
    from pyntpot._port import labels as lb

    bracket = [(100.0 + i * 8.0, 100.0) for i in range(11)]
    span = lb.Label(
        name="the long climb out of Aviemore",
        kind="climb",
        tier=lb.TIER_SPAN,
        size=14.0,
        px=140.0,
        py=80.0,
        mark=bracket,
    )
    beside = (108.0, 62.0, 194.0, 93.0)  # a two-line block over the middle
    off_end = (188.0, 72.0, 349.0, 88.0)  # one line, off the far end
    assert lb._mark_gap(off_end, span, 7.0) > lb._mark_gap(beside, span, 7.0)
    # And the rung the old measure would have reported is the same for both,
    # which is exactly why it could not tell them apart.
    assert lb._mark_gap(off_end, lb.Label(name="x"), 7.0) == 7.0


def test_a_span_name_sits_outboard_of_its_bracket_and_never_across_it():
    """The order the eye crosses is route, line, name.

    The proximity pull that keeps a name beside its own bracket, left alone,
    pulls it onto the bracket and then into the gap between the bracket and the
    road it belongs to: the cheapest block of all is the one centred on the
    line. Both are priced, so a name beside its own line beats a name over it
    and a name outboard beats a name inboard.
    """
    from pyntpot._port import labels as lb

    bracket = [(100.0 + i * 8.0, 100.0) for i in range(11)]
    # The anchor is outboard, which is what says which side outboard is.
    span = lb.Label(
        name="the long climb",
        kind="climb",
        tier=lb.TIER_SPAN,
        size=14.0,
        px=140.0,
        py=80.0,
        mark=bracket,
    )
    outboard = (110.0, 60.0, 190.0, 90.0)
    across = (110.0, 88.0, 190.0, 118.0)
    inboard = (110.0, 110.0, 190.0, 140.0)
    assert lb._mark_through(outboard, span) == 0.0
    assert lb._mark_through(across, span) >= lb.SPAN_MARK_THROUGH_COST
    assert lb._mark_through(inboard, span) == pytest.approx(lb.SPAN_INBOARD_COST)
    # Nothing that is not a span pays either: a river has its own rules.
    river = lb.Label(name="Lyn", kind="river")
    assert lb._mark_through(across, river) == 0.0


def test_a_span_name_lands_beside_the_bracket_it_belongs_to():
    """End to end, on a bracket short enough for the fault to bite.

    The whole point of the two costs above is what the placer does with them.
    A name whose block is a good deal wider than its own bracket still has to
    end up beside the bracket, on the outboard side, without the line through
    the words.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    route = [(100.0 + i * 6.0, 200.0) for i in range(16)]
    bracket = [(100.0 + i * 6.0, 170.0) for i in range(16)]
    span = lb.Label(
        name="the long climb out of Aviemore",
        kind="climb",
        tier=lb.TIER_SPAN,
        size=14.0,
        px=145.0,
        py=150.0,
        mark=bracket,
        span_range=(0, 15),
        anchors=[(115.0, 150.0), (145.0, 150.0), (175.0, 150.0)],
    )
    lb.place(
        [span], [], card, route, {"w": 2, "h": 2, "v": [[0.0, 0.0], [0.0, 0.0]]}, [], flat_measure
    )
    x0, y0, x1, y1 = span.box
    near = min(min(math.dist(((x0 + x1) / 2, y), q) for q in bracket) for y in (y0, y1))
    assert near < 3.0 * span.size, f"the name landed {near:.0f} px off its bracket"
    assert (y0 + y1) / 2 < 170.0, "the name sat between the bracket and the road"
    assert lb._mark_through(span.box, span) == 0.0


def test_a_settlement_name_is_never_broken():
    """A place name is one thing a reader looks up; two lines read as two places."""
    from pyntpot._port import labels as lb

    assert lb.wrap_forms("Monmouth Castle", "settlement") == [["Monmouth Castle"]]
    assert lb.wrap_forms("Lyn Valley Road", "road") == [["Lyn Valley Road"]]
    assert lb.wrap_forms("Heddon", "span") == [["Heddon"]], "nothing to break at"
    # A span carries its own vocabulary as its kind, so every one of them has
    # to be wrappable without being named here.
    for kind in lb.SPAN_GROUND + lb.SPAN_EFFORT:
        got = lb.wrap_forms("the long climb out of Aviemore", kind, lb.TIER_SPAN)
        assert len(got) > 1, kind
    # And the same word as a ground kind still does not wrap.
    assert len(lb.wrap_forms("Lyn Valley Road", "road", lb.TIER_ROAD)) == 1


def test_a_wrapped_name_is_written_on_the_lines_it_reserved():
    """The box is the block's, and the hand writes the block, not the name."""
    from pyntpot._port import labels as lb

    card = _Sheet()
    route = [(0.0, 295.0), (400.0, 295.0)]
    name = lb.Label(
        name="the long climb out of Aviemore",
        kind="span",
        tier=lb.TIER_SPAN,
        px=200.0,
        py=150.0,
        size=14.0,
    )
    name.lines = ["the long climb", "out of Aviemore"]
    wide, tall = lb.block_size(name.lines, name.size, flat_measure)
    lb._place_flat(name, wide, tall, card, [(route, 1.0)], _flat_dark(), [], [], len(name.lines))
    assert name.text_lines == name.lines
    assert name.box[3] - name.box[1] == pytest.approx(tall)
    # The two baselines both sit inside the box the placer reserved.
    second = name.ty + name.size * lb.WRAP_LEADING
    assert name.box[1] < name.ty < name.box[3]
    assert name.box[1] < second < name.box[3] + name.size


def test_a_rivers_two_names_are_kept_apart_along_the_water_not_across_the_sheet():
    """A river doubles back, so a straight line between two names is not the gap.

    The guard used to measure the distance across the paper, which on a
    meandering river is a fraction of the water between the two, and on the Lyn
    it rejected every window the second name had left.
    """
    from pyntpot._port import labels as lb

    card = _Sheet()
    # A hairpin: two long reaches whose ends are near each other on the sheet.
    down = [(60.0 + x * 0.6, 60.0 + x * 0.02) for x in range(0, 300, 4)]
    back = [(240.0 - x * 0.6, 74.0 + x * 0.02) for x in range(0, 300, 4)]
    water = down + back
    river = lb.Label(
        name="Lyn", kind="river", px=150.0, py=70.0, tier=lb.TIER_RIVER, size=13.0, baseline=water
    )
    second = lb.Label(
        name="Lyn", kind="river", px=150.0, py=90.0, tier=lb.TIER_RIVER, size=13.0, baseline=water
    )
    lb.place(
        [river, second], [], card, [(0.0, 295.0), (400.0, 295.0)], _flat_dark(), [], flat_measure
    )
    assert river.window and second.window, "the second name lost its water"
    # Far apart along the water, and that is what the guard measures.
    assert math.dist((river.tx, river.ty), (second.tx, second.ty)) > 20.0


def test_the_hand_writes_both_lines_of_a_wrapped_name():
    """The placer reserving two lines is only half of it; the hand has to write them."""
    from pyntpot._port import labels as lb
    from pyntpot.maps.lettering_marks import label_marks

    try:
        hand = _open_hand()
    except (ImportError, OSError):  # no fonttools or no face on disk
        pytest.skip("no face to letter with")
    one = lb.Label(
        name="the long climb out of Aviemore",
        kind="climb",
        tier=lb.TIER_SPAN,
        px=200.0,
        py=150.0,
        size=14.0,
        tx=200.0,
        ty=150.0,
        anchor="middle",
        flat=True,
    )
    two = lb.Label(
        name="the long climb out of Aviemore",
        kind="climb",
        tier=lb.TIER_SPAN,
        px=200.0,
        py=150.0,
        size=14.0,
        tx=200.0,
        ty=150.0,
        anchor="middle",
        flat=True,
        lines=["the long climb", "out of Aviemore"],
    )
    marks_one = [m for m in label_marks(hand, one) if m.role == "glyph"]
    marks_two = [m for m in label_marks(hand, two) if m.role == "glyph"]
    assert marks_one and marks_two
    wide_one = max(x for m in marks_one for x, _y in m.pts) - min(
        x for m in marks_one for x, _y in m.pts
    )
    wide_two = max(x for m in marks_two for x, _y in m.pts) - min(
        x for m in marks_two for x, _y in m.pts
    )
    assert wide_two < wide_one * 0.7, "the wrapped name is not narrower"
    tall_two = max(y for m in marks_two for _x, y in m.pts) - min(
        y for m in marks_two for _x, y in m.pts
    )
    assert tall_two > lb.WRAP_LEADING * two.size, "only one line was written"


def test_a_spans_end_tick_points_from_the_line_at_the_end_of_the_stretch():
    """The end tick replaces "square to the route".

    The end marks take their direction from the end of the line to the end of
    the segment, not perpendicular to the route's local bearing. So the direction is the vector from where the mark stops to where
    the span stops on the road. The route's own bearing at that index is a
    property of two GPS samples and is not what the reader is being shown.

    The lane here kinks in its last few samples, so the two rules point
    different ways and the test can tell them apart.
    """
    import math

    from pyntpot._port import labels as lb

    route = [(100.0 + i * 6.0, 200.0) for i in range(40)]
    route += [(334.0 + i * 2.0, 200.0 - i * 6.0) for i in range(1, 6)]
    span = lb.Span(name="the long climb", i0=0, i1=len(route) - 1)
    span.line = [(100.0, 160.0), (300.0, 130.0)]
    ticks = lb._span_ticks(span, route, 14.0)
    assert len(ticks) == 2
    for tick, at in zip(ticks, (span.i0, span.i1), strict=True):
        (x0, y0), (x1, y1) = tick[0], tick[-1]
        assert (x0, y0) == pytest.approx(span.line[0] if at == span.i0 else span.line[-1]), (
            "the tick does not start at the end of the line"
        )
        want = math.atan2(route[at][1] - y0, route[at][0] - x0)
        got = math.atan2(y1 - y0, x1 - x0)
        assert abs(math.degrees(want - got)) < 1.0, (
            "the tick does not point at the end of the stretch"
        )
        assert math.hypot(x1 - x0, y1 - y0) > 0.0
    # The far tick is not square to the route's own kink, which is the whole
    # point: square to it would send the tick off to the north-east.
    (fx0, fy0), (fx1, fy1) = ticks[1][0], ticks[1][-1]
    assert fx1 > fx0 and fy1 > fy0, "the tick took the route's micro-bearing"
    # And a tick stops short of the road rather than touching it.
    for tick in ticks:
        assert lb.clear_of_route(tick, route, 14.0 * lb.SPAN_CLEAR_CAPS)


def test_a_span_mark_sits_at_the_hand_drawn_offset():
    """The offset is measured off hand-drawn marks, not chosen between extremes.

    2.6 cap heights reads as detached and 0.9 reads as drawn on the road.
    Hand-drawn marks run 10.7 to 14.5 card pixels from the route at a 14 px
    cap height, which is 0.8 to 1.0 cap heights, and the offset is 1.2.
    """
    from pyntpot._port import labels as lb

    assert lb.SPAN_OFFSET_CAPS == 1.2
    assert 1.9 < lb.SPAN_RUNG_CAPS < 2.4
    # And the clearance is not scaled off it: a mark drawn nearer the road
    # still keeps half a cap height from every strand of it.
    assert lb.SPAN_CLEAR_CAPS == 0.5


def test_a_river_name_is_lifted_clear_of_the_water_it_names():
    """The centreline is not the water: the Lyn is painted nine pixels wide.

    The name was lifted half a type size off the middle of the river, which put
    the letters in it. The clearance carries the painted half-width of the
    watercourse now, so a wide river pushes its name further out than a thin
    one and a card drawn at another size scales with it.
    """
    from pyntpot._port import labels as lb

    thin = lb.Label(name="Heddon", kind="river", size=18.0, feature_px=2.2)
    wide = lb.Label(name="Lyn", kind="river", size=18.0, feature_px=8.4)
    assert lb.lift_px(wide) > lb.lift_px(thin), "a wide river lifts no further"
    # And both clear their own water: the baseline is off the centreline by
    # more than half the mark is wide.
    for label in (thin, wide):
        assert lb.lift_px(label) > label.feature_px * 0.5


def test_the_painted_width_of_a_watercourse_reaches_the_label_layer():
    """The label layer sees a centreline; the layers tell it the brush."""
    from pyntpot._port import labels as lb

    fresh = label_basemap(wet_px={"major": 9.5, "medium": 6.0, "minor": 2.4})
    # The layers carry the brush's nominal width and the brush lays down
    # more than that, so what reaches the label layer is the footprint.
    assert lb.feature_px(fresh, "river", "major") == pytest.approx(9.5 * lb.WET_SPREAD)
    # Layers with no width for the class fall back to the painter's defaults
    # rather than to nothing, so such a map letters its rivers where any
    # other does.
    assert lb.feature_px(label_basemap(), "river", "major") == pytest.approx(
        lb.WET_PX_DEFAULT["major"] * lb.WET_SPREAD
    )


# ------------------------------------------------- a name on its own water


class _WideCard:
    w = 900
    h = 671
    scale = 1.0

    @staticmethod
    def xy(x, y):
        return (float(x), float(y))


def _river_label(width_px):
    """One river of a given painted width, placed."""
    from pyntpot._port import labels as lb

    lines = {
        "rivers": [
            {
                "n": "Severn",
                "c": "major",
                "w": width_px,
                "wn": width_px,
                "d": [[100, 400], [800, 400]],
            }
        ]
    }
    basemap = label_basemap(wet_px={"major": 11.0})
    return lb.pick_rivers(basemap, lines, _WideCard(), [(100.0, 100.0), (800.0, 100.0)])[0]


def test_a_wide_river_carries_its_name_on_the_water():
    """Now that the Severn is drawn at the width it occupies, the name goes in it."""
    from pyntpot._port import labels as lb

    wide = _river_label(40.0)
    assert wide.in_water
    assert lb.lift_px(wide) == 0.0
    # The band of ink straddles the centreline rather than sitting off it.
    assert lb.lift_middle(wide, 1.0) == pytest.approx(0.0, abs=0.01)


def test_a_river_drawn_at_the_floor_keeps_its_name_beside_the_water():
    """A brook exaggerated up to be visible has no room for its own name."""
    from pyntpot._port import labels as lb

    thin = _river_label(11.0)
    assert not thin.in_water
    assert lb.lift_px(thin) > 0.0
    assert lb.lift_middle(thin, 1.0) != pytest.approx(0.0, abs=0.01)


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

    assert _ink(_river_label(40.0)) == "in_water"
    assert _ink(_river_label(11.0)) == "water"


def test_the_in_water_ink_beats_a_dark_one_on_the_river():
    """The water is a mid-tone: a dark ink fights it from the wrong side.

    Measured against the major watercourse's own pigment, which is what the
    letters are written over.
    """
    from pyntpot._port import paint

    style = paint.PaintStyle()
    river = BRUSH_COLOURS["RIV"]["a"]
    assert _contrast(style.label_in_water_ink, river) > _contrast("#0f1216", river)
    assert _contrast(style.label_in_water_ink, river) > 4.5


def test_a_name_on_the_water_asks_for_no_backing_wash():
    """A pale blob on a river reads as a hole in the water."""
    from pyntpot.maps.lettering_marks import label_marks

    hand = _open_hand()
    wet = label_marks(hand, _river_label(40.0))
    dry = label_marks(hand, _river_label(11.0))
    assert wet and not any(m.wash for m in wet)
    assert dry and all(m.wash for m in dry)


def test_a_name_is_not_charged_for_crossing_the_thing_it_names():
    """`road_lines` holds the watercourses as well as the tarmac.

    For a name set along its own feature that includes the feature itself, so
    every candidate window scored as "on a road" and the term cancelled out: the
    Severn could not be moved off a bridge because it was on a road wherever it
    went.
    """
    from pyntpot._port import labels as lb

    water = [(100.0, 400.0), (800.0, 400.0)]
    bridge = [(500.0, 300.0), (500.0, 500.0)]
    name = _river_label(40.0)
    kept = lb._off_own([water, bridge], name)
    assert kept == [bridge]
    # A name beside its feature is filtered the same way; everything else stays.
    assert lb._off_own([bridge], name) == [bridge]


def test_a_name_on_the_water_is_moved_off_a_bridge():
    """A bridge drawn through the letters is not ordinary cartography."""
    from pyntpot._port import labels as lb

    assert lb.IN_WATER_ROAD_COST > lb.ROAD_CROSS_COST
    from functools import partial

    from pyntpot.maps.lettering_marks import box_size

    hand = _open_hand()
    name = _river_label(40.0)
    bridge = [(450.0, 300.0), (450.0, 500.0)]
    dark = {"w": 2, "h": 2, "v": [[0.6, 0.6], [0.6, 0.6]]}
    lb.place(
        [name],
        [],
        _WideCard(),
        [(0.0, 0.0)],
        dark,
        [],
        partial(box_size, hand),
        [name.baseline, bridge],
    )
    cells = lb._curved_boxes(name.window, name, name.size, hand.measure)
    assert cells
    assert sum(lb._on_road(c, [bridge]) for c in cells) == 0


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


def test_a_river_name_may_sit_on_either_side_of_its_own_water():
    """Which side is a question about what is underneath, not about the river."""
    from pyntpot._port import labels as lb

    assert "river" in lb.TWO_SIDED_KINDS
    assert "road" in lb.TWO_SIDED_KINDS
    assert "settlement" not in lb.TWO_SIDED_KINDS


def test_an_unnamed_lane_and_a_watercourse_both_cost_a_name_that_crosses_them():
    """A mark on the paper is a mark on the paper, named or not.

    Only the named roads were charged, so a label could be laid across an
    unnamed lane for nothing and a settlement could sit on its own river.
    """
    from pyntpot._port import labels as lb

    class FlatCard:
        w = 400
        h = 300
        scale = 1.0

        @staticmethod
        def xy(x, y):
            return (float(x), float(y))

    named = {
        "roads": [{"n": "A361", "c": "major", "d": [[0, 10], [400, 10]]}],
        "rivers": [{"n": "Lyn", "c": "major", "d": [[0, 60], [400, 60]]}],
        "crossings": [[[0, 120], [400, 120]]],
    }
    lines = lb.road_lines(named, FlatCard())
    assert len(lines) == 3, "the lanes and the water are not in the crossing cost"
    for y in (10.0, 60.0, 120.0):
        assert lb._on_road((100.0, y - 4, 200.0, y + 4), lines) == 1.0


# ------------------------------------------------- one name, and one for a place


def _named(name, kind, tier, x, y):
    """One label at a point, for the repeat and near-duplicate guards."""
    from pyntpot._port import labels as lb

    return lb.Label(
        name=name, kind=kind, why="", px=float(x), py=float(y), tier=tier, size=lb.DEFAULT_LINE_PX
    )


def test_a_settlement_is_lettered_once_however_many_pools_found_it():
    """ "Elm" arrived as a settlement and again as the nearest named feature.

    The settlement pool and the landmark pool have never known about each
    other, so a village could be lettered twice, the second
    time at the end of a long leader from the top of the sheet. The guard is in
    the one funnel both pools go through.
    """
    from pyntpot._port import labels as lb

    elm_settlement = _named("Elm", "settlement", lb.TIER_SETTLEMENT, 495, 168)
    elm_landmark = _named("Elm", "place", lb.TIER_LANDMARK, 495, 168)
    kept = lb.dedupe_names([elm_settlement, elm_landmark], _Sheet())
    assert [label.name for label in kept] == ["Elm"]
    assert kept[0] is elm_settlement, "the lower tier is the one that survives"


def test_the_repeat_guard_is_per_kind_so_the_major_river_keeps_both_names():
    """A long river is read in pieces and is deliberately named twice.

    A guard that were one number for the whole sheet would either letter the
    Lyn once or letter Elm twice, so the allowance belongs to the family.
    """
    from pyntpot._port import labels as lb

    wye = [
        _named("Lyn", "river", lb.TIER_RIVER, 100, 100),
        _named("Lyn", "river", lb.TIER_RIVER, 300, 260),
    ]
    towns = [
        _named("Grasmere", "settlement", lb.TIER_SETTLEMENT, 40, 40),
        _named("Grasmere", "settlement", lb.TIER_SETTLEMENT, 340, 240),
    ]
    kept = lb.dedupe_names(wye + towns, _Sheet())
    names = [label.name for label in kept]
    assert names.count("Lyn") == lb.MAJOR_RIVER_LABELS == 2
    assert names.count("Grasmere") == 1
    assert lb.NAME_ALLOWANCE["water"] == lb.MAJOR_RIVER_LABELS


def test_two_names_for_one_place_keep_the_shorter_more_general_one():
    """High Cup Nick and High Cup Nick Cairn are the same headland.

    Five metres apart, and one name is the other with a structure on the end of
    it. The tiers rank what a name is, so a tie between two landmarks is broken
    by the shorter and more general name: the headland, not the chimney
    standing on it.
    """
    from pyntpot._port import labels as lb

    headland = _named("High Cup Nick", "viewpoint", lb.TIER_LANDMARK, 248, 554)
    chimney = _named("High Cup Nick Cairn", "ruin", lb.TIER_LANDMARK, 249, 553)
    kept = lb.dedupe_names([chimney, headland], _Sheet())
    assert [label.name for label in kept] == ["High Cup Nick"]


def test_a_town_and_a_monument_in_it_are_two_places_and_both_letter():
    """The string relationship alone is not enough, and neither is the distance.

    Monmouth and Monmouth War Memorial stand in the same word relationship as
    High Cup Nick and its chimney. What tells them apart is 485 m against five.
    """
    from pyntpot._port import labels as lb

    town = _named("Monmouth", "settlement", lb.TIER_SETTLEMENT, 294, 592)
    memorial = _named(
        "Monmouth War Memorial", "monument", lb.TIER_LANDMARK, 294 + lb.NEAR_DUPLICATE_M * 2.0, 592
    )
    kept = lb.dedupe_names([town, memorial], _Sheet())
    assert len(kept) == 2, "far enough apart to be a town and a thing in it"
    # And near enough, they are one place again.
    close = _named(
        "Monmouth War Memorial", "monument", lb.TIER_LANDMARK, 294 + lb.NEAR_DUPLICATE_M * 0.1, 592
    )
    assert [label.name for label in lb.dedupe_names([town, close], _Sheet())] == ["Monmouth"]


def test_a_shared_word_is_not_a_shared_place():
    """Two names that only overlap in the middle are two names."""
    from pyntpot._port import labels as lb

    assert lb._one_place("High Cup Nick", "High Cup Nick Cairn")
    assert lb._one_place("Grasmere", "Upper Grasmere"), "a qualifier is stripped"
    assert not lb._one_place("High Cup Nick", "High Cup Nicks")
    assert not lb._one_place("Abergavenny", "Lyn Valley Walk")
    assert not lb._one_place("Monmouth", "Monmouth Castle Field Museum")


def test_a_span_name_is_never_deduped():
    """A span's name is prose about a stretch, not a name for somewhere."""
    from pyntpot._port import labels as lb

    twice = [
        _named("the steady middle hour", "climb", lb.TIER_SPAN, 100, 100),
        _named("the steady middle hour", "fast", lb.TIER_SPAN, 110, 100),
    ]
    assert len(lb.dedupe_names(twice, _Sheet())) == 2


# ------------------------------------------------- the clearance a name keeps


def test_a_name_clears_its_own_feature_on_whichever_side_it_takes():
    """The clearance is a fact about the ink, and a baseline is not the ink.

    The lift used to be applied to the baseline, and letters sit above their
    baseline rather than straddling it: one side cleared the feature and the
    other wrote the whole ascent back across it. Both "Lyn" labels
    took the second side and seven glyph pixels in ten were in the river.
    """
    from pyntpot._port import labels as lb

    river = lb.Label(
        name="Lyn",
        kind="river",
        why="",
        px=0.0,
        py=0.0,
        tier=lb.TIER_RIVER,
        size=18.0,
        feature_px=11.4,
    )
    want = lb.lift_px(river)
    for side in (1.0, -1.0):
        base = lb.lift_baseline(river, side)
        # Letters sit above their baseline whichever side of the line the
        # baseline was put on, so the ink band is the same way up both times
        # and only one of its two edges is the near one.
        edges = (base + river.size * lb.INK_ASCENT_CAPS, base - river.size * lb.INK_DESCENT_CAPS)
        near = min(abs(e) for e in edges)
        assert near == pytest.approx(want), f"side {side} does not clear"
        assert base * side > 0.0, "the baseline is on the side that was chosen"


def test_the_box_a_curved_name_reserves_is_centred_on_its_own_ink():
    """The placer defends boxes and the pen writes glyphs, and they are one thing."""
    from pyntpot._port import labels as lb

    road = lb.Label(
        name="A361",
        kind="road",
        why="",
        px=0.0,
        py=0.0,
        tier=lb.TIER_ROAD,
        size=14.0,
        feature_px=6.75,
    )
    for side in (1.0, -1.0):
        base = lb.lift_baseline(road, side)
        middle = lb.lift_middle(road, side)
        top = base + road.size * lb.INK_ASCENT_CAPS
        bottom = base - road.size * lb.INK_DESCENT_CAPS
        assert middle == pytest.approx((top + bottom) / 2)


def test_the_clearance_scales_with_the_water_the_painter_actually_laid_down():
    """The layers carry the brush's nominal width, not its footprint.

    A brush bleeds, smooths and drifts past its own nominal edge, so a
    clearance taken against the nominal width stands the name off less water
    than it has to clear.
    """
    from pyntpot._port import labels as lb

    assert lb.WET_SPREAD > 1.0
    wide = label_basemap(wet_px={"major": 12.0, "medium": 3.0, "minor": 1.0})
    narrow = label_basemap(wet_px={"major": 4.0, "medium": 3.0, "minor": 1.0})
    big = lb.Label(
        name="Lyn",
        kind="river",
        why="",
        px=0.0,
        py=0.0,
        tier=lb.TIER_RIVER,
        size=18.0,
        feature_px=lb.feature_px(wide, "river", "major"),
    )
    small = lb.Label(
        name="Lyn",
        kind="river",
        why="",
        px=0.0,
        py=0.0,
        tier=lb.TIER_RIVER,
        size=18.0,
        feature_px=lb.feature_px(narrow, "river", "major"),
    )
    assert lb.lift_px(big) > lb.lift_px(small)
    # The clearance starts where the painted ink stops: the whole painted
    # half-width, then `LIFT_CAPS` of the type size as paper.
    assert lb.LIFT_FEATURE_FRAC == 1.0
    assert lb.lift_px(big) - big.feature_px * 0.5 == pytest.approx(big.size * lb.LIFT_CAPS)


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


def _leadered(name, x, y):
    """One landmark waiting to be placed."""
    from pyntpot._port import labels as lb

    return lb.Label(
        name=name,
        kind="monument",
        why="",
        px=float(x),
        py=float(y),
        tier=lb.TIER_LANDMARK,
        size=lb.DEFAULT_LINE_PX,
    )


class _FlatCard:
    w = 400
    h = 300
    scale = 1.0

    @staticmethod
    def xy(x, y):
        return (float(x), float(y))


def _dark():
    return {"w": 2, "h": 2, "v": [[0.1, 0.1], [0.1, 0.1]]}


def _seat(label, cx, cy, width):
    """Sit one placed name's block on a point, as the placer would have."""
    from pyntpot._port import labels as lb

    label.box = (cx - width / 2, cy - 10, cx + width / 2, cy + 10)
    label.flat = True
    label.leader = ((label.px, label.py), (cx, cy))
    lb._reseat(label, cx, cy)


def test_two_leaders_that_cross_are_swapped_over():
    """The placer is greedy, so two names can reach past each other.

    A reader meeting a crossing follows the wrong line to the wrong pin, and
    swapping the two names over is what shortens both leaders at once.
    """
    from pyntpot._port import labels as lb

    a, b = _leadered("Alpha", 100.0, 100.0), _leadered("Beta", 100.0, 200.0)
    # Seated deliberately the wrong way round: each name is off past the other.
    _seat(a, 300.0, 200.0, 60.0)
    _seat(b, 300.0, 100.0, 60.0)
    assert meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is not None
    lb._uncross_leaders(
        [a, b], _FlatCard(), [(0.0, 10.0), (400.0, 10.0)], [(0.0, 10.0), (400.0, 10.0)], _dark(), []
    )
    assert meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is None
    assert a.leader[1][1] < b.leader[1][1], "each name is still past the other"


def test_a_swap_that_reads_worse_is_refused():
    """The swap is offered, not imposed: a name is never pushed off the sheet.

    A wide name and a narrow one can cross, and the wide one does not fit where
    the narrow one is sitting. A shorter pair of leaders is not worth a name in
    the torn margin.
    """
    from pyntpot._port import labels as lb

    a, b = _leadered("Alpha", 100.0, 100.0), _leadered("Beta", 340.0, 100.0)
    _seat(a, 365.0, 200.0, 40.0)
    _seat(b, 110.0, 200.0, 160.0)
    assert meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is not None
    seats = (a.box, b.box)
    lb._uncross_leaders(
        [a, b], _FlatCard(), [(0.0, 10.0), (400.0, 10.0)], [(0.0, 10.0), (400.0, 10.0)], _dark(), []
    )
    assert (a.box, b.box) == seats, "a name was swapped off the paper"


def test_a_name_on_its_own_mark_is_never_swapped():
    """A settlement is its place: it has no leader and cannot be moved."""
    from pyntpot._port import labels as lb

    a = _leadered("Alpha", 150.0, 150.0)
    a.box, a.flat, a.leader = (270.0, 140.0, 330.0, 160.0), True, ((150.0, 150.0), (300.0, 150.0))
    town = lb.Label(
        name="Elm",
        kind="settlement",
        px=250.0,
        py=150.0,
        tier=lb.TIER_SETTLEMENT,
        size=lb.DEFAULT_LINE_PX,
    )
    town.box, town.flat, town.leader = (70.0, 140.0, 130.0, 160.0), True, None
    seat = town.box
    lb._uncross_leaders(
        [a, town],
        _FlatCard(),
        [(0.0, 10.0), (400.0, 10.0)],
        [(0.0, 10.0), (400.0, 10.0)],
        _dark(),
        [],
    )
    assert town.box == seat


def test_a_resolved_paint_style_has_the_type_of_the_default_in_every_field():
    """A JSON round trip keeps tuples as tuples, which `digest` cannot see."""
    resolved = json.loads(json.dumps(dataclasses.asdict(paint.PaintStyle())))
    rebuilt = paint.PaintStyle.from_resolved(resolved)
    default = paint.PaintStyle()
    for field in dataclasses.fields(paint.PaintStyle):
        got = getattr(rebuilt, field.name)
        want = getattr(default, field.name)
        assert type(got) is type(want), field.name
    assert rebuilt.digest() == default.digest()


def test_a_resolved_style_restores_tuples_nested_in_dicts():
    """Tuple values inside a dict field come back as tuples, not lists."""
    resolved = json.loads(json.dumps(dataclasses.asdict(paint.PaintStyle())))
    rebuilt = paint.PaintStyle.from_resolved(resolved)
    assert rebuilt.cover_cfg == paint.PaintStyle().cover_cfg
    assert all(isinstance(v, tuple) for v in rebuilt.cover_cfg.values())


def test_a_resolved_paint_style_refuses_an_unknown_field():
    """A field the style does not have is named, not silently dropped."""
    with pytest.raises(ValueError, match="nonsense"):
        paint.PaintStyle.from_resolved({"nonsense": 1})


def test_a_lettering_only_style_change_leaves_the_base_key_and_the_plates_alone(tmp_path):
    """Changing the hand's seed keeps `base_key`, and `paint` repaints nothing."""
    from pyntpot.maps import pipeline
    from pyntpot.maps.cache import Cache

    style = as_style(tiny_style())
    basemap = tiny_basemap()
    first = pipeline.paint(basemap, style, tmp_path)
    stamps = {name: path.stat().st_mtime_ns for name, path in first.paths.items()}
    reseeded = as_style(tiny_style(label_seed=2))
    assert reseeded.lettering_digest() != style.lettering_digest()
    assert Cache.base_key(basemap, reseeded) == Cache.base_key(basemap, style)
    again = pipeline.paint(basemap, reseeded, tmp_path)
    assert {name: path.stat().st_mtime_ns for name, path in again.paths.items()} == stamps
    assert again.hash == first.hash


def test_a_base_plate_style_change_changes_the_base_key_and_the_lettering_key():
    """A paper change moves `base_key`, and with it the key of a plate drawn against it."""
    from pyntpot.letters.setting import Mark
    from pyntpot.maps.cache import Cache

    style = as_style(tiny_style())
    other = as_style(tiny_style(paper_fibre=not tiny_style().paper_fibre))
    basemap = tiny_basemap()
    marks = [Mark(pts=[(1.0, 2.0), (3.0, 4.0)])]
    one, two = Cache.base_key(basemap, style), Cache.base_key(basemap, other)
    assert one != two
    assert Cache.lettering_key(marks, one, style) != Cache.lettering_key(marks, two, style)
