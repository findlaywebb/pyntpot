# Three benchmark pairs measure the same thing

P5.4 kept every benchmark from both sources: the four the plan named and the
seventeen from CodSpeed's onboarding PR. Where they overlapped, both versions
stayed with different inputs. Three pairs time the same operation at the same
cost:

| Operation | Plan benchmark | Onboarding benchmark | CodSpeed simulation |
| --- | --- | --- | --- |
| Sheet construction | `test_ink.py::test_sheet_construction` | `test_ink.py::test_building_a_sheet` | 735.8 ms and 736.8 ms |
| Distance transform | `test_ink.py::test_edt` | `test_ink.py::test_the_distance_transform` | 91.5 ms and 91.5 ms |
| Wash | `test_ink.py::test_wash` | `test_ink.py::test_laying_a_wash` | 208.5 ms and 208.5 ms |

Each pair adds CodSpeed run time and a second line to every report without
adding a signal: a regression in one shows identically in the other.

Possible fix: drop one benchmark of each pair, keeping the name that reads
better as a sentence (the onboarding names, "building a sheet", "laying a
wash", "the distance transform", match the rest of the file). Removing a
benchmark ends its CodSpeed history, so do it in one commit and note it in
`docs/explanation/performance.md`.
