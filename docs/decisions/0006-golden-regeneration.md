# 0006 — Golden regeneration

Status: proposed

## Context

The golden plates in `tests/golden/lynmouth/` were painted by the pre-port code. Three
changes the port needs move what those goldens record: the base hash takes its final
form (the typed basemap's canonical text and the base style digest, in place of a
hand-kept payload key list and the digest of every painter field), the seam between the
basemap and the painter stops rounding geometry to a tenth of a metre, and duplicated
polyline helpers are merged. The hash moves for certain; pixels may move by a bounded
amount.

Regenerating after each change would let a bug become golden unseen, and regenerating
never would leave the goldens describing code that no longer exists. So the changes land
inside one regeneration window: a run of commits, each compared against the output of
the commit before it on the same machine, with the goldens regenerated once at its end.

## Decision

Each step of the window is one commit. Before it is committed, the Lynmouth fixture is
painted and compared with the previous step's output, under gate options that say what
the step may move. A step whose compare fails is not committed. The committed goldens are
compared too, as the cumulative record, but that compare is not a gate. The tolerance
bound in `tests/golden/test_parity.py` (`MAX_DIFFERING_FRACTION = 0.005`,
`MAX_CHANNEL_DELTA = 2`) is not changed.

The hash input is final from the first step: compact sorted-key JSON of the card's box,
display grid, render grid and both scales and every `Layers` field, with every float
written to three decimals and negative zero written as zero. The manifest hash is the
first 16 hex digits of its SHA-256, a hyphen, and the style's base digest.

### Steps

| Step | Commit | Expected | Gate options |
|---|---|---|---|
| 0 | `020c3ff` | baseline, made on the window's starting commit | none |
| 1 | `Hash plates from the typed basemap and the style groups` | all five outputs byte-identical to step 0; the hash differs | `--require-identical all --require-hash differ` |

Step 1 wires the grouped style into the painter: the flat painter style, the effective
basemap options and the route ink all come from the packaged default theme, and the base
digest goes into the hash. It also changes the painter's consumer-only `label_font`
default to the vendored face; nothing in the painter reads it.

Step 1 compare, against step 0 (the gate):

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical yes, differing fraction 0.000000
map.png: identical yes, differing fraction 0.000000
manifest hash: 87624a4cd49063df-e5a5f1b4b3ca2177 here, c034e1a4d60bad70-77dce82bec370944 in step 0
```

Step 1 compare, against the committed goldens (cumulative record):

```
paper.webp: identical no, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.000000
map.png: identical no, differing fraction 0.000000
manifest hash: 87624a4cd49063df-e5a5f1b4b3ca2177 here, c034e1a4d60bad70-77dce82bec370944 in the goldens
```

The four outputs that are not byte-identical to the committed goldens were already so on
the starting commit, in this environment; they are within the channel bound everywhere.

### Hashes

- Old manifest hash (the committed goldens): `c034e1a4d60bad70-77dce82bec370944`.
- New manifest hash after step 1: `87624a4cd49063df-e5a5f1b4b3ca2177`, whose suffix is
  the default style's pinned base digest.

## Consequences

- Inside the window the golden-marked tests are known stale: the manifest-hash parity test
  fails until the goldens are regenerated, and the pixel cases still pass in tolerance.
- The hash no longer depends on any hand-kept key list, and a last-bit difference in a
  machine's maths library cannot move it.
- A lettering-only or route-ink style change no longer moves the base hash.
