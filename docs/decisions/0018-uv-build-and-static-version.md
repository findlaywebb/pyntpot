# 0018 — Build backend and versioning

Status: accepted

## Context

A pure Python package with no compiled code needs a simple, reproducible build, and a
version that cannot drift between the metadata and the code.

## Decision

The build backend is `uv_build` (`[build-system]` in `pyproject.toml`, with its version
range pinned). The version is static, the `version` field of `[project]`, and is bumped
with `uv version --bump`. `pyntpot.__version__` is read from the installed
distribution's metadata, so there is one source of truth.

## Consequences

- No dynamic version plugin and no version string in the source.
- A release is a bump commit, then a tag; the publishing workflow is
  `.github/workflows/publish.yml`.
