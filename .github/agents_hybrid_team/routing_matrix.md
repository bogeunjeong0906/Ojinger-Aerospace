# Hybrid Team Routing Matrix

| 요청 유형 | 1차 담당 | 2차 담당 | 비고 |
|---|---|---|---|
| 코드베이스 조사 | `hybrid-researcher` | `hybrid-planner` | 구조 파악 후 계획 수립 |
| CasADi/궤적 최적화 | `hybrid-flight-scientist` | `hybrid-implementer` | 계약 정의 후 구현 |
| kRPC/DPG/UI | `hybrid-ground-engineer` | `hybrid-implementer` | 문서 확인 후 구현 |
| kOS/PID/GNC | `hybrid-embedded-pilot` | `hybrid-implementer` | kOS 문법 제약 유지 |
| 버그 수정 | 도메인 전문가 | `hybrid-implementer` | 이벤트 체인 분석 필수 |
| 보안/품질 검수 | `hybrid-reviewer` | - | 구현 후 필수 |
| 문서화 | `hybrid-documentation-writer` | - | parity 유지 |
| 브라우저 E2E | `hybrid-browser-tester` | - | UI 변경 시 사용 |
| 환경/배포 | `hybrid-devops` | `hybrid-reviewer` | 승인/검증 포함 |

## 실행 원칙
- 단일 진입점은 `hybrid-orchestrator`
- 실제 코드 수정은 `hybrid-implementer`만 수행
- 독립 작업만 병렬 위임
- kOS/kRPC 심볼은 항상 `reference_docs/` 선검증
