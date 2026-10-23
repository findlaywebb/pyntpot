# Map lettering could prefer a place's Welsh name

**What exists today.** The map reads a feature's name from OpenStreetMap's
`name` tag only (`pyntpot.maps.osm_elements`). In Wales that tag often holds
the English name, with the Welsh one in `name:cy`, so a card of Y Fenni may
letter "Abergavenny".

**What the feature would add.** A style setting naming the tags to read, in
order (for example `name:cy`, then `name`), so a card can letter Welsh names
for Welsh places, or another language's names elsewhere.

**Why it is not a defect.** The map letters what OpenStreetMap calls the
place, as designed. The maintainer's rule "Welsh names for Welsh places"
(2026-10-23, P7 research Q-P4) covers the repo's own strings; the cards follow
the data until this feature exists.

**Possible shape.** A `lettering` group field, a tuple of tag names defaulting
to `("name",)` so no golden moves; `osm_elements` reads the first present. An
ADR, since a style field is public behaviour, and a test on a feature carrying
both tags.
