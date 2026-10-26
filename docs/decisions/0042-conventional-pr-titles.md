# 0042 — Conventional PR titles drive the changelog

Status: accepted

## Context

Pull requests are squash-merged, so each one lands on `main` as one commit whose subject is
the PR title. The titles had no fixed form ("P7.R: the 0.1.0 release", "Painter's
pigments"), so `CHANGELOG.md` was written by hand from memory and the PRs, and the 0.1.0
section had to be brought up to date with a revision round after the fact.

## Decision

- **The PR title is a Conventional Commit:** `type(scope): description`, in the imperative,
  British English, no full stop. Types: `feat`, `fix`, `perf`, `docs`, `refactor`, `test`,
  `build`, `ci`, `chore`. The scope is optional and is one of `ink`, `letters`, `maps`,
  `cli`, `docs`, `tests`, the same words as the `area:` issue labels. A breaking change adds
  `!` before the colon (`feat(maps)!: …`).
- **A PR with more than one user-visible change** takes the main one as its title and lists
  the others, one conventional line each, under "Changelog" in its description. The squash
  commit carries the description as its body (the repository's squash default is "pull
  request title and description"; a merge through the API passes the same text), and
  git-cliff reads every conventional line of the body as its own entry
  (`split_commits = true`). Prose lines are not conventional and are dropped.
- **Commits on a branch are not checked.** Only the squash commit reaches `main`.
- **The check.** `.github/workflows/pr-title.yml` fails a PR whose title does not match. It
  reads the title from the event environment, never interpolated into the script.
- **The draft.** `cliff.toml` maps `feat` to Added, `perf` to Changed and `fix` to Fixed,
  puts every `!` change under Breaking changes first, and drops `docs`, `refactor`, `test`,
  `build`, `ci` and `chore`. A release runs `uvx git-cliff@2.14.2 --unreleased --tag vX.Y.Z`
  and pastes the draft into `CHANGELOG.md`, then edits it by hand: the changelog stays
  prose a user reads, in the Keep a Changelog form it already has.

## Consequences

- Each changelog entry traces to a PR, and the release step starts from a draft.
- A PR must be titled for its user-facing effect, which also helps the issue workflow
  (`Closes #N` in the description).
- History before this ADR is not rewritten; git-cliff skips its non-conventional subjects.
