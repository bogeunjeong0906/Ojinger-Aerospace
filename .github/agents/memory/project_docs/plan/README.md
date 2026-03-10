# .github/agents/memory/project_docs/plan

이 폴더는 하이브리드 에이전트 팀이 작업 계획을 저장하고 이어서 수행하기 위한 내부 작업 공간입니다.

## 핵심 개념
- 각 사용자 요청은 하나의 `plan_id`를 가질 수 있습니다.
- 각 요청의 계획 파일은 `.github/agents/memory/project_docs/plan/{plan_id}/plan.yaml`에 저장됩니다.
- 관련 조사 결과는 같은 폴더 안의 `research_findings_*.yaml`에 저장할 수 있습니다.
- 필요하면 로그, 증거, 요약 문서도 같은 폴더에 저장할 수 있습니다.

## 누가 만드는가
기본적으로 사람은 이 폴더를 직접 만들거나 수정할 필요가 없습니다.
- `hybrid-orchestrator`: 계획 필요 여부 판단
- `hybrid-planner`: `plan.yaml` 생성/갱신
- 다른 에이전트: 같은 폴더의 산출물을 읽고 활용

## 최소 디렉터리 구조
- `.github/agents/memory/project_docs/plan/_template/`: 템플릿 보관
- `.github/agents/memory/project_docs/plan/{plan_id}/plan.yaml`: 실제 작업 계획

## 예시
- `.github/agents/memory/project_docs/plan/sample-1axis-hybrid-flow/plan.yaml`

## 상태 값 예시
- `pending_approval`
- `approved`
- `in_progress`
- `completed`
- `failed`

## 기본 사용 방식
1. 사용자가 자연어로 요청
2. 오케스트레이터가 계획 필요 여부를 판단
3. 필요 시 플래너가 `plan.yaml` 생성
4. 에이전트들이 해당 계획을 읽고 작업 수행
5. 결과를 사용자에게 보고
