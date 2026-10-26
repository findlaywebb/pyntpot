# ADR 0007 still says the engine names come from `_port`

GitHub issue: [#36](https://github.com/findlaywebb/pyntpot/issues/36)

ADR 0007 says the engine names are "re-exported from `_port` until the split".
The split happened at P4: `src/pyntpot/__init__.py` imports them from `ink`
and `letters`, and `_port` is gone. ADRs are append-only, so the fix is a
short note in a later ADR (or the decisions index) that the sentence is
history, not an edit to 0007.

Found by P7.11 (2026-10-24).
