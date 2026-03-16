# Agent state templates

Use these templates under `docs/agent_docs/plan/{plan_id}/`.

Files:

- `state.yaml`: orchestrator only
- `plan.yaml`: planner only
- `results/{task_id}.yaml`: worker only

Rule:

- one task
- one result file
- no memory
- read files every turn
