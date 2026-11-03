# Setting.wash is named for the backing wash

GitHub issue: [#TBD](https://github.com/findlaywebb/pyntpot/issues/TBD)

Area: letters.

`Setting.wash` in `letters/setting.py` is "Whether the backing wash is lifted under the
marks". `GLOSSARY.md` names that patch the backing wash, and keeps wash for a layer of
pigment laid over a coverage mask (`pyntpot.ink.wash`). A caller reading
`Setting(wash=False)` can take it to mean the name is not painted in a wash.
`NibStyle.label_wash` in `letters/style.py` says the same thing for the whole nib.

Possible fix: rename the field to `backing_wash` (and `label_wash` to
`label_backing_wash`), with an ADR, since `Setting` is public and themes carry
`label_wash`.
