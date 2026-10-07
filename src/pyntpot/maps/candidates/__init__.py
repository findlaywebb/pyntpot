"""Candidates: ranked options a map could name for a track.

The package holds one module per kind and the value they share. `candidate`
defines `Candidate`; `roads`, `climbs`, `places` and `landmarks` each rank one
kind, `landmark_classes` is the tag vocabulary the landmark ranking reads, and
`export` builds one track's candidate export from the kinds. A caller imports
the module it needs; this package exports nothing and imports nothing, so
reaching one module never loads the others.

It does not fetch features, choose what a map names, or merge kinds: the four
kinds have no common scale, so choosing between a road and a climb is the
caller's decision.
"""

__all__: list[str] = []
