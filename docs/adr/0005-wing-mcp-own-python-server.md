# 0005. WING live control: own Python MCP server, read-only first

- **Status:** Proposed
- **Scope:** wing, mcp
- **Date:** 2026-11-21

## Context

A WING can be controlled over the network (OSC, and the native protocol on port 2222 documented in the unofficial
WING Remote Protocols). An open-source Node.js WING MCP server exists. This repo is Python standard library only,
and a tool that writes to a live desk carries more risk than the offline builders.

## Decision

Build our own MCP server in Python over OSC, in this repo, using the existing server only as a reference. Start
read-only (names, patch, levels, mutes, sends, meters) and compare the desk with a `wing-snapshot` layout. Writes
come later, behind an explicit switch, an allowlist of parameters, a confirmation for every change and a show mode
that blocks all writes.

## Consequences

More work than adopting the existing server, but one language, our own safety rules and a direct link to
`wing-snapshot`. Testing needs a WING on the network; whether WING-Edit alone answers OSC is unknown.
