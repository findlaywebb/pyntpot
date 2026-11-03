"""Tests for keyed generators, and for the painting they decouple item from item."""

import math

import numpy as np

from pyntpot.ink.brush import brush_from_id, ink_aux
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.keyed import keyed_rng, line_key, ring_key, uniform_at
from pyntpot.ink.noise import chamfer_distance
from pyntpot.ink.pad import InkPad
from pyntpot.ink.raster import deform_rings
from pyntpot.ink.sheet import Sheet
from pyntpot.ink.stamp import stamp
from pyntpot.ink.wash import WashOptions, bloom, wash

#: `deform_rings` settings with the displacement on: seed, amount, rounds, decay, cap, stop.
DEFORM = (9, 0.26, 4, 0.55, 16.0, 0.5)


def circle(cx: float, cy: float, r: float, n: int = 96) -> list[tuple[float, float]]:
    """A ring of `n` points round a centre."""
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in a]


def line_at(y: float, x0: float, x1: float, n: int = 300) -> np.ndarray:
    """A straight stroke along one row, in render pixels."""
    return np.stack([np.linspace(x0, x1, n), np.full(n, y)], axis=1)


class TestKeys:
    """What a key is made of, and that it is the same everywhere."""

    def test_the_draws_are_the_pinned_ones(self):
        """The streams are pinned literals, so a platform or numpy change cannot reseed them."""
        assert [float(x) for x in keyed_rng(7, "wood", 3).random(2)] == [
            0.9582453384416164,
            0.9287152343806228,
        ]
        assert [float(x) for x in uniform_at(7, np.arange(3))] == [
            0.07297039858084936,
            0.38982974839127155,
            0.016788294528156167,
        ]

    def test_different_words_give_different_streams(self):
        """A seed, a string or an integer word each change the stream."""
        first = keyed_rng(7, "wood", 3).random()
        assert keyed_rng(8, "wood", 3).random() != first
        assert keyed_rng(7, "lake", 3).random() != first
        assert keyed_rng(7, "wood", 4).random() != first

    def test_a_line_is_named_by_its_points_rounded_to_the_grid(self):
        """A shift inside the grid or a finer sampling keeps the key; moving a cell changes it."""
        line = line_at(20.0, 10.0, 90.0, 40)
        assert line_key(line + 0.01, 1.0) == line_key(line, 1.0)
        assert line_key(line_at(20.0, 10.0, 90.0, 97), 1.0) == line_key(line, 1.0)
        assert line_key(line + 3.0, 1.0) != line_key(line, 1.0)
        assert line_key(line[:-3], 1.0) != line_key(line, 1.0)
        bent = line.copy()
        bent[20, 1] += 9.0
        assert line_key(bent, 1.0) != line_key(line, 1.0)
        assert line_key(np.zeros((0, 2)), 1.0) == (0, 0)

    def test_a_draw_at_an_index_does_not_depend_on_the_others(self):
        """Drawing a field at fewer or reordered indices gives each index the same draw."""
        idx = np.arange(5000)
        whole = uniform_at(3, idx)
        assert np.array_equal(uniform_at(3, idx[::-7]), whole[::-7])
        assert float(whole.min()) > 0.0 and float(whole.max()) < 1.0
        assert abs(float(whole.mean()) - 0.5) < 0.02


