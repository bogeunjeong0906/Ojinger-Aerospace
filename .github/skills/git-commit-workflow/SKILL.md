---
name: git-commit-workflow
description: "Review, stage, commit, and optionally push repository changes only when the user explicitly asks. Use when preparing a focused git commit, excluding unrelated changes, and handling push safely."
argument-hint: "requested commit scope and optional message"
user-invocable: true
---

# Git Commit Workflow

Use this skill when the user explicitly asks for a git stage, commit, or push action.

## Core Rules

- Do not stage, commit, or push anything unless the user explicitly requested it.
- Review the changed files before committing.
- Exclude unrelated changes from the commit whenever possible.
- If unrelated changes cannot be safely separated, stop and explain the issue.
- Push only when the user explicitly asked for a push.

## Procedure

1. Inspect the changed files.
2. Determine which changes belong to the requested scope.
3. Review the diff for those files.
4. Stage only the relevant files.
5. Write a focused commit message.
6. Commit only after the requested scope is confirmed.
7. Push only if the user asked for it.
8. If upstream is missing and the user asked for a push, set upstream only as part of that push flow.

## Commit Message Rules

- Keep the subject line specific and concise.
- Prefer describing the actual change over generic wording.
- Mention the workflow area when relevant, for example `tas`, `artifacts`, or `python-env`.

## Push Rules

- Verify the current branch before pushing.
- Prefer pushing the current branch to its configured upstream.
- If no upstream exists, use an explicit upstream-setting push only when the user asked for a push.
- Do not push unrelated branches or tags.

## Safety Checks

- Are there unrelated modified files?
- Are there generated files or temporary edits that should stay out of the commit?
- Did the user request commit only, or commit and push?
- Is the current branch the branch that should be pushed?

## Output Template

Use [assets/commit-summary.template.md](./assets/commit-summary.template.md) when reporting the git result.
