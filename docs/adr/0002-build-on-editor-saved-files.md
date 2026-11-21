# 0002. Build on editor-saved files and refuse unknown fields

- **Status:** Accepted
- **Scope:** all
- **Date:** 2026-11-21

## Context

None of the console formats is documented by its maker. A file written from scratch, or with a guessed field, can
load wrongly or not at all, and a console is a bad place to find out.

## Decision

Every builder starts from a file the console's own editor saved (LV1 session, WING-Edit INIT snapshot, DM Editor
session). It changes only fields that exist in that file, refuses unknown paths with one sentence and writes
nothing, and never invents device IDs or plugin parameter sets. It writes a new file, never over its inputs. Every
format fact in a skill's `reference/` states its proof: an editor load, a controlled save, or "unconfirmed".

## Consequences

Users must provide a base file and open every result in the editor before a desk. Features that need data only the
editor can create (a mounted stagebox, a loaded plugin) wait until the base has it.
