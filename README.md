# LV1 skills for Claude Code

[Claude Code](https://claude.com/claude-code) skills for the Waves eMotion LV1 mixer: prepare, change and review LV1 shows with an AI assistant, without clicking through every channel and bus.

LV1 session files (`.emo`) are SQLite databases. These skills read and write them by script, based on a format reference worked out by comparing sessions saved in LV1.

## Skills

| Skill | What it does |
|---|---|
| [`lv1-session`](lv1-session/) | Build a session from a layout (inputs, IEM / monitor mixes, FX, matrices), convert Behringer X32 channel processing to eMo F2 / D5 / Q4, edit a session you already worked on (copy a mix's setup to other mixes, Nx IEM, talkback, user keys), and review what changed between two sessions. |

## Install

```sh
git clone https://github.com/DominikKriss/lv1-skills.git ~/lv1-skills
mkdir -p ~/.claude/skills
ln -s ~/lv1-skills/lv1-session ~/.claude/skills/lv1-session
```

Then ask Claude Code about your LV1 session, or run `/lv1-session`. `git -C ~/lv1-skills pull` updates.

## Requirements

- macOS with Python 3; tested with LV1 17.3.
- The Waves plugins a skill works with installed through Waves Central (see each skill's README).

## Caution

Unofficial; not affiliated with or supported by Waves or Behringer. The `.emo` format was worked out by reverse-engineering, so keep a backup of every session. Load an edited session in LV1 before saving anything, or LV1 will write the old in-memory state over it. Check the result in LV1 before a show.

## Contributing

Issues and pull requests welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Format findings (one change made in LV1, diffed between two saves) are the most useful contribution.

The skills learn from use: when a run turns up something the skill should know (a fix, a format finding, a missing rule), Claude Code offers to open a pull request with it from your GitHub account. It shows the account, commit email and files first and only opens the PR if you say yes.

## License

[GPL-3.0](LICENSE). Waves, eMotion LV1 and SoundGrid are trademarks of Waves Audio Ltd.; Behringer and X32 are trademarks of Music Tribe. They are named only to describe compatibility.
