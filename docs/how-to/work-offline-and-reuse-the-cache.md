# Work offline and reuse the cache

Repaint a map with no network: on a train, on another machine, or after changing your
theme. The first run fills a cache with everything the providers sent and everything
pyntpot painted from it, and later runs read from that.

**Before you start:** run the track online once, for example with
[Map from the command line](map-from-the-command-line.md).

## Steps

1. Look at what the first run left in the cache directory. For the Ambleside track:

   ```text
   cache/
   ├── overpass-f0a137ce97afcb43.json
   ├── landcover-f0a137ce97afcb43.json
   ├── elevation-f0a137ce97afcb43.json
   └── plates/f0a137ce97afcb43/
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

2. Copy the whole directory, and your GPX file, to where you work offline. The key in the
   file names comes from your track's bounding box, the margin around it and the two
   providers' ids. The same track and providers give the same key on any machine. Your
   contact, your style and the servers' addresses are not part of it.

3. Run the same command. With all three payloads present, no provider is called and no
   request is sent, so it works with the network off:

   ```bash
   pyntpot map route.gpx -o out/route.png --cache cache/ --contact https://example.org/your-project
   ```

4. Change the theme or the route ink and run it again. A style change repaints only what
   it touches. A route ink change repaints nothing
   ([Change the route ink](change-the-route-ink.md)).

To guarantee that nothing reaches the network, paint from a script and give the providers
a budget of zero. A provider with no budget refuses before it sends a request. A payload
the cache lacks then stops the run instead of starting a download:

```python
track = Track.from_gpx(Path("route.gpx"))
features = OverpassFeatures("https://example.org/your-project", budget=0)
elevation = OpenTopoData("https://example.org/your-project", budget=0)
basemap = fetch(track, Cache(Path("cache")), features, elevation, Style.default())
```

The command line has no such switch. If the cache lacks a payload, the command asks the
public servers.

## Result

The run logs that the plates are current and writes the card in a few seconds. It sends
no request:

```text
plates in cache/plates/f0a137ce97afcb43 are current, nothing repainted
wrote out/route.png
```

## Make it fetch or repaint on purpose

- To fetch a payload again, delete its file from the cache directory. Or call
  `Cache.ensure(track, features, elevation, force=True)`, which fetches all three again.
  Nothing in the cache expires, so a payload is as old as the day it was fetched.
- To repaint the plates, delete the key's directory under `plates/`.
- Two tracks share payloads only when their bounding boxes match to about a tenth of a
  metre. A track that extends even a little further gets another key and fetches afresh.
- Do not paint into one cache directory from two processes at once. The cache takes no lock.

## When it goes wrong

- `FetchError: a provider could not answer: Overpass budget of 0 queries spent on this provider`:
  the cache has no feature or land cover payload for this track's key, and your zero budget
  refused to fetch it. The key differs from the one you copied, because the GPX file or a
  provider differs. Print the key with `cache.key(track, features, elevation)` and compare
  it with the file names.
- `FetchError: a provider could not answer: opentopodata-srtm30m would pass its budget of 0 calls`:
  the same, for the elevation payload.
- `FetchError: no cached features for key f0a137ce97afcb43: cache/overpass-f0a137ce97afcb43.json is missing`:
  the feature payload was removed or moved while the run was in progress. Run it again.
- The run fetches although you copied the cache: your `OpenTopoData` dataset differs from
  the one that fetched (its id is `opentopodata-<dataset>`), or your GPX file is not the
  one the cache was made from.
- The plates repaint every run and the log never says they are current: a value in the
  style's paper, wash, brush, card, ribbon, cover, route or basemap groups changes between
  runs, or you give `paint` a different plates directory each time. Pass
  `cache.plates_dir(key)`, as the command line does.
