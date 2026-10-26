# Credit the map data

Every map pyntpot paints is built from OpenStreetMap data and NASA elevation data, and
both ask to be credited when you share the map. pyntpot writes the credit onto the card
for you, at the bottom right. Most of the time you only need to leave it there and check
it can be read.

This page is practical guidance, not legal advice. It follows the OpenStreetMap
Foundation's [attribution guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines)
and its [guideline for maps and other produced works](https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline).
[Data policy](../explanation/data-policy.md) explains the reasoning.

## Steps

1. Leave the credit on. `compose` and `pyntpot map` both write it unless you turn it off.
   With the standard providers it reads:

   ```text
   © OpenStreetMap contributors (openstreetmap.org/copyright) · elevation: NASA SRTM
   ```

   That is what OpenStreetMap asks for on a map. You can share the map under any licence
   you like, as long as the credit goes with it.

2. Check you can read it at the size you publish. The credit is part of the picture, so a
   thumbnail or a scaled-down image can make it too small to read. If it is, put the same
   credit in text beside the image as well.

3. If you turn the credit off (`--no-attribution`, or `compose(..., attribution=False)`),
   add it yourself beside the image: in a caption if you can, otherwise a footnote or an
   acknowledgements page. Make it a link where you can. For example:

   ```text
   Map data © OpenStreetMap contributors, available under the Open Database Licence:
   openstreetmap.org/copyright. Elevation: NASA SRTM via OpenTopoData.
   ```

   For a restyled map like a watercolour, OpenStreetMap also accepts a shorter credit such
   as "Map data from OpenStreetMap".

4. To build the credit in code, read it from the basemap. Each credit has the full `text`,
   a link in `url`, and the `short` line drawn on the card:

   ```python
   for credit in basemap.credits:
       print(f"{credit.text}: {credit.url}")
   ```

   ```text
   © OpenStreetMap contributors: https://www.openstreetmap.org/copyright
   Elevation: NASA SRTM via OpenTopoData: https://www.opentopodata.org/
   ```

5. Sharing the data itself is different from sharing a picture. The cache directory,
   `vector_layers` and `candidate_export` give you OpenStreetMap data in other forms. If you
   publish a substantial part of that data, the Open Database Licence asks you to share it
   under the same licence. A painted map on its own does not count.

## Result

Every copy of the map you share carries the credit, either on the card or beside it, with
the `openstreetmap.org/copyright` address.

## When it goes wrong

- **No credit at the bottom right.** It was turned off with `--no-attribution` or
  `attribution=False`. Follow step 3.
- **The credit is there but too small to read.** The image was scaled down. Follow step 2.
- **You run your own elevation server with different data, and the card still says "NASA
  SRTM".** The credit comes from the provider, not the data it serves. Turn the credit off
  and write your own, covering OpenStreetMap and your elevation source
  ([Self-host the providers](self-host-providers.md)).
