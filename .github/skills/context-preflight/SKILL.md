---
name: context-preflight
description: "Estimate working-context demand before substantial work, detect context-shortage risk early, and trigger pre-work compaction or a reduced working set before the task becomes unstable. Use when a request spans multiple files, research artifacts, or large documentation rewrites."
argument-hint: "request scope and likely working set"
user-invocable: true
---

# Context Preflight

Use this skill before substantial research, planning, implementation, or documentation rewrites.

## Goals

- Estimate whether the upcoming task can fit safely in the agent's working context.
- Prefer pre-work compaction over emergency compaction in the middle of implementation.
- Preserve important constraints and decisions before context pressure becomes risky.

## Why This Exists

- Mid-task compaction can drop important implementation details, decisions, or constraints.
- A brief preflight is cheaper than re-deriving lost context after work has already started.
- Prompt-engineering guidance favors clear structure, relevant context only, and explicit separation of instructions versus supporting material.

## Capacity Model

- Estimate file-heavy technical material at roughly 1 token per 4 bytes.
- Estimate prose-heavy documentation at roughly 1 token per 3 bytes.
- Reserve working room for instructions, the active user request, interim notes, validation output, and the final response.
- Keep a safety margin of at least 25 percent of the practical working budget.

## Risk Bands

- Low risk: projected working set uses less than 55 percent of the practical budget.
- Medium risk: projected working set uses 55 to 75 percent of the practical budget.
- High risk: projected working set uses more than 75 percent of the practical budget or requires many large files plus long artifacts.

## Procedure

1. Identify the likely working set before deep reading.
2. Estimate code and prose token demand from file sizes or search results.
3. Add buffers for instructions, user intent, validation output, and planned artifact writing.
4. Classify the request as low, medium, or high risk.
5. If risk is high, compact before substantive work begins.
6. If direct `/compact` execution is unavailable, reduce the working set and refresh request artifacts with a concise summary before continuing.
7. Re-run the estimate if the scope expands materially during the task.

## Compaction Rules

- Prefer compaction before implementation, not during debugging or after multiple edits.
- Preserve active constraints, open questions, selected defaults, target files, and validation status in request artifacts before compaction.
- If a request can be split into phases instead of compacting, phased execution is acceptable.

## Fallback When `/compact` Is Unavailable

- Update the active request artifacts with a concise state summary.
- Narrow the working set to only the currently relevant files.
- Defer non-critical side quests or cleanup to a later request.

## Output Template

Use [assets/context-risk-decision.template.md](./assets/context-risk-decision.template.md) when recording the preflight result.
