# 0009 — The candidates facility: one ranking function per kind

Status: accepted

## Context

About 550 lines of the interim `geo` module rank things a map could name for a track:
`journal_candidates` (the landmarks and settlements near the track, most notable
first), `climbs` with `_felt_span` and `_steepest`, `route_places`, `named_roads` with
`road_run`, and `ground_climbs`, which gives each climb the roads, settlements and
features beside it. `landmark_export` stitches them into one payload for an external
label picker. The decision to keep this logic (A8) asks for it to leave `geo` as a
reusable facility in `maps` that ranks named roads, climbs and places for a track, usable
by any later annotation decision: which span to name, which road to number, what to
letter first.

There is one real caller in the fetch, paint and letter path. `journal_layers` calls
`journal_candidates` while it builds the `Basemap` and stores the rows in
`Basemap.candidates`. Three lettering functions read them: `journal_picks` (looks a pick
up by `name`, reads `class`, `x`, `y`), `journal_heuristic` (takes the first `cap` rows
in their stored order, reads `name`, `class`, `distance_m`, `x`, `y`) and `settlements`
(keeps rows whose `class` is `place`, reads `tags["place"]`, `distance_m`, `x`, `y`). The
stored order is part of the lettered output, so it is under the golden parity test.
`Basemap.candidates` is outside the base hash input.

Two facts constrain any shape:

- **The landmark rows are made before the basemap exists.** `journal_candidates` reads
  the `landmark_candidates` that `_osm_layers` collected and the projection; its output
  is an input to `Basemap`. A ranker that takes a finished `Basemap` cannot serve this
  caller.
- **Roads and settlements are ranked from the raw feature payload.** `named_roads` and
  `route_places` read the cached Overpass elements and project the full way geometry and
  the place nodes. `Layers.roads` holds the painted strokes, which are chained and
  simplified to the drawing tolerance, so a road run measured along them gives different
  metres. Exact parity means the rankers keep reading the payload.

## Two shapes

Both shapes share one value, a frozen dataclass in `maps/candidates/candidate.py`, a leaf
below the four kind modules:

```python
@dataclass(frozen=True)
class Candidate:
    kind: str                     # "road", "climb", "place" or "landmark"
    name: str                     # "" for a climb: naming one is the caller's judgement
    rank: int                     # 1-based, within its kind and its call
    at_m: float | None            # metres along the track where it starts or is passed
    where: Pt | None              # card metres; None for a road
    span: tuple[int, int] | None  # first and last track sample it covers
    detail: Mapping[str, Any]     # the kind's row, exactly as the export writes it
```

This refines the starting point's `Candidate(kind, name, score, at_m, where, detail)`.
`score` becomes `rank` because the four kinds have no common scale: a landmark is ordered
by a tier then a distance-to-reach ratio, a climb by metres gained, a road by metres run,
a settlement by where the route passed it. A float `score` would suggest the kinds can
be compared. `span` is added because grounding a climb needs its sample indices, and
converting `at_m` back to an index is not exact where the track repeats a point.

### Shape 1: ranking functions

```python
# maps/candidates/roads.py
def named_roads(payload: Mapping[str, Any], projection: Projection) -> list[dict[str, Any]]
def rank_roads(roads: Sequence[Mapping[str, Any]], line: Line, dist: Sequence[float],
               span: tuple[int, int]) -> list[Candidate]
# maps/candidates/climbs.py
def rank_climbs(track: Track, line: Line) -> list[Candidate]
# maps/candidates/places.py
def rank_places(payload: Mapping[str, Any], projection: Projection, track: Track,
                line: Line) -> list[Candidate]
def ground_climbs(climbs: Sequence[Candidate], places: Sequence[Candidate],
                  landmarks: Sequence[Candidate], roads: Sequence[Mapping[str, Any]],
                  track: Track, line: Line) -> list[Candidate]
# maps/candidates/landmarks.py
def rank_landmarks(entries: Sequence[Mapping[str, Any]], projection: Projection,
                   cap: int = LANDMARK_CAP) -> list[Candidate]
```

Each function returns its kind in the order the export writes it today. `line` is the
projected track (`Basemap.track`), `dist` its cumulative metres. `rank_climbs` returns
nothing when `track.ele` is `None`. `ground_climbs` returns new climb candidates whose
`detail` carries `from`, `through`, `to`, `near_start`, `near_top`, `roads` and
`features`; it does not mutate its input, unlike the function it replaces. It lives in
`places`, the highest module it calls into.

How a later annotation decision uses it:

- *Which span to name:* `ground_climbs(rank_climbs(track, line), ...)`, take the climb of
  `rank` 1, name it from `detail["roads"]` or `detail["from"]` and `detail["to"]`.
- *Which road to number:* `rank_roads(roads, line, dist, span)[0]` for the span's samples.
- *What to letter first:* `rank_landmarks(...)` in list order; settlements are the
  `place` rows among them.
