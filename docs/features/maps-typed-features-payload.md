# A `Features` provider could return a typed payload

GitHub issue: [#192](https://github.com/findlaywebb/pyntpot/issues/192)

**What exists today.** `Features`, the public feature provider protocol, returns Overpass
JSON text from `features` and `landcover`, unparsed (`maps/providers/base.py`). A
provider backed by anything other than Overpass has to fake an Overpass response to plug
in.

**What the feature would add.** A typed payload, records of the ways, relations and nodes
the basemap reads, so a non-OSM source or a local file of another format plugs in without
writing Overpass JSON.

**Possible shape.** A public record the protocol returns, with the Overpass provider
parsing into it. The fetch cache stores payloads keyed by the provider's `id`, so the
cache format and its key change, and the protocol is public: an ADR.

**Related.** `docs-how-to-write-a-provider.md`; ADR 0068, which made the protocols public.
