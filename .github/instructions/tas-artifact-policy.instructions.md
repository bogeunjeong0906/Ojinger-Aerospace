---
name: TAS Artifact Policy
description: "Use when TAS creates, updates, or reuses request artifacts for analysis, plan, and execution work while preserving prior context."
applyTo: "docs/agent_docs/**/*.md"
---

# TAS Artifact Policy

These rules apply to TAS request artifacts only.

- Use request artifacts for non-trivial TAS work.
- Store active work under `docs/agent_docs/request_XXXX/`.
- Treat `docs/agent_docs/request_0000/` as the template package and never as active work.
- TAS uses exactly three canonical artifacts: `research.md`, `plan.md`, and `report.md`.
- Default stage order is analysis, then plan, then execution.
- Do not skip directly from analysis to execution.
- Read `research.md` before plan work.
- Read both `research.md` and `plan.md` before execution work.
- Write artifact prose in the user's request language unless the user explicitly asks for another language.
- Keep code, commands, file names, APIs, and quoted external text in their original language when translation would reduce precision.

## Request Reuse

- Reuse the current request when the user is continuing the same primary outcome.
- Create a new request only when the primary deliverable, target area, or implementation direction changes materially.
- Ignore `request_0000` when choosing the next active request id.

## Turn Boundary

- By default, finish one stage and stop for user direction.
- If the user explicitly asks for chained work, continue sequentially in the same turn without skipping stages.

## Preservation Rules

- Do not replace an existing artifact with a fresh rewrite unless the user explicitly asks for a reset.
- Preserve prior findings, assumptions, decisions, risks, and history when updating an artifact.
- If earlier content is no longer valid, mark it as `Superseded` or `Revised` instead of deleting it silently.
- When the user asks for follow-up research on only one subtopic, keep the rest of the existing research intact.
- When the plan changes, append or revise the relevant section without erasing prior decisions.
- When execution discovers a deviation, record it in `report.md` instead of rewriting earlier artifacts to hide the change.
- If the user switches languages mid-request, preserve prior content and write new or revised prose in the latest user-request language unless the user asks for a full translation pass.

## Stage Expectations

### research.md

- Record the current summary, stable findings, implementation constraints, and open questions.
- Keep follow-up research additive unless a finding is explicitly superseded.
- Keep summary and conclusions readable in the user's request language.

### plan.md

- Convert research output into ordered execution steps.
- List target files, validation, completion criteria, and rollback triggers.
- Preserve prior planning notes when refining the plan.
- Keep actionable steps and validation notes in the user's request language.

### report.md

- Record what was implemented in the current execution stage.
- Record validation and self-review.
- Record deviations from the plan and remaining issues.
- Keep execution summaries and residual-risk notes in the user's request language.

## Completion Gate

- Keep artifacts synchronized with the actual task state.
- Do not mark a stage complete until its artifact contains enough information for the next stage or for a later session to resume safely.
