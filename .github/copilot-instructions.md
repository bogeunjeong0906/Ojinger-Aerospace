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