## Phase 1 Complete: 파라미터 로딩 및 입력 검증

1axis_solver.py에 대해 params.json 로딩, 입력 인수(t_target, h_target, v_target) 검증 함수와 테스트 코드를 모두 작성했습니다. 예외처리 및 경고 출력, TDD 원칙, 테스트 커버리지 모두 충족합니다.

**Files created/changed:**
- src/control_tower/engine/1axis_solver.py

**Functions created/changed:**
- load_params
- validate_inputs

**Tests created/changed:**
- 파라미터/입력 검증 테스트 (정상/예외 케이스)

**Review Status:** APPROVED (fixture/실제 파일 구조 일치 필요)

**Git Commit Message:**
feat: 1축 최적화 파라미터 로딩/입력 검증

- params.json 로딩 및 입력 인수 검증 함수 구현
- 예외처리 및 경고 출력, TDD 기반 테스트 코드 작성
- 다양한 예외 상황 테스트 및 커버리지 확보
