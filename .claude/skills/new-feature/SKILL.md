---
name: new-feature
description: Scaffold and drive a new feature through the spec-first agentic workflow — creates specs/NNN-name/{spec,plan,tasks}.md and drives it to "green CI + matches spec". Use when starting any feature, when the user says "new feature", "spec this", "let's build X", or names a feature with no existing specs/ dir.
---

# New feature (spec-first, agentic)

One feature = one spec dir = one branch = one PR. Done = green CI + matches spec.
**Never start implementation from a chat message alone — the spec is the artifact.**

This project is built agentically (`docs/decisions/0001-agentic-gates.md`): the gate stack
and a **plan-reviewer agent** replace human approval checkpoints. Agents proceed without
waiting for a human to sign off; humans set direction and resolve genuinely open product
questions.

## Steps

1. **Number it**: next `NNN` = highest existing `specs/NNN-*` + 1 (zero-padded). Kebab-case
   name. Create `specs/NNN-name/`.
2. **Interview first, write second** (if a human is available for product direction). Ask
   only the questions that change the shape of the work: scope edges, acceptance criteria,
   what's explicitly out, which layer(s) it touches, whether it changes a port/boundary
   (→ ADR in `docs/decisions/`). Don't ask what `docs/` already answers — read it first.
   **Recommend the best option, don't just enumerate.** When you surface a fork, lead with
   the option that is genuinely best by the standing criteria (best code, behaviour,
   maintainability) and say *why*. If a product fork has no human in the loop, pick the
   best-supported option, record the choice and its rationale in `plan.md`, and proceed.
3. **Write `spec.md`** (template below). Keep it thin — what + acceptance criteria, not
   design. No human approval gate; the spec is the durable record agents execute against.
4. **Write `plan.md`** (template below). This is where the engineering lives: files to
   touch, files to leave alone, the test plan, the delegation map (apply the
   `orchestrate-subagents` calculus), and the file-ownership partition, plus any new
   port/boundary (→ ADR). **Then dispatch a fresh-context `plan-reviewer` agent** (sceptical
   staff engineer) over the plan; it **blocks** — do not start implementation until it
   passes. Address its findings and re-run if needed. (This replaces the human plan
   checkpoint.)
5. **Write `tasks.md`**: dependency-ordered checklist. Implement test-first on a feature
   branch (the `test-driven-development` skill), ticking tasks off; commit working
   checkpoints. Review your own diff in two ordered passes: **spec/plan compliance first**
   (does the diff do what `spec.md`/`plan.md` say, and nothing they exclude?), **quality
   second**.
6. **Fresh-context gates before the PR**: a fresh-context diff review **against the plan**,
   then an elegance pass over the feature diff. Triage findings yourself: accept/reject with
   reasons, apply accepted rewrites on green, commit before handoff.

## Sizing rule

Size by reviewability and agent reliability, not build effort. Decompose into multiple specs
when the diff wouldn't be reviewable in one ~15–20 minute pass, or the implementation run
would span many context windows — agents hit a reliability cliff as task length grows.

## spec.md template

```markdown
# NNN — {Feature name}

## Problem
{2–4 sentences: current vs desired behaviour, why now.}

## Acceptance criteria
- [ ] {Testable, observable outcomes — these become tests.}

## Out of scope
- {Explicit non-goals — the scope-creep fence.}
```

## plan.md template

```markdown
# NNN — plan

## Approach
{The how, in a paragraph. Name the layer(s); flag any port/boundary change (→ ADR).}

## Files to touch
- `path` — {what changes}

## Files to leave alone
- `path` — {why it's tempting and why not}

## Test plan
{Unit / architecture / golden tests; what each acceptance criterion maps to.}

## Delegation
{The orchestrate-subagents calculus, applied at plan time: which work is dispatched
(plan-time reads, the plan-reviewer gate, the diff review, the elegance pass, isolated
tasks), at which model; what stays in the main context and why. Name the integrator's job:
full gate suite + seam verification after each track.}

## File-ownership partition
{Carve the implementation into file-disjoint tracks; name the files each owns and the
dispatch order (A→B→…, dependency-aware). A clean partition enables serial
execute-context dispatch and, only if work runs concurrently, worktree isolation.}

## Decisions
{Open questions resolved during planning — including any product fork picked with no human
in the loop, with its rationale; ADR links if any.}
```

## tasks.md template

```markdown
# NNN — tasks

- [ ] {Ordered, dependency-aware steps. Small enough to commit after each.}
```
