# 0001. Each skill folder is self-contained

- **Status:** Accepted
- **Scope:** all
- **Date:** 2026-11-21

## Context

Users install a skill by symlinking its folder into `~/.claude/skills/`, often one skill only. Code outside that
folder is not there at run time.

## Decision

A skill never imports from another skill's folder or from the repo root. A helper several skills need is copied into
each skill (the X32 scene reader, `contribute.sh`). Where copies must stay identical, CI compares them.

## Consequences

Skills install and run alone. Shared code exists more than once, so a fix lands in every copy in the same PR; for
`contribute.sh` CI enforces it.
