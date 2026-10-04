"""The painter's smoke box: the plates it writes, the approved bytes and what each style flag moves.

Everything here paints a box a few dozen pixels across, so the suite stays fast.
"""

import dataclasses
import hashlib
from typing import Any

import numpy as np
from PIL import Image

from pyntpot.ink.sheet import rgb
from pyntpot.maps.basemap import Basemap, Line, River, Road
from pyntpot.maps.painter.plates import paint_plates
from pyntpot.maps.style import Style

from support.basemaps import (
    PAINT_GROUPS,
    class_style,
    tiny_basemap,
    tiny_style,
    with_fields,
)


def read(style: Style, name: str) -> Any:
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
    style, basemap = smoke_box()
    manifest = paint_plates(basemap, style, tmp_path).manifest
    got = {
        name: hashlib.sha256((tmp_path / fn).read_bytes()).hexdigest()
        for name, fn in manifest.files.items()
    }
    assert got == SMOKE_SHA


def test_every_flag_on_together_still_paints_the_box(tmp_path):
    """And with all three on it is a different plate, not a broken one."""
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
    style, basemap = smoke_box(brush_organic=True, ink_joins=True, stroke_smooth=True, ink_ss=2)
    manifest = paint_plates(basemap, style, tmp_path).manifest
    got = {
        name: hashlib.sha256((tmp_path / fn).read_bytes()).hexdigest()
        for name, fn in manifest.files.items()
    }
    assert got["paper"] == SMOKE_SHA["paper"]  # nothing here touches the card
    assert got["wash"] != SMOKE_SHA["wash"]
    assert got["pen"] != SMOKE_SHA["pen"]


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


# ------------------------------------------------------ the encoder and the ramp


def test_the_style_decides_how_the_plates_are_written(tmp_path):
    """Lossless is the default, and turning it off is the old encoder back."""
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
