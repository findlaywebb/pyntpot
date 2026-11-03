# The example scripts could be copied out and run anywhere

GitHub issue: [#174](https://github.com/findlaywebb/pyntpot/issues/174)

**What exists today.** `examples/` holds 28 scripts, ten themes and `places.toml`. Small
things make them harder to use than to read:

- **Themes resolve against the repository root.** `place_card.py` and `how_to_route_ink.py`
  join `--theme` to `REPO_ROOT = Path(__file__).resolve().parent.parent`; `map_styles.py`
  reads `THEMES_DIR` beside the script, a third way. A script copied into another project,
  or given a path relative to the working directory, finds the wrong file.
- **`map.png` is overwritten.** `map_styles.py` and `place_card.py` write `out_dir / "map.png"`
  whatever the theme or place, so running the themes or places into one `out/` keeps only
  the last card. Every other multi-figure script names its file by figure.
- **Run output lands in the clone untracked.** The docstrings write into `out/` and
  `cache/`, and `first-map.md` copies the fixture to `ambleside/` at the top of the clone;
  `.gitignore` covers none of the three.
- **`fern_family.py` copies `fern.py`.** It repeats `MAPS`, `PROBABILITIES`, `LEFT_LEAFLET`,
  `fern_points`, `_count`, `_cover`, `_thicken` and `_dabs`, with `fern_points` taking
  different arguments, where `trees.py` paints the single tree and the family with `figure=`.
- **`kaleidoscope.py`'s `_dense` does nothing.** `stamp` already resamples a path evenly by
  arc length (`_trace` in `ink/stamp.py`), yet `symmetry.md` quotes
  `stamp(acc, _dense(points, 1.0), brush, rng)` as if the spacing mattered.
- **Six scripts have no fast test**: `word`, `how_to_own_shapes`, `how_to_route_ink`,
  `place_card`, `social_preview` and `map_styles` appear nowhere in `tests/examples/`. They
  run only through the golden-marked docs pins, which the main CI job leaves out.
- **No README.** Nothing in `examples/` says which scripts teach and which build the site
  (`site_theme.py`, `social_preview.py`).

**What the feature would add.** Scripts a reader can copy out and run: `main` takes a plain
theme `Path` that the caller resolves; output named `map-<theme>.png` and `<place>.png`;
`out/`, `cache/` and `ambleside/` in `.gitignore`; the fern family as `fern.py
--figure family`; `_dense` gone from the script and the page, with `stamp`'s docstring
saying that any spacing of points is fine; a small-size smoke test for each untested
script; an `examples/README.md` that splits teaching scripts from docs build scripts.

**Possible shape.** Small independent slices. The theme path and the output names move the
`REPO_ROOT /` join into the docs images registry, `make_docs_images.py` and the pin test,
and should move no pinned pixels; folding the fern family keeps its seeds so its image
stays exact. The map scripts' smoke tests can share the offline Lynmouth paint
(`tests-shared-lynmouth-paint.md`).

**Related.** `docs-examples-review.md` (#63), `tests-shared-lynmouth-paint.md` (#90),
`docs-tutorials-lead-on.md`, `docs-labelled-grid-helper.md`.
