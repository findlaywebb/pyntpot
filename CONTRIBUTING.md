# Contributing

## The gate

Run this before every commit. It is what CI runs.

```bash
uv sync && uv run prek run --all-files && uv run pytest
```

A red gate means fix the code. Never loosen a contract or a budget to get green. Changing
a contract is an ADR in `docs/decisions/`.

`numpy`, `pillow` and `fonttools` are pinned exactly for the golden parity test, and Dependabot ignores them.

## Spec flow

One feature is one spec dir under `specs/NNN-name/`, one branch and one pull request.
Write `spec.md`, then `plan.md`, and have the plan reviewed before any code. See
`specs/README.md`.

Three skills under `.claude/skills/` are copied from an MIT-licensed upstream; see
`.claude/skills/THIRD-PARTY-LICENSES.md`.

## Commits

- Imperative, one line.
- No co-authorship trailers.

## Place names in tests and examples

Use real UK countryside names, spread across regions so no file clusters round one area.
A few landmark city names are fine. Never invent a name. Where a string is drawn,
measured or compared, pick a real name of the same length.

- **Towns and villages:** Abergavenny, Ambleside, Aviemore, Bakewell, Braemar,
  Brecon, Buxton, Castleton, Crickhowell, Glencoe, Grasmere, Hawes, Keswick,
  Malham, Monmouth, Pitlochry, Settle, St Ives, Zennor.
- **Rivers:** Dee, Derwent, Eden, Exe, Kennet, Medway, Severn, Tay, Tweed, Usk.
- **Roads:** A470, A5, A66, A591, A82, A9, B4521.
- **Parks and landmarks:** Regent's Park, Dovedale, Malham Cove, Cat Bells, Snowdon.

Coordinates always stay inside the Lynmouth fixture box. Names that belong to the
Lynmouth fixture (Lyn, Heddon, Brendon, Watersmeet) stay as they are.

## Security scanning

CodeQL runs through GitHub's default setup, not a workflow file in this repository.
Report vulnerabilities as described in `SECURITY.md`.
