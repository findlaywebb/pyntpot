# Map from the command line

You have a GPX file of a walk, ride or run and want a painted map of it as a PNG, without
writing any Python. `pyntpot map` does that in one command.

You need the tutorial's first map behind you ([First map](../tutorials/first-map.md)),
pyntpot installed, a GPX file with at least two track points (`trkpt` elements), and a
network connection for the first run only.

## Steps

1. Run the command with your track, an output file, a cache directory and a contact:

   ```bash
   pyntpot map route.gpx -o out/route.png --cache cache/ --contact https://example.org/your-project
   ```

   `--contact` is how the operators of the public Overpass and OpenTopoData servers can
   reach you if your requests cause them trouble. Give a web address for your project or an
   email address. pyntpot sends it in each request's `User-Agent` and keeps it nowhere else.
   From a checkout of the repository, write `uv run pyntpot` for `pyntpot`.

2. Wait for the first run. It asks Overpass for the map features and the land cover, asks
   OpenTopoData for a grid of elevations, and paints the plates, so it takes a minute or
   two, most of it pauses the public servers ask for. The log goes to standard error:

   ```text
   cached overpass-f2f4692b66d96eb9.json, 2816505 bytes
   cached landcover-f2f4692b66d96eb9.json, 3777758 bytes
   elevation 100/6400
   elevation 200/6400
   ...
   cached elevation-f2f4692b66d96eb9.json, 43998 bytes
   wrote out/route.png
   ```

   The 16 characters in the file names are the cache key for your route's box, and the byte
   counts differ for every route; these are the Keswick track's.

3. Open `out/route.png`. It is the route map card: the land painted in washes, the pen
   plates for roads and water, the names lettered by hand, your route in crimson, and the
   data credit at the bottom right.

4. Run the same command again. The cache holds the payloads and the painted plates, so
   nothing is fetched or repainted and the card is composed in a few seconds:

   ```text
   plates in cache/plates/f2f4692b66d96eb9 are current, nothing repainted
   wrote out/route.png
   ```

To paint with your own theme, add `--style my-theme.toml`
([Write a theme](write-a-theme.md)). To leave the credit off the card, add
`--no-attribution`, and read [Credit the map data](credit-the-map-data.md) first, because
the duty to credit then falls to you.

## Result

![The Keswick route map card: a looping route in crimson over washes of green and blue, with rivers, roads and names lettered by hand.](../images/gallery/route-map.webp)

*Painted by `examples/route_map.py`, which makes the same card as the command.*

## When it goes wrong

Find the line that matches what you see.

- `pyntpot map: error: the following arguments are required: track, -o/--output, --cache, --contact`: You left out a required argument. Each of the track, `-o`, `--cache` and `--contact` is needed. `pyntpot --help` and `pyntpot map --help` list them, and [the command line reference](../reference/cli.md) describes each.
- `pyntpot: error: the following arguments are required: command`: You ran `pyntpot` alone. Give it the `map` command first.
- `FileNotFoundError: [Errno 2] No such file or directory: 'route.gpx'`: The track path is wrong for the directory you ran the command in. Paths are used as you write them, relative to where you run it.
- `xml.etree.ElementTree.ParseError: syntax error: line 1, column 0`: The file is not GPX, or not XML at all. Open it in a text editor; a GPX file starts with `<?xml` or `<gpx`.
- `ValueError: a track needs at least two points`: The file has fewer than two `trkpt` elements. pyntpot reads track points only, so a GPX file that holds a planned route (`rte`) or waypoints (`wpt`) reads as no track. Export the recorded track instead.
- `ValueError: GPX time '2026-10-24T09:30:00' has no time zone`: A point's `time` has no zone. GPX times end in `Z` or an offset such as `+01:00`. Add one, or remove the `time` elements.
- `FetchError: a provider could not answer: every Overpass endpoint refused the query`: Overpass was busy or unreachable. The log above the error says why, for example a 429 for too many requests; after a 429 pyntpot waits 30 seconds before it tries the next server. Run the same command again later. Payloads fetched before the failure are already in the cache, so the rerun fetches only what is missing.
- `FetchError: a provider could not answer: opentopodata-srtm30m ...`: OpenTopoData failed after Overpass had answered. The same remedy applies: rerun, and the features and land cover are not fetched again. The public OpenTopoData server allows 1000 calls a day, and one map takes 64, so a day of heavy use can spend it.
- `ValueError: Overpass needs a contact string, such as an email address`: `--contact` was empty. Give a web address or an email address.
- `pydantic_core._pydantic_core.ValidationError: ... for Style`: Your `--style` theme is missing a group, names a key that does not exist or has a value of the wrong type. The lines under the error name the group and the key. [Write a theme](write-a-theme.md) lists the groups.
- The card has no credit at the bottom right: You passed `--no-attribution`, or the picture was scaled down until the small lettering no longer shows. [Credit the map data](credit-the-map-data.md) says where else to put it.
