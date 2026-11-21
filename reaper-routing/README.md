# reaper-routing

Route a REAPER project for live multitrack recording and virtual soundcheck without clicking through 64 tracks:
record inputs, hardware outputs (1:1, offset, stereo pairs), master send, track names from the console show
(LV1 `.emo`, X32 `.scn`, WING `.snap`, text list) and a rec / play switch. See [SKILL.md](SKILL.md) for the
commands and [reference/rpp-format.md](reference/rpp-format.md) for the format.

## Status

- Script tested on a REAPER 7.35 / Windows 64-track project (2026-11-21): only the intended lines change, CRLF kept.
- REAPER load of a script-written project: **not yet confirmed** (see `reference/rpp-format.md`, Open).

## Tests

```sh
python3 -m unittest discover -s tests -t tests
```
