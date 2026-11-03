# The elevation credit always names NASA SRTM, whatever dataset was served

GitHub issue: [#160](https://github.com/findlaywebb/pyntpot/issues/160)

Area: maps (providers).

`OpenTopoData(contact, endpoint, dataset="srtm30m", ...)` in
`src/pyntpot/maps/providers/opentopodata.py` samples whatever dataset it is given: its
`id` becomes `opentopodata-<dataset>`. Its `credit`, though, is a class attribute fixed to
`Credit("Elevation: NASA SRTM via OpenTopoData", ..., "elevation: NASA SRTM")`.
`fetch` in `maps/pipeline.py` passes `elevation.credit` to the card, so a map built from
the public server's `eudem25m` or `aster30m`, or from a self-hosted server with other data,
is credited to NASA SRTM.

The basemap's own source list has the same fault: `basemap` in `maps/layers.py` appends
the fixed string `"SRTM 30 m via OpenTopoData"` whenever an elevation payload exists,
whichever provider or dataset wrote it.

The constructor has no `credit` argument, and `Credit` is not exported from
`pyntpot.maps`. The documented remedy (`docs/how-to/credit-the-map-data.md`, "When it goes
wrong", and `docs/how-to/self-host-providers.md`) is to turn the credit off with
`--no-attribution` or `attribution=False` and write one by hand, so the user loses the
on-card credit.

Possible fix: give the provider a `credit=` keyword (or derive the credit from the dataset
name for the public server's known datasets), export `Credit`, take the basemap's source
line from the provider rather than a literal, and rewrite both "When it goes wrong"
entries.
