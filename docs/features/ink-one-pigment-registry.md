# One pigment registry, and layers that take a pigment by name

GitHub issue: [#72](https://github.com/findlaywebb/pyntpot/issues/72)

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

**Aliases and plain colour names** (maintainer, 2026-10-25). Each pigment carries a list
of aliases, so an example can ask for a colour by an ordinary name (`blue`, `green`,
`brown`) or a painter's name (`ultramarine`, `sap_green`) and reach the same pigment, and
the map roles become aliases rather than the only names. Today an example that is not a
map still borrows the map's role names as its colours, which reads oddly, for example:

```python
SHAPES: dict[str, list[list[Polar]]] = {
    "water": [_petal(0.12, 0.58, 14.0, 11.0)],
    "wetland": [_petal(0.20, 0.56, 30.0, 4.5)],
    "wood": [[(0.60, 30.0), (0.78, 21.0), (0.94, 30.0), (0.78, 39.0)]],
    "heath": [_disc(0.76, 0.0, 0.07), [(0.11, 30.0), (0.11, 90.0), (0.11, 150.0)]],
}
```

where the keys are colours for a kaleidoscope, not land cover. With aliases the same code
names the colours it means.

**Why it is not a defect.** The tables work and are documented; the cost is in every
caller, and in a second table pair added this round (ADR 0039) instead of one model.

**Possible shape.** A frozen `Pigment` dataclass and a `pigments` registry in
`ink/pigment.py`; `PigmentLayer` accepting `(density, str | Pigment | RGB)` with an
optional override; `composite` and `multiply_plate` resolving names; themes naming
pigments by the same keys. The four old tables kept as deprecated views for one minor
release, then removed. A public API change, so an ADR (superseding the table shape of 0039),
the glossary rows, and the examples, tutorial and reference pages rewritten to the shorter
form. Pixels must not move: a test paints the reference sheets both ways and compares.
