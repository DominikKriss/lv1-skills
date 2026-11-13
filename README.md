# lv1-session: Claude Code skill for Waves eMotion LV1 sessions

A [Claude Code](https://claude.com/claude-code) skill that edits an LV1 session file (`.emo`) by script:

- input / FX / Mon / Matrix names and faders
- monitor (IEM) sends with pick-off points, a musician's own sources pre-fade, talkback in every mix
- FX sends and returns, including dedicated per-singer reverbs
- Mon / Matrix mono or stereo, Matrix fed by its Mon
- eMo F2 / D5 / Q4, trim and polarity converted from a Behringer X32 scene (`.scn`)

The layout is a JSON file ([example](examples/layout.example.json)); see [SKILL.md](SKILL.md) for the fields, the procedure and the X32 → eMo conversion rules.

## Install

```sh
git clone <this repo> ~/.claude/skills/lv1-session
```

Then ask Claude Code to prepare or edit an LV1 session, or run `/lv1-session`. The scripts also run on their own:

```sh
python3 ~/.claude/skills/lv1-session/scripts/build_lv1_session.py in.emo out.emo layout.json [scene.scn]
```

## Requirements

- macOS with Python 3; LV1 17.3 (other versions untested).
- eMo F2, D5 and Q4 installed through Waves Central. The script reads their parameter lists from the installed plugins.

## Caution

Unofficial; not affiliated with or supported by Waves or Behringer. The `.emo` format was worked out by reverse-engineering, so keep a backup of every session. Load the edited session in LV1 before saving anything, or LV1 will write the old in-memory state over it. Check one channel in LV1 after each build.
