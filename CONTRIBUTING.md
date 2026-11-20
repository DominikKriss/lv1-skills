# Contributing

Found a bug, a wrong value, or something the editor showed differently? Please tell us: every report makes the skills better for the next engineer. Issues and pull requests are welcome for every skill (`lv1-session`, `wing-snapshot`, `dm7-session`). `main` is protected: every change goes through a pull request that the maintainer reviews and merges.

The quickest route: open an issue with the [bug report](https://github.com/DominikKriss/mixing-console-skills/issues/new?template=bug_report.yml) or [format finding](https://github.com/DominikKriss/mixing-console-skills/issues/new?template=format_finding.yml) form. If you use Claude Code, it offers to open the pull request for you after a run that taught a skill something.

## Reporting a problem

Open an issue with:

- the skill, and the console / editor version (LV1 and Session Editor, WING-Edit, DM Editor), firmware, OS
- the command you ran and its full output
- what the editor showed after loading the result, and what you expected

Don't attach your show files (`.emo`, `.snap`, `.dmxf`, `.dm7f`, `.scn`) unless you're happy for them to be public: they contain your channel names, patching and device names.

## Reporting a session-format finding

Most of this skill comes from comparing two saved sessions that differ by one change made in LV1. If you find a field that isn't in a skill's format reference (e.g. [lv1-session/reference/emo-format.md](lv1-session/reference/emo-format.md)):

1. Save a session, make one change in LV1 (one key, one bus, one plugin), save it under a new name.
2. Run `python3 lv1-session/scripts/diff_lv1_sessions.py before.emo after.emo`.
3. Open an issue or a pull request with the diff output, what you changed in LV1, and your LV1 version.

## Pull requests

The easiest way: after a run that taught a skill something, Claude Code offers to open the pull request for you (`<skill>/scripts/contribute.sh`, the same script in every skill, which needs the GitHub CLI logged in). It forks the repo to your account and commits only the skill folder; check the dry-run output for the commit email you want to publish.

- One topic per pull request. Update the skill's `SKILL.md` and format reference along with the scripts. A new skill goes in its own folder with a `SKILL.md`, a README and a row in the repository README.
- Python 3 standard library only.
- Add or update the tests in the skill's `tests/` folder (`python3 -m unittest discover -s tests -t tests` from the skill folder). Tests use synthetic sessions from `tests/fixtures.py`, never a real `.emo`. GitHub Actions runs them on every pull request.
- Test on a copy of a real show and include in the PR (LV1):
  - the script output, ending with `integrity: ok` and `presets with wrong ref_count: 0`
  - the `diff_lv1_sessions.py` output before → after
  - confirmation that LV1 loaded the result and showed the change
- Never commit show files (`.emo`, `.snap`, `.dmxf`, `.dm7f`, `.scn`; `.gitignore` blocks them). For WING and DM7, include the builder output and what the editor (WING-Edit, DM Editor) showed after loading the result.

By contributing you agree that your contribution is licensed under the [GPL-3.0](LICENSE).
