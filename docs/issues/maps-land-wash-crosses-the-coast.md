# The land wash pokes over the coast into the sea

GitHub issue: [#223](https://github.com/findlaywebb/pyntpot/issues/223)

Area: maps (painter).

On the theme preview card, painted by `examples/theme_preview.py` from the synthetic fixture
`tests/fixtures/preview/`, every packaged and example theme lays a pale bump of the deckled
land wash north over the coastline and into the sea, above the `East Lyn River`'s mouth. At
600 px display width the bump sits at roughly x 330 to 480 px, y 30 to 90 px of the card.

The sea is built from the coastline (`sea_from_coast`, `src/pyntpot/maps/sea.py`), and the
land wash is the ribbon wash round the route (`src/pyntpot/maps/painter/ribbon.py`). The
ribbon is meant to stop at the shore: `RibbonStyle.coast_hard_mask` defaults to `True`
(`src/pyntpot/maps/style_groups.py`), and `paint_ribbon` then multiplies the ground by the
land side of `stack.sea_cov`. The bump appears all the same, so something reaches the sea
that this mask does not cover: another layer of the stack, the pooled rim, or a `sea_cov`
that does not match the painted sea there. Not traced yet.

The preview card exists to show meetings like this one, so it is the reproduction: paint
`uv run python examples/theme_preview.py --theme default out/` and look above the river mouth.
Fixing it moves every card with a coast (the preview, Skye), so it needs a golden
regeneration window.
