# Work offline and reuse the cache

You want to repaint a map without the network: on a train, on another machine, or after
changing your theme. The fetch cache makes that possible, because it holds everything the
providers sent and everything pyntpot painted from it.

You need the tutorial's first map behind you ([First map](../tutorials/first-map.md)) and one
online run of the same track, such as the command in
[Map from the command line](map-from-the-command-line.md).

## Steps

1. Look at what the first run left in the cache directory. For the Keswick track:

   ```text
   cache/
   ├── overpass-f2f4692b66d96eb9.json
   ├── landcover-f2f4692b66d96eb9.json
   ├── elevation-f2f4692b66d96eb9.json
   └── plates/f2f4692b66d96eb9/
       ├── paper.webp
       ├── wash.webp
       ├── pen.webp
       ├── labels-centreline.webp
       ├── labels-centreline.json
       └── plates.json
   ```

   The three JSON files are the providers' payloads: the map features, the land cover and
   the elevation grid. The `plates` directory holds the painted plates and their manifest.
   [Cache layout](../reference/cache-layout.md) describes every file.

2. Copy the whole directory to where you work offline, with your GPX file. The key in the
   file names is made from your track's bounding box, the margin around it and the two
   providers' ids, so the same track and the same providers give the same key on any
   machine. Your contact, your style and the server's address are not part of it.

3. Run the same command. With all three payloads present, no provider is called and no
   request is sent, so it works with the network off:

   ```bash
   pyntpot map route.gpx -o out/route.png --cache cache/ --contact https://example.org/your-project
   ```

4. Change the theme or the route ink and run it again. A style change repaints only what
   it touches, and the route ink repaints nothing
   ([Change the route ink](change-the-route-ink.md)).

If you want a guarantee that nothing reaches the network, paint from a script and give the
providers a budget of zero. A provider with no budget refuses before it sends a request, so
a payload the cache lacks stops the run instead of starting a download:

```python
track = Track.from_gpx(Path("route.gpx"))
features = OverpassFeatures("https://example.org/your-project", budget=0)
elevation = OpenTopoData("https://example.org/your-project", budget=0)
basemap = fetch(track, Cache(Path("cache")), features, elevation, Style.default())
```

The command line has no such switch. A cache missing a payload makes it try the public
servers.

## Result

The run logs that the plates are current and writes the card in a few seconds, with no
request sent:

```text
plates in cache/plates/f2f4692b66d96eb9 are current, nothing repainted
wrote out/route.png
```

## Make it fetch or repaint on purpose

- To fetch a payload again, delete its file from the cache directory, or call
  `Cache.ensure(track, features, elevation, force=True)`, which fetches all three again.
  Nothing in the cache expires, so a payload is as old as the day it was fetched.
- To repaint the plates, delete the key's directory under `plates/`.
- Two tracks over the same ground share one key's payloads. A track that runs a few metres
  further gets another key and fetches afresh.
- Do not paint into one cache directory from two processes at once: the cache takes no lock.

## When it goes wrong

- `FetchError: a provider could not answer: Overpass budget of 0 queries spent on this provider`:
  the cache has no feature or land cover payload for this track's key, and your zero budget
  refused to fetch it. The key is different from the one you copied: the GPX file differs,
  or a provider differs. Print the key with `cache.key(track, features, elevation)` and
  compare it with the file names.
- `FetchError: a provider could not answer: opentopodata-srtm30m would pass its budget of 0 calls`:
  the same, for the elevation payload.
- `FetchError: no cached features for key f2f4692b66d96eb9: cache/overpass-f2f4692b66d96eb9.json is missing`:
  the feature payload was removed or moved while the run was in progress. Run again.
- The run fetches although you copied the cache: the dataset of your `OpenTopoData` differs
  from the one that fetched (its id is `opentopodata-<dataset>`), or your GPX file is not
  the one the cache was made from.
- The plates repaint every run, and the log never says they are current: something in the
  style's paper, wash, brush, card, ribbon, cover, route or basemap groups changes between
  runs, or you give `paint` a different plates directory each time. Pass
  `cache.plates_dir(key)` as the command line does.
