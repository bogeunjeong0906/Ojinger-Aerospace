# GitHub Copilot Instructions for Rocket Mission Project

<Overview>
- **Name**: GitHub Copilot Instructions for Rocket Mission Project
- **Purpose**: Manage automated space mission systems (trajectory optimization & rocket control).
</Overview>

<ResponseLanguage>
- **Explanations**: Always provide descriptions and explanations in **Korean**.
- **Artifacts**: All Code, Comments, Diagrams, and Documentation must be in **English**.
- **Tone**: Professional and technical.
</ResponseLanguage>

<DomainKnowledgeAndTooling>
- **Source of Truth**: Reference `.github/domain_knowledge/` directory.
- **Target Tools**:
    - **kOS**: Reference `KOS_DOC`.
    - **kRPC**: Reference `KRPC_DOC`.
    - **DearPyGui**: Reference `dearpygui_example.py`.
- **Rule**: DO NOT use pre-trained internal knowledge for these tools. Strictly follow provided reference files.
</DomainKnowledgeAndTooling>

<StandardToolset>
- **UI**: `dearpygui`
- **Optimization**: `casadi` (Prioritize symbolic modeling)
- **Environment**: Always activate `.venv` via `conda activate ./.venv`.
</StandardToolset>

<AgentWorkflowPrerequisites>
- **Model Policy**: Use `GPT-5 mini` (for context window). **Forbidden**: `gpt 4o`, `raptor mini`.
- **Preload Step**: Attach agent files and explicitly "read and internalize" before delegation.
- **Halt Condition**: If context is lost or files are missing, halt and request reattachment.
</AgentWorkflowPrerequisites>

<OrchestrationRules>
- **Delegation**: Use `#runsubagent` for all tasks. Orchestrator must not work directly.
- **Execution**: Wait for subagent completion and collect results before responding.
- **No Premature Replies**: Do not say "Delegating..." without actually executing.
</OrchestrationRules>

<RequestTypes>
- **간편요청 (Simple)**: Low-risk, single-step tasks. Partial workflow allowed.
- **일반요청 (General)**: Complex tasks. **Must** follow full: Research → Planning → Execution → Review.
- **Clarification**: If type is unspecified, ASK: "이 요청은 '간편요청'입니까, 아니면 '일반요청'입니까?"
</RequestTypes>

<ChangeLog>
- Added request-type (간편/일반) logic and clarifying question requirement.
- Removed all redundant sections for context efficiency.
</ChangeLog>

<AgentTeamOverview>
- **Core Workflow**: 중앙 오케스트레이터(`gem-orchestrator`)가 Phase Detection → Research → Planning → Execution Loop → Summary 순으로 워크플로를 이끌며 모든 실행은 하위 에이전트에 위임됩니다.
- **Delegation Rule**: 모든 작업은 `runSubagent`를 통해 위임하고, 오케스트레이터는 직접 워크스페이스를 수정하지 않습니다.
- **Base Parameters**: 위임 시 기본으로 포함해야 할 파라미터는 `task_id`, `plan_id`, `plan_path`, `task_definition`, `contracts` 입니다.
- **Concurrency & Waves**: 작업은 'wave' 단위로 그룹화되며, 각 파동 내에서 최대 4개의 에이전트를 병렬 실행할 수 있고 파동 완료 후 다음 파동으로 진행합니다.
- **Failure Handling**: 실패 유형에 따라 분기합니다 — `transient`는 재시도(최대 3회), `needs_replan`은 `gem-planner`에게 재계획 위임, `escalate`는 작업을 `blocked`로 표기하고 사용자에 에스컬레이션합니다. 실패 로그는 `docs/plan/{plan_id}/logs/`에 기록됩니다.
- **Agent Roles**: 주요 에이전트는 `gem-researcher`, `gem-planner`, `gem-implementer`, `gem-reviewer`, `gem-browser-tester`, `gem-devops`, `gem-documentation-writer`이며 각각 연구/계획/구현/검토/테스트/배포/문서를 담당합니다.
- **Announcements**: 오케스트레이터는 단계 시작, 파동 시작/완료, 실패/에스컬레이션, 사용자 피드백, 플랜 완료 시 짧고 에너지 있는 공지를 합니다.
</AgentTeamOverview>