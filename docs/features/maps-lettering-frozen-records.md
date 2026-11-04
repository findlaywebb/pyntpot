# The lettering could return frozen `Label` and `Span` records

GitHub issue: [#191](https://github.com/findlaywebb/pyntpot/issues/191)

**What exists today.** `Label` and `Span` are public and keyword-only, and mutable while
the placer fills them: it writes them in place at about thirty sites in
`maps/lettering/placement.py`, `placement_flat.py`, `placement_leaders.py` and
`spans.py`. ADR 0068 makes writing to a returned one unsupported, so freezing them is not
a breaking change. The other records ADR 0068 made public are frozen and keyword-only.

**What the feature would add.** `letter` returns frozen `Label` and `Span` records, so a
caller cannot change a placed label by accident and a returned record is safe to share.

**Also in scope.** Separating the returned record from the placer's working state. These
fields are the placer's state, not what a caller needs, and ADR 0068 leaves them
changeable without an ADR until this lands: `Label.window`, `flat`, `anchors`, `mark`,
`span_range`, `in_water`, `tx`, `ty` and `lift`; `Span.rank`, `offset_px` and `side`.

**Possible shape.** The placer works on private mutable state and builds the frozen public
record once, at the end; or it keeps the records and replaces each with
`dataclasses.replace` in place of each write. Either way the goldens and `PINNED_LABELS`
must not move. Dropping a placement-state field from the public record is a public API
change and gets an ADR.
