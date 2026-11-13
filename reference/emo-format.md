# LV1 session (.emo) format

Found by reverse-engineering LV1 17.3 sessions (not documented by Waves).

## Summary

An LV1 `.emo` session (v17.3) is a plain SQLite database and can be edited with a script. Channel settings are named parameters stored only when they differ from the default. Plugin settings are XML preset chunks that list values by position.

## Details

- **Open read-only with** `sqlite3 "file:x.emo?immutable=1"`: plain `-readonly` fails with "unable to open database file". Sessions live in `/Users/Shared/Waves/eMotion/Sessions/`. `CurrentLV1.dat` (+ `-wal`) is LV1's live state; don't write to it.
- **LV1 keeps the open session in memory.** Save writes that state over the file, so a script edit is lost unless the session is loaded again first. Edit a copy, then load it from the session menu.
- **Objects:** `object` (`obj_type` → `cluster_type`: 0 Input, 1 Group, 2 Aux (FX), 6 Matrix, 25 Mon). The name is in `snapshot_chainer.name` per snapshot (-1 = Active, 0.. = stored).
- **Mono/stereo:** `chainer.num_inputs` 1 / 2. This applies to Mon aux and Matrix; the plugins (CFLS/CDYS/MQ4S) stay the same.
- **Parameters:** `snapshot_chainer_params(chainer_id, snapshot_id, param_id, value)`. Names are in `chainer_params` and defaults in `chainer_params_default_values`.
  - Sends `PARAM_AUX_SEND_{GAIN,ONOFF,SOURCE}_<slot>`: FX 1-8 = slots 0-7, Mon 1-8 = 8-15, Mon 9-16 = `2_0`-`2_7`, Mon 17-24 = `3_0`-`3_7`.
  - Gain is stored in dB (-144 = off) and On = 1.
  - SOURCE: 0 INP, 1 PRE, 2 PST, 3 PSP. FX sends default to 3, Mon sends to 1.
  - `PARAM_OUTPUT_GAIN` is the fader (default -144).
- **Trim and polarity:** the UI reads `PARAM_INPUT_DIGITAL_TRIM_L/_R` and `PARAM_INPUT_PHASE_ONOFF_L/_R`; writing only the base param doesn't show. Trim max is +10 dB.
- **Matrix source:** a row in `snapshot_assignment` (src = Mon object, `src_section_type` 7, control 0, asgn 0; dst = Matrix object, `dst_section_type` 0, `dst_section_index` = source slot).
- **Plugins:**
  - `plug(chainer_id, slot, plugin_name)` sets the rack order.
  - `snapshot_plugin.preset_id` points to `plugin_preset(hash, ref_count, preset)`.
  - The hash is SHA3-256 of the chunk text. `ref_count` = number of `snapshot_plugin` rows using the preset.
- **Preset chunks:** `<Parameters Type="RealWorld">` holds the values in the order of the plugin's `Contents/Resources/ParamXML/1000.xml` (in `/Applications/Waves/Plug-Ins V*/EMO-*.bundle`); `*` = display-only.
  - The Session Editor shows no plugins until they're installed through Waves Central.
  - eMo codes:
    - Q4 band 1 type: 0 Bell, 1 Low-Shelf, 2 Hi-Pass. Band 2: Bell / Low-Shelf. Band 3: Bell / Hi-Shelf. Band 4: Bell, Hi-Shelf, Low-Pass.
    - D5 knee: 0 Soft, 1 Normal, 2 Hard.
    - D5 release mode: 0 Manual. The release knob is `PARAM_COMP_MAX_REL`.
    - Gate/Exp: 0 Gate.
    - All of these were confirmed in LV1 on KICK.
