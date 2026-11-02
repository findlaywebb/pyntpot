# The tests could move off Lynmouth

GitHub issue: [#82](https://github.com/findlaywebb/pyntpot/issues/82)

**What exists today.** Lynmouth, Devon is the one test place (D10): the
recorded provider payloads, the track, every golden and every map test read
`tests/fixtures/lynmouth/`. The docs focus on other places (the Lake District,
Skye, Eryri, Keswick, Ambleside, Oxford, Y Fenni), each with its own recorded
fixture.

**What the feature would add.** The goldens and the map tests move to the focus
places, and the Lynmouth fixture, its golden directory and its coordinate box
are deleted.

**Why it is not a defect.** Lynmouth stays the test place while the API and the
painted look are still settling, because moving it regenerates every golden
(maintainer, 2026-10-23, P7 research Q-P2).

**Possible shape.** One golden regeneration window under the golden ADR
process, after a stable release: new goldens from one or two focus-place
fixtures, the coordinate gate's Lynmouth box removed, the fixture README and
CONTRIBUTING updated.
