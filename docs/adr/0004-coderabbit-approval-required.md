# 0004. CodeRabbit approval is required to merge

- **Status:** Accepted
- **Scope:** all
- **Date:** 2026-11-21

## Context

The repo has one maintainer and wants outside contributions. Every PR needs a review before it lands on `main`.

## Decision

CodeRabbit reviews every PR with automatic approvals on (`.coderabbit.yaml`): it requests changes on actionable
findings and approves when they are resolved; the PR author cannot approve through a command. The `main` ruleset
requires one approval and the `CodeRabbit` check. The maintainer keeps the admin bypass so an outage cannot block
`main`.

## Consequences

Contributor PRs merge only after CodeRabbit approval (or a maintainer approval). A skipped or rate-limited review
passes the required check, so the maintainer still watches merges. Findings are fixed or answered with a reason,
never silently dismissed.
