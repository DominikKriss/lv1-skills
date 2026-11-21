---
name: reaper-routing
description: >-
  Route a REAPER project (.rpp) for live multitrack recording and virtual soundcheck by script: record inputs and
  hardware outputs for every track from range maps (1:1 or offset, mono or stereo pairs), master send on / off,
  track names from the console show (Waves LV1 .emo, Behringer X32 .scn, WING .snap, or a text list), and a rec /
  play switch (armed with no hardware outs, or disarmed with hardware outs). Use when the user asks to route,
  patch, name or set up REAPER tracks / inputs / outputs, prepare a multitrack recording or virtual soundcheck,
  or says routing 32 / 64 channels in REAPER by hand is painful.
user_invocable: true
---

# REAPER routing

`scripts/route_reaper.py` reads a project REAPER saved and writes a new `.rpp` with the routing changed. It touches
only the track-level `NAME`, `REC`, `MAINSEND` and `HWOUT` lines; items, FX, envelopes and everything else stay
byte for byte, line endings included. The format and how sure each field is: [`reference/rpp-format.md`](reference/rpp-format.md).

## Safety

- Start from a project REAPER saved with the tracks already there (create 64 tracks in REAPER first; the script
  doesn't add tracks). Close the project in REAPER, or REAPER's next save overwrites the script's file.
- Write the new file **in the same folder** as the source: item paths like `Media\01-take.wav` are relative to the
  project. The script refuses to overwrite the source or an existing file.
- After the run, open the new file in REAPER and check the routing matrix (Alt+R / Option+R) before a show.

## Commands

```sh
python3 scripts/route_reaper.py SRC.rpp DEST.rpp [options]
```

| Option | Does |
|---|---|
| `--in 1-64` | record input N for track N (mono). `--in 41-64:17` = tracks 41-64 from input 17 on. Repeatable. |
| `--out 1-64` | one hardware out per track, track N → out N (mono, from track channel 1). `--out 1-8:33` = outs 33-40. Repeatable. Replaces the track's existing hardware outs. |
| `--stereo 7,41-42` | these tracks take an input pair and an output pair starting at the mapped channel (map them to odd channels). |
| `--master off` | master / parent send off, so playback reaches only the hardware outs. `on` turns it back on. |
| `--names FILE` | track names: `.emo` (LV1 inputs by index), `.scn` (X32 `/ch/NN/config`), `.snap` (WING `ch.N.name`), `.txt` (one per line), `.csv` (first column). Name N goes to track N. |
| `--device NAME` | with an LV1 `.emo`: name track N after what LV1 patched to channel N of this SoundGrid DAW device (the recording computer, as LV1's device list or its hostname shows it; case and `-` / `_` / spaces ignored). Stereo LV1 channels get ` L` / ` R`; unpatched channels keep their name. Use this whenever the recording went through an LV1 patch. |
| `--mode rec` | arm every track and remove its hardware outs (no input echo into the console while recording). |
| `--mode play` | disarm every track; keeps or sets hardware outs (needs `--out` or outs already in the project). |
| `--only 1-40` | change only these tracks. |
| `--src-stereo` | mono hardware outs take track channels 1/2 mixed to mono (REAPER's default when routed by hand) instead of channel 1. |

Typical virtual soundcheck setup, then switching back to record:

```sh
python3 scripts/route_reaper.py show.rpp show_play.rpp --in 1-64 --out 1-64 --master off --names show.emo --device REC-PC --mode play
python3 scripts/route_reaper.py show_play.rpp show_rec.rpp --mode rec
```

`--mode rec` drops the hardware outs; to play again, run `--mode play --out ...` on the rec file.

The script prints one row per track (name, input, output, master, armed). Check it with the user against the
console patch. Without `--device`, names follow the console's channel order and are right only when the
recording channels are patched 1:1 to the console channels; with an LV1 session, ask which device recorded and use
`--device` (a wrong name lists the DAW devices in the session).

## Learn from the run: offer a pull request

This skill gets better from the people who use it. At the end of every run, check whether the run taught the skill something that would help the next user:

- the script failed, was refused where it shouldn't be, or gave a wrong result
- REAPER showed a value differently from what was written, dropped it, or refused the file
- a field or behaviour not in [`reference/rpp-format.md`](reference/rpp-format.md), or an item there proven or disproven by a REAPER load
- a routing feature the user needed that the script doesn't do

Show-specific content isn't a lesson: the user's track names and patch stay in their own files.

If there is a lesson:

1. **Make the change in this skill folder**, kept generic (no band, venue, channel or device names), following the repo's `AGENTS.md` and `CONTRIBUTING.md`: `SKILL.md` and `reference/rpp-format.md` updated with the scripts, tests added, Python standard library only. A fix to `scripts/contribute.sh` is the exception: the script is shared by every skill and publishes only this folder, so offer an issue for it instead of a pull request.
2. **Write the PR body** to a scratch file: what changed, what happened in the run that showed it, and evidence (REAPER version and OS, the script's output, what REAPER's routing matrix showed after loading the result). No project files or show names.
3. **Dry run and ask.** Run `bash <skill-dir>/scripts/contribute.sh --title "<title>" --body-file <file> --dry-run`, show the user the output (GitHub account, commit author, files) and ask whether to open the pull request from their account. Offer their GitHub noreply address with `--email` if they'd rather not publish their email.
4. **Only after a clear yes**, run it without `--dry-run` and give the user the PR link.

If the user found a bug but no fix, or has no GitHub CLI, offer an issue at https://github.com/DominikKriss/mixing-console-skills/issues/new/choose with the same body instead. The script is the same in every skill (see `lv1-session/SKILL.md` for its details).
