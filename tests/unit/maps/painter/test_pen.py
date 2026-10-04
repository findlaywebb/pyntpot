"""The pen phase: watercourses, the coast and roads laid as ink, and the route's own plate."""

import dataclasses

from pyntpot.maps.basemap import River, Road
from pyntpot.maps.painter.job import PlateStack
from pyntpot.maps.painter.pen import paint_pen, paint_route_pen

from .jobs import tiny_job, tiny_style


def _river() -> River:
    """A river crossing the card, painted at its own width."""
    line = tuple((float(x), 60.0 + 0.2 * x) for x in range(10, 300, 20))
    return River(line=line, cls="major", name="Lyn", width_px=6.0, name_width_px=6.0)


def _road() -> Road:
    """A major road across the card."""
    line = tuple((float(x), 200.0 - 0.1 * x) for x in range(10, 300, 20))
    return Road(line=line, cls="major", band="major", highway="primary", name="", ref="")


def test_an_empty_card_has_no_ink(tmp_path):
    """With no rivers, coast or roads no ink layer is laid."""
    assert paint_pen(tiny_job(tmp_path)) == []


def test_a_river_and_a_road_lay_one_layer_each(tmp_path):
    """The watercourse pad and the major road pad come back as two layers."""
    job = tiny_job(tmp_path, rivers=(_river(),), roads=(_road(),))
    layers = paint_pen(job)
    assert len(layers) == 2
    for density, _colour, *_ in layers:
        assert density is not None
        assert density.shape == job.shape
        assert density.max() > 0.0


def test_minor_roads_are_laid_only_when_the_card_carries_them(tmp_path):
    """A lane draws nothing when `minor_roads` is off and an ink layer when it is on."""
    lane = dataclasses.replace(_road(), band="minor")
    off = tiny_job(tmp_path, roads=(lane,))
    on = tiny_job(tmp_path, roads=(lane,), minor_roads=True)
    assert paint_pen(off) == []
    assert len(paint_pen(on)) == 1


def test_the_route_plate_is_written_and_recorded(tmp_path):
    """The route pen plate lands on disk and in the stack's files and sizes."""
    job = tiny_job(tmp_path)
    stack = PlateStack.blank(job.shape)
    paint_route_pen(job, stack)
    assert stack.files == {"pen": "pen.webp"}
    assert (tmp_path / "pen.webp").stat().st_size == stack.sizes["pen"]


def test_the_route_plate_is_skipped_when_the_style_turns_it_off(tmp_path):
    """With the route pen off no plate is written and nothing is recorded."""
    base = tiny_style()
    style = base.model_copy(update={"route": dataclasses.replace(base.route, route_pen=False)})
    job = tiny_job(tmp_path, style)
    stack = PlateStack.blank(job.shape)
    paint_route_pen(job, stack)
    assert stack.files == {}
    assert not (tmp_path / "pen.webp").exists()
