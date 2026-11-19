# lv1-session: Claude Code skill for Waves eMotion LV1 sessions

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

## Install

```sh
git clone https://github.com/DominikKriss/lv1-session-skill.git ~/.claude/skills/lv1-session
```

Then ask Claude Code to prepare or edit an LV1 session, or run `/lv1-session`. The scripts also run on their own:

```sh
python3 ~/.claude/skills/lv1-session/scripts/build_lv1_session.py in.emo out.emo layout.json [scene.scn]
python3 ~/.claude/skills/lv1-session/scripts/edit_lv1_session.py in.emo out.emo edits.json
python3 ~/.claude/skills/lv1-session/scripts/diff_lv1_sessions.py before.emo after.emo
```

## Requirements

- macOS with Python 3; LV1 17.3 (other versions untested).
- eMo F2, D5 and Q4 installed through Waves Central. The script reads their parameter lists from the installed plugins.

## Caution

Unofficial; not affiliated with or supported by Waves or Behringer. The `.emo` format was worked out by reverse-engineering, so keep a backup of every session. Load the edited session in LV1 before saving anything, or LV1 will write the old in-memory state over it. Check one channel in LV1 after each build.

## Contributing

Issues and pull requests welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Format findings (one change made in LV1, diffed with `diff_lv1_sessions.py`) are the most useful contribution.

## License

[GPL-3.0](LICENSE). Waves, eMotion LV1 and SoundGrid are trademarks of Waves Audio Ltd.; Behringer and X32 are trademarks of Music Tribe. They are named only to describe compatibility.
