# Private helpers in maps are imported by other modules

Several `maps` modules import another module's underscore-prefixed names, so
those names are private in form but part of the package's internal interface:

- `pyntpot.maps.track_index._densify`, imported by `pyntpot.maps.layers` and
  `pyntpot.maps.rivers`;
- `pyntpot.maps.osm._osm_layers` and `pyntpot.maps.relief_layers._relief_layers`,
  imported by `pyntpot.maps.layers`;
- `pyntpot.maps.osm_elements._polygon_rings`, imported by `pyntpot.maps.cover`;
- `pyntpot.maps.contours._ring_is_wet`, `pyntpot.maps.masks._spread` and
  `pyntpot.maps.relief_strokes._jitter`, imported by `pyntpot.maps.generalise`;
- `pyntpot.maps.contours._grid_line_to_metres` and `pyntpot.maps.contours._pad`,
  imported by `pyntpot.maps.relief`.

A reader taking the underscore at its word would expect to change one of these
freely, and the module docstrings describe some of them as key names of their
module. P6 renames no identifier, so the names stay as they are.

Possible fix: drop the underscore from each name that another module imports
(or move the shared helper to the module that uses it most), repointing the
importers and tests in one refactor slice with G-self, since the AST changes.
