# lv1-session

Part of [LV1 skills for Claude Code](../README.md).

A [Claude Code](https://claude.com/claude-code) skill that builds, edits and reviews LV1 session files (`.emo`) by script.

**Build** a monitor session from a JSON layout ([example](examples/layout.example.json)):

- input / FX / Mon / Matrix names and faders
- monitor (IEM) sends with pick-off points, a musician's own sources pre-fade, talkback in every mix
- FX sends and returns, including dedicated per-singer reverbs
- Mon / Matrix mono or stereo (with the stereo eMo variants), Matrix fed by its Mon at 0 dB
- eMo F2 / D5 / Q4, trim and polarity converted from a Behringer X32 scene (`.scn`)

**Edit** a session you have already worked on in LV1, from a JSON edits file ([example](examples/edits.example.json)):

- copy one Mon / Matrix bus to others: rack and plugin settings, mono / stereo, Nx IEM type and per-input Nx positions, matrix levels
- add a plugin from one bus (e.g. an IEM EQ curve on Cue) to others
- talkback presets, Sends-on-Fader and talkback user keys

**Review**: a readable diff of two sessions (what changed, by bus).

See [SKILL.md](SKILL.md) for the fields, the procedure and the X32 → eMo conversion rules.

## Usage

Install as described in the [repository README](../README.md), then ask Claude Code to prepare, edit or review an LV1 session, or run `/lv1-session`. The scripts also run on their own:

```sh
python3 ~/lv1-skills/lv1-session/scripts/build_lv1_session.py in.emo out.emo layout.json [scene.scn]
python3 ~/lv1-skills/lv1-session/scripts/edit_lv1_session.py in.emo out.emo edits.json
python3 ~/lv1-skills/lv1-session/scripts/diff_lv1_sessions.py before.emo after.emo
```

## Requirements

- macOS with Python 3; LV1 17.3 (other versions untested).
- eMo F2, D5 and Q4 installed through Waves Central. The script reads their parameter lists from the installed plugins.

See the [repository README](../README.md) for the caution note, contributing and license.
