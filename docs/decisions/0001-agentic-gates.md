# 0001 — Gates are the source of truth; no human approval gates

Status: accepted

## Context

This project is built agentically: agents do most of the work end to end, with far fewer
manual approval points than a human-in-the-loop workflow. A workflow that blocks on a human
to approve a spec and then a plan (the pattern the template was derived from) does not fit —
the human is not in the loop on every feature, so a checkpoint that waits for them stalls
the agent rather than improving the outcome.

## Decision

The **deterministic gate stack is the source of truth**, not human approval:

- ruff (format + a wide lint set), `ty` (the sole type gate), import-linter, the AST
  architecture fitness tests, and `pytest --cov`.
- A **plan-reviewer agent** (fresh context, sceptical staff engineer) reviews each `plan.md`
  and **blocks** until it passes — replacing the human plan-approval checkpoint. There is no
  human spec-approval gate; the spec is still the durable artifact agents execute against.
- A fresh-context diff review and an elegance pass run before merge, as agents, not humans.

A red gate means "fix the code", never "loosen the contract". Changing a contract (a
boundary, a port, the coverage bar) is itself an ADR.

## Consequences

- The gates must be strong enough to catch what a human reviewer would: keep the lint set
  wide, the boundary contract machine-checked, coverage meaningful, and add gates rather
  than prose when a class of mistake recurs.
- Strengthen the gates as the project matures: set a coverage threshold, and run mutation
  testing in CI.
- Humans still set direction and resolve genuinely open product decisions; they are removed
  from the *mechanical* approval path, not from the project.
