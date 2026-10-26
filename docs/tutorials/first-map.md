# First map

![A hand-painted map of Ambleside and Rydal Water: green and ochre washes with a pink route that loops from Ambleside up Loughrigg Fell and back past Rydal Water, blue strokes for the rivers Rothay and Brathay, rust-coloured roads and the names written by hand](../images/tutorials/route-map.webp)

*Painted by `examples/route_map.py`.*

You have painted a paper, a wash, a brush, two pigments, a pen and a hand. Now you
paint real country. You give the script a GPX track. It gets the roads, rivers, woods
and heights round the route. Then it lays the paper and washes, pulls the brushes, takes
up the pen and letters the names, in the order you have just learned. The result is a
card: one painted picture of one walk.

The painting has nothing new in it. The shapes now come from OpenStreetMap data and
from an elevation grid. The engine also has to decide where each name can sit.

Do [Paint a watercolour](paint-a-watercolour.md) first if you have not, so that the
terms below are familiar.

## Copy the Ambleside files

The first map paints a loop from Ambleside in the Lake District, from four files you
already have. They are in your clone's
[`tests/fixtures/ambleside`](https://github.com/findlaywebb/pyntpot/tree/main/tests/fixtures/ambleside)
directory:

| File | What it holds |
| --- | --- |
| `track.gpx` | The route: a loop of about nine kilometres from Ambleside up Loughrigg Fell, east past Rydal Cave and along Rydal Water, and back beside the Rothay. It was made for the repository and follows public paths; it records nobody's walk. |
| `overpass-f0a137ce97afcb43.json` | The map features round the route, as OpenStreetMap's Overpass service returned them. |
| `landcover-f0a137ce97afcb43.json` | The land cover round the route, from the same service. |
| `elevation-f0a137ce97afcb43.json` | The heights, as OpenTopoData returned them. |

Copy the directory to `ambleside` in the top directory of your clone:

```console
$ cp -r tests/fixtures/ambleside ambleside
```

Work on the copy, not on the fixture. The run writes its painted plates into the cache
directory, and a copy keeps them out of the repository.

Keep the three data files' names exactly as they are. Each name ends in the cache's key
for this track and these providers, and that is how the cache finds a payload it already
holds. With all three in the directory, the cache holds everything the first map needs,
and the script sends no request.

## Paint it from the cache

Run the script with the track, the directory that holds the cache, a directory to write
into and a contact:

```console
$ uv run python examples/route_map.py ambleside/track.gpx ambleside/ out/ you@example.org
INFO:__main__:wrote out/map.png
```

The contact is a placeholder here. The command line asks for one on every run because
the public servers see it when you fetch from them. This run fetches nothing, so nothing
is sent. The first run takes about a minute, because it paints every plate of the card.
The cache keeps the plates in a `plates` directory beside the payloads. A later run reads
them instead of painting again.

Open `out/map.png`. It is the picture at the top of this page. Here is the script's
`main`:

<!-- from examples/route_map.py -->
```python
def main(
    out_dir: Path,
    *,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
) -> Path:
    """Fetch what the cache lacks for a track, paint, letter and compose it, and save the card.

    Args:
        out_dir: Where `map.png` is written; created when missing.
        track: The GPX file of the route.
        cache_dir: The fetch cache: provider payloads, and the plates painted from them.
        features: The map feature and land cover provider.
        elevation: The elevation provider.

    Returns:
        The path of the saved card, `out_dir / "map.png"`.
    """
    route = Track.from_gpx(track)
    cache = Cache(cache_dir)
    style = Style.default()
    basemap = fetch(route, cache, features, elevation, style)
    plates = paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))
    lettering = letter(plates, basemap, None, style)
    card = compose(plates, lettering, basemap, style)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "map.png"
    card.save(path)
    log.info("wrote %s", path)
    return path
```

It has four stages:

1. `Track.from_gpx` reads the route.
2. `fetch` builds the basemap. It asks the cache first, and the providers only for what
   the cache lacks: `OverpassFeatures` for the features and land cover, `OpenTopoData`
   for the elevation.
3. `paint` lays the paper, the washes and the pen plates in the `Style.default()` look.
   `letter` places the names and writes them with the hand.
4. `compose` stacks the plates and the lettering into one card, with the credit the data's
   licences ask for drawn at its foot.

### What to notice

- The land is washed, not filled. The greens and ochres are washes with the edge
  darkening and the grain you met in the second rung. Rydal Water is soft blue at the
  upper left.
- The rivers, the Rothay and the Brathay, are blue brush strokes. The roads are
  rust-coloured strokes. These are the brushes you pulled on the third rung.
- The route is a pink line, laid over the washes and the roads.
- The names are in the hand's writing: "Ambleside", "Rydal", "Pelter Bridge",
  "Loughrigg Fell" and "St Mary's". "Rothay" and "Brathay" follow the curve of their
  rivers. "A591" sits beside its road. Each name goes where placing it costs least, which
  keeps it clear of the route where it can.
- At the foot, small lettering credits OpenStreetMap, whose data the card is made from.

**Try changing** the command to the one the package installs. It reads the same cache,
finds the plates already painted, says so and writes the card in a few seconds:

```console
$ uv run pyntpot map ambleside/track.gpx -o out/ambleside.png --cache ambleside/ --contact you@example.org
```

## Paint your own track

Now use a track of your own, a GPX file of a walk or a ride. The Ambleside files were
saved from the public services. Yours will come from them. Two things change:

- The cache is empty for your track, so the first run fetches from the public Overpass
  and OpenTopoData servers. They are free, shared and rate-limited, so the first run
  takes longer. The shipped providers keep to the servers' usage limits: one request at
  a time, a pause when a server says it is busy, and a cap on how many queries one run
  may send.
- The contact is no longer a placeholder. It tells the servers' operators how to reach
  whoever is sending requests. Give a way of reaching you that you are content for them
  to see, such as a web address for your project. It is sent with every request and is
  not part of the cache's key.

With the command the package installs, from the top of the repository:

```console
$ uv run pyntpot map my-walk.gpx -o out/my-walk.png --cache cache/ --contact "you@example.org"
```

Replace `you@example.org` with your own contact. The command fills `cache/` with the
payloads your track lacks, then paints, letters and writes the card. Run it a second
time and nothing is fetched. `--style` takes a TOML theme for another look.
`--no-attribution` leaves the credit off the card. If you publish the card, leave the
credit on.

If you prefer the script, it takes the same pieces in the same order:

```console
$ uv run python examples/route_map.py my-walk.gpx cache/ out/ "you@example.org"
```

The script reads your track from the file you give and copies it nowhere. The two
public servers see the box your track covers, with a margin, and your contact. They do
not see the track itself.

## Where next

The card is the engine's first application, and every layer of it is one you have
already used. Open `examples/route_map.py` beside `examples/composition.py`. They are
the same work at two scales.
