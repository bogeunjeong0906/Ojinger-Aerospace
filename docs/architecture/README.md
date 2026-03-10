# Architecture Artifacts Guide

This directory is the mandatory architecture source for structure-sensitive work in Ojinger-Aerospace.

## Required artifact families

### 1. Intent architecture

Human-authored artifacts derived from natural-language requirements.

Required standard artifacts:

- `architecture_manifest.yaml`
- `goal_map.mmd`
- `system_context.mmd`
- `container_view.mmd`
- `component_view.mmd`
- `architecture_decisions.md`

### 2. As-built architecture

Mechanically generated artifacts derived from code.

Preferred mechanism:

- `pyreverse` or equivalent non-agent automation for Python package/class structure.

Required as-built evidence when structure/interfaces changed:

- `as_built/package_view.*`
- `as_built/class_view.*`
- `as_built/generation_manifest.json`
- `architecture_drift_report.md`

## Rules

- Agents must consult relevant architecture artifacts before planning, implementing, or reviewing structure-sensitive work.
- As-built artifacts are evidence and must not be manually edited into design diagrams.
- If code structure changes, the as-built architecture must be refreshed before final review.
- The Python↔`kOS` boundary must be represented as a contract/runtime boundary, not as an invented class dependency graph.

## Suggested layout

You may keep one architecture pack per subsystem or per plan.

Example:


Each pack should include its own `architecture_manifest.yaml`.
