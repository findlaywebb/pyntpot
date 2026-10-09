"""Hand lettering: the face, the trace, the hand and the nib.

Public names: `Hand`, which sets a text along a line or beside an anchor in the
face its style names (the vendored one by default); `Setting` and `Mark`, what the
hand is asked to write and the marks it writes; `FaceStyle`, `HandStyle` and
`NibStyle`, its style groups, with `NibGroups`, the groups the nib reads; and
`NibSurface` and `nib_plate`, which strokes marks onto one RGBA plate and writes it.
It does not choose or place names: that is the caller's job.
"""

from pyntpot.letters.hand import Hand
from pyntpot.letters.nib import NibSurface, nib_plate
from pyntpot.letters.setting import Mark, Setting
from pyntpot.letters.style import FaceStyle, HandStyle, NibGroups, NibStyle

__all__: list[str] = [
    "FaceStyle",
    "Hand",
    "HandStyle",
    "Mark",
    "NibGroups",
    "NibStyle",
    "NibSurface",
    "Setting",
    "nib_plate",
]
