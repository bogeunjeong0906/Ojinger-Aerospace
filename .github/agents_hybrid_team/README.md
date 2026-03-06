# Hybrid Agent Team

이 팀은 `.github/agents_bogeun`의 도메인 제약과 `.github/agents_gem_team`의 orchestration/workflow를 결합한 하이브리드 팀입니다.

## 설계 목표
- KSP 오토파일럿 도메인 정확도 유지
- `runSubagent` 기반 단일 진입점 운영
- 연구 → 계획 → 도메인 검증 → 구현 → 리뷰 → 문서화 흐름 표준화
- 독립 작업에 한해 fan-out/fan-in 방식 위임 허용

## 구성
- `hybrid-orchestrator`: 단일 진입점, phase 관리, 작업 위임
- `hybrid-researcher`: 코드/문서 조사 및 구조화 보고
- `hybrid-planner`: `plan.yaml` 및 계약(contract) 설계
- `hybrid-flight-scientist`: CasADi/궤적/최적화 도메인 전문가
- `hybrid-ground-engineer`: kRPC/DPG/UI/텔레메트리 전문가
- `hybrid-embedded-pilot`: kOS/GNC/PID/실시간 제어 전문가
- `hybrid-implementer`: 실제 코드 수정 및 검증 담당
- `hybrid-reviewer`: 보안/PRD/문서 근거/역할 경계 검수
- `hybrid-documentation-writer`: 문서 및 운영 가이드 정리
- `hybrid-browser-tester`: 브라우저 기반 E2E/UI 검증
- `hybrid-devops`: 환경/배포/CI 운영

## 운영 원칙
- 사용자 응답은 한국어
- 내부 handoff는 JSON/YAML 우선
- kOS/kRPC 심볼은 `reference_docs/`에서 먼저 검증
- 문서 미발견 시 즉시 중단: `문서 미발견: '<심볼>' — 사용자 확인 필요`
- 코드 수정은 `hybrid-implementer`가 담당
- 버그 수정은 반드시 이벤트 체인 분석부터 시작

## 병렬 위임 규칙
- 가능: 독립 연구 주제, 동일 wave의 독립 작업, 리뷰와 문서 준비 등 비충돌 작업
- 불가: 선행 contract가 없는 구현, 동일 파일을 동시에 수정하는 작업, 종속 관계가 있는 wave 간 작업
- 해석: 완전한 비동기 백그라운드 큐가 아니라 orchestrator 주도의 fan-out/fan-in 구조
