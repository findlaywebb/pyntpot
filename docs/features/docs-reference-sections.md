# The API reference pages could be grouped into sections

GitHub issue: [#190](https://github.com/findlaywebb/pyntpot/issues/190)

**What exists today.** Each API reference page (`docs/reference/ink.md`, `letters.md`,
`maps.md`) lists its layer's public names in one run. `pyntpot.maps` exports 52 names,
up from 21 before ADR 0068 made every type a public signature reaches public, so its page
is a long list with no way in. Each layer package's docstring already groups its names by
task.

**What the feature would add.** Each reference page split into sections that mirror the
package docstring's task groups, so a reader finds the records `fetch` returns, the style
groups and the providers under their own headings.

**Possible shape.** One heading a task group, each with its own directives, in the order
the package docstring gives. `tests/architecture/test_site.py` keeps checking that every
public name is rendered once.

**Related.** `docs-defaults-render-as-values.md`.
