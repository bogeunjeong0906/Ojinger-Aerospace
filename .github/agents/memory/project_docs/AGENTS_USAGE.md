# Hybrid Agents Quick Start

## 가장 간단한 사용법
자연어로 요청하면 됩니다.

예시:
- `현재 1axis_problem 구조를 조사하고 필요한 작업 계획부터 세워줘`
- `kOS 제어 코드 버그를 분석하고 수정 계획을 세워줘`
- `ground station GUI와 solver 연결 구조를 조사한 뒤 수정해줘`

## 내부적으로 일어나는 일
1. `hybrid-orchestrator`가 요청을 정리합니다.
2. 필요하면 `.github/agents/memory/project_docs/plan/{plan_id}/plan.yaml`을 자동 생성합니다.
3. 다른 에이전트가 이 계획을 읽고 작업합니다.
4. 결과를 다시 사용자에게 요약합니다.

## 사용자가 직접 해야 하는 일
기본적으로 없습니다.
- `.github/agents/memory/project_docs/plan/`은 내부 운영 폴더입니다.
- `plan.yaml`도 기본적으로 에이전트가 생성합니다.

## 사람이 직접 개입할 수 있는 경우
- 큰 작업 계획을 검토하고 싶을 때
- 특정 task를 다시 시키고 싶을 때
- 에이전트의 작업 순서를 바꾸고 싶을 때

## 참고 파일
- `.github/agents_hybrid_team/README.md`
- `.github/agents_hybrid_team/shared_policy.md`
- `.github/agents/memory/project_docs/plan/README.md`
- `.github/agents/memory/project_docs/plan/_template/plan.template.yaml`
- `.github/agents/memory/project_docs/plan/sample-1axis-hybrid-flow/plan.yaml`
