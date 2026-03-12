# Ojinger v2 Agent Team

Production-ready project agent team for Ojinger-Aerospace.


## Core design goals

- Optimize for GPT-4.1 reliability first.
- Preserve gem-team strengths: phase detection, research-first grounding, DAG/wave planning, contracts, verification, review gates, and bounded escalation.
- Preserve Ojinger specialization: `kOS`, `kRPC`, `CasADi`, `DearPyGui`, `system/control_tower`, `system/vessle`, `.github/agents/memory/project_docs/plan`, `.github/agents/memory/project_docs/architecture`, and `.github/agents/memory/domain_knowledge`.
- Treat architecture as a first-class required artifact, not optional documentation.
- Require every answer to include an explicit orchestration report and task-allocation report.
- Treat `.github/agents/memory/` as the durable project-development memory root; keep team-bound rules and the team README under `.github/agents/`, not in memory.
- 모든 에이전트팀 작업(연구, 계획, 구현, 리뷰, 아키텍처 갱신 등)은 반드시 루트경로 ./.venv(miniconda) 환경을 활성화한 상태에서 진행해야 합니다.
- 모든 커맨드/스크립트/파이썬 실행 전 conda activate ./.venv 를 먼저 실행하고, 환경 활성화 상태를 확인해야 합니다.
- 환경 활성화 체크는 $CONDA_DEFAULT_ENV, python sys.prefix, 또는 conda info --envs | grep '/.venv' 등으로 검증합니다.
- 환경 미활성화 상태에서는 작업을 시작하지 않습니다.

## Core agents

1. `ojinger-orchestrator` — receives the request, detects phase, routes work, and summarizes orchestration.
2. `ojinger-researcher` — gathers factual domain/codebase findings only.
3. `ojinger-architect` — owns intent architecture, as-built architecture, and architecture drift analysis.
4. `ojinger-planner` — creates and updates DAG plans, contracts, architecture-linked tasks, and PRD-aligned execution records.
5. `ojinger-implementer` — performs bounded code changes with diagnostics/tests.
6. `ojinger-reviewer` — performs read-only audit, diagnostics review, architecture conformance review, and release-risk checks.

## Why the team size is 6

GPT-4.1 has enough input context to keep one compact specialist layer beyond the standard research/planning/implementation/review flow.

- 5 agents was slightly too small because architecture had no single owner.
- 6 agents is still compact enough for GPT-4.1 while preserving strong role boundaries.
- More than 6 core agents would add routing and summarization overhead without enough benefit for the current workspace.

## Shared policy

All agents must load and treat [._shared-policy.md](._shared-policy.md) as authoritative before acting.

The shared policy defines:

- GPT-4.1 default / GPT-5.4 escalation gates,
- source-of-truth priority,
- mandatory architecture references,
- orchestration and allocation reporting rules,
- diagnostics / Problems-panel expectations,
- review-before-final-summary behavior,
- anti-drift and scope-control rules.

## Mandatory architecture workflow

Two architecture tracks are required.

1. **Intent architecture**
   - Generated from natural-language requirements.
   - Standard artifacts: Mermaid, UML-style component views, goal maps, architecture decisions, manifest.
   - Used as planning and implementation constraints.

2. **As-built architecture**
   - Generated mechanically from code.
   - Primary mechanism: `pyreverse` or equivalent non-agent automation.
   - Used as evidence, not hand-authored design.

Architecture artifacts are mandatory references for future work because they provide the system-level view faster than reading files line-by-line.

## Expected workflow

1. **Phase detection**
   - No valid plan/context -> research.
   - Research exists but architecture baseline is missing/stale -> architecture.
   - Architecture exists but no approved executable plan -> planning.
   - Approved plan with ready tasks -> execution.
   - Structural/code changes complete -> as-built refresh when needed.
   - Implementation complete -> mandatory review.
   - Final summary follows review unless the user explicitly declines review.

2. **Research**
   - Use local `.github/agents/memory/domain_knowledge/`, `.github/agents/memory/project_docs/architecture/`, `.github/agents/memory/project_docs/plan/`, code, and `system/tests/`.

3. **Architecture**
   - Build/update intent architecture from requirements.
   - Build/update as-built architecture mechanically from code when structure or interfaces changed.

4. **Planning**
   - Build DAG tasks with waves, contracts, architecture references, acceptance criteria, and verification.

5. **Implementation**
   - Execute bounded tasks.
   - Preserve architecture boundaries.
   - Report diagnostics/tests.

6. **Review**
   - Validate contracts, architecture conformance, diagnostics, risks, and PRD/plan alignment.

## Orchestration reporting requirement

Every answer must include:

- an `orchestration_report`: phase, why that phase was chosen, what was delegated, and what remains,
- an `allocation_report`: which agent owned which subtask, or explicit `self_owned` when no delegation occurred.

This requirement exists so orchestration quality and parallel execution remain auditable on every request.

## Orchestrator rule

`ojinger-orchestrator` is the most important team member.

- It may explain, route, summarize, and coordinate.
- It must not perform specialized code/architecture/research/review work itself.
- If a request needs professional code, architecture, research, or review output, the orchestrator must delegate that work to the corresponding subagent.

## Ojinger-specific operating assumptions

- `system/vessle/` is the onboard runtime domain; keep scripts compact and deployment-aware.
- `system/control_tower/` is the host-side control stack.
- `.github/agents/memory/domain_knowledge/KOS_DOC/` and `.github/agents/memory/domain_knowledge/KRPC_DOC/` are the first place to resolve runtime and command questions.
- `.github/agents/memory/project_docs/plan/{plan_id}/` is the persistent execution record.
- `.github/agents/memory/project_docs/architecture/` is the persistent architecture record and must be consulted for structure-sensitive work.

## Conditional non-core agents

These remain excluded from core v2 unless the workload justifies them:

- browser/testing specialist,
- devops/infrastructure specialist,
- large-scale documentation specialist.

## Recommended entry point

Use `ojinger-orchestrator` for almost all user-facing requests.
