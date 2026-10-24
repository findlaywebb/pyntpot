# Credit the map data

You want to publish a map you painted, and to credit its data the way the data's licences
ask. The card draws the credit for you unless you turn it off, so the work is knowing what
it says, and what you owe when it is not on the card.

This guide is practical, not legal advice. Its sources are the OpenStreetMap Foundation's
[attribution guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines) and
its [guideline for Produced Works](https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline).
[Data policy](../explanation/data-policy.md) explains the reasoning.

You need a painted card and a decision about where it will be shown.

## Steps

1. Leave the credit on the card. `compose` writes it by hand at the bottom right, and
   `pyntpot map` does too unless you pass `--no-attribution`. With the shipped providers it
   reads:

   ```text
   © OpenStreetMap contributors (openstreetmap.org/copyright) · elevation: NASA SRTM
   ```

   The first part is the credit OpenStreetMap asks of a map that shows its data, with the
   address of the copyright page. A map is a Produced Work under the Open Database Licence
   (ODbL), and you may share it under any licence you like, provided it carries this credit
   when it is published.

2. Check that it can be read where the map is shown. The lettering is small, 11 display
   pixels, and it is part of the picture, so a card scaled down for a web page or a thumbnail
   can lose it. Where the credit cannot be read at the size you publish, put it in text
   beside the image as well.

3. If you turn the credit off with `--no-attribution`, or `compose(..., attribution=False)`
   in a script, the duty moves to you. Credit beside the image, in a caption, a footnote or
   an acknowledgements page, in that order of preference, and make the credit a link where
   the page allows one. Wording that meets the guideline:

   ```text
   Map data © OpenStreetMap contributors, available under the Open Database Licence:
   openstreetmap.org/copyright. Elevation: NASA SRTM via OpenTopoData.
   ```

   The OpenStreetMap guidelines encourage a qualified credit such as "Map data from
   OpenStreetMap" when the data has been restyled, as a watercolour map has, and that is
   acceptable too.

4. To build the line from what your run used, rather than typing it, read the credits the
   basemap carries. Each has the full `text`, a link in `url` and the `short` line drawn on
   the card:

   ```python
   for credit in basemap.credits:
       print(f"{credit.text}: {credit.url}")
   ```

   ```text
   © OpenStreetMap contributors: https://www.openstreetmap.org/copyright
   Elevation: NASA SRTM via OpenTopoData: https://www.opentopodata.org/
   ```

5. If you share more than the picture, think about the data itself. The cache directory,
   `vector_layers` and `candidate_export` hand you OpenStreetMap data in other forms. A
   substantial extract that you republish is a Derivative Database, and the ODbL asks that
   you share it under the same licence. A painted card is not one.

## Result

Every published copy of the card carries the credit, on the card or beside it, with the
`openstreetmap.org/copyright` address.

## When it goes wrong

- The credit at the bottom right is missing: `--no-attribution` or `attribution=False` was
  set. Follow step 3.
- The credit is there but you cannot read it: the picture has been scaled down, or the card
  is small. Follow step 2 and credit in text beside the image.
- You use another elevation dataset on a self-hosted server and the card still says
  "elevation: NASA SRTM": the credit comes from the provider class and names SRTM whatever
  dataset the server serves. If your dataset is another, turn the credit off and write your
  own, covering OpenStreetMap and your elevation source ([Self-host the providers](self-host-providers.md)).
- `FetchError: a provider could not answer: Overpass budget of 100 queries spent on this
  provider`: the provider has spent its budget. The defaults keep to the public servers'
  published limits: Overpass asks for well under 10,000 queries and 1 GB a day, and the
  public OpenTopoData server allows 100 locations a call, one call a second and 1000 calls a
  day. For heavier use, run your own servers and raise the budgets
  ([Self-host the providers](self-host-providers.md)).
