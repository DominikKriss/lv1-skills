# Contributing

Issues and pull requests are welcome. `main` is protected: every change goes through a pull request that the maintainer reviews and merges.

## Reporting a problem

Open an issue with:

- LV1 version (and Session Editor or console), macOS version
- the command you ran and its full output
- what LV1 showed after loading the session, and what you expected

Don't attach your `.emo` sessions unless you're happy for them to be public: they contain your channel names, patching and device names.

## Reporting a session-format finding

Most of this skill comes from comparing two saved sessions that differ by one change made in LV1. If you find a field that isn't in [reference/emo-format.md](reference/emo-format.md):

1. Save a session, make one change in LV1 (one key, one bus, one plugin), save it under a new name.
2. Run `python3 scripts/diff_lv1_sessions.py before.emo after.emo`.
3. Open an issue or a pull request with the diff output, what you changed in LV1, and your LV1 version.

## Pull requests

- One topic per pull request. Update `SKILL.md` and `reference/emo-format.md` along with the scripts.
- Python 3 standard library only.
- Test on a copy of a real session and include in the PR:
  - the script output, ending with `integrity: ok` and `presets with wrong ref_count: 0`
  - the `diff_lv1_sessions.py` output before → after
  - confirmation that LV1 loaded the result and showed the change
- Never commit `.emo` files (`.gitignore` blocks them).

By contributing you agree that your contribution is licensed under the [GPL-3.0](LICENSE).
