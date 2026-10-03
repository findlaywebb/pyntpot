---
name: test-driven-development
description: Use when implementing any feature task or bug fix, before writing implementation code — each tasks.md item, each defect. Triggers include "implement the next task", "fix this bug", starting implementation after plan.md review, or noticing implementation code exists with no test yet. Embodies red–green–refactor — write the failing test first and watch it fail for the right reason; a bug fix starts with a failing reproduction test.
---

# test-driven-development

Makes the failing test the first artifact of every task: the check exists *before* the code it constrains, instead of being back-filled to describe whatever got built.

## The one principle

**A test written first answers "what should this do"; a test written after answers "what does this do".** Tests-after pass immediately, which proves nothing — you never saw them catch anything. Watching the test fail is what proves it tests the right thing.

## When to use

- Every implementation task ticked off `tasks.md` — the spec's acceptance criteria become tests, and this is how each one lands.
- Every bug fix: the failing reproduction test comes first, becomes the regression guard.
- Refactors: green suite before, green suite after, no new behaviour.

## When NOT to use

- Exploratory spikes — explore freely to learn the shape, then **throw the spike away** and build test-first from what you learned.
- Architecture tests, gate config, scaffolding with no behaviour of its own.

## The cycle

1. **RED — one minimal failing test.** One behaviour, named for that behaviour, exercising real code (mock only at process/network edges — never the code under test).
2. **Watch it fail** (`uv run pytest path/to/test.py -x`). It must *fail*, not error, and fail because the behaviour is missing — not a typo. A test that passes immediately is testing existing behaviour: fix the test.
3. **GREEN — minimal code to pass.** No extra parameters, options, or generality the test didn't ask for; the rule of three forbids speculative abstraction anyway.
4. **Watch it pass**, with the rest of the suite still green and the output clean.
5. **REFACTOR on green only.** Names, duplication, extraction — no behaviour changes. Then the next failing test.

Commit on green at each working checkpoint.

## Wrote code before the test?

Stop adding to it. Write the test now, watch it fail against a reverted/disabled version of the change, then bring the code back under it. The point isn't ceremony — it's that the test must demonstrably *catch* the absence of the behaviour once. If the test can't be made to fail, it isn't guarding anything.

## Red flags

- A test that never failed in front of you.
- "I'll add tests after this works" — coverage without proof.
- "Too simple to test" — simple code breaks; the test costs 30 seconds.
- Hard to test → the design is hard to use. Listen to it: inject the dependency, simplify the interface. In this codebase that pressure points the same way the boundary rules do (core stays pure, config injected).
- A bug fixed with no reproduction test — the bug is free to return.

## Gotchas

- **Structural invariants are test-first naturals**: rules like "no clock reads in the package" or "no personal content" belong as architecture tests written before the code that could violate them.
- **`tasks.md` granularity is the TDD granularity** — if a task needs five tests, it was five tasks. Feed that back into the plan rather than batching.
