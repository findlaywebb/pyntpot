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

from support.paths import FIXTURE_DIR, KEY

FIXTURE_GPX = FIXTURE_DIR / "track.gpx"

#: A short synthetic track inside the Lynmouth box.
LATS = [51.2250 + 2e-5 * i for i in range(60)]


LNGS = [-3.8400 + 0.00040 * i for i in range(60)]


def tiny_style(**over: object) -> paint.PaintStyle:
    """The approved style, painted small enough to be a unit test."""
    return paint.PaintStyle(display_px=80, supersample=2, **over)


def square(cx: float, cy: float, r: float) -> str:
    """One closed square ring as path data, in metres."""
    pts = [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]
    return geo.path_d(pts, close=True)


def tiny_payload(**over: object) -> dict:
    """A whole payload for a small box, with nothing in it but the route."""
    style = over.pop("style", None) or tiny_style()
    route = [(float(x), 40.0 + 30.0 * math.sin(x / 260.0)) for x in range(0, 1400, 40)]
    payload = {
        "id": "iTINY",
        **geo.journal_geometry(route, style),
        "route": [[round(x, 1), round(y, 1)] for x, y in route],
        "cover": {},
        "cover_order": [],
        "lakes": [],
        "sea": [],
        "coastline": [],
        "roads": [],
        "rivers": [],
        "places": [],
        "candidates": [],
        "sources": [],
    }
    payload.update(over)
    return payload


# --------------------------------------------------------------------------- painter


def test_a_tiny_box_paints_a_card_a_wash_and_a_manifest(tmp_path):
    """The painter writes two plates plus the pen, and says what it did."""
    style = tiny_style()
    manifest = paint.paint(tiny_payload(style=style), style, tmp_path)
    assert set(manifest["files"]) == {"paper", "wash", "pen"}
    for name in manifest["files"].values():
        assert (tmp_path / name).stat().st_size > 0
    assert (tmp_path / "plates.json").exists()
    assert manifest["display"][0] == 80
    assert manifest["render"][0] == 160
    assert manifest["dark"]["w"] == style.dark_grid[0]
    assert len(manifest["dark"]["v"]) == style.dark_grid[1]


def test_the_plates_are_webp_the_size_they_were_painted(tmp_path):
    """A plate is a WebP at the render size, not at the display size."""
    from PIL import Image

    style = tiny_style()
    manifest = paint.paint(tiny_payload(style=style), style, tmp_path)
    with Image.open(tmp_path / manifest["files"]["wash"]) as img:
        assert img.format == "WEBP"
        assert img.size == tuple(manifest["render"])
    with Image.open(tmp_path / manifest["files"]["pen"]) as img:
        assert img.mode in ("RGBA", "P")


def test_a_repaint_is_only_needed_when_the_style_or_the_data_changes(tmp_path):
    """The hash is what stops a render ever having to paint."""
    style = tiny_style()
    payload = tiny_payload(style=style)
    first = paint.paint_hash(payload, style)
    assert paint.paint_hash(tiny_payload(style=style), style) == first
    assert paint.paint_hash(payload, tiny_style(ribbon_mult=1.25)) != first
    moved = tiny_payload(style=style)
    moved["rivers"] = [{"c": "minor", "n": "", "d": "M0,0 L100,100"}]
    assert paint.paint_hash(moved, style) != first
    manifest = paint.paint(payload, style, paint.plates_dir("iTINY", tmp_path))
    assert paint.load_plates("iTINY", tmp_path)["hash"] == manifest["hash"]


def test_no_plates_is_not_an_error(tmp_path):
    """A box that has never been painted reads back as nothing, not a crash."""
    assert paint.load_plates("iNOTHING", tmp_path) is None
    (tmp_path / "plates" / "iBROKEN").mkdir(parents=True)
    (tmp_path / "plates" / "iBROKEN" / "plates.json").write_text("{not json")
    assert paint.load_plates("iBROKEN", tmp_path) is None


def test_the_plates_live_under_the_geo_cache(tmp_path):
    """Redirect the cache and the plates go with it."""
    assert paint.plates_dir("iX", tmp_path) == tmp_path / "plates" / "iX"


# --------------------------------------------------------------------------- brushes


def test_a_brush_id_names_a_treatment_and_a_colour():
    """The five approved picks resolve to the rows and inks they name."""
    style = paint.PaintStyle()
    major, colour = paint.brush_from_id("MAJ2-a", 3.6, 2.0, style)
    assert colour == "#b5623f"
    assert major.width == pytest.approx(7.2)
    track, olive = paint.brush_from_id("TRK4-d", 2.4, 2.0, style)
    assert olive == "#6f6636"
    assert track.dry > major.dry  # the track is the dry, broken brush
    lane, umber = paint.brush_from_id("LAN5-a", 1.8, 2.0, style, "lane")
    assert umber == "#6b4423"
    assert lane.pool == pytest.approx(1.4)  # the pen touch-down, as last tuned
    river, cobalt = paint.brush_from_id("RIV1-a", 8.4, 2.0, style)
    assert cobalt == "#255d80"
    assert river.dry < track.dry


def test_a_brush_id_that_names_nothing_is_refused():
    """A style naming a brush the sheet does not carry fails where it is set."""
    with pytest.raises(ValueError, match="no such brush"):
        paint.brush_from_id("MAJ9-a", 3.0, 2.0, paint.PaintStyle())
    with pytest.raises(ValueError, match="no such brush"):
        paint.brush_from_id("RIV1-z", 3.0, 2.0, paint.PaintStyle())


def test_every_class_the_plate_paints_has_a_brush():
    """The plate's brush table covers every class the layers can carry."""
    brushes = paint.plate_brushes(
        paint.PaintStyle(), 2.0, {"major": 8.0, "medium": 5.0, "minor": 2.0}
    )
    assert set(brushes) == {"major", "medium", "minor", "coast", "road_major", "lane", "track"}
    assert brushes["coast"][0].width < brushes["medium"][0].width


def test_a_dry_brush_breaks_where_a_wet_one_does_not():
    """Dryness is one number, and it is what makes a track scratchy."""
    sheet = paint.Sheet(60, 220, gran_px=6.0, seed=3)
    line = np.stack([np.linspace(10, 210, 80), np.full(80, 30.0)], axis=1)
    marks = {}
    for key, brush_id in (("wet", "RIV1-a"), ("dry", "TRK4-d")):
        brush, _ = paint.brush_from_id(brush_id, 3.0, 2.0, paint.PaintStyle())
        acc = np.zeros((60, 220), np.float32)
        paint.stamp(acc, line, brush, np.random.default_rng(7))
        marks[key] = paint.ink_density(acc, brush, sheet)
    band = slice(24, 37)
    wet = marks["wet"][band] > 0.25
    dry = marks["dry"][band] > 0.25
    assert wet.mean() > dry.mean()
    assert dry.any()  # broken, not absent


def test_the_pen_sets_down_where_it_touches_and_nowhere_else():
    """A nib meeting the paper: extra ink over about a width, then nothing."""
    from dataclasses import replace

    tuned, _ = paint.brush_from_id("LAN5-a", 2.0, 2.0, paint.PaintStyle(), "lane")
    assert tuned.load > 0 and tuned.pool > 0
    assert tuned.load_px == pytest.approx(tuned.width * 0.85)
    bare = replace(tuned, load=0.0, pool=0.0)
    line = np.stack([np.linspace(10, 190, 90), np.full(90, 20.0)], axis=1)
    marks = []
    for brush in (tuned, bare):
        acc = np.zeros((40, 200), np.float32)
        paint.stamp(acc, line, brush, np.random.default_rng(5))
        marks.append(acc)
    assert marks[0][:, 8:18].sum() > marks[1][:, 8:18].sum() * 1.3
    assert marks[0][:, 60:160].sum() == pytest.approx(marks[1][:, 60:160].sum(), rel=1e-4)


def test_two_strokes_crossing_never_double():
    """Saturation is what stops a crossing reaching twice the black."""
    sheet = paint.Sheet(60, 60, gran_px=6.0, seed=2)
    brush, _ = paint.brush_from_id("MAJ2-a", 3.0, 2.0, paint.PaintStyle())
    across = np.stack([np.linspace(5, 55, 40), np.full(40, 30.0)], axis=1)
    down = np.stack([np.full(40, 30.0), np.linspace(5, 55, 40)], axis=1)
    one = np.zeros((60, 60), np.float32)
    paint.stamp(one, across, brush, np.random.default_rng(1))
    both = one.copy()
    paint.stamp(both, down, brush, np.random.default_rng(1))
    d_one = paint.ink_density(one, brush, sheet)
    d_both = paint.ink_density(both, brush, sheet)
    assert d_both.max() <= 1.0
    assert d_both[28:33, 28:33].max() <= d_one.max() + 0.05


# ------------------------------------------------------- phase 1: the brush flags

#: The smoke box: a route, three roads and two watercourses, so every brush the
#: plate carries is stamped. Small enough to paint in a fraction of a second.
SMOKE_ROADS = [
    {"b": "major", "d": "M0,200 L400,180 L900,240 L1390,200"},
    {"b": "minor", "d": "M40,60 L600,140 L1340,90"},
    {"b": "path", "d": "M30,340 L700,300 L1360,360"},
]


SMOKE_RIVERS = [
    {"c": "major", "n": "Lyn", "d": "M20,10 L400,120 L900,60 L1380,150"},
    {"c": "minor", "n": "", "d": "M60,300 L500,250 L1100,320"},
]


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


def smoke_box(**over: object) -> tuple[paint.PaintStyle, dict]:
    """The smoke box's style and payload, with any style fields moved."""
    style = paint.PaintStyle(display_px=120, supersample=2, **over)
    payload = tiny_payload(style=style, roads=SMOKE_ROADS, rivers=SMOKE_RIVERS)
    payload["id"] = "iSMOKE"
    return style, payload


def long_stroke(
    brush_id: str, width_px: float, over: str = "", length: int = 1500, **style_over: object
) -> tuple[np.ndarray, paint.Brush]:
    """One straight 1500 px stroke's density, as the swatch sheet paints it."""
    h = 44
    style = paint.PaintStyle(**style_over)
    brush, _ = paint.brush_from_id(brush_id, width_px, 2.0, style, over)
    sheet = paint.Sheet(h, length, gran_px=9.0, seed=11)
    pts = np.stack([np.linspace(20.0, length - 20.0, 900), np.full(900, h / 2)], axis=1)
    acc = np.zeros((h, length), np.float32)
    aux = paint.ink_aux((h, length), brush)
    paint.stamp(acc, pts, brush, np.random.default_rng(91), aux=aux)
    return paint.ink_density(acc, brush, sheet, aux), brush


