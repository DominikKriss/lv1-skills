# Architecture decision records

One file per decision that cuts across skills or would surprise a contributor. Format facts stay in each skill's
`reference/`; ADRs record choices. Copy [template.md](template.md) to `NNNN-short-title.md`, add a row here, and keep
status and scope in the file and in this table the same (CI checks it).

- **Status:** Proposed, Accepted, Deprecated, or `Superseded by NNNN`. Superseded ADRs stay listed.
- **Scope:** `all` or skill labels (`lv1`, `wing`, `dm7`, `mcp`), the same names as the issue labels.

| # | Title | Status | Scope | Date |
|---|---|---|---|---|
| [0001](0001-self-contained-skills.md) | Each skill folder is self-contained | Accepted | all | 2026-11-21 |
| [0002](0002-build-on-editor-saved-files.md) | Build on editor-saved files and refuse unknown fields | Accepted | all | 2026-11-21 |
| [0003](0003-vendored-code-unchanged.md) | Vendored code stays unchanged | Accepted | dm7 | 2026-11-21 |
| [0004](0004-coderabbit-approval-required.md) | CodeRabbit approval is required to merge | Accepted | all | 2026-11-21 |
| [0005](0005-wing-mcp-own-python-server.md) | WING live control: own Python MCP server, read-only first | Proposed | wing, mcp | 2026-11-21 |
