---
name: wing-snapshot
description: >-
  Build a Behringer WING snapshot (.snap) by script from a JSON layout on top of a WING-Edit INIT CONSOLE save:
  input names, colours, socket patch (stereo sources on odd/even sockets, auto or explicit), monitor buses, group
  buses with members, FX buses with reverb / delay, FX inserts and bus dynamics models, mains, matrices fed from
  the main, DCAs, output patch, and channel processing (low cut, polarity, gate, compressor, key filters, EQ)
  converted from a Behringer X32 scene (.scn). Use when the user asks to prepare, build or fill a WING show /
  scene / snapshot, move an X32 show or an input list to a WING, or patch a WING to DL32 / AES50 stageboxes.
user_invocable: true
---

# WING snapshot builder

`scripts/build_wing_scene.py BASE.snap layout.json OUT.snap [--dry-run] [--changes]`

## Rules

1. The base is a snapshot WING-Edit saved: INIT CONSOLE (everything), then save as a snapshot, from the editor
   version and model of the target desk. Ask the user for it; never write a snapshot from scratch.
2. The builder only changes keys that are in the base and refuses unknown paths. FX slots and bus dynamics models
   are written as the model alone (`mdl`); bus dynamics stay off. Whether WING-Edit fills the model's default
   parameters is unconfirmed, so tell the user to check them.
3. Run `--dry-run` first, read the patch sheet and notes, then write to a new file (never over the base).
4. The user opens the result in WING-Edit, checks it, saves it from WING-Edit and loads only that save on a desk,
   first at prep, never at the show.

## Layout

See `examples/layout-auto.example.json` (sockets allocated one after another from `in_sockets` / `out_sockets`)
and `examples/layout-explicit.example.json` (every input has `src`, every output `sock`; groups, DCAs, inserts).

- `inputs`: `strip` (`ch.1`-`ch.40`, `aux.1`-`aux.8`), `name` (max 16), `group` (a `colours` key), `stereo`,
  `src` `[group, socket]` (`A`/`B`/`C` AES50, `LCL`, ...). A stereo source needs an odd socket.
- `mons`: mono pre-fader buses; `groups`: GRP-mode buses with `members` (members leave the main), optional
  `preins` / `postins` `{slot, model}` and `dyn` (bus dynamics model); `fx`: buses with the effect inserted
  (INS 1, 100% wet) and on the main; premium models (reverbs, delays) only in slots 1-8.
- `main`, `main_extra`, `matrices` (`mono`), all matrices fed from the main at 0 dB; `dcas` (`#Dn` strip tags).
- `outputs`: `src` `BUS` / `MTX`, `strip`, `stereo`, optional `sock`. Sources count left then right, so a mono
  bus n plays `BUS 2n-1`.
- `processing` (optional): `x32_scene` (relative to the layout), `from_x32` `{strip: x32 channel}`,
  `lowcut_rest` `{freq, slope, eq_token, skip}`. Aux inputs have no input filter, so their low cut is the EQ low
  band set to `eq_token`.

## X32 conversion

Low cut, polarity, gate (`GATE`), compressor (thr, ratio, knee, makeup, attack, hold, release, mix, detector,
envelope), key filters (bandpass Q to `BP`, LC / HC to `HP` / `LP`), comp pre / post EQ (`proc` `GDEI` /
`GEDI`), EQ (PEQ / VEQ to bells, shelves to the low / high band, HCut / LCut to the input filters). Preamp trim is
not converted: the gain sits on the stagebox.

Format notes and what is unconfirmed: `reference/wing-format.md`.

## Learn from the run: offer a pull request

This skill gets better from the people who use it. At the end of every run, check whether the run taught the skill something that would help the next user:

- the builder failed, was refused where it shouldn't be, or gave a wrong result
- the editor showed a value differently from what was written, dropped it, or refused the file
- a field, code or behaviour not in [`reference/wing-format.md`](reference/wing-format.md), or an item there proven or disproven by an editor load
- a layout feature or X32 conversion the user needed that the builder doesn't do

Show-specific content isn't a lesson: the user's layout, channel names and levels stay in their own files.

If there is a lesson:

1. **Make the change in this skill folder**, kept generic (no band, venue, channel or device names), following the repo's `AGENTS.md` and `CONTRIBUTING.md`: `SKILL.md` and `reference/wing-format.md` updated with the scripts, tests added, Python standard library only. A fix to `scripts/contribute.sh` is the exception: the script is shared by every skill and publishes only this folder, so offer an issue for it instead of a pull request.
2. **Write the PR body** to a scratch file: what changed, what happened in the run that showed it, and evidence (WING-Edit version, the builder's change count and notes, what WING-Edit showed after loading the result (and after saving it, if a value moved)). No show files or show names.
3. **Dry run and ask.** Run `bash <skill-dir>/scripts/contribute.sh --title "<title>" --body-file <file> --dry-run`, show the user the output (GitHub account, commit author, files) and ask whether to open the pull request from their account. Offer their GitHub noreply address with `--email` if they'd rather not publish their email.
4. **Only after a clear yes**, run it without `--dry-run` and give the user the PR link.

If the user found a bug but no fix, or has no GitHub CLI, offer an issue at https://github.com/DominikKriss/mixing-console-skills/issues/new/choose with the same body instead. The script is the same in every skill (see `lv1-session/SKILL.md` for its details).