def thirds(dens: np.ndarray) -> list[float]:
    """Ink per column, averaged over each third of the stroke."""
    cols = dens.sum(axis=0)
    n = len(cols)
    return [float(cols[i * n // 3 : (i + 1) * n // 3].mean()) for i in range(3)]


def test_every_phase_1_brush_flag_is_off_by_default():
    """A field added here must not move a plate until a theme asks for it."""
    style = paint.PaintStyle()
    assert not (style.ink_starve or style.dry_directional or style.pen_starve)
    brush, _ = paint.brush_from_id("TRK4-d", 2.4, 2.0, style, "track")
    assert not (brush.starve or brush.dir_dry or brush.pen_starve)
    assert paint.ink_aux((8, 8), brush) is None


def test_the_flags_off_still_paint_the_plates_that_were_approved(tmp_path):
    """The whole point of the flags: the same seed still writes the same bytes."""
    import hashlib

    style, payload = smoke_box()
    manifest = paint.paint(payload, style, tmp_path)
    got = {
        name: hashlib.sha256((tmp_path / fn).read_bytes()).hexdigest()
        for name, fn in manifest["files"].items()
    }
    assert got == SMOKE_SHA


def test_every_flag_on_together_still_paints_the_box(tmp_path):
    """And with all three on it is a different plate, not a broken one."""
    import hashlib

    style, payload = smoke_box(ink_starve=True, dry_directional=True, pen_starve=True)
    manifest = paint.paint(payload, style, tmp_path)
    got = {
        name: hashlib.sha256((tmp_path / fn).read_bytes()).hexdigest()
        for name, fn in manifest["files"].items()
    }
    assert got["paper"] == SMOKE_SHA["paper"]  # nothing here touches the card
    assert got["wash"] != SMOKE_SHA["wash"]
    assert got["pen"] != SMOKE_SHA["pen"]


def test_a_starved_brush_runs_out_along_the_stroke():
    """The mark starts loaded and breaks into skips, rather than fading evenly."""
    off, _ = long_stroke("TRK4-d", 2.4, "track")
    on, brush = long_stroke("TRK4-d", 2.4, "track", ink_starve=True)
    assert brush.starve and brush.run_px > 0
    # Against the same stroke unstarved, because a path's own ink wanders: what
    # the reservoir has to do is take more out of the end than out of the start.
    kept = [n / f for n, f in zip(thirds(on), thirds(off), strict=True)]
    assert kept[2] < kept[0] * 0.9
    assert thirds(off)[2] > thirds(on)[2] * 1.3
    assert on[:, -400:].max() > 0.2  # broken, not absent


def test_the_reservoir_is_read_off_the_final_density_not_the_deposits():
    """A per-sample gate is diluted by the splat: the mark must break, not thin.

    With the gate on the deposits alone a starved mark comes out evenly paler.
    Reading it off the accumulated density instead is what puts holes in it, so
    the last third loses more of its area than it loses of its ink.
    """

    def patchiness(dens: np.ndarray) -> float:
        cols = dens[:, -500:].sum(axis=0)
        return float(cols.std() / max(cols.mean(), 1e-6))

    for brush_id, width, over in (
        ("TRK4-d", 2.4, "track"),
        ("STR3-a", 2.2, "minor"),
        ("MAJ2-a", 3.6, "road_major"),
    ):
        off, _ = long_stroke(brush_id, width, over)
        on, _ = long_stroke(brush_id, width, over, ink_starve=True)
        assert patchiness(on) > patchiness(off) * 1.1, brush_id


def turned_stroke(
    vertical: bool, **style_over: object
) -> tuple[np.ndarray, paint.Sheet, paint.Brush]:
    """The same dry brush drawn across the same sheet, one way then the other."""
    size = 420
    style = paint.PaintStyle(**style_over)
    brush, _ = paint.brush_from_id("TRK4-d", 6.0, 2.0, style, "track")
    sheet = paint.Sheet(size, size, gran_px=9.0, seed=11)
    t = np.linspace(20.0, size - 20.0, 600)
    mid = np.full(600, size / 2)
    pts = np.stack([mid, t] if vertical else [t, mid], axis=1)
    acc = np.zeros((size, size), np.float32)
    aux = paint.ink_aux((size, size), brush)
    paint.stamp(acc, pts, brush, np.random.default_rng(91), aux=aux)
    return paint.ink_density(acc, brush, sheet, aux), sheet, brush


def test_a_directional_break_follows_the_stroke_not_the_sheet():
    """Where the mark breaks stops being a fact about the paper under it.

    The isotropic gate reads `sheet.paper` at the pixel, so a dry mark breaks
    wherever the paper happens to be low and the break is the same blotch
    whichever way the stroke was drawn. On the flag the break comes from a
    texture in the stroke's own frame, stretched along it, so the paper stops
    explaining where the mark is thin.
    """

    def explained(dens: np.ndarray, sheet: paint.Sheet) -> float:
        inked = dens > 0.02
        return abs(
            float(np.corrcoef(sheet.paper[inked].astype(float), dens[inked].astype(float))[0, 1])
        )

    for vertical in (False, True):
        off, sheet, base = turned_stroke(vertical)
        on, _, brush = turned_stroke(vertical, dry_directional=True)
        assert brush.dir_dry and not base.dir_dry
        assert explained(off, sheet) > 0.2
        assert explained(on, sheet) < explained(off, sheet) * 0.4
        # It swaps where the break falls; it does not remove it or darken it.
        assert (on[on > 0.02] < 0.35).mean() > 0.1
        assert on.sum() == pytest.approx(off.sum(), rel=0.12)


def test_a_wet_brush_is_left_alone_by_the_directional_break():
    """A river is not a dry brush, so the flag barely moves it."""
    off, _ = long_stroke("RIV1-a", 8.4)
    on, _ = long_stroke("RIV1-a", 8.4, dry_directional=True)
    assert on.sum() == pytest.approx(off.sum(), rel=0.03)


def test_a_nib_thins_and_lightens_as_it_runs_down():
    """A pen does not break, it runs down: the line narrows and pales."""
    off, base = long_stroke("LAN5-a", 1.8, "lane")
    on, brush = long_stroke("LAN5-a", 1.8, "lane", pen_starve=True)
    assert brush.pen and brush.pen_starve and not brush.starve
    assert not base.pen_starve
    a, _b, c = thirds(on)
    assert c < a  # it runs down along the stroke
    wide = [(on[:, i * 500 : (i + 1) * 500] > 0.25).sum(axis=0).mean() for i in range(3)]
    assert wide[2] < wide[0]
    assert thirds(off)[2] > c  # and it is lighter than the same nib full


def test_a_nib_comes_back_at_the_reload():
    """The seam a dip leaves is what makes a long line look drawn."""
    run, _ = long_stroke("MAJ6-e", 3.0, "route", length=9000, pen_starve=True, pen_reservoir=60.0)
    cols = (run > 0.25).sum(axis=0).astype(float)
    # Somewhere past the first dip the line is back to its full width.
    assert cols[3000:8000].max() >= cols[200:800].max() * 0.95


def test_a_brush_never_takes_the_nib_treatment_or_the_other_way_round():
    """The two reservoirs are separate flags on separate tools."""
    both = paint.PaintStyle(ink_starve=True, pen_starve=True)
    track, _ = paint.brush_from_id("TRK4-d", 2.4, 2.0, both, "track")
    lane, _ = paint.brush_from_id("LAN5-a", 1.8, 2.0, both, "lane")
    assert track.starve and not track.pen_starve
    assert lane.pen_starve and not lane.starve
    assert paint.PEN_ROWS == frozenset({"5", "6", "8"})


# ---------------------------------------------------- phase 2: brush quality

#: The classes whose repeat was worth measuring, with the brush and width the
#: plate paints each of them at.
REPEATERS = [
    ("MAJ6-e", 3.0, "route"),
    ("RIV1-a", 8.4, ""),
    ("LAN5-a", 1.8, "lane"),
    ("MAJ2-a", 3.6, "road_major"),
]


def padded(
    brush_id: str,
    width_px: float,
    over: str = "",
    length: int = 1500,
    seed: int = 91,
    sheet_seed: int = 11,
    h: int = 44,
    **style_over: object,
) -> np.ndarray:
    """One straight stroke's density, through the pad the painter uses."""
    style = paint.PaintStyle(**style_over)
    brush, _ = paint.brush_from_id(brush_id, width_px, 2.0, style, over)
    sheet = paint.Sheet(h, length, gran_px=9.0, seed=sheet_seed)
    pts = np.stack([np.linspace(20.0, length - 20.0, 900), np.full(900, h / 2)], axis=1)
    pad = paint.InkPad((h, length), brush, style)
    pad.lay([(brush, pts)], np.random.default_rng(seed))
    return pad.read(brush, sheet)


def shared_repeat(
    brush_id: str, width_px: float, over: str, seeds: int = 6, **style_over: object
) -> tuple[float, int]:
    """The strongest repeat a class carries beyond the bristle scale.

    An autocorrelation along one stroke cannot tell a period from a lucky run
    of noise. Averaging it over strokes drawn on different sheets with
    different bristles can: what the brush itself repeats stays where it is and
    everything else cancels. Lags under 120 render pixels are left out, because
    the bristles, the tip and the paper's own coarse cell all live under that
    and are meant to.

    Args:
        brush_id: The brush sheet cell.
        width_px: The display width the class is painted at.
        over: The class's key in the style's brush overrides.
        seeds: How many strokes to average over.
        style_over: Paint style fields to move.

    Returns:
        The strongest correlation beyond that lag, and the lag it sits at.
    """
    acs = []
    for s in range(seeds):
        dens = padded(
            brush_id, width_px, over, seed=91 + 7 * s, sheet_seed=11 + 3 * s, **style_over
        )
        x = dens.sum(axis=0)[80:-80].astype(float)
        k = 201
        trend = np.convolve(np.pad(x, k // 2, mode="edge"), np.ones(k) / k, mode="valid")[: len(x)]
        x = x - trend
        f = np.fft.rfft(x, 2 * len(x))
        ac = np.fft.irfft(f * np.conj(f))[:900]
        acs.append(ac / max(ac[0], 1e-9))
    mean = np.mean(acs, axis=0)[120:]
    return float(mean.max()), int(np.argmax(mean)) + 120


def test_every_phase_2_brush_flag_but_the_ink_grid_is_off_by_default():
    """A field added here must not move a plate until a theme asks for it.

    `ink_ss` is the one exception and is on at 3, because a mark under four
    render pixels wide cannot be held by the plate's own grid: that is the
    stair that reads as scratchiness. The rest still have to be
    inert, and `ink_ss` back at 1 still has to be the pad it always was.
    """
    style = paint.PaintStyle()
    assert style.ink_ss == 3
    assert not (style.brush_organic or style.ink_joins or style.stroke_smooth)
    brush, _ = paint.brush_from_id("TRK4-d", 2.4, 2.0, style, "track")
    assert not brush.organic and brush.smooth == 0.0 and brush.unit == 1.0
    assert paint.scaled_brush(brush, 1) is brush
    pad = paint.InkPad((8, 8), brush, paint.PaintStyle(ink_ss=1))
    assert pad.ss == 1 and pad.tol == 0.0 and not pad.any()
    assert paint.InkPad((8, 8), brush, style).ss == 3


def tip_across(
    brush_id: str,
    width_px: float,
    over: str = "",
    ss: int = 3,
    seeds: tuple[int, ...] = (91, 7, 33),
    **style_over: object,
) -> np.ndarray:
    """One stroke's accumulator sampled across the tip, on the ink's own grid.

    The fault the tip knobs are for lives in the accumulator, before the paper
    gate and before the reduce, so this reads it there. Each profile is
    normalised by its own mean, so what comes back is the shape of the tip and
    not how much ink it carried.

    Args:
        brush_id: The brush sheet cell.
        width_px: The display width the class is painted at.
        over: The class's key in the style's brush overrides.
        ss: The ink grid, as a multiple of the plate's.
        seeds: The tip patterns to pool over, because one draw is one tip.
        style_over: Paint style fields to move.

    Returns:
        `(windows, samples across)`, each row a normalised cross-tip profile.
    """
    style = paint.PaintStyle(**style_over)
    b, _ = paint.brush_from_id(brush_id, width_px, 2.0, style, over)
    sb = paint.scaled_brush(b, ss)
    h, w = 150 * ss, 360 * ss
    # A shallow diagonal, so the tip crosses the pixel grid the way a road on
    # the card does rather than landing on whole rows.
    ang = np.radians(20.0)
    s = np.linspace(0.0, 320.0 * ss, 700)
    x0, y0 = 20.0 * ss, 40.0 * ss
    pts = np.stack([x0 + s * np.cos(ang), y0 + s * np.sin(ang)], 1).astype(np.float32)
    s = np.arange(60.0 * ss, 260.0 * ss)
    cx, cy = x0 + s * np.cos(ang), y0 + s * np.sin(ang)
    u = np.linspace(-0.28, 0.28, 61) * sb.width
    px = cx[:, None] - np.sin(ang) * u[None, :]
    py = cy[:, None] + np.cos(ang) * u[None, :]
    ix = np.clip(np.floor(px).astype(int), 0, w - 2)
    iy = np.clip(np.floor(py).astype(int), 0, h - 2)
    fx, fy = px - ix, py - iy
    rows = []
    for seed in seeds:
        acc = np.zeros((h, w), np.float32)
        paint.stamp(acc, pts, sb, np.random.default_rng(seed))
        val = (
            acc[iy, ix] * (1 - fx) * (1 - fy)
            + acc[iy, ix + 1] * fx * (1 - fy)
            + acc[iy + 1, ix] * (1 - fx) * fy
            + acc[iy + 1, ix + 1] * fx * fy
        )
        n = len(val) // 40 * 40
        rows.append(val[:n].reshape(-1, 40, val.shape[1]).mean(1))
    prof = np.concatenate(rows)
    # Against the mark's own envelope rather than its mean, so what comes back
    # is the holes and steps inside the mark and not the tip's bell, nor the
    # sideways wander of the whole mark, which is a wander and not a fault.
    env = paint._tip_band(prof, prof.shape[1] / 5.0)
    return prof / np.maximum(env, 1e-9)


def test_the_tip_no_longer_folds_over_itself():
    """Streaking: a tip laying filaments, not a band.

    Every bristle's sideways drift was drawn independently of the one beside
    it, and on `road_major` that drift is 0.55 render pixels either way against
    a bristle spacing of 0.23. So neighbours crossed, the tip collapsed into
    four or five coincident filaments with bare paper between them, and because
    the phases do not change along the stroke those gaps ran its whole length.
    Sharing the drift across a quarter of the tip is what makes it a tip again.
    """
    was = tip_across(
        "MAJ2-a", 3.6, "road_major", bristle_drift_coherence=0.0, bristle_bandlimit_px=0.0
    )
    now = tip_across("MAJ2-a", 3.6, "road_major")
    # The deepest hole inside the mark, against the mark's own envelope. A
    # quarter is a bristle's worth of nearly bare paper in the middle of a
    # road; a tip laying a band sits close to 1.
    assert float(was.min(1).mean()) < 0.30
    assert float(now.min(1).mean()) > 0.85
    # And the step from one lane to the next, which is what reads as harsh.
    assert (
        float(np.abs(np.diff(now, axis=1)).max()) < float(np.abs(np.diff(was, axis=1)).max()) * 0.45
    )


def test_both_tip_knobs_are_wired_and_each_one_earns_its_place():
    """The fold and the bandlimit are two faults, and both have to be fixed.

    The tip carries a fixed number of logical bristles whatever it is painted
    at, so most of its detail is finer than the plate can draw and comes back
    as an alias. That is a second fault under the fold, and it only shows once
    the fold is gone: with the drift shared but the weights unbandlimited the
    tip is still twice as uneven as it needs to be.
    """
    style = paint.PaintStyle()
    assert style.bristle_drift_coherence == 0.25
    assert style.bristle_bandlimit_px == 0.9
    assert style.bristle_contrast == 1.0
    b, _ = paint.brush_from_id("MAJ2-a", 3.6, 2.0, style, "road_major")
    assert (b.coherence, b.band_px, b.contrast) == (0.25, 0.9, 1.0)
    assert paint.scaled_brush(b, 3).coherence == 0.25

    both = float(tip_across("MAJ2-a", 3.6, "road_major").std(1).mean())
    drift_only = float(
        tip_across("MAJ2-a", 3.6, "road_major", bristle_bandlimit_px=0.0).std(1).mean()
    )
    neither = float(
        tip_across(
            "MAJ2-a", 3.6, "road_major", bristle_drift_coherence=0.0, bristle_bandlimit_px=0.0
        )
        .std(1)
        .mean()
    )
    assert drift_only < neither * 0.55
    assert both < drift_only * 0.35
    # And the contrast knob is the user's, so it has to move the tip both
    # ways: down to a smoother lane and up to a harder one.
    softer = float(tip_across("MAJ2-a", 3.6, "road_major", bristle_contrast=0.5).std(1).mean())
    harder = float(tip_across("MAJ2-a", 3.6, "road_major", bristle_contrast=2.0).std(1).mean())
    assert softer < both < harder


def test_the_phase_2_brush_flags_on_together_still_paint_the_box(tmp_path):
    """All four on is a different plate, not a broken one, and not the card."""
    import hashlib

    style, payload = smoke_box(brush_organic=True, ink_joins=True, stroke_smooth=True, ink_ss=2)
    manifest = paint.paint(payload, style, tmp_path)
    got = {
        name: hashlib.sha256((tmp_path / fn).read_bytes()).hexdigest()
        for name, fn in manifest["files"].items()
    }
    assert got["paper"] == SMOKE_SHA["paper"]  # nothing here touches the card
    assert got["wash"] != SMOKE_SHA["wash"]
    assert got["pen"] != SMOKE_SHA["pen"]


def test_the_drift_along_a_stroke_repeats_and_the_flag_stops_it():
    """The complaint was repetition, and it was four sines saying the same thing.

    Every wander in a stroke was a sine, so a long mark came back to itself:
    the bristle drift every 390 render pixels and every bristle in step with
    the rest, the line's wobble every 210, the pressure every 2 pi cells, and
    each bristle's break between 116 and 215 with a beat near 500 where two of
    them differed a little. The route pen carries it plainest, because nothing
    else is happening on a nib.
    """
    off, lag = shared_repeat("MAJ6-e", 3.0, "route")
    assert off > 0.4
    assert 340 <= lag <= 430  # the bristle drift, 2 pi times its own 62 px
    for brush_id, width_px, over in REPEATERS:
        was, _ = shared_repeat(brush_id, width_px, over)
        now, _ = shared_repeat(brush_id, width_px, over, brush_organic=True)
        assert now < 0.15, brush_id
        # MAJ2-a no longer clears the second bar, and the reason is worth
        # keeping: its own repeat fell from 0.22 to 0.09 when the bristle drift
        # stopped being drawn independently per bristle. What carried the
        # sine's period into the density on a road was the tip folding into
        # filaments and the whole set of them swinging together; with the tip
        # laying a band there is almost nothing left for the sine to modulate,
        # so the flag has no period to remove and only the bar above applies.
        if was >= 0.15:
            assert now < was * 0.7, brush_id


def test_a_road_split_into_ways_is_one_mark_again():
    """OSM splits a road wherever a tag changes, and the joins show.

    Each way took a fresh tip pattern, a fresh set-down blob and a lift taper
    at both ends, so a road arrived as a chain of tapered lozenges. Joined
    first, the same six pieces paint the mark that was drawn in one.
    """
    h, w = 44, 1200
    whole = np.stack([np.linspace(20.0, w - 20.0, 901), np.full(901, h / 2)], axis=1)
    pieces = [whole[i * 150 : (i + 1) * 150 + 1] for i in range(6)]
    assert len(paint.chain_lines(pieces, 2.5)) == 1
    sheet = paint.Sheet(h, w, gran_px=9.0, seed=11)

    def lay(lines: list[np.ndarray], **style_over: object) -> np.ndarray:
        style = paint.PaintStyle(**style_over)
        brush, _ = paint.brush_from_id("MAJ2-a", 3.6, 2.0, style, "road_major")
        pad = paint.InkPad((h, w), brush, style)
        pad.lay([(brush, line) for line in lines], np.random.default_rng(91))
        return pad.read(brush, sheet).sum(axis=0)[60:-60]

    ref = lay([whole])
    thin = float(np.median(ref)) * 0.6
    assert (lay(pieces) < thin).sum() > 40  # the tapers, in the mark's body
    assert (lay(pieces, ink_joins=True) < thin).sum() == 0
    assert lay(pieces, ink_joins=True) == pytest.approx(ref, abs=1e-4)


def test_a_way_that_arrives_backwards_is_still_joined():
    """A junction hands the painter whichever end it has; both are the mark."""
    a = np.stack([np.linspace(0.0, 100.0, 60), np.zeros(60)], axis=1)
    b = np.stack([np.linspace(220.0, 100.0, 60), np.zeros(60)], axis=1)
    chains = paint.chain_lines([a, b], 2.5)
    assert len(chains) == 1
    assert chains[0][0][0] == pytest.approx(0.0)
    assert chains[0][-1][0] == pytest.approx(220.0)
    # And two that meet nowhere are left as the two marks they are.
    far = np.stack([np.linspace(400.0, 500.0, 60), np.zeros(60)], axis=1)
    assert len(paint.chain_lines([a, far], 2.5)) == 2


def test_a_corner_is_rounded_to_the_brush_rather_than_stamped_through():
    """A tip stamped through a 90 degree vertex folds over itself.

    The generalised track turns 82 degrees at the 95th percentile of its
    vertices. The normal swings through a turn like that in a couple of
    samples, the far side of the tip runs backwards, and what lands is a bead
    sitting in the quadrant outside the corner. No brush draws a corner
    tighter than it is wide.
    """
    h = w = 200
    leg_a = np.stack([np.linspace(20.0, 100.0, 300), np.full(300, 60.0)], axis=1)
    leg_b = np.stack([np.full(300, 100.0), np.linspace(60.0, 180.0, 300)], axis=1)
    pts = np.concatenate([leg_a, leg_b])
    sheet = paint.Sheet(h, w, gran_px=9.0, seed=11)
    yy, xx = np.mgrid[0:h, 0:w]
    outside = (xx > 100) & (yy < 60)

    def mark(smooth: bool) -> tuple[np.ndarray, paint.Brush]:
        style = paint.PaintStyle(stroke_smooth=smooth)
        brush, _ = paint.brush_from_id("MAJ2-a", 3.6, 2.0, style, "road_major")
        acc = np.zeros((h, w), np.float32)
        aux = paint.ink_aux((h, w), brush)
        paint.stamp(acc, pts, brush, np.random.default_rng(91), aux=aux)
        return paint.ink_density(acc, brush, sheet, aux), brush

    off, base = mark(False)
    on, brush = mark(True)
    assert base.smooth == 0.0
    assert brush.smooth == pytest.approx(brush.width * 0.7)
    assert float(on[outside].sum()) < float(off[outside].sum()) * 0.75
    # It rounds the corner; it does not shorten the road or thin it.
    assert on.sum() == pytest.approx(off.sum(), rel=0.06)
    assert on[58:63, 25:75].sum() == pytest.approx(off[58:63, 25:75].sum(), rel=0.05)


def test_a_finer_grid_converges_on_the_mark_the_brush_describes():
    """What the eye reads as pixelation is the ink's own grid.

    The saturation and the paper gate are per pixel, so the plate's grid is
    where a thin mark's edge is decided. Painting the whole ink pipeline on a
    finer grid and reducing the density back converges: against a stroke
    painted six times finer, the plate's own grid is most of twice as far off
    as a grid twice as fine.
    """
    h, w = 40, 500
    t = np.linspace(20.0, w - 20.0, 900)
    pts = np.stack([t, 8.0 + t / 7.0], axis=1)  # a shallow diagonal: the worst case
    sheet = paint.Sheet(h, w, gran_px=9.0, seed=11)

    def at(ss: int) -> np.ndarray:
        style = paint.PaintStyle(ink_ss=ss)
        brush, _ = paint.brush_from_id("MAJ6-e", 3.0, 2.0, style, "route")
        pad = paint.InkPad((h, w), brush, style)
        assert pad.acc.shape == (h * ss, w * ss)
        pad.lay([(brush, pts)], np.random.default_rng(91))
        return pad.read(brush, sheet)

    ref = at(6)
    err = [float(np.abs(at(ss) - ref).mean()) for ss in (1, 2, 3)]
    assert err[0] > err[1] > err[2]
    assert err[1] < err[0] * 0.7


def test_a_finer_grid_lays_the_same_weight_of_ink():
    """The accumulator holds a thickness, not a count of deposits.

    Without the grid factor in the normalisation the same mark on a grid twice
    as fine comes out half as dark, which is a bug and not a look.
    """
    for brush_id, width_px, over in REPEATERS:
        one = float(padded(brush_id, width_px, over, ink_ss=1).sum())
        two = float(padded(brush_id, width_px, over, ink_ss=2).sum())
        assert two == pytest.approx(one, rel=0.2), brush_id
        assert two < one  # a sharper mark spreads less, and is honest about it


# --------------------------------------------------------------------------- ribbon


def _loop_distance(size: int = 120) -> np.ndarray:
    """Distance to a square loop, so the inside of it is a hole."""
    mask = np.zeros((size, size), bool)
    mask[30, 30:90] = True
    mask[89, 30:90] = True
    mask[30:90, 30] = True
    mask[30:90, 89] = True
    return paint.edt(mask)


def test_the_ribbon_fills_the_inside_of_a_loop():
    """A loop is a shape, not a band: what the outside cannot reach is painted."""
    sheet = paint.Sheet(120, 120, gran_px=6.0, seed=4)
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
    sheet = paint.Sheet(120, 120, gran_px=6.0, seed=4)
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
    payload = tiny_payload(style=style)
    cx0, cy0, cx1, cy1 = payload["card"]
    mid = ((cx0 + cx1) / 2, (cy0 + cy1) / 2)
    payload["cover"] = {
        "farmland": [square(mid[0], mid[1], 400)],
        "wood": [square(mid[0], mid[1], 300)],
    }
    payload["cover_order"] = ["farmland", "wood"]
    manifest = paint.paint(payload, style, tmp_path)
    from PIL import Image

    with Image.open(tmp_path / manifest["files"]["wash"]) as img:
        arr = np.asarray(img.convert("RGB"), np.float32) / 255
    h, w, _ = arr.shape
    centre = arr[h // 2, w // 2]
    wood = paint.rgb(style.pigments["wood"])
    farmland = paint.rgb(style.pigments["farmland"])
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
    proj, _ = geo.track_projection(LATS, LNGS)
    rings = geo.cover_rings("iTAGS", proj, (-9000.0, -9000.0, 9000.0, 9000.0), 2.0, tmp_path)
    assert list(rings) == ["wood"]


def test_a_box_with_no_land_cover_cached_is_bare_paper(tmp_path):
    """Where nobody has drawn a field the ground stays paper, and that is honest."""
    proj, _ = geo.track_projection(LATS, LNGS)
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
    payload = geo.journal_layers(
        KEY, lat, lng, paint.PaintStyle(), cache_dir=FIXTURE_DIR, places=[]
    )
    assert payload is not None
    assert payload["ribbon_m"] == 553
    assert payload["display"] == [900, 728]
    assert "wood" in payload["cover"]
    assert payload["cover_order"][-1] == "wood"
    assert {r["b"] for r in payload["roads"]} <= {"major", "minor", "path"}
    assert payload["minor_roads"] is True


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


def two_squares(h: int = 200, w: int = 320) -> tuple:
    """Two land classes meeting along a seam, on a sheet, for the wash tests."""
    sheet = paint.Sheet(h, w, gran_px=8.0, seed=5)
    left = np.zeros((h, w), np.float32)
    left[40:160, 40:160] = 1.0
    right = np.zeros((h, w), np.float32)
    right[40:160, 160:280] = 1.0
    return sheet, left, right


def test_every_phase_one_option_is_off_by_default():
    """The default plates paint as before until a theme turns one on."""
    style = paint.PaintStyle()
    assert not style.km_glazing
    assert not style.paper_fibre
    assert not style.wet_bleed
    assert not style.flow_rim
    assert not style.blooms


def test_a_wash_given_no_option_is_the_wash_it_always_was():
    """Passing the phase 1 arguments at their inert values changes nothing."""
    sheet, left, _ = two_squares()
    plain = paint.wash(left, sheet, 0.52, 0.20, rim_px=7.0)
    same = paint.wash(
        left, sheet, 0.52, 0.20, rim_px=7.0, wet=None, gran_gamma=0.0, flow=None, blooms=None
    )
    assert np.array_equal(plain, same)


def test_a_sheet_with_no_fibre_is_the_sheet_it_always_was():
    """The fibre draws last, so the five fields and the stream after them hold."""
    plain = paint.Sheet(60, 90, gran_px=6.0, seed=4)
    same = paint.Sheet(60, 90, gran_px=6.0, seed=4, fibre=0.0)
    laid = paint.Sheet(60, 90, gran_px=6.0, seed=4, fibre=0.35)
    for name in ("paper", "coarse", "fine", "wet", "gran"):
        assert np.array_equal(getattr(plain, name), getattr(same, name))
        if name != "paper":
            assert np.array_equal(getattr(plain, name), getattr(laid, name))
    assert np.array_equal(plain.noise(20.0), same.noise(20.0))
    assert not np.array_equal(plain.paper, laid.paper)


def test_multiply_is_still_multiply_when_glazing_is_off():
    """The compositing path with the flag off is the arithmetic it replaced."""
    sheet, left, right = two_squares(80, 120)
    layers = [
        (paint.wash(left, sheet, 0.52, 0.20), paint.rgb(paint.PIGMENTS["farmland"]), 0.10),
        (paint.wash(right, sheet, 0.72, 0.30), paint.rgb(paint.PIGMENTS["wood"])),
    ]
    base = np.ones((80, 120, 3), np.float32)
    assert np.array_equal(
        paint.composite(layers, base, paint.PaintStyle()),
        np.clip(base * paint.multiply_plate(layers, 80, 120), 0, 1),
    )


# --- 1: Kubelka-Munk glazing


def test_a_full_wash_over_white_gives_back_its_own_pigment():
    """The step that is easy to miss: S derived from Rw and Rb, or all goes black."""
    for key in ("wood", "water", "heath", "relief"):
        pig = paint.rgb(paint.PIGMENTS[key])
        thick = np.ones((2, 2), np.float32)
        out = paint.km_plate(
            [(thick, pig, paint.TRANSPARENCY[key])], np.ones((2, 2, 3), np.float32)
        )
        assert out[0, 0] == pytest.approx(pig, abs=2e-3), key
        # And nothing laid down is nothing changed.
        clear = paint.km_plate(
            [(np.zeros((2, 2), np.float32), pig, 0.05)], np.ones((2, 2, 3), np.float32)
        )
        assert clear[0, 0] == pytest.approx([1.0, 1.0, 1.0], abs=1e-4)


def test_a_wash_crossing_another_keeps_its_own_hue_under_glazing():
    """Multiply averages two pigments into an olive; glazing does not."""

    def hue(c: np.ndarray) -> float:
        mx, mn = float(c.max()), float(c.min())
        if mx - mn < 1e-9:
            return 0.0
        r, g, b = (float(v) for v in c)
        i = int(np.argmax(c))
        turn = (
            ((g - b) / (mx - mn)) % 6
            if i == 0
            else (2 + (b - r) / (mx - mn))
            if i == 1
            else (4 + (r - g) / (mx - mn))
        )
        return turn * 60.0

    wood = paint.rgb(paint.PIGMENTS["wood"])
    water = paint.rgb(paint.PIGMENTS["water"])
    under = np.ones((4, 4), np.float32)
    over = np.full((4, 4), 0.6, np.float32)
    base = np.ones((4, 4, 3), np.float32)
    mul = paint.multiply_plate([(under, water), (over, wood)], 4, 4)[0, 0]
    glazed = paint.km_plate([(under, water, 0.04), (over, wood, 0.05)], base)[0, 0]
    # The wood is the top wash, so the crossing should read as wood over water,
    # not as the two colours multiplied into one another.
    assert abs(hue(glazed) - hue(wood)) < abs(hue(mul) - hue(wood)) - 5.0


# --- 2: one cold-press paper field, with granulation bound to it


def test_the_fibre_field_lies_along_one_axis():
    """Cold press has a direction: a fibre is about three times longer than wide."""
    rng = np.random.default_rng(1)
    iso = paint.fbm(200, 300, 4.2, 3, np.random.default_rng(1))
    laid = paint.fbm_aniso(200, 300, 4.2, 3, rng, 3.0, 0.42)

    def ratio(f: np.ndarray) -> float:
        return float(np.abs(np.diff(f, axis=0)).mean() / np.abs(np.diff(f, axis=1)).mean())

    assert ratio(iso) == pytest.approx(1.0, abs=0.06)
    assert ratio(laid) > 1.4


def test_granulation_settles_in_the_pits_the_dry_brush_breaks_on():
    """Bound to the paper's own height, not to an fbm unrelated to it."""
    sheet = paint.Sheet(200, 300, gran_px=8.0, seed=5, fibre=0.35)
    square_m = np.zeros((200, 300), np.float32)
    square_m[40:160, 60:240] = 1.0
    body = square_m > 0.5
    loose = paint.wash(square_m, sheet, 0.55, 0.22, rim_px=7.0)
    bound = paint.wash(square_m, sheet, 0.55, 0.22, rim_px=7.0, gran_gamma=1.7)

    def follows(d: np.ndarray) -> float:
        a = d[body] - d[body].mean()
        b = sheet.paper[body] - sheet.paper[body].mean()
        return float((a * b).mean() / (a.std() * b.std()))

    # Negative because the pits are where the paper is low and the pigment high.
    assert follows(bound) < follows(loose) - 0.20


# --- 3: one wet-area map shared across the classes


def test_two_classes_wet_at_once_bleed_into_each_other_rather_than_butt():
    """A boundary inside the land is not an edge; the outer silhouette still is."""
    sheet, left, right = two_squares()
    union = np.clip(left + right, 0, 1)
    wet = paint.smoothstep(paint.edt(union < 0.5) - np.float32(16.0), 16.0)
    assert wet[100, 160] > 0.9, "the seam is inside the wet area"
    assert wet[100, 41] < 0.1, "the outer edge is not"

    def total(**kw):
        return paint.wash(left, sheet, 0.52, 0.20, rim_px=7.0, **kw) + paint.wash(
            right, sheet, 0.58, 0.26, rim_px=7.0, **kw
        )

    dry = total()
    damp = total(wet=wet, bleed_px=5.0, bleed_mix=0.55, rim_drop=0.7)
    seam, band = slice(150, 172), slice(70, 130)

    def step(d: np.ndarray) -> float:
        return float(np.abs(np.diff(d[band, seam], axis=1)).mean())

    assert step(damp) < step(dry) * 0.6
    assert damp[band, seam].max() < dry[band, seam].max() - 0.1
    # The land's own outer edge keeps its rim: the wet area ends before it.
    assert damp[band, 38:48].max() == pytest.approx(dry[band, 38:48].max(), abs=2e-3)


# --- 4: edge darkening from an outward flow term


def test_the_flow_rim_is_wider_on_a_bigger_wash():
    """Mask minus blur is one width everywhere; a drying edge is not."""
    sheet = paint.Sheet(260, 400, gran_px=8.0, seed=5)
    depths = {}
    for tag, radius in (("small", 18), ("big", 90)):
        yy, xx = np.ogrid[:260, :400]
        disc = ((yy - 130) ** 2 + (xx - 200) ** 2 < radius * radius).astype(np.float32)
        a = np.clip((paint.blur(disc, 2.4) - 0.5) * 3.2 + 0.5, 0, 1)
        inward = paint.edt(~(a > 0.5))
        for name, rim in (
            ("old", np.clip(a - paint.blur(a, 7.0), 0, 1)),
            ("flow", paint.flow_edge(a, sheet, 7.0, 0.125, 0.02, 0.38)),
        ):
            depths[name, tag] = float((rim * inward).sum() / max(rim.sum(), 1e-6))
    grew = depths["flow", "big"] / depths["flow", "small"]
    held = depths["old", "big"] / depths["old", "small"]
    assert grew > held * 1.3
    assert depths["flow", "small"] < depths["old", "small"], "it sits in against the edge"


# --- 5: blooms


def test_a_bloom_lifts_the_centre_and_deposits_it_at_the_front():
    """A backrun: lighter inside, a darker crenellated ridge where it stopped."""
    sheet, left, _ = two_squares()
    body = left > 0.5
    core = body & (paint.edt(~body) > 12)
    flat = paint.wash(left, sheet, 0.52, 0.20, rim_px=7.0)
    blown = paint.wash(
        left, sheet, 0.52, 0.20, rim_px=7.0, blooms=(np.random.default_rng(3), 3, 0.17, 0.45, 0.45)
    )
    assert blown[core].std() > flat[core].std() * 1.5
    assert blown[core].min() < flat[core].min() - 0.1, "a lighter centre"
    assert blown[core].max() > flat[core].max() + 0.05, "and a darker ring"
    # Deterministic from the seed it is given, like everything else here.
    again = paint.wash(
        left, sheet, 0.52, 0.20, rim_px=7.0, blooms=(np.random.default_rng(3), 3, 0.17, 0.45, 0.45)
    )
    assert np.array_equal(blown, again)


# ------------------------------------------------------- phase 2: the wash flags
#
# The wash half of phase 2: deformed silhouettes, two-pigment washes and the
# bounded shallow-water pass. Same rule as phase 1 - off by default, one test a
# flag, and the flag has to be shown doing the thing it is named for.

#: The smoke box with land cover in it, because the phase 2 wash flags all need
#: a class to work on. Two blocks either side of the route, one of them the
#: wood, in the box's own metres.
COVER_BOX = {
    "wood": ["M200,-140 L640,-140 L640,220 L200,220 Z"],
    "farmland": ["M720,-140 L1320,-140 L1320,220 L720,220 Z"],
}


def cover_box(**over: object) -> tuple[paint.PaintStyle, dict]:
    """The smoke box with two land classes in it, and any style fields moved."""
    style, payload = smoke_box(**over)
    payload["cover"] = {k: list(v) for k, v in COVER_BOX.items()}
    payload["cover_order"] = ["farmland", "wood"]
    return style, payload


def painted(tmp_path, **over: object) -> dict[str, str]:
    """The cover box's plates, as a digest a name."""
    import hashlib

    style, payload = cover_box(**over)
    out = tmp_path / ("on" if over else "off")
    manifest = paint.paint(payload, style, out)
    return {
        name: hashlib.sha256((out / fn).read_bytes()).hexdigest()
        for name, fn in manifest["files"].items()
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

    style, payload = smoke_box()
    manifest = paint.paint(payload, style, tmp_path)
    got = {
        name: hashlib.sha256((tmp_path / fn).read_bytes()).hexdigest()
        for name, fn in manifest["files"].items()
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


# --- 7: polygon deformation for the wash silhouette


def ring_of(n: int = 96, r: float = 200.0) -> list[tuple[float, float]]:
    """A circle, as the ring the deformation is given."""
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return [(float(r * math.cos(t)), float(r * math.sin(t))) for t in a]


def test_an_outline_given_no_deform_is_the_outline_it_was():
    """The inert path hands back the same objects, not a copy of them."""
    rings = [ring_of(), ring_of(40, 90.0)]
    assert paint.deform_rings(rings, None) is rings


def test_the_deformed_outline_wobbles_at_more_than_one_scale():
    """One frequency everywhere is what the blurred-mask edge already does."""
    ring = np.asarray(ring_of(), float)
    out = paint.deform_ring(ring, np.random.default_rng(5), 0.26, 4, 0.55, 16.0, 0.5)
    assert len(out) == len(ring) * 16
    rad = np.hypot(out[:, 0], out[:, 1]) - 200.0
    # Split the deviation into what a long smoothing keeps and what it removes.
    k = np.ones(33) / 33.0
    coarse = np.convolve(np.concatenate([rad[-16:], rad, rad[:16]]), k, "same")[16:-16]
    fine = rad - coarse
    assert coarse.std() > 1.0, "no wobble the eye reads as a lobe"
    assert fine.std() > 0.3, "no wobble at the scale of a brush edge"
    # Neither scale swamps the other: that mixture is the whole point of it.
    assert 0.15 < fine.std() / coarse.std() < 6.0
    # And it is a deformation, not a new shape: the ring keeps its place.
    assert abs(float(out[:, 0].mean())) < 12.0
    assert abs(float(np.hypot(out[:, 0], out[:, 1]).mean()) - 200.0) < 12.0


def test_no_one_displacement_runs_away_with_a_long_segment():
    """A field boundary drawn as two points must not be thrown across the sheet."""
    box = [(0.0, 0.0), (4000.0, 0.0), (4000.0, 3000.0), (0.0, 3000.0)]
    out = paint.deform_ring(box, np.random.default_rng(2), 0.26, 4, 0.55, 16.0, 0.5)
    # Every point stays within the cap of the straight edge it came off, give or
    # take the caps the earlier rounds already spent.
    assert float(np.abs(out[:, 1]).min()) < 1e-9
    assert float(out[:, 1].max()) < 3000.0 + 16.0 * 4


def test_the_deformation_is_the_same_ring_from_the_same_seed():
    """Everything in the painter has to come back the same from its seed."""
    a = paint.deform_ring(ring_of(), np.random.default_rng(9), 0.26, 4, 0.55, 16.0, 0.5)
    b = paint.deform_ring(ring_of(), np.random.default_rng(9), 0.26, 4, 0.55, 16.0, 0.5)
    assert np.array_equal(a, b)


def test_the_surveyed_coast_is_not_deformed(tmp_path):
    """The coast is a fact. Only the land cover's own outlines are pushed about."""
    import hashlib

    def sea_only(**over: object) -> str:
        style, payload = smoke_box(**over)
        payload["sea"] = ["M-400,-400 L600,-400 L600,-160 L-400,-160 Z"]
        payload["lakes"] = ["M800,20 L1000,20 L1000,120 L800,120 Z"]
        out = tmp_path / ("on" if over else "off")
        manifest = paint.paint(payload, style, out)
        return hashlib.sha256((out / manifest["files"]["wash"]).read_bytes()).hexdigest()

    assert sea_only(silhouette_deform=True) == sea_only()


# --- 8: two-pigment washes on the Kubelka-Munk path


def test_a_class_that_is_not_named_stays_the_one_wash_it_was():
    """Only the classes a theme names separate, and only when the flag is on."""
    sheet, left, _ = two_squares(80, 120)
    dens = paint.wash(left, sheet, 0.72, 0.30, rim_px=7.0)
    pig = paint.rgb(paint.PIGMENTS["wood"])
    for style in (paint.PaintStyle(), paint.PaintStyle(pigment_separation=True)):
        out = paint.separated(dens, "heath", pig, 0.14, sheet, style)
        assert len(out) == 1
        assert out[0][0] is dens


def test_the_heavy_pigment_settles_in_the_tooth_and_the_light_one_floats():
    """Two pigments out of one wash: one in the pits, one over them."""
    sheet, left, _ = two_squares(200, 320)
    dens = paint.wash(left, sheet, 0.72, 0.30, rim_px=7.0)
    style = paint.PaintStyle(pigment_separation=True)
    light, heavy = paint.separated(
        dens, "wood", paint.rgb(paint.PIGMENTS["wood"]), 0.05, sheet, style
    )
    body = left > 0.5

    def follows(d: np.ndarray) -> float:
        a = d[body] - d[body].mean()
        b = sheet.paper[body] - sheet.paper[body].mean()
        return float((a * b).mean() / (a.std() * b.std()))

    # Negative because the pits are where the paper is low and the pigment high.
    assert follows(heavy[0]) < follows(light[0]) - 0.5
    # The wash is redistributed, not added to: the two together are what one was.
    assert (light[0] + heavy[0])[body].mean() == pytest.approx(dens[body].mean(), rel=0.06)
    assert heavy[1].tolist() != light[1].tolist(), "and it is a second pigment"
    assert light[0][body].std() < heavy[0][body].std()


# --- 9: one bounded shallow-water pass


def fluid_fields(h: int = 96, w: int = 128) -> tuple:
    """A wet area, some pigment in it, and a sheet of paper under it."""
    rng = np.random.default_rng(4)
    wet = np.zeros((h, w), np.float32)
    wet[12:84, 16:112] = 1.0
    pig = paint.fbm(h, w, 20.0, 2, rng)
    paper = paint.fbm(h, w, 4.0, 3, rng)
    return wet, pig, paper


def test_the_fluid_pass_is_deterministic_because_it_counts_rather_than_converges():
    """A tolerance would make the iteration count depend on the arithmetic."""
    wet, pig, paper = fluid_fields()
    a = paint.shallow_water(wet, pig, paper, 20, 4, 41, 0.6)
    b = paint.shallow_water(wet, pig, paper, 20, 4, 41, 0.6)
    assert np.array_equal(a, b)
    assert np.isfinite(a).all(), "the relaxation has to stay bounded"
    assert not np.array_equal(a, paint.shallow_water(wet, pig, paper, 30, 4, 41, 0.6))


def test_the_water_carries_pigment_out_to_the_edge_it_dries_at():
    """FlowOutward is what puts the deposit at the contact line, not the middle."""
    wet, _, paper = fluid_fields()
    # A flat pigment field, so what shows is the water's own doing and not the
    # noise it was handed.
    dep = paint.shallow_water(wet, np.ones_like(wet), paper, 40, 4, 41, 0.6)
    inside = wet > 0.5
    d = paint.edt(~inside)
    near = inside & (d <= 3)
    deep = inside & (d > 14)
    assert dep[near].mean() > dep[deep].mean() * 1.1
    # And it varies around the shape rather than being one ring: that is the
    # thing a rim of a fixed width cannot do.
    band = dep[12:84, 16:19].mean(axis=1)
    assert band.std() / max(band.mean(), 1e-6) > 0.15


def test_the_fluid_pass_modulates_the_washes_and_never_becomes_them():
    """The rule the pass is held to: a failure degrades to today's plate."""
    wet, _, _ = fluid_fields()
    sheet = paint.Sheet(96, 128, gran_px=8.0, seed=5)
    style = paint.PaintStyle(fluid_pass=True)
    before = paint.wash(wet, sheet, 0.55, 0.22, rim_px=7.0)
    layers = [(before.copy(), paint.rgb(paint.PIGMENTS["wood"]), 0.05)]
    after = paint.fluid_modulate(layers, wet, sheet, style)[0][0]
    body = wet > 0.5
    assert after.min() >= 0.0 and after.max() <= 1.0
    a = after[body] - after[body].mean()
    b = before[body] - before[body].mean()
    assert float((a * b).mean() / (a.std() * b.std())) > 0.8, "still the same wash"
    assert not np.allclose(after[body], before[body]), "but it has been worked"
    # Dry paper is dry paper: away from the wet area nothing is touched at all.
    dry = paint.edt(body) > 8
    assert np.array_equal(after[dry], before[dry])


def test_a_sheet_with_nothing_wet_on_it_comes_back_untouched():
    """A pass that has nothing to do hands the plate straight back."""
    sheet = paint.Sheet(64, 64, gran_px=8.0, seed=5)
    layers = [(np.zeros((64, 64), np.float32), paint.rgb(paint.PIGMENTS["wood"]))]
    same = paint.fluid_modulate(
        layers, np.zeros((64, 64), np.float32), sheet, paint.PaintStyle(fluid_pass=True)
    )
    assert same is layers


# ------------------------------------------------------------------ phase 2: tuning and sea


def test_every_phase_two_tuning_field_is_inert_by_default():
    """A field added here must not move a plate until a theme asks for it."""
    style = paint.PaintStyle()
    assert style.bloom_strength == 1.0
    assert style.wet_close_px == 0.0
    assert not style.sea_variation


def _sea_cover(h: int = 160, w: int = 220) -> np.ndarray:
    """A coast running down the card, sea to the left of it."""
    cov = np.zeros((h, w), np.float32)
    for r in range(h):
        cov[r, : 90 + int(12 * math.sin(r / 22.0))] = 1.0
    return cov


def test_the_sea_dries_in_broad_patches_rather_than_flat():
    """The largest wash on the card stops reading as a fill."""
    cov = _sea_cover()
    sheet = paint.Sheet(*cov.shape, gran_px=8.0, seed=5)
    style = paint.PaintStyle(sea_variation=True)
    flat = paint.wash(cov, sheet, 0.60, 0.34, rim_px=7.0)
    varied = paint.sea_patches(flat, cov, 3.0, style)
    body = cov > 0.5
    assert varied.min() >= 0.0 and varied.max() <= 1.0
    # Broader variation than the wash had, and still the same sea.
    coarse = paint.blur(varied, 24.0)[body].std() / paint.blur(flat, 24.0)[body].std()
    assert coarse > 1.5
    assert abs(float(varied[body].mean() - flat[body].mean())) < 0.06
    # Deterministic: the same card paints the same sea every time.
    assert np.array_equal(varied, paint.sea_patches(flat, cov, 3.0, style))
    # And the amount is the dial: at 0 the wash comes back untouched.
    off = paint.PaintStyle(sea_variation=True, sea_variation_amount=0.0)
    assert paint.sea_patches(flat, cov, 3.0, off) is flat


def test_the_streaking_runs_along_the_coast_not_across_it():
    """The direction is read off the shore, not chosen in advance."""
    cov = _sea_cover()
    angle = paint.coast_run(paint.edt(cov <= 0.5), cov > 0.5, 40.0)
    # The shore runs down the card, so the run of it is about a quarter turn.
    assert abs(abs(angle) - math.pi / 2) < 0.35
    turned = paint.coast_run(paint.edt(cov.T <= 0.5), cov.T > 0.5, 40.0)
    assert abs(turned) < 0.35  # the same coast laid the other way


def test_closing_the_cover_puts_the_class_seams_under_water():
    """The wet map's whole point: two washes that meet, meet wet.

    The classes do not abut, they meet along hairlines of unmapped ground, so
    the union taken as it stands leaves every seam dry however wide the bleed
    is set. Closing over the gap is what reaches them, and the land's outer
    silhouette is the one edge that has to survive it.
    """
    h, w = 120, 200
    label = np.zeros((h, w), np.uint8)
    label[20:100, 20:108] = 1
    label[20:100, 110:180] = 2  # a two pixel hairline between the two classes
    seam = np.zeros((h, w), bool)
    seam[20:100, 106:112] = True
    raw = paint.smoothstep(paint.edt(label == 0) - np.float32(12.0), 12.0)
    gap = np.float32(5.0)
    closed_dry = ~(paint.edt(~(paint.edt(label > 0) <= gap)) > gap)
    closed = paint.smoothstep(paint.edt(closed_dry) - np.float32(12.0), 12.0)
    assert float(raw[seam].mean()) < 0.05
    assert float(closed[seam].mean()) > 0.5
    # The outer silhouette keeps its dry margin: the close only fills gaps.
    outside = paint.edt(label > 0) > 2.0
    assert not closed_dry[label > 0].any()
    assert closed_dry[outside].all()


# --------------------------------------------------------------------------- labels


def test_the_manifest_keeps_the_lines_a_name_can_be_set_along(tmp_path):
    """Named roads and watercourses survive the paint; unnamed ones do not.

    The geo payload is transient and re-deriving it at label time costs seven
    seconds and a network the renderer must not need, so the centrelines a
    curved baseline is taken from are kept beside the plates.
    """
    payload = tiny_payload(
        roads=[
            {
                "c": "major",
                "b": "major",
                "k": "primary",
                "n": "A39",
                "d": geo.path_d([(0.0, 0.0), (300.0, 4.0), (600.0, 0.0)]),
            },
            {
                "c": "minor",
                "b": "minor",
                "k": "unclassified",
                "n": "",
                "d": geo.path_d([(0.0, 90.0), (600.0, 90.0)]),
            },
        ],
        rivers=[
            {
                "c": "major",
                "n": "River Lyn",
                "d": geo.path_d([(0.0, 40.0), (400.0, 44.0), (800.0, 40.0)]),
            }
        ],
        coastline=[geo.path_d([(0.0, 10.0), (900.0, 12.0)])],
    )
    manifest = paint.paint(payload, tiny_style(), tmp_path)
    geom = manifest["label_geom"]
    assert [r["n"] for r in geom["roads"]] == ["A39"]
    assert [r["n"] for r in geom["rivers"]] == ["River Lyn"]
    assert len(geom["coast"]) == 1
    assert all(len(line["d"]) >= 2 for line in geom["roads"] + geom["rivers"])


def test_the_labels_hash_moves_when_the_picks_do(tmp_path):
    """A plate lettered from yesterday's picks must be tellable from today's.

    `paint_hash` cannot see the picks: they live in the analysis payload, not
    the geo payload. So the labels carry their own key.
    """
    style = tiny_style()
    one = [{"name": "The old kiln", "x": 100.0, "y": 40.0}]
    two = [{"name": "The new kiln", "x": 100.0, "y": 40.0}]
    assert paint.labels_hash(one, style) == paint.labels_hash(list(one), style)
    assert paint.labels_hash(one, style) != paint.labels_hash(two, style)
    assert paint.labels_hash(one, style) != paint.labels_hash(one, tiny_style(label_seed=2))
    manifest = paint.paint(tiny_payload(), style, tmp_path, labels=one)
    assert manifest["labels_hash"] == paint.labels_hash(one, style)


def _labelled_card(tmp_path, **payload_over):
    """A painted tiny box and the card that projects into it, for the label rules."""
    from pyntpot._port.card import _Card

    manifest = paint.paint(tiny_payload(**payload_over), tiny_style(), tmp_path)
    card = _Card(manifest)
    route = [(float(x), 40.0 + 30.0 * math.sin(x / 260.0)) for x in range(0, 1400, 40)]
    return manifest, card, [card.xy(x, y) for x, y in route]


def _place_node(name, kind, x, y, off):
    """One settlement as `journal_candidates` writes it into the manifest."""
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


def test_upper_and_lower_are_one_place_under_their_shared_stem(tmp_path):
    """A reader says Grasmere; OSM has two nodes and neither is called that."""
    from pyntpot._port import labels as lb

    manifest, card, route_px = _labelled_card(
        tmp_path,
        candidates=[
            _place_node("Upper Grasmere", "village", 200.0, 44.0, 241),
            _place_node("Lower Grasmere", "village", 340.0, 40.0, 70),
        ],
    )
    found = lb.settlements(manifest)
    assert [e["name"] for e in found] == ["Grasmere"]
    # Positioned on the member the route actually came nearest.
    assert found[0]["off_route_m"] == 70


def test_the_settlements_are_chosen_by_rank_and_by_route_not_by_distance(tmp_path):
    """A distance sort spends every slot inside one town. This one does not."""
    from pyntpot._port import labels as lb

    manifest, card, route_px = _labelled_card(
        tmp_path,
        candidates=[
            _place_node("Little Combes", "hamlet", 100.0, 42.0, 4),
            _place_node("Tarns Bridge", "hamlet", 180.0, 44.0, 18),
            _place_node("Abergavenny", "town", 600.0, 45.0, 3),
            _place_node("Monmouth", "town", 1100.0, 20.0, 441),
            _place_node("Faraway", "village", 700.0, 60.0, 4000),
        ],
    )
    picked = [lb.name for lb in lb.pick_settlements(manifest, card, route_px)]
    assert "Abergavenny" in picked and "Monmouth" in picked
    assert "Faraway" not in picked, "over 1.5 km off the route is not this ride"
    assert len(picked) <= lb.settlement_budget(card.w)


def test_a_hamlet_alone_in_empty_country_is_not_worth_a_name(tmp_path):
    """A floor, so a run through nowhere gets one label or none, not three."""
    from pyntpot._port import labels as lb

    manifest, card, route_px = _labelled_card(
        tmp_path,
        candidates=[
            _place_node("Brendon", "hamlet", 300.0, 44.0, 700),
        ],
    )
    assert lb.pick_settlements(manifest, card, route_px) == []


def test_the_river_the_route_crossed_beats_the_one_it_did_not(tmp_path):
    """Run length alone cannot separate two tributaries; the route can."""
    from pyntpot._port import labels as lb

    crossed = [[float(x), 40.0 + 30.0 * math.sin(x / 260.0)] for x in range(0, 1400, 40)]
    away = [[float(x), 900.0] for x in range(0, 1400, 40)]
    manifest, card, route_px = _labelled_card(tmp_path)
    manifest["label_geom"] = {
        "roads": [],
        "coast": [],
        "rivers": [
            {"n": "River Heddon", "c": "medium", "d": crossed},
            {"n": "River Medway", "c": "medium", "d": away},
            {"n": "Hebden Beck", "c": "minor", "d": crossed},
        ],
    }
    named = [x.name for x in lb.pick_rivers(manifest, card, route_px)]
    assert named[0] == "Heddon", "the name loses its 'River', the water says it"
    assert "Hebden Beck" not in named, "a beck is noise at this scale"


def test_home_is_untouched_by_the_new_keys():
    """`Home` has a symbol, no kind and no always_label, and draws as it always did."""
    entries = [{"name": "Home", "symbol": "house", "lat": 51.2255, "lng": -3.835}]
    assert entries[0]["name"] == "Home"
    marks = geo._place_marks(
        entries,
        geo.Projection(
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
    out = paint.deform_line(line, rng, 0.06, 4, 0.62, 6.0, 1.0)
    assert len(out) > len(line)
    assert tuple(out[0]) == (0.0, 0.0)
    assert tuple(out[-1]) == (80.0, 0.0)
    assert abs(out[:, 1]).max() > 0.0, "the line did not move at all"
    assert abs(out[:, 1]).max() <= 6.0
    # Seeded, so the same leader is the same curve on every render.
    again = paint.deform_line(line, np.random.default_rng(3), 0.06, 4, 0.62, 6.0, 1.0)
    assert np.allclose(out, again)


def test_a_plate_can_carry_its_own_colour_and_its_own_alpha(tmp_path):
    """Multiply can only darken; a backing wash in the paper's colour lightens."""
    from PIL import Image

    rgb = np.zeros((4, 6, 3), np.float32)
    rgb[..., 0] = 1.0
    alpha = np.linspace(0.0, 1.0, 24, dtype=np.float32).reshape(4, 6)
    path = tmp_path / "labels.webp"
    assert paint.save_rgba(rgb, alpha, path) > 0
    back = Image.open(path).convert("RGBA")
    assert back.size == (6, 4)
    assert back.getchannel("A").getextrema()[0] == 0


# ----------------------------------------------------------------- letterforms


def test_the_face_measures_a_name_instead_of_counting_its_characters():
    """The flat eight pixels a character is what every placement fault came from.

    A real face knows that `Abergavenny` and `Wllllllllll` are not the same
    width, and the default cannot: it counts characters. This is the change
    that moves every label on the sheet.
    """
    from pyntpot._port import labels as lb
    from pyntpot._port import outlinefont, paint

    hand = lb.Hand(paint.PaintStyle())
    assert isinstance(hand.font, outlinefont.OutlineFont)
    narrow = hand.measure("iiiiiiiiiii", 20.0)[0]
    wide = hand.measure("WWWWWWWWWWW", 20.0)[0]
    assert wide > narrow * 1.8, "the face is not measuring, it is counting"
    assert lb.measure("iiiiiiiiiii", 20.0) == lb.measure("WWWWWWWWWWW", 20.0)


def test_both_letterform_routes_draw_every_glyph_of_a_name():
    """Centreline and outline are two answers, and neither drops a letter.

    Thinning is the risk in the whole module, so the outline contour is not a
    fallback that sits unused: it is drawn on its own merits and it is tested
    on the same string.
    """
    from pyntpot._port import outlinefont as of

    for route in (of.CENTRELINE, of.OUTLINE):
        face = of.load(route=route)
        for ch in "Abergavenny 12%":
            glyph = face.glyph(ch)
            assert glyph.advance > 0
            assert glyph.ink or ch == " ", f"{ch!r} came back blank on {route}"
            for path in glyph.paths:
                assert len(path) >= 2


def test_a_name_is_never_set_along_a_line_that_turns_too_far():
    """Curved baselines for linear things, and only where they stay readable.

    Total turning across the run is the test that matters, not curvature at a
    point: a river bend reads, a switchback does not, and the difference
    between elegant and unreadable is this one rule.
    """
    import math

    from pyntpot._port import labels as lb
    from pyntpot._port import paint

    hand = lb.Hand(paint.PaintStyle())
    straight = [(float(x), 100.0 + 4.0 * math.sin(x / 90.0)) for x in range(0, 400, 8)]
    hairpin = [
        (100.0 + 40.0 * math.cos(a / 9.0), 100.0 + 40.0 * math.sin(a / 9.0)) for a in range(0, 80)
    ]
    gentle = lb.Label(name="Heddon", kind="river", px=200.0, py=100.0, size=14.0, baseline=straight)
    tight = lb.Label(name="Heddon", kind="river", px=100.0, py=100.0, size=14.0, baseline=hairpin)
    assert hand._baseline(gentle, hand.font.measure("Heddon", 14.0)[0])
    assert hand._baseline(tight, hand.font.measure("Heddon", 14.0)[0]) is None


def test_the_label_plate_carries_its_own_colour_and_its_own_alpha(tmp_path):
    """The plate is composited normally, so it can lighten as well as darken.

    A backing wash in the paper's own colour is the whole reason it is not on
    the wash plate: multiply can only darken, and a white wash multiplied over
    the card does nothing at all.
    """
    from PIL import Image

    from pyntpot._port import labels as lb
    from pyntpot._port import paint

    manifest = paint.paint(tiny_payload(), tiny_style(), tmp_path)
    manifest["dir"] = str(tmp_path)
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
    plate = lb.draw_plate(manifest, placed, [], [(10.0, 10.0), (70.0, 40.0)], tiny_style())
    assert plate is not None and plate.exists()
    img = Image.open(plate)
    assert img.mode == "RGBA"
    assert img.size == tuple(manifest["render"])
    assert img.getchannel("A").getextrema()[1] > 0, "nothing was written"
    # And it is cached on what is lettered, so a second call writes nothing new.
    stamp = plate.stat().st_mtime_ns
    assert lb.draw_plate(manifest, placed, [], [(10.0, 10.0), (70.0, 40.0)], tiny_style()) == plate
    assert plate.stat().st_mtime_ns == stamp


# ------------------------------------------------------ the encoder and the ramp


def _ramp_plate(h: int = 96, w: int = 96) -> np.ndarray:
    """A card carrying narrow coloured marks on a grainy ground.

    Three or four pixels wide, drawn at an angle, on paper with fine noise on
    it: the plate the lossy encoder is worst at and the one the painter writes.
    """
    rng = np.random.default_rng(3)
    arr = np.full((h, w, 3), 0.93, np.float32)
    arr -= rng.random((h, w, 1)).astype(np.float32) * 0.03
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    for x0, pig in ((22.0, (0.42, 0.24, 0.13)), (58.0, (0.15, 0.36, 0.50))):
        d = np.abs(xx - (x0 + yy * 0.32))
        cov = np.clip(1.0 - d / 1.9, 0.0, 1.0) ** 0.8
        arr *= 1.0 - cov[..., None] * (1.0 - np.array(pig, np.float32))
    return np.clip(arr, 0.0, 1.0)


def _plateau_share(arr: np.ndarray) -> float:
    """Share of steps across the marks that do not move at all.

    The fault, as a number: a ramp that is two
    flats and a jump spends most of its width not changing, and a continuous
    one moves at nearly every pixel.
    """
    got = []
    grey = arr.mean(axis=2)
    for r in range(8, arr.shape[0] - 8):
        for c in (22, 58):
            x0 = int(c + r * 0.32)
            seg = grey[r, max(x0 - 5, 0) : x0 + 6]
            if seg.size > 6:
                got.append(float((np.abs(np.diff(np.round(seg * 255))) < 1).mean()))
    return float(np.mean(got))


def _grain(arr: np.ndarray) -> float:
    """High-frequency energy: what is left of the paper after a 3 by 3 mean."""
    a = arr.mean(axis=2)
    k = (a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:] + a[1:-1, 1:-1]) / 5.0
    return float(np.abs(a[1:-1, 1:-1] - k).mean())


def test_the_lossy_encoder_is_what_flattens_a_narrow_strokes_ramp(tmp_path):
    """The two plateaus and the step between them are the encoder, not the paint.

    A mark under four pixels wide is narrower than the 4 by 4 block the lossy
    encoder transforms in and than the half resolution chroma plane it carries,
    so its edge-to-centre ramp comes back as a light flat, a jump and a dark
    flat. Lossless returns the ramp the painter composed, exactly.
    """
    from PIL import Image

    truth = _ramp_plate()
    img = paint.to_img(truth, np.random.default_rng(23))
    ref = np.asarray(img, np.float32) / 255.0

    lossy = tmp_path / "lossy.webp"
    clean = tmp_path / "clean.webp"
    n_lossy = paint.save_webp(img, lossy, quality=74)
    n_clean = paint.save_webp(img, clean, quality=74, lossless=True)
    back_lossy = np.asarray(Image.open(lossy).convert("RGB"), np.float32) / 255.0
    back_clean = np.asarray(Image.open(clean).convert("RGB"), np.float32) / 255.0

    assert np.array_equal(back_clean, ref)  # exactly what was composed
    assert np.abs(back_lossy - ref).max() > 0.02  # and the lossy one is not
    # The fault itself: flats across the mark, and the paper's grain gone.
    assert _plateau_share(back_lossy) > _plateau_share(back_clean) * 1.4
    assert _grain(back_lossy) < _grain(back_clean) * 0.75
    assert n_clean > n_lossy  # which is what it costs


def test_the_style_decides_how_the_plates_are_written(tmp_path):
    """Lossless is the default, and turning it off is the old encoder back."""
    from PIL import Image

    assert paint.PaintStyle().plate_lossless

    style, payload = smoke_box(plate_lossless=False)
    lossy = paint.paint(payload, style, tmp_path / "lossy")
    style, payload = smoke_box()
    clean = paint.paint(payload, style, tmp_path / "clean")
    assert clean["bytes"] > lossy["bytes"]

    # The pen plate is alpha, which WebP already stored losslessly, so the flag
    # only tidies the flat white beside it and the plate does not grow.
    assert clean["sizes"]["pen"] <= lossy["sizes"]["pen"]
    for name in ("paper", "wash"):
        assert clean["sizes"][name] > lossy["sizes"][name] * 4

    with Image.open(tmp_path / "clean" / clean["files"]["wash"]) as got:
        assert got.size == tuple(payload["render"])


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
        label = lb._span_label(span, [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)], 14.0, lb.measure)
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
    got = lb.place([river, later], [], card, [(0.0, 290.0), (400.0, 290.0)], _flat_dark(), [])
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
    lb.place([free], [], card, route, _flat_dark(), [], None, [])
    # A road laid straight down the middle of the box the placer just chose.
    x0, y0, x1, y1 = free.box
    road = [[((x0 + x1) / 2, 0.0), ((x0 + x1) / 2, 300.0)]]
    assert lb._crossings(free.box, road) > 0

    moved = lb.Label(name="Castle", kind="monument", px=200.0, py=150.0, size=14.0)
    lb.place([moved], [], card, route, _flat_dark(), [], None, road)
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
    manifest = {
        "label_geom": {
            "rivers": [
                {"n": "River Lyn", "c": "major", "d": big},
                {"n": "Heddon", "c": "medium", "d": small},
            ]
        }
    }

    class _Card:
        w, h, scale = 400.0, 300.0, 0.1

        @staticmethod
        def xy(x, y):
            """Metres to card pixels, at a tenth of a pixel a metre."""
            return (x * 0.1, y * 0.1 + 40.0)

    route = [(float(x), 60.0) for x in range(0, 400, 10)]
    got = lb.pick_rivers(manifest, _Card(), route)
    names = [label.name for label in got]
    assert names.count("Lyn") == lb.MAJOR_RIVER_LABELS == 2
    assert names.count("Heddon") == 1
    a, b = [label for label in got if label.name == "Lyn"]
    apart = math.dist((a.px, a.py), (b.px, b.py))
    assert apart > lb._run(a.baseline) * lb.RIVER_REPEAT_FRAC * 0.9


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
    assert math.dist(line[0], line[-1]) > 0.33 * lb._run(line)
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
        assert lb.place_spans([span], card, route, _flat_dark(), cap_px=14.0)
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
        placed = lb.place_spans([span], card, route, _flat_dark(), cap_px=14.0)
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
    assert lb._run(line) > 2.0 * 20.0, "the doubled-back stretch drew no mark"
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
    assert lb._run(line) < 0.4 * lb._run(route)
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
    assert lb.place_spans([span], card, route, _flat_dark(), cap_px=14.0)
    gaps = [lb._foot_on(p, route)[0] for p in span.line]
    # It stands off the route the whole way, and it does not hold one distance.
    assert min(gaps) >= 14.0 * lb.SPAN_CLEAR_CAPS
    assert max(gaps) - min(gaps) > 0.25 * span.offset_px, (
        f"the mark holds its distance: {min(gaps):.1f} to {max(gaps):.1f}"
    )
    # It has the corner in it, and it has only a few turns in all.
    assert 1 <= _corners(span.line) <= 6, f"{_corners(span.line)} turns is not a few strokes"
    assert _corners(span.line) >= _corners(geo.simplify(route, 3.0)) - 2


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
    assert lb.place_spans([span], card, route, _flat_dark(), cap_px=14.0)
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
        placed = lb.place_spans([span], card, route, _flat_dark(), cap_px=14.0)
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
        assert lb.place_spans([span], card, route, _flat_dark(), cap_px=14.0, lines=lines)
        out.append(sum(y for _, y in span.line) / len(span.line))
    assert south[0] > 150.0, "the mark stayed on the water"
    # And the river only tips a choice: it is not allowed to lose the mark.
    span = lb.Span(name="the lane", kind="climb", i0=0, i1=59)
    both = [[(60.0 + i * 4.0, 150.0 + s) for i in range(60)] for s in (-20.0, 20.0)]
    assert lb.place_spans([span], card, route, _flat_dark(), cap_px=14.0, lines=both), (
        "water on both sides lost the mark"
    )


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
    assert lb.place_spans([span], card, route, _flat_dark(), cap_px=14.0)
    assert len(span.ticks) == 2
    clear = 14.0 * lb.SPAN_CLEAR_CAPS
    for tick in span.ticks:
        assert lb.clear_of_route(tick, route, clear)
        assert lb._run(tick) > 0.0


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
    return max(len(geo.simplify(pts, tol)) - 2, 0)


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
    paint.save_rgba(rgb, alpha, clean)
    paint.save_rgba(rgb, alpha, lossy, lossless=False)
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
    manifest = {
        "label_geom": {
            "roads": [
                {"n": "Lyn Valley Road", "c": "major", "r": "A361", "d": numbered},
                {"n": "Aviemore Road", "c": "major", "r": "", "d": unnumbered},
            ]
        }
    }

    class _Card:
        w, h, scale = 400.0, 300.0, 0.1

        @staticmethod
        def xy(x, y):
            """Metres to card pixels, at a tenth of a pixel a metre."""
            return (x * 0.1, y * 0.1 + 40.0)

    route = [(float(x), 45.0) for x in range(0, 400, 10)]
    got = lb.pick_roads(manifest, _Card(), route, budget=2)
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
    lb.place([river], [], card, [(0.0, 295.0), (400.0, 295.0)], _flat_dark(), [])
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
    lb.place([road], [], card, [(0.0, 295.0), (400.0, 295.0)], _flat_dark(), [])
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

    wide, tall = lb.block_size(["the long climb", "out of Aviemore"], 14.0, lb.measure)
    one_wide, one_tall = lb.block_size(["the long climb out of Aviemore"], 14.0, lb.measure)
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
    lb.place([span], [], card, route, {"w": 2, "h": 2, "v": [[0.0, 0.0], [0.0, 0.0]]}, [])
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
    wide, tall = lb.block_size(name.lines, name.size, lb.measure)
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
    lb.place([river, second], [], card, [(0.0, 295.0), (400.0, 295.0)], _flat_dark(), [])
    assert river.window and second.window, "the second name lost its water"
    # Far apart along the water, and that is what the guard measures.
    assert math.dist((river.tx, river.ty), (second.tx, second.ty)) > 20.0


def test_the_hand_writes_both_lines_of_a_wrapped_name():
    """The placer reserving two lines is only half of it; the hand has to write them."""
    from pyntpot._port import labels as lb
    from pyntpot._port import paint

    pstyle = paint.PaintStyle()
    try:
        hand = lb.Hand(pstyle)
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
    marks_one = [m for m in hand._label_marks(one) if m.role == "glyph"]
    marks_two = [m for m in hand._label_marks(two) if m.role == "glyph"]
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


#: What each letter's own skeleton is made of: how many free ends it has, how
#: many junctions, and how many separate pieces of ink the glyph is drawn from.
#: An `H` is two stems and a crossbar, so four ends and two junctions; an `M`
#: is two stems and a bowl joining them, so the same four ends and two
#: junctions; an `i` is one stem and its tittle, so two ends, no junction and
#: two pieces. A test that only asked whether some strokes came back is what
#: let the card read `Honmouth` twice: the M's bowl was there, it had simply
#: lost its arms into the stems. These counts are the shape of the letter and
#: nothing else agrees with them by accident.
GLYPH_TOPOLOGY = {
    "A": (2, 2, 1),
    "B": (0, 2, 1),
    "C": (2, 0, 1),
    "D": (1, 1, 1),
    "E": (3, 1, 1),
    "F": (4, 2, 1),
    "G": (3, 1, 1),
    "H": (4, 2, 1),
    "I": (2, 0, 1),
    "J": (2, 0, 1),
    "K": (4, 2, 1),
    "L": (2, 0, 1),
    "M": (4, 2, 1),
    "N": (4, 2, 1),
    "O": (0, 0, 1),
    "P": (1, 1, 1),
    "Q": (2, 2, 1),
    "R": (2, 2, 1),
    "S": (2, 0, 1),
    "T": (3, 1, 1),
    "U": (2, 0, 1),
    "V": (3, 1, 1),
    "W": (5, 3, 1),
    "X": (4, 2, 1),
    "Y": (3, 1, 1),
    "Z": (4, 2, 1),
    "a": (1, 1, 1),
    "b": (1, 1, 1),
    "c": (2, 0, 1),
    "d": (2, 2, 1),
    "e": (1, 1, 1),
    "f": (4, 1, 1),
    "g": (1, 1, 1),
    "h": (3, 1, 1),
    "i": (2, 0, 2),
    "j": (2, 0, 2),
    "k": (4, 2, 1),
    "l": (2, 0, 1),
    "m": (3, 1, 1),
    "n": (3, 1, 1),
    "o": (0, 0, 1),
    "p": (2, 2, 1),
    "q": (1, 1, 1),
    "r": (3, 1, 1),
    "s": (2, 0, 1),
    "t": (4, 2, 1),
    "u": (3, 1, 1),
    "v": (3, 1, 1),
    "w": (3, 1, 1),
    "x": (4, 2, 1),
    "y": (3, 1, 1),
    "z": (2, 0, 1),
    "0": (0, 0, 1),
    "1": (2, 0, 1),
    "2": (2, 0, 1),
    "3": (3, 1, 1),
    "4": (3, 1, 1),
    "5": (2, 0, 1),
    "6": (1, 1, 1),
    "7": (4, 2, 1),
    "8": (0, 2, 1),
    "9": (1, 1, 1),
    "-": (2, 0, 1),
    "'": (2, 0, 1),
    ".": (0, 0, 1),
}


#: Every string this map actually letters, so the alphabet sheet and the tests
#: cover the same ground the card does.
MAP_STRINGS = (
    "Monmouth",
    "Monmouth Castle",
    "Abergavenny",
    "Grasmere",
    "Lyn",
    "Heddon",
    "A361",
    "A3052",
    "the long climb out of Aviemore",
    "the A39 drag to St Anne's Cross",
)


def _glyph_bitmaps(ch):
    """One glyph's filled bitmap, its thinned skeleton and the fill's origin."""
    from pyntpot._port import outlinefont as of

    face = of.load()
    name = face._name_of(ch)
    rec = face._pen_cls(face._glyphs)
    face._glyphs[name].draw(rec)
    flat = of._Flatten()
    rec.replay(flat)
    img, ox, oy = of._fill(flat.contours, face.upem)
    return face, img, of.thin(img), ox, oy


def _raster(face, ch, ox, oy):
    """One glyph's drawn paths, back in the raster the fill was made on."""
    from pyntpot._port import outlinefont as of

    k = of.RASTER_EM / face.upem
    return [
        [((x * face.upem - ox) * k, (y * face.upem - oy) * k) for x, y in path]
        for path in face.glyph(ch).paths
    ]


def test_every_letter_the_map_writes_has_the_topology_that_letter_should_have():
    """The skeleton of each glyph is counted, not merely produced.

    Free ends, junctions and separate pieces of ink. A test that asked only
    whether some strokes came back passed on a card that read Honmouth twice.
    """
    import numpy as np

    from pyntpot._port import outlinefont as of

    wrong = []
    for ch, want in GLYPH_TOPOLOGY.items():
        _face, img, skel, _ox, _oy = _glyph_bitmaps(ch)
        on = {(int(r), int(c)) for r, c in zip(*np.nonzero(skel), strict=True)}
        cross = {p: of._crossings(p, on) for p in on}
        got = (
            sum(1 for p in on if cross[p] == 1),
            sum(1 for p in on if cross[p] >= 3),
            len(of._components(img)),
        )
        if got != want:
            wrong.append(f"{ch!r}: wanted ends/junctions/pieces {want}, got {got}")
    assert not wrong, "; ".join(wrong)


def test_no_piece_of_a_letter_is_left_undrawn():
    """A blob of ink with no stroke through it is a letter missing a part.

    Zhang-Suen deletes a small round component from both sides at once and
    leaves nothing at all, which is how the tittle of an `i`, the tittle of a
    `j` and the whole of a full stop went missing from the card.
    """
    from pyntpot._port import outlinefont as of

    missed = []
    for ch in GLYPH_TOPOLOGY:
        face, img, _skel, ox, oy = _glyph_bitmaps(ch)
        drawn = [p for path in _raster(face, ch, ox, oy) for p in path]
        for blob in of._components(img):
            rows = [r for r, _c in blob]
            cols = [c for _r, c in blob]
            near = any(
                min(cols) - 2 <= x <= max(cols) + 2 and min(rows) - 2 <= y <= max(rows) + 2
                for x, y in drawn
            )
            if not near:
                missed.append(f"{ch!r} has a piece of ink nothing is drawn through")
    assert not missed, "; ".join(missed)


def test_no_stroke_of_a_letter_is_drawn_outside_its_own_ink():
    """A pen that leaves the letter has been thrown there, not written.

    The end of a chain used to be pushed out by the inscribed disc whether it
    was a free end or a junction, and at a junction that disc is as wide as
    every stroke meeting in it: the M and the W each grew a star.
    """
    stray = []
    for ch in GLYPH_TOPOLOGY:
        face, img, _skel, ox, oy = _glyph_bitmaps(ch)
        h, w = img.shape
        for path in _raster(face, ch, ox, oy):
            for x, y in path:
                c, r = int(round(x)), int(round(y))
                inside = (
                    0 <= r < h
                    and 0 <= c < w
                    and img[max(r - 2, 0) : r + 3, max(c - 2, 0) : c + 3].any()
                )
                if not inside:
                    stray.append(f"{ch!r} draws at ({c}, {r}), outside its own ink")
                    break
    assert not stray, "; ".join(stray[:6])


def _inner_edge(ch, frac, tol=0.05):
    """How far in from the left the letter's own ink reaches, at one height.

    Measured as a share of the letter's width, over the ink in the left half
    only, so it is the inside face of the left-hand stroke: the boundary of
    the white the reader sees inside the letter.
    """
    from pyntpot._port import outlinefont as of

    paths = of.load().glyph(ch).paths
    pts = [p for path in paths for p in path]
    lo, hi = min(x for x, _y in pts), max(x for x, _y in pts)
    cap = max(y for _x, y in pts)
    band = [
        (x - lo) / (hi - lo)
        for x, y in pts
        if abs(y / cap - frac) <= tol and (x - lo) / (hi - lo) < 0.5
    ]
    return max(band) if band else 0.0


def test_the_capital_m_is_not_written_as_an_h():
    """Monmouth, twice on one card, read Honmouth. This is that fault.

    Patrick Hand's M carries its bowl's arms into the stems from about half
    the cap height upwards, so the ink there is one mass and its medial axis
    is one line: thinning handed back two full stems joined by a shallow curve
    sitting exactly where an H's crossbar sits. `_flanks` gives the arms back
    off the width of the mass.

    The two letters are told apart here the way a reader tells them apart, by
    the white inside them. Above the bowl an M's left-hand ink leans inward as
    it climbs, and an H's does not: its stem is a straight edge from the
    crossbar to the cap. Without the arms the M's figure is the H's, which is
    what the reader was seeing.
    """
    m_low, m_high = _inner_edge("M", 0.60), _inner_edge("M", 0.70)
    h_low, h_high = _inner_edge("H", 0.60), _inner_edge("H", 0.70)
    assert m_low > 0.3, "the M has no bowl"
    assert m_high > 0.08, "the M's bowl has no arms: it is an H with a dip"
    assert h_high < 0.06, "the H has grown something above its crossbar"
    assert m_high > h_high * 2.5, "an M and an H are drawn the same"
    assert h_low < 0.2, "the H's crossbar is not a crossbar"


def test_every_name_this_map_letters_comes_back_whole():
    """The real strings, not a sample: every glyph of each has ink and width."""
    from pyntpot._port import outlinefont as of

    face = of.load()
    for text in MAP_STRINGS:
        assert face.measure(text, 20.0)[0] > 0
        for ch in text:
            glyph = face.glyph(ch)
            assert glyph.advance > 0, f"{ch!r} in {text!r} has no advance"
            assert glyph.ink or ch == " ", f"{ch!r} in {text!r} came back blank"


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
    """The label layer sees a centreline; the manifest tells it the brush."""
    from pyntpot._port import labels as lb

    fresh = {"wet_px": {"major": 9.5, "medium": 6.0, "minor": 2.4}}
    # The manifest carries the brush's nominal width and the brush lays down
    # more than that, so what reaches the label layer is the footprint.
    assert lb.feature_px(fresh, "river", "major") == pytest.approx(9.5 * lb.WET_SPREAD)
    # A manifest painted before the key falls back to the painter's defaults
    # rather than to nothing, so an old plate letters its rivers where a new
    # one does.
    assert lb.feature_px({}, "river", "major") == pytest.approx(
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

    manifest = {
        "label_geom": {
            "rivers": [
                {
                    "n": "Severn",
                    "c": "major",
                    "w": width_px,
                    "wn": width_px,
                    "d": [[100, 400], [800, 400]],
                }
            ]
        },
        "wet_px": {"major": 11.0},
    }
    return lb.pick_rivers(manifest, _WideCard(), [(100.0, 100.0), (800.0, 100.0)])[0]


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
    from pyntpot._port import labels as lb
    from pyntpot._port import paint

    hand = lb.hand(paint.PaintStyle())
    assert hand is not None
    assert hand._ink(_river_label(40.0)) == "in_water"
    assert hand._ink(_river_label(11.0)) == "water"


def test_the_in_water_ink_beats_a_dark_one_on_the_river():
    """The water is a mid-tone: a dark ink fights it from the wrong side.

    Measured against the major watercourse's own pigment, which is what the
    letters are written over.
    """
    from pyntpot._port import paint

    style = paint.PaintStyle()
    river = paint.BRUSH_COLOURS["RIV"]["a"]
    assert _contrast(style.label_in_water_ink, river) > _contrast("#0f1216", river)
    assert _contrast(style.label_in_water_ink, river) > 4.5


def test_a_name_on_the_water_asks_for_no_backing_wash():
    """A pale blob on a river reads as a hole in the water."""
    from pyntpot._port import labels as lb
    from pyntpot._port import paint

    hand = lb.hand(paint.PaintStyle())
    wet = hand._label_marks(_river_label(40.0))
    dry = hand._label_marks(_river_label(11.0))
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
    from pyntpot._port import paint

    assert lb.IN_WATER_ROAD_COST > lb.ROAD_CROSS_COST
    hand = lb.hand(paint.PaintStyle())
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
        hand.measure if hand else None,
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

    class _Card:
        w = 900
        h = 671
        scale = 1.0

        @staticmethod
        def xy(x, y):
            return (float(x), float(y))

    def rivers(x1):
        manifest = {
            "label_geom": {
                "rivers": [{"n": "Severn", "c": "major", "w": 30.0, "d": [[100, 400], [x1, 400]]}]
            },
            "wet_px": {"major": 11.0},
        }
        return lb.pick_rivers(manifest, _Card(), [(100.0, 100.0), (800.0, 100.0)])

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

    class _Card:
        w = 400
        h = 300
        scale = 1.0

        @staticmethod
        def xy(x, y):
            return (float(x), float(y))

    manifest = {
        "label_geom": {
            "roads": [{"n": "A361", "c": "major", "d": [[0, 10], [400, 10]]}],
            "rivers": [{"n": "Lyn", "c": "major", "d": [[0, 60], [400, 60]]}],
            "crossings": [[[0, 120], [400, 120]]],
        }
    }
    lines = lb.road_lines(manifest, _Card())
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
    """The manifest carries the brush's nominal width, not its footprint.

    A brush bleeds, smooths and drifts past its own nominal edge, so a
    clearance taken against the nominal width stands the name off less water
    than it has to clear.
    """
    from pyntpot._port import labels as lb

    assert lb.WET_SPREAD > 1.0
    wide = {"wet_px": {"major": 12.0, "medium": 3.0, "minor": 1.0}}
    narrow = {"wet_px": {"major": 4.0, "medium": 3.0, "minor": 1.0}}
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

    manifest = {
        "label_geom": {
            "roads": [
                {"n": "Hollow Lane", "c": "major", "r": "A3052", "d": leg(0, 500, 0)},
                {"n": "Coastguard Road", "c": "major", "r": "A3052", "d": leg(500, 1000, 0)},
                {"n": "New Road", "c": "major", "r": "A3052", "d": leg(1000, 1500, 0)},
            ]
        }
    }

    class _Card:
        w, h, scale = 400.0, 300.0, 0.1

        @staticmethod
        def xy(x, y):
            """Metres to card pixels, at a tenth of a pixel a metre."""
            return (x * 0.1, y * 0.1 + 40.0)

    route = [(float(x), 41.0) for x in range(0, 150, 5)]
    got = lb.pick_roads(manifest, _Card(), route, budget=2)
    assert [label.name for label in got] == ["A3052"]
    # No one leg is long enough on its own; the number is what gathers them.
    assert lb._run(got[0].baseline) > lb.road_min_px(got[0].size)


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
    assert lb._meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is not None
    lb._uncross_leaders(
        [a, b], _FlatCard(), [(0.0, 10.0), (400.0, 10.0)], [(0.0, 10.0), (400.0, 10.0)], _dark(), []
    )
    assert lb._meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is None
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
    assert lb._meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is not None
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