class TestRingKeys:
    """What names a closed ring: its centroid and root area, not where it starts."""

    def test_a_ring_is_named_by_what_it_encloses(self):
        """Closing it, starting it elsewhere or resampling an edge keeps the key."""
        square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        key = ring_key(square, 1.0)
        assert key == (1159970523152480690, 3068994725590552575)
        assert ring_key([*square, square[0]], 1.0) == key
        assert ring_key(square[2:] + square[:2], 1.0) == key
        assert ring_key([square[0], (5.0, 0.0), *square[1:]], 1.0) == key

    def test_a_ring_that_moves_or_grows_is_renamed(self):
        """A shift of a cell, a larger ring or the other winding each change the key."""
        ring = np.array(circle(40.0, 30.0, 25.0))
        key = ring_key(ring, 1.0)
        assert ring_key(ring + np.array([3.0, 0.0]), 1.0) != key
        assert ring_key(ring + np.array([0.0, 3.0]), 1.0) != key
        assert ring_key((ring - 40.0) * 1.2 + 40.0, 1.0) != key
        assert ring_key(ring[::-1], 1.0) != key
        assert ring_key(ring + 0.01, 1.0) == key

    def test_a_ring_with_no_area_is_named_by_its_mean(self):
        """Points on one line have no centroid, so the mean names them; nothing is (0, 0)."""
        flat = [(0.0, 5.0), (4.0, 5.0), (8.0, 5.0)]
        assert ring_key(flat, 1.0) == ring_key([(4.0, 5.0), (8.0, 5.0), (0.0, 5.0)], 1.0)
        assert ring_key(flat, 1.0) != ring_key([(0.0, 9.0), (4.0, 9.0), (8.0, 9.0)], 1.0)
        assert ring_key(np.zeros((0, 2)), 1.0) == (0, 0)

    def test_a_small_nudge_renames_a_ring_less_often_than_its_points_would(self):
        """Points nudged by under 0.05 m rename far fewer rings than `line_key` would."""
        rng = np.random.default_rng(0)
        by_ring = by_line = 0
        for _ in range(400):
            n = int(rng.integers(8, 300))
            angle = np.sort(rng.uniform(0.0, 2 * math.pi, n))
            radius = rng.uniform(20.0, 800.0) * (1 + 0.3 * rng.uniform(-1, 1, n))
            ring = np.stack(
                [
                    rng.uniform(-5e3, 5e3) + radius * np.cos(angle),
                    rng.uniform(-5e3, 5e3) + radius * np.sin(angle),
                ],
                axis=1,
            )
            ring = np.vstack([ring, ring[:1]])
            nudged = ring + rng.uniform(-0.05, 0.05, ring.shape)
            nudged[-1] = nudged[0]
            by_ring += ring_key(ring, 1.0) != ring_key(nudged, 1.0)
            by_line += line_key(ring, 1.0) != line_key(nudged, 1.0)
        assert by_ring < 30
        assert by_ring * 4 < by_line


