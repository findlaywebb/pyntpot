# Some src docstrings and comments still use names the glossary replaces

`GLOSSARY.md` gives one name per concept, and the docstring audit moved most of
`src/pyntpot` onto those names. A grep at the end of the prose audit
(`grep -rnI -i "activit\|label agent\|darkness grid" src/pyntpot`) still finds
three of the old names:

| Name in the text | Canonical name | Sites (dotted path, line hint) |
| --- | --- | --- |
| activity | track (`maps.track.Track`) | `pyntpot.maps.candidates.export` module docstring (line 3); `pyntpot.maps.candidates.export.landmark_export`, the `inputs` entry (line 60); the `#:` comment on `pyntpot.maps.lettering.label.SPAN_GROUND` (line 199) |
| label agent | no glossary term; the code hands the candidates to the caller | the `#:` comment on `pyntpot.maps.osm_elements.LANDMARK_TAG_KEYS` (line 36) |
| darkness grid | dark grid (`maps.plates.DarkGrid`) | `pyntpot.maps.lettering.placement_costs.Backdrop` and `.Terms`, the `dark` attribute (lines 69 and 91); `pyntpot.maps.lettering.spans.SpanSurroundings`, the `dark` attribute (line 129); `pyntpot.maps.lettering.placement_along._place_along`, the `terms` entry (line 212) |

The `dark` field these name is the painter's dark grid carried as a dict:
`pyntpot.maps.lettering.pipeline` builds it as `{"w": dark.w, "h": dark.h,
"v": dark.values}` from the `DarkGrid` on the plates, so "dark grid" is the
right name for it. The prose audit of the docs owns no `src/` file, so it
corrected the `backdrop` and `terms` rows of `GLOSSARY.md` and left these
sites.

Possible fix: in one docs-only commit, write "track" for "activity", "the
caller" for "the label agent", and "dark grid" for "darkness grid" at each site
above, then re-run the grep; the AST-neutral check proves no code moved.
