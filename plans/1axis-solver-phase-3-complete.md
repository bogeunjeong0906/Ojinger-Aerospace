## Phase 3 Complete: 다중구간슈팅 최적화 및 비용함수 구현

casadi 기반 다중구간슈팅 최적화, 연료 최소화 비용함수, 연속성/목표 도달 제약식, 초기값(스로틀=1) 적용 및 테스트(TDD) 모두 구현/통과했습니다.

**Files created/changed:**
- src/control_tower/engine/1axis_solver.py

**Functions created/changed:**
- cost_function
- constraint_function
- setup_multiple_shooting

**Tests created/changed:**
- 비용함수/제약식/최적화 검증 테스트 (정상/예외 입력)

**Review Status:** APPROVED

**Git Commit Message:**
feat: 다중구간슈팅 최적화/비용/제약식 구현

- casadi 기반 다중구간슈팅 최적화, 연료 최소화 비용함수, 목표 도달 제약식 구현
- 초기값(스로틀=1) 적용, TDD 기반 테스트 코드 작성
- 테스트 커버리지 및 함수 명확성 충족
