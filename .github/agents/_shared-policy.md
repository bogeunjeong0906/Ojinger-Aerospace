# Ojinger v2 Shared Policy

## Purpose

This team is optimized for GPT-4.1 reliability first. Agents must prefer narrow scope, explicit checklists, structured outputs, verification, strong delegation, and controlled escalation over improvisation.

## Default model policy

- Default working model: GPT-4.1.
- Escalate to GPT-5.4 only when one of these is true:
  1. repeated failure after 2 verification/retry loops,
  2. cross-domain ambiguity spans `kOS`, `kRPC`, `CasADi`, `DearPyGui`, contracts/PRD, and architecture artifacts without local resolution,
  3. the task requires non-trivial architectural synthesis that changes contracts, state machines, mission workflow semantics, or subsystem decomposition,
  4. live-environment behavior is critical and cannot be inferred safely from workspace code plus `.github/agents/memory/domain_knowledge/` and current architecture artifacts.
- Escalation output must state:
  - why GPT-4.1 is insufficient,
  - blocking uncertainty,
  - recommended next action.

## Reliability rules

- Every directly invocable agent must load and treat `.github/team/agents_ojinger_v2/_shared-policy.md` as authoritative before acting.
- Work from the current task only. Do not widen scope without explicit plan support.
- Restate the objective internally before action.
- Prefer deterministic workspace evidence over assumptions.
- If a requirement is ambiguous, search local references first. If still ambiguous, escalate instead of guessing.
- Never mark work complete while required verification is pending or failing.
- Every answer must include:
  - `orchestration_report`,
  - `allocation_report`.


## Environment Policy

- 모든 에이전트팀 작업(연구, 계획, 구현, 리뷰, 아키텍처 갱신 등)은 반드시 루트경로 ./.venv(miniconda) 환경을 활성화한 상태에서 진행해야 함.
- 모든 커맨드/스크립트/파이썬 실행 전 conda activate ./.venv 를 먼저 실행하고, 환경 활성화 상태를 확인해야 함.
- 환경 활성화 체크는 $CONDA_DEFAULT_ENV, python sys.prefix, 또는 conda info --envs | grep '/.venv' 등으로 검증.
- 환경 미활성화 상태에서는 작업을 시작하지 않음.

## Memory layout rules

- `.github/agents/` stores the active team definition, team README, team-bound rules, and `.github/agents/memory/`.
- `.github/agents/memory/project_docs/` stores durable project docs, including architecture and plan records.
- `.github/agents/memory/domain_knowledge/` stores durable domain references such as `kOS`/`kRPC` documentation.
- `system/tests/` is the canonical automated test location.

## Source-of-truth priority

1. `.github/agents/memory/domain_knowledge/` for `kOS`/`kRPC` behavior and command semantics.
2. `.github/agents/memory/project_docs/architecture/` artifacts for system structure, boundaries, flows, and as-built evidence.
3. `.github/agents/memory/project_docs/plan/{plan_id}/plan.yaml`, `prd.yaml`, `research_findings*.yaml`, `runbook.md` for current intent and execution state.
4. Existing production code under `system/` and automated tests under `system/tests/`.
5. Templates under `.github/agents/memory/project_docs/plan/_template/` and `.github/agents/memory/project_docs/architecture/_template/`.

## Architecture rules

- Architecture artifacts are mandatory references whenever a task touches:
  - system structure,
  - module/package boundaries,
  - contracts,
  - mission workflow,
  - state machines,
  - telemetry/data flow,
  - cross-layer interactions.
- Maintain two architecture tracks:
  - **intent architecture** from user requirements,
  - **as-built architecture** generated mechanically from code.
- Intent architecture is human-authored and standardized.
- As-built architecture must be generated mechanically using `pyreverse` or equivalent automation where applicable, not hand-drawn.
- As-built artifacts are evidence and must not be manually edited into a misleading design diagram.
- If code changes alter structure/interfaces and the as-built view becomes stale, architecture refresh is required before final review.
- Agents must explicitly report:
  - `architecture_artifacts_checked`,
  - `architecture_constraints_applied`,
  - `architecture_refresh_required`.

## Ojinger domain rules

- `system/vessle/` is the canonical onboard path spelling. Do not rename it opportunistically.
- Keep the hybrid boundary intact:
  - `system/vessle/*.ks` = onboard `kOS` runtime scripts.
  - `system/control_tower/backend/` = contracts, optimizer, telemetry, supervisor, runtime/services.
  - `system/control_tower/manager/` = workflow/application orchestration.
  - `system/control_tower/ui/` = optional DearPyGui shell.
  - `system/control_tower/main.py` = CLI/bootstrap entrypoint.
- Treat `kRPC` and `DearPyGui` as optional/late-bound unless the task explicitly changes that policy.
- Keep headless-safe execution paths intact.
- `CasADi` logic belongs in backend optimization flows, not UI glue.
- `kOS` scripts must respect constrained runtime assumptions:
  - small, explicit data structures,
  - file/volume exchange via documented `kOS` mechanisms,
  - no host-only assumptions,
  - preserve launch safety and abort behavior.
- Prefer contract-first changes when data crosses tower/onboard boundaries.

## Planning and execution rules

- Use phase detection: research -> architecture -> planning -> execution -> as-built refresh -> review -> summary.
- Parallelism is encouraged when subtasks are independent, traceable, and reviewable.
- Do not impose arbitrary numeric subagent caps in policy text.
- If too much parallel work would reduce traceability, verification quality, or reviewability, batch it conservatively.
- Plans must be DAG-based with explicit waves, dependencies, contracts, and architecture references.
- Each implementation task should map to one primary deliverable and one primary owner.
- Consumers in later waves must verify producer contracts before relying on them.
- Reviewer handoff is mandatory by default after implementation and before any final summary, unless the user explicitly declines review.
- Retries must be bounded and logged in outputs.

## Verification baseline

- Minimum verification after edits:
  - check diagnostics / Problems-panel expectations,
  - run targeted tests for changed behavior when feasible,
  - confirm plan acceptance criteria touched by the task,
  - confirm architecture artifacts were respected or refreshed when required.
- If diagnostics remain:
  - distinguish pre-existing vs introduced,
  - do not ignore introduced errors,
  - escalate if they cannot be resolved safely within scope.

## Output rules

- Prefer structured JSON or YAML exactly when requested.
- Keep summaries short and factual.
- Every answer must state:
  - current phase,
  - what was delegated,
  - how work was allocated,
  - verification status,
  - next action when incomplete.

## Anti-drift checklist

Before finalizing, confirm:

- objective still matches the requested task,
- only necessary files were touched,
- role boundary was respected,
- local reference docs were consulted for domain-sensitive changes,
- architecture artifacts were checked for structure-sensitive changes,
- diagnostics/tests were checked when code changed,
- unresolved ambiguity was escalated rather than guessed.
