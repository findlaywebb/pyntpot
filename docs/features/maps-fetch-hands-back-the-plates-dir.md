# Fetch could hand back what paint needs

GitHub issue: [#167](https://github.com/findlaywebb/pyntpot/issues/167)

**What exists today.** `pyntpot.maps.fetch(track, cache, features, elevation, style)` works
out the cache key (`cache.ensure` returns it) and then drops it: the `Basemap` it returns
carries no key, by design ("the cache owns its keys", `src/pyntpot/maps/basemap.py`). So
`paint(basemap, style, out_dir)` needs the plates directory rebuilt by the caller, who passes
the two providers a second time:

```python
plates = paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))
```

That line appears in 4 scripts under `examples/` (`route_map.py`, `place_card.py`,
`map_styles.py`, `how_to_route_ink.py`, which rebuilds the directory again for its grid), in
three docs pages
(`docs/tutorials/first-map.md`, `docs/how-to/change-the-route-ink.md`,
`docs/how-to/self-host-providers.md`), in the command line (`src/pyntpot/maps/cli.py`) and
in `tests/support/golden.py`. `candidate_export(track, cache, key)` and
`vector_layers(track, cache, key, style)` take the same key. Building it needs `Features` and
`Elevation`, which are not public.

**What the feature would add.** A map in three calls with no key rebuilt: whatever `fetch`
returns is enough for `paint`, `candidate_export` and `vector_layers`, and the tutorial's
first code line is the map, not the cache's keying.

**Possible shape.** A suggestion; either of:

- `fetch` returns a `Fetched` value holding the basemap and its key (or its plates
  directory), and the later stages take it.
- `paint(basemap, style, cache)` with the key on the basemap, which reverses the basemap's
  stated invariant.

Either is a public API change, so an ADR (amending 0027 for `candidate_export` and
`vector_layers`). A one-call `render` that the CLI and the examples share could sit on top,
but is a separate decision. No pixels move; the examples, the three docs pages and the
reference page change.

**Related.** `cli-wider-commands` (#68), which a shared pipeline call would serve;
`maps-public-provider-protocols` (#78), since the key today needs the private protocols.
