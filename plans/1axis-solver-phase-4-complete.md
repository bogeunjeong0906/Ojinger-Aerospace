## Phase 4 Complete: 최적화 솔버 통합 및 DearPyGui 그래프 출력

solve_1axis_optimal() 함수로 전체 최적화 실행, 결과(time, altitude, velocity, throttle)를 DearPyGui로 영어 표기 그래프 출력하는 기능을 구현했습니다. TDD 원칙, 함수 분리, 예외 처리, 테스트 커버리지 모두 충족합니다.

**Files created/changed:**
- src/control_tower/engine/1axis_solver.py

**Functions created/changed:**
- solve_1axis_optimal
- plot_result_dearpygui

**Tests created/changed:**
- 최적화 결과 검증, 그래프 출력 확인 테스트

**Review Status:** APPROVED

**Git Commit Message:**
feat: 최적화 솔버 통합 및 DearPyGui 그래프 출력

- solve_1axis_optimal 함수로 최적화/시뮬레이션/입력 검증 통합
- plot_result_dearpygui 함수로 영어 표기 그래프 출력 구현
- TDD 기반 테스트 및 예외 처리, 커버리지 충족
