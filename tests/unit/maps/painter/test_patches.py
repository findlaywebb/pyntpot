"""Small land-cover patches folded into the ground around them."""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

from pyntpot.maps.painter.cover import paint_cover
from pyntpot.maps.painter.job import PlateStack
from pyntpot.maps.painter.patches import merge_small_patches, patches

from .jobs import square, tiny_job, tiny_style


def _two_fields() -> np.ndarray:
    """A meadow (1) on the left and a wood (2) on the right, eight by six pixels."""
    label = np.zeros((6, 8), np.uint8)
    label[:, :4] = 1
    label[:, 4:] = 2
    return label


class TestPatches:
    """The four-connected patches of a label raster."""

    def test_pieces_are_four_connected_and_counted(self):
        """Two diagonal pixels of one class are two patches; a run joined below is one."""
        label = np.array([[1, 0, 1], [0, 1, 1], [0, 0, 0]], np.uint8)
        ids, sizes, classes = patches(label)
        assert ids[0, 0] != ids[1, 1]
        assert ids[0, 2] == ids[1, 1] == ids[1, 2]
        assert sizes[ids[0, 2]] == 3 and sizes[ids[0, 0]] == 1
        assert classes[ids[0, 0]] == 1 and classes[ids[2, 0]] == 0

    def test_ids_are_stable_and_sizes_add_up(self):
        """The same raster gives the same ids, and the patches cover every pixel once."""
        label = _two_fields()
        label[2, 1] = 3
        ids, sizes, _ = patches(label)
        again, _, _ = patches(label.copy())
        assert np.array_equal(ids, again)
        assert int(sizes.sum()) == label.size


class TestMergeSmallPatches:
    """Patches under the floor take their largest neighbour's class, or clear."""

    def test_a_speck_inside_a_field_takes_the_field_class(self):
        """One pixel of heath in the meadow becomes meadow; the large fields are untouched."""
        label = _two_fields()
        label[2, 1] = 3
        out = merge_small_patches(label, 2)
        assert np.array_equal(out, _two_fields())

    def test_a_speck_between_two_fields_takes_the_larger(self):
        """A patch touching a 4-pixel meadow and a 20-pixel wood becomes wood."""
        label = np.full((5, 6), 2, np.uint8)
        label[0:2, 0:2] = 1
        label[2, 2] = 3
        label[1, 2] = 3
        out = merge_small_patches(label, 3)
        assert out[2, 2] == 2 and out[1, 2] == 2
        assert (out[0:2, 0:2] == 1).all()

    def test_a_patch_nothing_painted_touches_is_kept(self):
        """An island's wood in a lake has no neighbour to take, so it stays as it is."""
        label = np.zeros((7, 7), np.uint8)
        label[3, 3] = 4
        assert np.array_equal(merge_small_patches(label, 2), label)

    def test_unlabelled_ground_is_never_painted(self):
        """A hole of paper, or water, inside a field stays 0 however small it is."""
        label = _two_fields()
        label[2, 1] = 0
        out = merge_small_patches(label, 10)
        assert out[2, 1] == 0

    @pytest.mark.parametrize("floor", [0, -1.0], ids=["zero", "negative"])
    def test_a_floor_of_zero_changes_nothing(self, floor):
        """The default off keeps every speck."""
        label = _two_fields()
        label[2, 1] = 3
        assert np.array_equal(merge_small_patches(label, floor), label)

    def test_a_piece_at_the_floor_is_kept(self):
        """The floor is the smallest patch kept: a two-pixel speck survives a floor of 2."""
        label = _two_fields()
        label[2, 1:3] = 3
        assert np.array_equal(merge_small_patches(label, 2), label)
        assert (merge_small_patches(label, 3)[2, 1:3] == 1).all()

    def test_the_input_is_not_changed(self):
        """The function returns a new raster."""
        label = _two_fields()
        label[2, 1] = 3
        merge_small_patches(label, 2)
        assert label[2, 1] == 3

    @settings(max_examples=60, deadline=None)
    @given(
        arrays(
            np.uint8, st.tuples(st.integers(1, 12), st.integers(1, 12)), elements=st.integers(0, 3)
        )
    )
    def test_after_a_merge_only_floor_sized_pieces_or_merged_ones_remain(self, label):
        """No patch that was at the floor changes, and no unlabelled pixel is painted."""
        floor = 3
        ids, sizes, _ = patches(label)
        out = merge_small_patches(label, floor)
        big = sizes[ids] >= floor
        assert np.array_equal(out[big], label[big])
        assert not out[label == 0].any()


class TestPaintCoverFloor:
    """The theme's floor, in display pixels, as the cover phase applies it."""

    def test_a_copse_below_the_floor_is_painted_as_the_meadow_round_it(self, tmp_path):
        """A 16 m copse in a meadow is wood with no floor, and meadow with a 64 display px floor."""
        cover = {
            "meadow": (square(20.0, 20.0, 300.0, 220.0),),
            "wood": (square(100.0, 100.0, 116.0, 116.0),),
        }
        order = ("meadow", "wood")
        plain = tiny_job(tmp_path / "a", cover=cover, cover_order=order)
        floored = tiny_job(
            tmp_path / "b",
            tiny_style(cover={"min_patch_px": 64.0}),
            cover=cover,
            cover_order=order,
        )
        stacks = []
        for job in (plain, floored):
            stack = PlateStack.blank(job.shape)
            paint_cover(job, stack)
            stacks.append(stack)
        # 16 m is 8 render pixels a side, under 64 display pixels (256 render pixels at scale 2).
        copse = stacks[0].label == 2
        assert copse.any()
        assert (stacks[1].label[copse] == 1).all()
        assert stacks[1].wood_mask is None or not stacks[1].wood_mask.any()
