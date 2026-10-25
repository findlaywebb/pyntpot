# Architecture Decision Records

One file per decision, `NNNN-title.md`, append-only (supersede, don't rewrite). Add an ADR
for any change to a boundary, a port, or a public API surface. A red architecture gate is
the contract speaking — change the ADR first, then the checks, never the other way round.

## Index

| ADR | Decision |
|---|---|
| 0001 | Agentic gates |
| 0002 | Layered package, enforced by import-linter and AST tests |
| 0003 | Card frame and typed seam |
| 0004 | Provider protocols, usage limits and the fetch cache key |
| 0005 | Style groups |
| 0006 | Golden regeneration |
| 0007 | Public API |
| 0008 | Hand writes settings |
| 0009 | Candidates |
| 0010 | Layers contract and the end of the port package |
| 0011 | Coverage baseline |
| 0012 | Mutation threshold |
| 0013 | The name and the layered package (points to 0002, 0010) |
| 0014 | How the code was ported |
| 0015 | Pydantic at the boundary only |
| 0016 | Providers as protocols, attribution on by default (points to 0004) |
| 0017 | The fetch cache key (points to 0004) |
| 0018 | Build backend and versioning |
| 0019 | The upstream SVG page consumes public pipeline stages (points to 0007) |
| 0020 | The default style is the resolved one (points to 0005) |
| 0021 | Every technique cites its source |
| 0025 | Second golden regeneration |
| 0026 | Widen the public API |
| 0027 | Candidate export, vector layers and route ink |
| 0028 | Fetch wraps provider errors |
| 0029 | Provider errors public and the cache wraps |
| 0030 | Smoke lock tolerant on CI |
| 0031 | Third golden regeneration: the East Lyn label |
| 0032 | Focus-place fixtures (amends D10) |
| 0033 | Docs images and examples (amends 0006 and 0026) |
| 0035 | Lettering name tags (amends 0005) |
| 0036 | Fourth golden regeneration: the engine fixes of revision round 1 |
| 0037 | Showcase style fields (amends 0005) |
| 0038 | Journal notes |
| 0039 | Painter's pigments |
| 0040 | Fetch margins (amends 0004 and 0029) |
