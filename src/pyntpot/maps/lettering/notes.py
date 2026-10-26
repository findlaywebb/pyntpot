"""Journal notes on the card: a note's label, and its seat among the names.

Key names: `note_labels`, the caller's journal notes as labels anchored on the card;
`seat_notes`, which seats them one at a time, through `best_flat`, as flat blocks with leaders and returns them
with the boxes they take; `NOTE_KIND`, the kind such a label carries.

It does not pick, order, dedupe or swap names, and it draws nothing: a note is seated here,
before `place` runs, and `place` is only told the boxes the notes took. A note is not
counted against the style's label cap.

Invariants: a note's leader starts on its own point; a note is written on one line unless
that line is wider than a third of the card, and then on its most balanced two lines; a note
whose point is off the card, or whose cheapest seat is off the paper, raises `ValueError`
naming it; a note is seated against the boxes already taken and the notes seated before it.
"""

from pyntpot.maps.annotations import Annotations
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.lettering.label import Box, Label, Measure, block_size, wrap_forms
from pyntpot.maps.lettering.placement_costs import Backdrop, Terms, box_on_paper
from pyntpot.maps.lettering.placement_flat import best_flat

#: The kind a journal note's label carries. Not a no-leader kind, so a note takes a leader,
#: and not a no-wrap kind, so a long one may take two lines.
NOTE_KIND = "note"

#: How wide one line of a note may be, as a share of the card's width, before it is
#: broken over two lines.
NOTE_LINE_SHARE = 1 / 3


def note_labels(annotations: Annotations | None, basemap: Basemap, size: float) -> list[Label]:
    """The caller's journal notes as labels, each anchored on its point, in the caller's order.

    Args:
        annotations: The caller's request, or `None` for no notes.
        basemap: The basemap, for the projection and the card.
        size: The type size a note is written at, in display pixels.

    Returns:
        The labels, not yet seated.

    Raises:
        ValueError: A note's point is off the card.
    """
    card = basemap.card
    out: list[Label] = []
    for note in annotations.notes if annotations is not None else ():
        x, y = card.xy(*basemap.projection(note.lat, note.lng))
        if not (0 < x < card.w and 0 < y < card.h):
            raise ValueError(f"journal note {note.text!r} is off the card")
        out.append(Label(name=note.text, kind=NOTE_KIND, px=x, py=y, size=size))
    return out


def seat_notes(
    notes: list[Label], ground: Backdrop, taken: list[Box], measure_fn: Measure
) -> tuple[list[Label], list[Box]]:
    """Seat each note on the cheapest rung, one at a time, against what is already taken.

    Args:
        notes: The labels `note_labels` made.
        ground: The card, the route, the dark grid and the roads the seat is priced against.
        taken: The boxes already spoken for, such as the home glyph's.
        measure_fn: How wide and tall a name is set flat.

    Returns:
        The notes, each carrying its box and leader, and the boxes now taken: the ones given
        followed by the notes'.

    Raises:
        ValueError: A note's cheapest seat is off the paper.
    """
    boxes = list(taken)
    for lb in notes:
        terms = Terms(ground.card, ground.dark, boxes, ground.roads, [(ground.thin, 1.0)])
        best_flat(lb, terms, measure_fn, [_form(lb, ground.card.w, measure_fn)])
        if lb.box is None or not box_on_paper(lb.box, ground.card):
            raise ValueError(f"journal note {lb.name!r} has no seat on the paper")
        boxes.append(lb.box)
    return notes, boxes


def _form(lb: Label, card_w: float, measure_fn: Measure) -> list[str]:
    """The single line, or the most balanced two when one line is wider than a third of the card."""
    forms = wrap_forms(lb.name, lb.kind, lb.tier)
    if len(forms) > 1 and block_size(forms[0], lb.size, measure_fn)[0] > card_w * NOTE_LINE_SHARE:
        return forms[1]
    return forms[0]
