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
