"""Map lettering: what a card names, how names and spans are placed, and the stage that letters a card.

Key modules: `label` (the `Label` and `Span` types and their tiers and wrapping),
`span_clear`, `span_line`, `span_sides` and `span_ends` (a span's line, side, ticks and
name, drawn beside the route), `spans` (resolving span requests and placing them), the
`placement*` modules (where each name sits), the `picks*` modules (which settlements, rivers,
roads, landmarks and markers a card names) and `pipeline` (the `letter` stage and the label
plate it strokes).

Importing a leaf module never imports `pipeline`, so a leaf is usable without the stage.
This package holds no names of its own.
"""

__all__: list[str] = []
