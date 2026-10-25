# The mainland beside Skye is painted as sea

On the Skye card everything east of Kyle of Lochalsh is the sea's blue, with rivers and
roads drawn over it, so the Skye Bridge seems to land in the water. `maps/sea.py` fills the
sea from the coastline rings; the mainland's coastline is cut open by the fetch box, so its
land is on the side of the open line that reads as water.

Found by the round-2 map critique (2026-10-25).

To show it: paint `docs/images/places/skye.webp` from `tests/fixtures/skye/`.

Possible fix: close open coastline chains against the box edge before the fill, keeping
land on the left of the chain's direction, or fill only polygons on the water side of the
coast. The sea plate and docs images move, so it needs a regeneration window of its own with
an ADR.
