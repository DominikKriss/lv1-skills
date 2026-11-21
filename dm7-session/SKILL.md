---
name: dm7-session
description: >-
  Build a Yamaha DM7 session (.dmxf / .dm7f, firmware V2.01) by script from a JSON layout on top of a DM Editor
  2.0.1 session: channel names (8 characters), colours, stereo pairs, Dante input patch and Tio1608-D / Rio
  subscriptions, monitor mixes (pre-fader), FX send mixes with FX rack routing and paired returns, Stereo A name,
  matrices (pairs) fed from ST A, Dante output patch, HPF, and channel processing (HPF, polarity, gate, compressor,
  key filter, EQ, LPF, EQ / dynamics order) converted from a Behringer X32 scene (.scn). Use when the user asks to
  prepare or fill a DM7 show / session, move an X32 show or an input list to a DM7, or patch a DM7 to Tio stageboxes.
user_invocable: true
---

# DM7 session builder

`scripts/build_dm7.py BASE.dmxf layout.json OUT.dmxf [--dry-run] [--changes]`

## Rules

1. The base is a full session saved by DM Editor 2.0.1 for a DM7 (not Compact), firmware V2.01. A scene-only
   export or a V1.x file is refused. Ask the user to mount the stageboxes (Tio1608-D) in the Dante setup and put a
   reverb and a delay in the FX rack before saving: device IDs and plugin parameters are never invented, so Dante
   subscriptions and FX routing are skipped (with a note) when the base lacks them.
2. Parsing and rebuilding use `vendor/yamaha_tool.py` (show-file-skills, MIT). Its own writes are limited to
   names, colours, faders, ON, HPF, patch and head amps; this builder also writes buses, sends, pairs, EQ, dynamics,
   FX routing and the Dante patch from show-file-skills' `dm7-fields.md`. Those fields are not proven by a DM Editor
   load of this builder's output yet, so the user checks them.
3. Run `--dry-run` first, then write a new file. The builder refuses to write if the result fails `yamaha_tool`'s
   check.
4. The Dante subscriptions sit in the Setup entry: DM Editor loads it only with "Load with System Setting".
5. The user opens the result in DM Editor, checks it, saves there and loads only that save on the console.

## Layout

See `examples/layout.example.json`. Inputs as in the WING skill (`name`, `group`, `stereo`); groups listed in
`dante_playback_groups` come over Dante from a playback computer from `playback_dante_start`, the others go one
after another on `tio_units` x `tio_inputs` stagebox inputs. Stereo sources become odd/even channel pairs (spare
channels keep the alignment). `processing` as in the WING skill (`x32_scene`, `from_x32` keyed by `ch.N` list
position, `lowcut_rest`).

## X32 conversion

Gate to DYN1 `GATE`, compressor to DYN2 Legacy Comp (`PM Comp`, knee 0-5 like the X32; ratio x10, 100:1 = inf),
comp pre EQ to `EQDynOrder` 1, low / high shelves on bands 1 / 4 and bells in frequency order on the free bands,
EQ HCut to the LPF (12 dB/oct). The DM7 key filter is HPF only: X32 bandpass and LP key filters are left off with
a note. Preamp trim is not converted.

Field notes: `reference/dm7-fields-used.md`.

## Learn from the run: offer a pull request

This skill gets better from the people who use it. At the end of every run, check whether the run taught the skill something that would help the next user:

- the builder failed, was refused where it shouldn't be, or gave a wrong result
- the editor showed a value differently from what was written, dropped it, or refused the file
- a field, code or behaviour not in [`reference/dm7-fields-used.md`](reference/dm7-fields-used.md), or an item there proven or disproven by an editor load
- a layout feature or X32 conversion the user needed that the builder doesn't do

Show-specific content isn't a lesson: the user's layout, channel names and levels stay in their own files.

If there is a lesson:

1. **Make the change in this skill folder**, kept generic (no band, venue, channel or device names), following the repo's `AGENTS.md` and `CONTRIBUTING.md`: `SKILL.md` and `reference/dm7-fields-used.md` updated with the scripts, tests added, Python standard library only. A fix to `scripts/contribute.sh` is the exception: the script is shared by every skill and publishes only this folder, so offer an issue for it instead of a pull request.
2. **Write the PR body** to a scratch file: what changed, what happened in the run that showed it, and evidence (DM Editor version, the builder's change count and notes, `vendor/yamaha_tool.py check` on the output, what DM Editor showed after loading the result). No show files or show names.
3. **Dry run and ask.** Run `bash <skill-dir>/scripts/contribute.sh --title "<title>" --body-file <file> --dry-run`, show the user the output (GitHub account, commit author, files) and ask whether to open the pull request from their account. Offer their GitHub noreply address with `--email` if they'd rather not publish their email.
4. **Only after a clear yes**, run it without `--dry-run` and give the user the PR link.

If the user found a bug but no fix, or has no GitHub CLI, offer an issue at https://github.com/DominikKriss/mixing-console-skills/issues/new/choose with the same body instead. The script is the same in every skill (see `lv1-session/SKILL.md` for its details).
