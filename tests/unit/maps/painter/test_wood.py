"""The wood phase: a texture and dabs over the wood's mask, cross faded across printed scales."""

from pyntpot.maps.painter.job import PlateStack
from pyntpot.maps.painter.wood import _crossfade, paint_wood

from .jobs import tiny_job, tiny_style


def _wooded(tmp_path, **cover):
    """A job and a stack whose wood mask holds the card's right half."""
    job = tiny_job(tmp_path, tiny_style(cover=cover))
    stack = PlateStack.blank(job.shape)
    stack.wood_mask[:, 80:] = True
    return job, stack


class TestCrossfade:
    """The weights a slider gives the printed scales."""

    def test_a_slider_at_the_ends_picks_one_scale_and_between_blends_two(self):
        """The weights walk from the first scale to the last, two at a time."""
        assert _crossfade(1.0, 3) == [0.0, 0.0, 1.0]
        assert _crossfade(0.5, 3) == [0.0, 1.0, 0.0]
        assert _crossfade(0.75, 3) == [0.0, 0.5, 0.5]

    def test_a_slider_near_zero_is_gated_down(self):
        """Below a quarter the whole blend fades out, so zero paints nothing."""
        assert _crossfade(0.0, 3) == [0.0, 0.0, 0.0]
        assert sum(_crossfade(0.05, 3)) < 0.25

    def test_one_scale_takes_the_slider_itself(self):
        """With a single printed scale the weight is the clamped slider."""
        assert _crossfade(1.7, 1) == [1.0]
        assert _crossfade(-1.0, 1) == [0.0]


class TestPaintWood:
    """What the phase lays and draws."""

    def test_the_wood_gets_texture_and_dabs_only_inside_the_mask(self, tmp_path):
        """Every layer is zero outside the wood, and some carry density inside it."""
        job, stack = _wooded(tmp_path)
        paint_wood(job, stack)
        assert stack.trimmed
        dabs = [layer[0] for layer in stack.trimmed]
        assert all(d[:, :70].max() < 0.05 for d in dabs)
        assert any(d[:, 80:].max() > 0.0 for d in dabs)

    def test_no_wood_draws_nothing_and_leaves_the_generator_untouched(self, tmp_path):
        """With an empty mask no layer is laid and the dither generator has not moved."""
        job = tiny_job(tmp_path)
        stack = PlateStack.blank(job.shape)
        paint_wood(job, stack)
        fresh = tiny_job(tmp_path)
        assert stack.trimmed == []
        assert job.dither_rng.random() == fresh.dither_rng.random()

    def test_the_sliders_at_zero_paint_nothing(self, tmp_path):
        """Both sliders at zero lay no layer even over a wood."""
        job, stack = _wooded(tmp_path, wood_texture=0.0, wood_dabs=0.0)
        paint_wood(job, stack)
        assert stack.trimmed == []
