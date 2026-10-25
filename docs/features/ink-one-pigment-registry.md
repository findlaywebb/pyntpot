# One pigment registry, and layers that take a pigment by name

**What exists today.** Colour lives in four parallel tables in `pyntpot.ink`: `PIGMENTS`
and `TRANSPARENCY`, keyed by map role (`water`, `wood`, `relief`, ...), and
`PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY`, keyed by painter's name (`ultramarine`,
`burnt_sienna`, ...). A `PigmentLayer` is a tuple of a density, an RGB array and an
optional transparency, so every caller looks the colour up in one table, converts it with
`rgb`, and looks the transparency up in another (15 files under `examples/` and `src/` do
this). Fifteen lines of an example can be lookups.

```python
(
    wash(_disc(W, h, x + w * cx, y + ch / 2, 0.36 * ch), sheet, 0.7, 0.4),
    rgb(PAINTERS_PIGMENTS[key]),
    PAINTERS_TRANSPARENCY[key],
)
```

**What the feature would add.** The goal (maintainer, 2026-10-25) is one lookup, an object
that holds a pigment's information, and inputs that take a base term and work out the rest,
with overrides. The shape below, and the code after it, are a suggestion, not a requirement:

- One `Pigment` object holding everything a pigment is: its colour, transparency, and room
  for the properties a painter cares about (staining, granulation), and one registry of
  them keyed by pigment name. The map roles become names in the same registry (or aliases
  to painter's pigments), not a second table.
- More pigments defined in it.
- Inputs that accept base terms and resolve them inside the method, as matplotlib does
  with colour names: a layer, a brush or a theme takes a pigment name, a `Pigment`, or a
  plain colour, and the library works out the RGB and transparency. Overrides stay
  possible, for example a keyword or `Pigment.replace(transparency=0.3)`.

```python
(
    wash(_disc(W, h, x + w * cx, y + ch / 2, 0.36 * ch), sheet, 0.7, 0.4),
    key,
)
```

**Why it is not a defect.** The tables work and are documented; the cost is in every
caller, and in a second table pair added this round (ADR 0039) instead of one model.

**Possible shape.** A frozen `Pigment` dataclass and a `pigments` registry in
`ink/pigment.py`; `PigmentLayer` accepting `(density, str | Pigment | RGB)` with an
optional override; `composite` and `multiply_plate` resolving names; themes naming
pigments by the same keys. The four old tables kept as deprecated views for one minor
release, then removed. A public API change, so an ADR (superseding the table shape of 0039),
the glossary rows, and the examples, tutorial and reference pages rewritten to the shorter
form. Pixels must not move: a test paints the reference sheets both ways and compares.
