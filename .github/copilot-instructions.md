# Ojinger Aerospace Project Instructions

## Scope

- This file contains project-specific always-on guidance for this repository.
- Generic agent behavior remains defined by the agent file and reusable core customizations under `.github/agents`, `.github/instructions`, and `.github/skills`.
- Project-specific file instructions are stored under `.github/instructions/project/`.
- Project-specific skills are stored under `.github/skills/` with the `ojinger-` prefix.

## Language

- Respond in Korean by default.
- You may keep technical terms, APIs, and package names in English when that is clearer.

## Knowledge Sources

- Before writing or editing project code, check whether the task depends on repository domain references under `docs/domain_knowledge`.
- Treat these sources as authoritative for project-specific syntax and workflows:
  - `docs/domain_knowledge/KOS_DOC` and `docs/domain_knowledge/KOS_cheatsheet` for kOS
  - `docs/domain_knowledge/KRPC_DOC` for kRPC
  - `docs/domain_knowledge/dearpygui_example.py` for dearpygui usage patterns
  - `docs/domain_knowledge/casADI/` for CasADi examples

## Standard Stack

- Real-time KSP control: `kOS`
- Remote control and telemetry: `krpc`
- UI: `dearpygui`
- Data processing and math: `numpy`
- Numerical analysis and optimization: `casadi`

## Architecture And Documentation

- Follow repository architecture documents under `docs/` and `report/` when they are relevant to the task.
- When documenting structure or behavior with diagrams, use UML semantics and Mermaid syntax.

## Python Environment

- Prefer the repository-local environment before running Python for project tasks.
- Default activation command for project Python work: `conda activate ./.venv`
- If that environment is unavailable, fall back to the active environment only after checking project constraints.

## Git And Safety

- Do not push without explicit user approval.
- Do not assume that multi-step work implies permission to commit.
- If the user explicitly asks for commits during a larger workflow, keep commits aligned to meaningful checkpoints.

## KOS Cheatsheet Workflows

- For KOS HTML source conversion rules, use the project instruction in `.github/instructions/project/ojinger-kos-html-cheatsheet.instructions.md`.
- For non-HTML cheatsheet authoring workflows, use the `ojinger-kos-nonhtml-cheatsheet` skill.
- For cheatsheet inspection and verdict workflows, use the `ojinger-kos-quality-inspection` skill.