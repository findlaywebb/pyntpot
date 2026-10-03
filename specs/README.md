# specs/

The durable planning artifact: **one feature = one spec dir = one branch = one PR.**
The spec persists and evolves with the feature; the chat does not survive, the spec does.

```
specs/NNN-feature-name/
  spec.md     # WHAT — problem, acceptance criteria, explicit out-of-scope
  plan.md     # HOW — approach, files to touch, files to LEAVE ALONE, test plan, delegation
  tasks.md    # SEQUENCE — dependency-aware checklist, ticked off during implementation
```

Numbering: zero-padded, monotonically increasing (`001-…`). Never reuse a number. A
sub-spec (`NNNa`, `NNNb`) is a spin-off of `NNN` (a deferred slice or a hardening pass) and
does not consume a roadmap integer.

## The gate, not a human checkpoint

This project is built agentically (`docs/decisions/0001-agentic-gates.md`): there is **no
human spec/plan approval gate**. Instead:

1. Write `spec.md` — what + acceptance criteria, kept thin.
2. Write `plan.md` — the engineering: files to touch, files to leave alone, the test plan,
   the delegation map. A **plan-reviewer agent** (fresh context, sceptical staff engineer)
   reviews it and **blocks** until it passes — this replaces the human plan checkpoint.
3. Write `tasks.md` and implement test-first against the plan, committing working checkpoints.
4. A fresh-context agent reviews the diff **against the plan**, then an elegance pass runs.

**Done = green CI + matches spec.** A "ticket"/backlog item = a spec stub with acceptance
criteria. No spec → not in the queue.

Use the `new-feature` skill (`.claude/skills/new-feature/`) to scaffold a spec dir.
