"""Map lettering: the label and span types, how spans are drawn and placed, and the stage that letters a card.

Key modules: `label` (the `Label` and `Span` types and their tiers and wrapping),
`span_clear`, `span_line`, `span_sides` and `span_ends` (a span's line, side, ticks and
name, drawn beside the route), `spans` (resolving span requests and placing them), and
`pipeline` (the `letter` stage).

Importing a leaf module never imports `pipeline`, so a leaf is usable without the stage.
This package holds no names of its own.
"""

__all__: list[str] = []
