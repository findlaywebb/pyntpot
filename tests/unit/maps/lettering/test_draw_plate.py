"""`draw_plate` strokes the placed names into an RGBA label plate beside the painted plates."""

from PIL import Image

from pyntpot.maps.lettering.label import Label
from pyntpot.maps.lettering.pipeline import draw_plate
from pyntpot.maps.painter.plates import paint_plates

from support.basemaps import tiny_basemap, tiny_style


def test_the_label_plate_carries_its_own_colour_and_its_own_alpha(tmp_path):
    """The plate is composited normally, so it can lighten as well as darken.

    A backing wash in the paper's own colour is the whole reason it is not on
    the wash plate: multiply can only darken, and a white wash multiplied over
    the card does nothing at all.
    """
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
    plate = draw_plate(plates, placed, [], [(10.0, 10.0), (70.0, 40.0)], tiny_style())
    assert plate is not None and plate.exists()
    img = Image.open(plate)
    assert img.mode == "RGBA"
    assert img.size == plates.card.render
    assert img.getchannel("A").getbbox() is not None, "nothing was written"
    # And it is cached on what is lettered, so a second call writes nothing new.
    stamp = plate.stat().st_mtime_ns
    assert draw_plate(plates, placed, [], [(10.0, 10.0), (70.0, 40.0)], tiny_style()) == plate
    assert plate.stat().st_mtime_ns == stamp