- *Today's caller:* `journal_layers` stores
  `tuple(c.detail for c in rank_landmarks(entries, projection))` in
  `Basemap.candidates`, the same rows in the same order as now.

For: flat; each function is the function it replaces plus a wrapper, so each is tested
alone on the tests that already exist; a caller pays only for the kinds it asks for.
Against: a caller wanting several kinds calls several functions and merges by hand.

### Shape 2: one value with queries

```python
class Candidates:
    @classmethod
    def for_track(cls, track: Track, basemap: Basemap,
                  payload: Mapping[str, Any]) -> Candidates
    def top(self, kind: str | None = None, n: int = 8) -> tuple[Candidate, ...]
    def along(self, start_m: float, end_m: float) -> tuple[Candidate, ...]
```

The four rankers and the grounding are private; `for_track` runs them all. The payload
argument is needed beside the starting point's `(track, basemap)` for the parity reason
above.

How a later annotation decision uses it:

- *Which span to name:* `c.top("climb", n=1)`.
- *Which road to number:* `[x for x in c.along(s0, s1) if x.kind == "road"]`.
- *What to letter first:* `c.top("landmark", n=8)`; or `c.top(n=8)` across kinds.
- *Today's caller:* cannot call `for_track`, which needs the `Basemap` that the
  candidates are an input to. It would call the private landmark ranker, or
  `Basemap.candidates` would change to hold a `Candidates` built after the basemap.

For: one entry point; `along` answers "what is on this stretch" in one call. Against:
every call computes every kind, so the fetch path would detect climbs and measure road
runs it never reads; `top(kind=None)` needs a cross-kind order, which is an annotation
judgement with no caller to settle it; `along` over roads needs a road ranking for the
whole track, which nothing computes today.

## Decision

**Shape 1, ranking functions over one `Candidate` value**, with the signatures above.

Against the criteria:

| Criterion | Shape 1 | Shape 2 |
|---|---|---|
| Today's caller (`journal_candidates` into `Basemap.candidates`) served | yes, `rank_landmarks` alone | no: `for_track` needs the basemap it feeds |
| `Basemap.candidates` may change shape | not needed: it keeps the `detail` rows | needed |
| No Protocol (rule of three) | none | none |
| Testable on the Lynmouth fixture | each function alone; climbs on literal tracks, since the fixture has no elevation | only through `for_track`, whose climbs are always empty on the fixture |
| Parity exact | each wraps the function it replaces | re-orchestrates them; extra work in every fetch |

The deciding reason: the one real caller builds candidates *before* the basemap exists
and needs only landmarks. Shape 2's single entry point cannot be that caller's entry
point, and its cross-kind `top` presumes a common scale the kinds do not have. Merging
kinds by hand is the honest cost: choosing between a road and a climb is the annotation
decision itself, not a fact about the track.

- `Basemap.candidates` keeps its type, `tuple[Mapping[str, Any], ...]`, and its rows.
  `basemap.py`, `labels.py` and `mapcard.py` do not change for the facility.
- `landmark_export` writes `[dict(c.detail) for c in ...]` for every kind, so its JSON is
  unchanged; the private `_a`, `_b` and `_at` keys become `span`.
- `read_gpx_elevation` is replaced by `Track.ele`.
- `maps/candidates/__init__.py` exports nothing; callers import the kind module.

## Facts relied on

This decision was written against `main` at `186ac3f`, before the slices that precede it
in the plan had landed. It relies on these facts, which those slices may change; the
facility slice checks them before it starts:

- `journal_layers` builds `Basemap.candidates` from `journal_candidates(base, proj)`, and
  `journal_picks`, `journal_heuristic` and `settlements` are its only readers, through
  the keys listed above; `mapcard` calls the first two.
- `landmark_export` takes `key`, `lat`, `lng`, `ele`, `style`, `route`, `cache_dir` and
  `places`, builds its basemap with `GeoOptions` and reads the payload through
  `overpass_path`. The slices that add `candidate_basemap` and delete `GeoOptions`
  change how it builds the basemap, not what it ranks.
- `Track` (`maps.track`) carries `ele` as a tuple or `None`.
- The feature payload is read from the fetch cache as Overpass JSON; a change to the
  cache layout changes where the rankers get it, not their signatures.
- At `186ac3f` the zero-caller functions are still present: `alphabet_sheet`,
  `sport_from_gpx`, `_journal_picks`, `_journal_heuristic`, `_place_journal_labels` and
  `with_display`. Their deletion is confirmed by `grep` when the facility is built.

## Consequences

- The facility is four kind modules plus `candidate.py`, each tested alone, and the
  fetch path pays only for landmarks, as it does now.
- A later annotation decision composes the kinds itself; if three such decisions merge
  kinds the same way, that merge is the place for a shared helper or a value like
  Shape 2, decided then by a new ADR.
- `Candidate` is the unit any annotation decision reads. A change to its fields, or to
  `Basemap.candidates` holding something other than the landmark `detail` rows, is
  itself an ADR.
