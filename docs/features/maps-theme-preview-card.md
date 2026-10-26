# A preview card for map styles

**What exists today.** To see a theme, an author paints a real place card from a recorded
fixture. A real card shows only what that place holds: Ambleside has no coast, Oxford no
relief, Skye no dense streets. So a theme can look right on one card and break on
another, and the interactions that go wrong (a label on a dark wash, a road crossing a
river, a route doubling back beside a stream, an island in a lake) are scattered across
places or missing.

**What the feature would add** (maintainer, 2026-10-25). One template image that a new
map style is easy to judge on: a small synthetic card holding every kind of feature and
the awkward interactions between them, painted fast. For example: a coast with an island
and sea; a lake with an island; a braided river and a stream meeting it; major and minor
roads crossing the water and each other; wood, meadow, heath, built-up and rock patches,
including some small ones; a hill with relief; a route that doubles back beside a road
and a river; a settlement, a landmark callout, a journal note and the credit.

**Why it is not a defect.** Themes can be judged on the place cards today; the cost is the
time and the gaps.

**Possible shape.** A hand-built fixture (made up, within the test coordinate box, or
synthetic layers that need no provider) and an example script `theme_preview.py` taking a
theme path, painting the card in seconds, with a test that every theme in
`examples/themes/` paints on it. The map styles page and the theme how-to would show
each theme on this card.
