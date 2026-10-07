# Test identifiers say "sheet" for the drawn map

`GLOSSARY.md` gives *sheet* to `pyntpot.ink.sheet.Sheet`, the paper's noise fields, and
the docstrings and comments are being brought into line: "map" for the card as drawn on
the maps side. Some test identifiers still use "sheet" for the drawn map, and a docs
pass changes no identifier, so they are left for a rename of their own:

- `tests/support/lettering.py::sheet_card`, the smallest card the placer accepts, and its
  uses in `tests/unit/maps/lettering/test_spans.py`, `test_placement.py`,
  `test_placement_names.py` and `test_placement_flat.py` (28 lines);
- `tests/unit/maps/test_rings.py::test_a_polygon_bigger_than_the_sheet_is_clipped_not_dropped`;
- `tests/unit/maps/lettering/test_span_clear.py::test_a_span_takes_its_name_along_it_only_when_it_runs_across_the_sheet`;
- `tests/unit/maps/lettering/test_placement.py::test_a_river_follows_its_bend_even_when_the_bend_runs_down_the_sheet`
  and `::test_a_rivers_two_names_are_kept_apart_along_the_water_not_across_the_sheet`.

The identifiers that mean the `Sheet` stay as they are: `sheet_seed`,
`pyntpot.letters.nib._sheet`, `pyntpot.ink.brush._sheet_brush` (the brush sheet),
`test_a_sheet_with_no_fibre_is_the_sheet_it_always_was`,
`test_a_sheet_with_nothing_wet_on_it_comes_back_untouched`,
`test_a_directional_break_follows_the_stroke_not_the_sheet`, `test_building_a_sheet` and
`test_sheet_constructs_from_the_top_level`.

To show it: `grep -rnI sheet_card tests --include=*.py` and
`grep -rnIE "_the_sheet_(is_clipped|runs)|runs_down_the_sheet|not_across_the_sheet" tests --include=*.py`.

Possible fix: rename the builder after what it builds (a small card) and the four tests
after the map, with every use repointed in the same change; tests only, so no pixel moves.
