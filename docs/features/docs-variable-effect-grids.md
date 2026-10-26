# The docs could show what changing each setting does

GitHub issue: [#67](https://github.com/findlaywebb/pyntpot/issues/67)

**What exists today.** The tutorials name the settings a script takes and some pages show a
grid (the route inks, the map styles), but most settings are described in words: what
raising a wash's edge darkening or a brush's dryness does is told, not shown.

**What the feature would add.** A small grid of pictures for each important setting, the
same picture painted at three to five values side by side, under the paragraph that
describes it: wash strength and edge, granulation size, brush load and dryness, nib width
and angle, glaze order, relief strength.

**Why it is not a defect.** The settings are documented and correct; this makes them
easier to understand.

**Possible shape.** One helper in `examples/` that paints a picture across a list of values
and writes a labelled grid, registered in the docs images registry like the other images,
so each grid is pinned and repainted by `make_docs_images.py`.
