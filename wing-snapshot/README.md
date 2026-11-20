# wing-snapshot

Builds a Behringer WING snapshot from a JSON layout, on top of a blank snapshot saved by WING-Edit.

```sh
python3 scripts/build_wing_scene.py "INIT.snap" examples/layout-explicit.example.json "event.snap" --dry-run
python3 scripts/build_wing_scene.py "INIT.snap" examples/layout-explicit.example.json "event.snap"
```

Prints the number of changed keys, notes (anything not converted or unconfirmed) and the patch sheet; `--changes`
lists every key. Open the result in WING-Edit, save it there, load that save on the desk.

## Status

- Built and spot-checked against a WING-Edit 3.2.1 INIT save (`snapshot.10`, one-line JSON), which round-trips
  byte for byte through the builder.
- 2026-11-20: a generated snapshot (32 inputs, explicit AES50 A / local patch, groups with FX inserts and bus
  dynamics models, FX buses, matrices, DCAs) opened in WING-Edit without any visible error. Individual values not
  yet checked one by one.
- Not yet confirmed field by field: everything marked unconfirmed in `reference/wing-format.md`.

## Tests

`python3 -m unittest discover -s tests -t tests` (synthetic snapshot in `tests/fixtures.py`).

## Credits

Key names and value laws come from the WING notes in
[show-file-skills](https://github.com/michaelkeithlewis/show-file-skills) (`behringer/wing/references/FORMAT.md`,
contributed by markcarlberg).
