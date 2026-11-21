# 0003. Vendored code stays unchanged

- **Status:** Accepted
- **Scope:** dm7
- **Date:** 2026-11-21

## Context

`dm7-session` parses DM7 files with `yamaha_tool.py` from show-file-skills (MIT). Local edits would drift from
upstream and make updates and credit unclear.

## Decision

Third-party code lives under `<skill>/vendor/`, byte for byte as published, with its licence file and the upstream
commit noted in the skill README. It is updated only as a whole file from upstream. Problems found in it are raised
upstream; our own code works around them (for example by running the tool's full check on every output).

## Consequences

Review findings on vendored files are answered, not fixed here. Updating means replacing the file and rerunning the
tests.
