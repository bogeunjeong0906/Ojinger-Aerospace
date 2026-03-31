---
name: problems-lint-gate
description: "Require agents to inspect VS Code Problems output and relevant lint results before and after edits, then fix any new syntax or lint errors in touched files before finishing the task. Use when editing code, Markdown, prompts, agents, instructions, or skills."
argument-hint: "changed scope or target files"
user-invocable: true
---

# Problems and Lint Gate

Use this skill whenever an agent changes repository files and needs to ensure that no new syntax or lint problems were introduced.

## Goals

- Treat the VS Code Problems state as a mandatory completion gate.
- Catch syntax, frontmatter, Markdown, and lint issues before the task is reported as complete.
- Prevent agents from leaving touched files in a worse state than before the edit.

## Core Rules

- Check the current Problems state before making substantial edits.
- Re-check Problems after the edit on the touched files at minimum.
- If the workspace has an existing lint, build, or validation task that feeds the Problems panel, run it when it is relevant.
- If no such task exists, use the Problems data directly as the minimum validation gate.
- Do not finish while touched files contain new errors that were introduced by the current task.
- Apply this rule to Markdown files and customization files as well as source code.

## Procedure

1. Identify the files or directories likely to be changed.
2. Capture a baseline Problems snapshot for that scope.
3. If an existing lint or validation task is available and relevant, run it so VS Code can populate the Problems view.
4. Make the planned edits.
5. Re-run the relevant validation task or Problems check.
6. Fix any new errors in touched files.
7. If pre-existing unrelated problems remain unchanged, note them without claiming they were fixed.

## Decision Rules

- Prefer workspace-native lint or build commands when they exist because they can feed the Problems panel through problem matchers.
- If the workspace has no lint command, the agent must still inspect Problems output for the changed files.
- Warnings may be deferred when the task does not require cleanup, but new syntax or structural errors are blocking.
- Frontmatter parse errors, Markdown structure errors, and broken references count as blocking problems for customization files.

## Completion Checklist

- Baseline Problems checked
- Post-edit Problems checked
- Relevant lint or validation task run when available
- New errors in touched files fixed
- Residual unrelated issues noted only if they predated the change

## Output Template

Use [assets/problems-lint-checklist.template.md](./assets/problems-lint-checklist.template.md) when recording the validation result in a plan, report, or review artifact.
