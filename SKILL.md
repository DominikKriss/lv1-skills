---
name: lv1-session
description: >-
  Build or edit a Waves eMotion LV1 session (.emo) by script: input / FX / Mon / Matrix names, faders,
  monitor sends with pick-off points, FX returns, Mon / Matrix mono-stereo, Matrix sources, and eMo F2 / D5 / Q4,
  trim and polarity converted from a Behringer X32 scene (.scn). Use when the user asks to prepare, change or
  fill an LV1 show / session / scene, copy X32 channel processing into LV1, set up IEM / monitor mixes in LV1,
  or edit an .emo file.
user_invocable: true
---

# LV1 session builder

An `.emo` session is a plain SQLite database. `scripts/build_lv1_session.py` takes the user's saved session, applies a layout from a JSON config, and optionally converts an X32 scene into eMo plugin settings. The file format is documented in [`reference/emo-format.md`](reference/emo-format.md); read it before changing the scripts.

## Inputs

- **Source session:** a session the user saved in LV1 or the LV1 Session Editor, in `/Users/Shared/Waves/eMotion/Sessions/<name>.emo`. Always start from a session the user saved, never from a blank file.
- **Layout config:** JSON, one per band / show, kept next to the user's project files (example: [`examples/layout.example.json`](examples/layout.example.json)):
  - `inputs`: LV1 channel names in order (index 0 = ch 1).
  - `mons`: Mon aux in order. Each has `name`, `stereo`, an optional `matrix` (1-based matrix fed by this Mon), `own` (inputs sent at `own_db` pre-fade in this mix) and `sends: false` for mixes left empty (spares).
  - `levels`: `other_db` (every other input, post-pan) and `own_db`. `always_pre_0db` lists inputs sent pre-fade at `own_db` into every mix (talkback).
  - `fx`: FX aux in order. `feeds` maps input → `[dB, "INP"|"PRE"|"PST"|"PSP"]`; `dedicated_to` = the Mon name that gets this FX back at `fx_returns.own_db` (`other_db` everywhere else). FX without feeds get no returns.
  - `x32_to_lv1`: X32 channel → LV1 channel (1-based). Needed only with an X32 scene.
- **X32 scene (optional):** a complete `.scn` exported from the X32 (check that `file` reports ASCII and that the file isn't truncated).

## Procedure

1. **Ask for or find the layout and the X32 scene.** If the user keeps project notes, read them first.
2. **Copy the source session into the user's working folder** (`<name>.orig.emo`) as the backup. Inspect it read-only with `sqlite3 "file:<f>?immutable=1"`: plain `-readonly` fails.
3. **Write or update the layout config.** The script exits if any name in `own`, `feeds` or `always_pre_0db` is not in `inputs`.
4. **Run the build into the working folder:**
   ```
   python3 <skill-dir>/scripts/build_lv1_session.py <orig.emo> <work-dir>/<name>.emo <layout.json> [<scene.scn>]
   ```
   The output lists each X32 → LV1 channel with its rack order and any clamped value. The last line must say `integrity: ok` and show `preset refs N/N` (equal).
5. **Put the result in the Sessions folder.** Use a new name unless the user asked to edit their session in place. Never write `CurrentLV1.dat`.
6. **Tell the user to load the session from LV1's session menu before saving.** LV1 keeps the open session in memory, and Save overwrites a script edit with the old state.
7. **Verify with the user on one channel with dynamics and EQ.** Check:
   - trim and polarity
   - rack order
   - F2 frequency
   - Q4 type, frequency, gain and Q per band
   - D5 gate (open, floor, key filters)
   - D5 comp (threshold, ratio, knee, Manual release, makeup)
   - Mon / Matrix stereo

## Conversion rules (X32 → eMo)

- **Trim:** X32 trim goes to LV1 digital trim, max +10 dB. The rest goes to the Q4 output gain.
- **High-pass:** X32 low cut → F2 HPF.
- **EQ:** the four X32 bands are placed into Q4 slots in frequency order, within each slot's limits:
  - band 1: Bell / Low-Shelf / Hi-Pass
  - band 2: Bell / Low-Shelf
  - band 3: Bell / Hi-Shelf
  - band 4: Bell / Hi-Shelf / Low-Pass

  Flat bands are skipped. A band that doesn't fit is dropped and reported.
- **Rack order:** an X32 compressor set to POST EQ → F2 → Q4 → D5; otherwise F2 → D5 → Q4.
- **Gate:** floor = −range; release capped at 1000 ms. X32 bandpass key filters become HPF/LPF at the −3 dB edges.
- **Compressor:**
  - ratio capped at 20
  - knee: X32 0 → Hard, 1–2 → Normal, 3–5 → Soft
  - release Manual, written to `PARAM_COMP_MAX_REL`
- **Not converted:** X32 preamp gain and phantom (set on the stagebox), and PEAK/RMS and LIN/LOG detection (no D5 equivalent).

## Not done by the script

Adding plugins (reverb, delay, limiter, volume), stereo-linking inputs, and patching or I/O devices. To add one of these, have the user make the change on one channel in LV1 and save under a new name. Diff the two sessions' `.dump` output, record the finding in `reference/emo-format.md`, then add it to the script. A save of the stock defaults won't show the field, because parameters at their default value aren't stored.

## Prerequisites

- Python 3 and `sqlite3` (macOS has both).
- The eMo F2, D5 and Q4 plugins installed through Waves Central (the LV1 Session Editor also needs them to show plugins). The script reads each plugin's parameter order from `/Applications/Waves/Plug-Ins V*/EMO-*.bundle/Contents/Resources/ParamXML/1000.xml`; set `LV1_EMO_PARAMXML_DIR` to a folder with `EMO-F2-ParamXML.xml` etc. to override. It refuses a preset whose value count differs from the ParamXML.
- Tested with LV1 17.3 on macOS; other versions may store things differently.
