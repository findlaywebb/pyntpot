# Self-host the providers

You want pyntpot to ask your own Overpass and OpenTopoData servers for its data instead of
the public ones. You might do this for heavy use, for a private network, or to stay clear
of the public servers' limits.

This guide covers the two providers pyntpot ships, `OverpassFeatures` and `OpenTopoData`,
pointed at servers you control. It does not cover writing a provider of your own. The
`Features` and `Elevation` protocols are not among `pyntpot.maps`'s public names.
[A caller could write their own data provider](../features/maps-public-provider-protocols.md)
describes the gap.

You need the tutorial's first map ([First map](../tutorials/first-map.md)), an Overpass
server whose database covers your track, and an OpenTopoData server with a dataset loaded
(the default is `srtm30m`). The services' own documentation covers setting them up.

## Steps

1. Build the two providers with your servers' addresses. Overpass takes the full URL of its
   interpreter, in a tuple because it tries them in order. OpenTopoData takes the base URL
   up to the version, without the dataset, and then the dataset's name:

   ```python
   contact = "https://example.org/your-project"
   features = OverpassFeatures(
       contact,
       ("http://localhost:12345/api/interpreter",),
       budget=10_000,
   )
   elevation = OpenTopoData(
       contact,
       "http://localhost:5000/v1",
       "srtm30m",
       budget=10_000,
       sleep=lambda seconds: None,
   )
   ```

   The contact is still required. It goes in the `User-Agent` of each request, so your own
   server's logs show who asked. The `budget` is the most queries or calls one provider
   instance sends. The defaults, 100 and 1000, match the public servers' limits and are too
   low for a busy day on your own server. `sleep` is what OpenTopoData calls to pause 1.1
   seconds after each call, a pause the public server asks for. A function that does
   nothing, as here, removes the pause and takes about 70 seconds off a map.

2. Use the providers where the script used the public ones. `examples/route_map.py`'s `main`
   takes them as arguments. In your own script they go to `fetch` and to `Cache.key`:

   ```python
   route = Track.from_gpx(Path("route.gpx"))
   cache = Cache(Path("cache"))
   style = Style.default()
   basemap = fetch(route, cache, features, elevation, style)
   plates = paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))
   lettering = letter(plates, basemap, None, style)
   card = compose(plates, lettering, basemap, style)
   Path("out").mkdir(exist_ok=True)
   card.save("out/self-hosted.png")
   ```

   The imports are `Cache`, `OpenTopoData`, `OverpassFeatures`, `Style`, `Track`, `compose`,
   `fetch`, `letter` and `paint` from `pyntpot.maps`, and `Path` from `pathlib`.

3. To send the requests through authentication, a proxy or your own certificate authority,
   build an `httpx.Client` set up that way and pass it as `client=` to either provider.
   Every request goes through it. You own the client and close it yourself.

4. Run the script. One map sends two queries to Overpass and 64 calls to OpenTopoData. The
   elevation grid is 80 by 80 points, at 100 points a call.

## Result

The card is painted from your servers' data. The cache directory holds the same three
payload files as a public run, and the credit on the card is the same.

The cache key has two consequences. It is made from the track's box and the providers'
ids. An id is `overpass` or `opentopodata-<dataset>`, never an address. So your server reuses a
payload cached from the public server, and the other way round. To fetch again from your own
server, delete the payload files or call `Cache.ensure(..., force=True)`. A different dataset
has a different id, so it gets its own key.

## When it goes wrong

- `FetchError: a provider could not answer: every Overpass endpoint refused the query`: the
  log line above it, `overpass <url> refused the query: ...`, gives the reason httpx
  reports. `[Errno 111] Connection refused` means nothing is listening. A status such as
  `Client error '404 Not Found'` means a wrong path. The URL must be the interpreter's,
  ending in `/api/interpreter` on a standard install.
- `FetchError: a provider could not answer: opentopodata-srtm30m request failed: ...`: the
  reason follows. A `404` is usually the dataset's name, which must be the one your server
  loads, or a base URL that already ends in the dataset.
- `FetchError: a provider could not answer: opentopodata-srtm30m said 'INVALID_REQUEST'`:
  the server answered but refused the request. pyntpot asks for 100 locations a call, so a
  server set to allow fewer refuses it. Raise its limit to 100 or more.
- `FetchError: a provider could not answer: opentopodata-srtm30m answered something unreadable`:
  the reply was not the JSON an OpenTopoData server sends. A proxy that answers with a
  login page causes this.
- `FetchError: a provider could not answer: Overpass budget of 100 queries spent on this
  provider`, or `opentopodata-srtm30m would pass its budget of 1000 calls`: the instance
  has spent its budget. Pass a larger `budget=`. The count is per instance, so a new
  instance starts at zero again.
- `ValueError: Overpass needs at least one endpoint`: the endpoints tuple is empty. A
  single address needs its trailing comma, `("http://...",)`. Without it you have a string.
- The map has no relief, or the land is flat: OpenTopoData's reply had no elevation for
  those points, and pyntpot reads that as `0.0`, sea level. Check that your dataset covers
  the track.
- The card says "elevation: NASA SRTM" over another dataset: the credit comes from the
  provider class and does not follow the dataset. See
  [Credit the map data](credit-the-map-data.md).
