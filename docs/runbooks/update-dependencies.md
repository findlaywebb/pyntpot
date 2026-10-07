# Runbook: updating dependencies

## Python (uv)

```bash
uv sync --upgrade            # refresh the lock to the latest allowed versions
uv run pytest                # prove the suite still passes
uv audit --preview-features audit-command   # OSV advisory scan (also a CI gate)
```

CI syncs with `--locked --preview-features malware-check` (aborts before running a package
flagged by an OSV MAL advisory) and runs `uv audit`. Commit the updated `uv.lock`.

`numpy`, `pillow` and `fonttools` carry floors in `pyproject.toml`, and `uv.lock` holds
their exact versions. The golden parity test stays exact, so move them one commit at a
time, with the parity test still passing; a bump that moves golden pixels is a
regeneration decision, not a loosened tolerance.

Keep the pinned uv version in `.github/workflows/ci.yml` in step with what the project
actually uses.
