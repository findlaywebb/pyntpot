# Label placement could find better seats, and show why it chose them

GitHub issue: [#113](https://github.com/findlaywebb/pyntpot/issues/113)

**What exists today** (as of PR #112, `fix/53-river-name-clipped`, where the water costs
land; line numbers are that branch's). `place` puts every name in its cheapest seat, one at
a time in tier order (`maps/lettering/placement.py:137`), and only afterwards swaps pairs of
flat names whose leaders cross (`placement_leaders.uncross_leaders`, `:155`). A flat seat is
priced as a sum of hand-set constants spread over five modules: `ROAD_CROSS_COST` 90,
`LEADER_COST_PX` 0.4, `LEADER_RUNGS` up to 64 px, `SEPARATION_WEIGHT` 0.55, `ANCHOR_PULL`
0.22 and `WRAP_COST` 26 (`placement_flat.py:59-129`); `WATER_COST` 480 and
`WATER_UNDER_COST` up to 160 (`placement_water.py:36-40`); `ROUTE_ON_COST` 260 and
`SEPARATION_CAP_PX` 90 (`placement_costs.py:34-45`); the dark grid at 150 and a seat off the
paper at 400, inline in `_place_flat` (`placement_flat.py:208-225`). Some of what that adds
up to:

- **One tier's change moves another's names.** Measuring river and road boxes with their
  tracking (#48) changed the separation term every later name is scored on, so on the
  Yr Wyddfa card "Afon Nant Peris" took another window and Crib Goch, Glaslyn and
  Llyn Llydaw other seats.
- **The water costs made some seats worse.** On Oxford, "Christ Church" jumps far
  north-west of its pin, wrapped onto two lines, on a long leader over the route. On
  Yr Wyddfa, "Glaslyn" and "Llyn Llydaw" sit below their lakes on long leaders that cross
  the water, and "Garnedd Ugain" wraps onto two lines it does not need. On Ambleside,
  "Grasmere" sits on its lake's north shore with a leader into the water.
- **The leader is barely priced.** A seat is charged its rung's distance, not the length
  of the leader drawn to it, which is longer on a diagonal; and a pixel of separation
  (0.55) is worth more than a pixel of leader (0.4), so in clear paper the far rung wins.
  A leader is priced for the boxes it cuts (`leader_crossings`, `placement_costs.py:136`)
  and nothing else: not the route, not the water. It is priced as a straight segment but
  drawn bent, by a random fraction of its run (`lettering_furniture.leader`), so a long
  leader drawn can stray from the one priced.
- **The backing wash runs under the furniture.** Pins and leaders go through the nib with
  the name's wash (ADR 0008; `lettering_marks._furniture`, `:218`), so a long leader over a
  lake lifts a pale band across it. PR #112's ADR left this alone because changing it
  changes 0008.
- **Nothing says why a name went where it did.** Tuning means editing a constant,
  repainting and comparing by eye; the before-and-after crops for #53 were cut by hand
  with PIL in a scratchpad.
- #52 stays open for "Cherwell" written along its own stroke and "Magdalen Bridge" set
  across dense roads on Oxford.

`tests/golden/test_places.py:212` now asserts, for every focus place, that no two leaders
cross and that no flat name sits on a lake. Nothing measures how long the leaders are, how
many names wrap, or how many were dropped.

**What the feature would add.** The ask (maintainer, 2026-11-02): "Improve auto label
placement, and better facilitate tuning where labels and leaders fall." Three parts:
placement quality, tuning facilities, and a tool to place names by hand.

*Placement quality*, as candidate directions, each with its cost:

- **Price the leader as drawn**, by its length and its bend, with a hard cap past which a
  seat is not offered. Shorter leaders, but a dense card has fewer
  seats, so more names fall back onto the route or are dropped.
- **Price a wrap against the best one-line seat**, not as a flat 26: a second line only
  when the best one-line seat is materially worse. Fewer needless wraps; a long name in a
  tight spot loses its narrow fallback.
- **Price the leader's crossings of water and the route**, as `leader_crossings` does for
  boxes. Grasmere's and Glaslyn's leaders cross less water; but a lake name pinned in its
  lake always crosses some shore, so the price has to allow its own water or move its pin
  to the shore.
- **Take the backing wash off pins and leaders** (`wash=False` in `_furniture`). No band
  across a lake; a leader over a dark wash reads less well. Decided: both the leaders and
  the pins. It still needs an ADR amending 0008, and a golden regeneration.
- **Look past pure greed.** After the greedy pass, a repair pass reseats the worst-priced
  names against everything else on the card, or a small search re-tries the few names
  near each one that moved. One tier's change then settles locally instead of cascading;
  it costs time per card, and a repair needs a bound so it terminates. Decided: behind a
  switch.
- **#52's two cases**: offset a name set along water clear of its stroke and price the water
  for it, and scale the road cost by how many roads the style draws.

*Tuning facilities*:

- **One home for the weights.** Every placement price in one frozen value, injected (not
  `os.environ`), with the shipped numbers as its defaults. Decided: a theme can tune it,
  in its `[lettering]` table (`LetteringPolicy`, `style_groups.py:233`), so a change
  re-letters without repainting (`lettering_digest`).
- **A placement report.** Per name: the seat chosen, the next few seats tried, and each
  one's cost broken down by term (route, overlap, dark grid, road, water, leader, wrap,
  separation, pull). As data, and as a debug overlay on the card drawing each name's box,
  its runners-up and its leader.
- **A before-and-after compare** for the docs images and goldens: given two lettering
  results for one card, side-by-side crops round every name whose seat moved. Decided: a
  command.
- **Quality metrics on the focus places**: crossed leaders, names on water, mean and
  longest leader, wraps, names dropped. Reported per place on every run; some gated as
  `test_places.py` gates crossings and lakes today (which ones is open).

*An interactive label placement tool* (maintainer, 2026-11-02: "I also want to mock up
label placing tool that lets you drag, click, type. I plan to add more features to this
eventually."):

- It shows a painted card with its names, leaders and pins.
- **Drag** a name to a new seat and its leader follows. **Click** a name to see its cost
  breakdown and its runner-up seats. **Type** to edit a name's text, add a name, or pin
  one where it is.
- What the tool changes is saved as overrides the placer reads, not as edited pixels:
  per-name fixed seats, text overrides and hidden names. A fixed seat could be seated
  first and never moved, as a journal note is (`maps.lettering.notes`), and every other
  name priced round it. The paint stays deterministic, and a card with overrides is
  reproducible and can be pinned in a golden like any other.
- It reads the placement report and overlay above, so the tool and the tests share one
  model of seats and costs: the report is the tool's data, and a seat the tool shows is a
  seat the placer priced.
- It is the first of several tools the maintainer plans here, so its design leaves room
  for more: a small UI shell that a later tool plugs into, and the placement state (seats,
  costs, overrides) as a plain data model that does not depend on the UI.
- Where it lives is open. The layers `maps -> letters -> ink` hold the library; the tool
  is likely outside them (a separate tool, or a CLI command that serves it), with the
  overrides model in `maps`, and `ink` and `letters` still free of `httpx` and
  `pydantic`. What it runs on is open too: a local web page over a saved card and its
  placement as JSON is likely the simplest, since the painted card is already a PNG and
  the report is already data.

**Why it is not a defect.** Each case above is placement working as priced: the seats are
the cheapest the constants allow, and the fixes for #48, #52 and #53 traded one fault for
another within those prices. What is missing is better prices and the means to tune them.

**Possible shape.** The tuning facilities first, because they make the rest measurable: the
weights gathered into one value in the theme's `[lettering]` table with the shipped
numbers (pixels must not move), the report, the metrics and the compare command. The tool
after the report, on the same data. Then the quality changes one at a time, each with its
metrics before and after on the five focus places: the repair pass behind its switch, and
the backing wash off leaders and pins under its own ADR. Outcomes an eventual spec could
adopt:

- Every placement price lives in one typed value a theme can set; the placer reads no
  other constant.
- A test letters a card with two weight sets and the report shows the cost of every term
  for every name.
- On the focus places no leader crosses another, the route or a lake; no flat name sits on
  water; no leader is longer than the cap; no name wraps where its one-line seat is within
  a margin of its best; the names pinned in `test_places.py` are all still placed.
- A card lettered with a fixed seat, a text override and a hidden name paints the same
  pixels on every run, and the other names are priced round the fixed seat.
- Changing one landmark's weights moves no name in another tier unless the report says
  which shared term moved it.

Not in it: what is named (the picks), the hand's lettering and the nib, where a span's
bracket is drawn (`place_spans`), and the backing wash's own shape (ADR 0066). Related: #50 and
#51, which this would likely close or narrow.

**Decided** (maintainer, 2026-11-02):

- Placement weights are tunable by a theme, in its `[lettering]` table: yes.
- The backing wash comes off the furniture: leaders and pins both. Needs an ADR amending
  0008.
- The slower repair pass: behind a switch.
- The before-and-after compare: a command.

**Open questions.**

1. Which metrics are gates, and which are only reported?
2. What form does the placement tool take (a local web page, a desktop app, a notebook
   widget), and where does it live against the layers? Do its overrides belong in the
   theme's TOML, or in a file per card (beside the caller's annotations)?
