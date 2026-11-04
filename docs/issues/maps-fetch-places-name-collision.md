# fetch(places=) and Annotations.places mean different things

GitHub issue: [#180](https://github.com/findlaywebb/pyntpot/issues/180)

Area: maps.

`fetch(..., places=...)` in `maps/pipeline.py` takes places of interest to mark, each a
mapping with a `name`, `lat` and `lng`. `Annotations.places` in `maps/annotations.py`
is a tuple of settlement names the lettering should always letter, and `GLOSSARY.md`
defines a place as exactly that: a settlement the caller names. The same word names two
different inputs on the same path, one of them against the glossary.

ADR 0068 does not rename either.

Possible fix: rename the `fetch` parameter to say what it carries (points of interest),
with an ADR, since `fetch` is public API; `Annotations.places` keeps the glossary's
meaning.
