# Shared Policy for Hybrid Team

## 1. Language
- 사용자 대상 응답은 한국어로 작성한다.
- 기술 용어는 영어 병기를 허용한다.
- 내부 산출물은 JSON/YAML을 우선 사용한다.

## 2. Domain Evidence Policy
- kOS 관련 심볼은 `reference_docs/KOS_DOC/`에서 먼저 확인한다.
- kRPC 관련 심볼은 `reference_docs/KRPC_DOC/`에서 먼저 확인한다.
- 문서에 없는 심볼은 생성하지 않는다.
- 사용 보고 형식:
  - `문서 미발견: '<심볼>' — 사용자 확인 필요`

## 3. Ownership
- `hybrid-flight-scientist`: 수학/비행역학/최적화
- `hybrid-ground-engineer`: 지상 UI, kRPC, 시각화
- `hybrid-embedded-pilot`: kOS 실시간 제어
- `hybrid-implementer`: 코드 수정, 테스트, 정적 검증
- `hybrid-reviewer`: 보안, PRD, 문서 근거, 역할 경계 검수

## 4. Debugging Protocol
버그 수정 요청은 다음 순서를 따른다.
1. `[트리거 -> 연쇄 이벤트]` 나열
2. 손상된 체인과 인접 체인 분리
3. 로그 패치 또는 관측 포인트 제안
4. 수정안 제시

## 5. Testing Policy
- 도메인 전문가 에이전트는 테스트 실행의 주체가 아니다.
- 테스트 실행과 정적 검증은 `hybrid-implementer` 또는 `hybrid-reviewer`가 담당한다.
- 사용자가 원하지 않으면 불필요한 무거운 검증은 피한다.

## 6. Parallel Delegation Policy
- 병렬 위임은 독립 작업에만 허용한다.
- 종속 관계가 있으면 wave 단위 순차 실행을 강제한다.
- 동일 파일/동일 계약을 동시에 수정하는 작업은 병렬 위임 금지.
- `runSubagent` 기반 위임은 사용자 입장에서 단일 대화 경험을 제공하지만, 완전한 백그라운드 비동기 작업 큐로 간주하지 않는다.

## 7. Output Policy
- 최종 사용자 응답은 짧고 실행 가능해야 한다.
- 파일 수정이 포함되면 변경 범위와 다음 단계만 요약한다.
- 근거 없는 추정 구현, 역할 침범, 문서 미검증 API 사용을 금지한다.
