# A theme could declare only what it changes, in YAML

**What exists today.** A theme is a TOML file that `Style.from_toml(path)` loads, and it
needs every group present. Each example theme in `examples/themes/` is a full copy of
`maps/themes/default.toml`, about 355 lines, of which it changes 31 to 56. A change to the
default theme has to be copied into ten files by hand.

**What the feature would add.** Themes written in YAML that name a base theme and give only
their overrides, merged over the base when loaded:

```yaml
extends: default
route_inks:
  hike:
    pigment: perylene_maroon
cover:
  relief_strength: 0.6
```

**Why it is not a defect.** Full theme files are the shipped design: `from_toml` checks
every group is present, which catches a missing field at load time.

**Possible shape.** `Style.from_yaml(path)` and a deep merge over the base theme, with
validation of the merged result (an unknown key is still an error); the example themes
rewritten as overrides; TOML kept or retired by an ADR; the digest computed from the merged
style, so an override file and its expanded copy give the same digest. Pairs with named
themes (`maps-named-themes.md`), the pigment registry (`ink-one-pigment-registry.md`) and
data-driven brushes and pigments (`ink-data-driven-brushes-and-pigments.md`).
