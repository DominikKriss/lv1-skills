# dm7-session

Builds a Yamaha DM7 session from a JSON layout, on top of a session saved by DM Editor 2.0.1 (firmware V2.01).

```sh
python3 scripts/build_dm7.py base.dmxf examples/layout.example.json event.dmxf --dry-run
python3 scripts/build_dm7.py base.dmxf examples/layout.example.json event.dmxf
python3 vendor/yamaha_tool.py show event.dmxf
```

## Status

- Built against a DM Editor 2.0.1 DM7 session: 1,304 changes for a 60-channel layout, `yamaha_tool.py check` ok.
- Not yet confirmed by a DM Editor load: the writes beyond yamaha_tool's proven set (see `SKILL.md`).
- Tio output patch (which DM7 Dante output feeds each Tio output) is not written: patch it in DM Editor or Dante
  Controller.

## Tests

`python3 -m unittest discover -s tests -t tests` (no Yamaha file needed; the conversion is tested on a fake session).

## Credits and licence

`vendor/yamaha_tool.py` is from [show-file-skills](https://github.com/michaelkeithlewis/show-file-skills) at
ed5cfb5, unchanged, MIT (`vendor/LICENSE-show-file-skills`), by Michael Lewis and contributors; the DM7 field map
(`yamaha/references/dm7-fields.md`) is by markcarlberg.
