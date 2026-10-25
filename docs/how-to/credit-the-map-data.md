# Credit the map data

You want to publish a map you painted and credit its data as the data's licences ask. The
card draws the credit for you unless you turn it off. The work is knowing what the credit
says and what you owe when it is not on the card.

This guide is practical, not legal advice. It draws on the OpenStreetMap Foundation's
[attribution guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines) and
its [guideline for Produced Works](https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline).
[Data policy](../explanation/data-policy.md) explains why.

You need a painted card and a decision about where it will be shown.

## Steps

1. Leave the credit on the card. `compose` writes it by hand at the bottom right, and so
   does `pyntpot map` unless you pass `--no-attribution`. With the shipped providers it
   reads:

   ```text
   © OpenStreetMap contributors (openstreetmap.org/copyright) · elevation: NASA SRTM
   ```

   The first part is the credit OpenStreetMap asks for on a map that shows its data, with
   the address of its copyright page. A map is a Produced Work under the Open Database
   Licence (ODbL). You may share it under any licence you like, if it carries this credit
   when it is published.

2. Check that you can read the credit where the map is shown. It is lettered small, and it
   is part of the picture. A card scaled down for a web page or a thumbnail can lose it. If
   you cannot read it at the size you publish, also put it in text beside the image.

3. If you turn the credit off with `--no-attribution`, or `compose(..., attribution=False)`
   in a script, the duty is yours. Credit the data beside the image: in a caption, a
   footnote or an acknowledgements page, in that order of preference. Make the credit a
   link where the page allows one. This wording meets the guideline:

   ```text
   Map data © OpenStreetMap contributors, available under the Open Database Licence:
   openstreetmap.org/copyright. Elevation: NASA SRTM via OpenTopoData.
   ```

   For restyled data, such as a watercolour map, the OpenStreetMap guidelines also accept a
   qualified credit like "Map data from OpenStreetMap".

4. To build the line from what your run used, read the credits the basemap carries. Each
   has the full `text`, a link in `url` and the `short` line drawn on the card:

   ```python
   for credit in basemap.credits:
       print(f"{credit.text}: {credit.url}")
   ```

   ```text
   © OpenStreetMap contributors: https://www.openstreetmap.org/copyright
   Elevation: NASA SRTM via OpenTopoData: https://www.opentopodata.org/
   ```

5. If you share more than the picture, think about the data itself. The cache directory,
   `vector_layers` and `candidate_export` give you OpenStreetMap data in other forms. If
   you republish a substantial extract, it is a Derivative Database, and the ODbL asks you
   to share it under the same licence. A painted card is not one.

## Result

Every published copy of the card carries the credit, on the card or beside it, with the
`openstreetmap.org/copyright` address.

## When it goes wrong

- The credit at the bottom right is missing: `--no-attribution` or `attribution=False` was
  set. Follow step 3.
- The credit is there but you cannot read it: the picture has been scaled down, or the card
  is small. Follow step 2 and credit in text beside the image.
- You serve another elevation dataset from a self-hosted server and the card still says
  "elevation: NASA SRTM": the credit comes from the provider class, so it names SRTM
  whatever dataset the server serves. Turn the credit off and write your own. Cover
  OpenStreetMap and your elevation source
  ([Self-host the providers](self-host-providers.md)).
- `FetchError: a provider could not answer: Overpass budget of 100 queries spent on this
  provider`: the provider has spent its budget. The defaults keep to the public servers'
  published limits. Overpass asks for well under 10,000 queries and 1 GB a day. The public
  OpenTopoData server allows 100 locations a call, one call a second and 1000 calls a day.
  For heavier use, run your own servers and raise the budgets
  ([Self-host the providers](self-host-providers.md)).