class TestDecoupled:
    """A change to one item moves only that item's pixels."""

    def test_a_stroke_that_changes_moves_no_other_stroke(self):
        """Lengthening one stroke, so it draws more, leaves the stroke laid after it as it was."""
        h, w = 90, 400
        style = BrushStyle()
        brush, _ = brush_from_id("MAJ2-a", 3.6, 2.0, style, "road_major")
        sheet = Sheet(h, w, gran_px=9.0, seed=11)

        def laid(first: np.ndarray) -> np.ndarray:
            pad = InkPad((h, w), brush, style)
            pad.lay([(brush, first), (brush, line_at(65.0, 20.0, 380.0))], 91)
            return pad.read(brush, sheet)

        before = laid(line_at(20.0, 20.0, 300.0))
        after = laid(line_at(20.3, 20.0, 340.0, 340))
        assert not np.array_equal(before[:42], after[:42]), "the changed stroke moved"
        # The bleed's blur runs sums across the whole pad, which leaves a last-bit
        # difference everywhere; another bristle pattern differs by tenths.
        assert float(np.abs(before[45:] - after[45:]).max()) < 1e-4

    def test_a_ring_that_changes_moves_no_other_ring(self):
        """A ring moved by a twentieth of a metre leaves the ring deformed after it as it was."""
        rings = [circle(0.0, 0.0, 200.0), circle(900.0, 0.0, 150.0, 80)]
        moved = [[(x + 0.05, y) for x, y in rings[0]], rings[1]]
        before, after = deform_rings(rings, DEFORM), deform_rings(moved, DEFORM)
        assert np.array_equal(before[1], after[1])
        assert not np.array_equal(before[0], after[0])

    def test_an_edge_that_moves_moves_no_bloom_far_from_it(self):
        """Trimming one far edge of a wash leaves the blooms across the rest of it as they were."""
        h, w = 260, 400
        sheet = Sheet(h, w, gran_px=8.0, seed=5)
        a = np.zeros((h, w), np.float32)
        a[20:240, 20:380] = 1.0
        trimmed = a.copy()
        trimmed[20:240, 376:380] = 0.0
        flat = np.full((h, w), 0.5, np.float32)
        before, after = flat.copy(), flat.copy()
        bloom(before, a, sheet, (3, 6, 0.06, 0.45, 0.45))
        bloom(after, trimmed, sheet, (3, 6, 0.06, 0.45, 0.45))
        far = chamfer_distance(trimmed != a) > 60
        assert not np.array_equal(before, flat), "the blooms were laid"
        assert np.array_equal(before[far], after[far])

    def test_a_wash_trimmed_far_off_keeps_its_blooms_with_the_flow_rim_on(self):
        """Through `wash` with the flow rim, a trimmed far edge leaves the far blooms as laid.

        The flow rim's width follows the wash's area and its peak is normalised, so the
        trim moves the density everywhere by a last bit and the bloom radius by a share
        of a pixel. Neither may move a bloom: the blooms' own change far off stays below
        a thousandth, where a resized or reseated bloom differs by tenths.
        """
        h, w = 300, 460
        sheet = Sheet(h, w, gran_px=8.0, seed=5)
        cover = np.zeros((h, w), np.float32)
        cover[30:270, 30:430] = 1.0
        trimmed = cover.copy()
        trimmed[30:270, 426:430] = 0.0

        def lay(c: np.ndarray, blooms: tuple[int, int, float, float, float] | None):
            options = WashOptions(flow=(0.125, 0.02, 0.38), blooms=blooms)
            return wash(c, sheet, 0.52, 0.20, options)

        blooms = (3, 6, 0.17, 0.45, 0.45)
        before = lay(cover, blooms) - lay(cover, None)
        after = lay(trimmed, blooms) - lay(trimmed, None)
        far = chamfer_distance(trimmed != cover) > 80
        assert float(np.abs(before[far]).max()) > 0.3, "the blooms were laid far off"
        assert float(np.abs(before[far] - after[far]).max()) < 1e-3


class TestPadStreams:
    """Which generator the pad stamps each stroke from."""

    def test_a_stroke_is_stamped_from_its_own_keyed_generator(self):
        """The pad lays a stroke as `stamp` does from the seed, the stroke's key and a count of 0."""
        h, w = 60, 300
        style = BrushStyle(ink_ss=1, ink_starve=True)
        brush, _ = brush_from_id("MAJ2-a", 3.6, 2.0, style, "road_major")
        line = line_at(30.0, 20.0, 280.0)
        pad = InkPad((h, w), brush, style)
        pad.lay([(brush, line)], 91)
        acc = np.zeros((h, w), np.float32)
        aux = ink_aux(acc.shape, brush)
        assert aux is not None, "the reservoir brush fills its accumulators"
        stamp(acc, line, brush, keyed_rng(91, *line_key(line, 1.0), 0), aux=aux)
        assert np.array_equal(pad.acc, acc)
        assert pad.aux is not None
        assert all(np.array_equal(pad.aux[k], aux[k]) for k in aux)

    def test_a_repeated_stroke_takes_the_next_count(self):
        """The same stroke laid twice in one call is told apart from itself by its count."""
        h, w = 60, 300
        style = BrushStyle(ink_ss=1)
        brush, _ = brush_from_id("MAJ2-a", 3.6, 2.0, style, "road_major")
        line = line_at(30.0, 20.0, 280.0)
        pad = InkPad((h, w), brush, style)
        pad.lay([(brush, line), (brush, line)], 91)
        acc = np.zeros((h, w), np.float32)
        for nth in (0, 1):
            stamp(acc, line, brush, keyed_rng(91, *line_key(line, 1.0), nth))
        assert np.array_equal(pad.acc, acc)
