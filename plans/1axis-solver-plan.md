## Plan: 1축 로켓 최적화 솔버 개발 (Casadi, Multiple Shooting, RK4)

로켓의 수직상승/하강만 시뮬레이션하며, 머리는 항상 하늘방향으로 고정. 목표는 넉넉한 t_target까지 h_target 고도에 v_target(기본값 0)으로 도달하는 것. 비용함수는 연료 소모량이며, 연료소모율은 isp로 계산. 입력은 params.json(로켓 파라미터), t_target, h_target, v_target.

**Phases 4**
1. **Phase 1: 파라미터 로딩 및 입력 검증**
    - params.json, t_target, h_target, v_target 로딩 및 검증
    - 함수: load_params(), validate_inputs()
    - 테스트: 입력/파라미터 검증

2. **Phase 2: 플랜트 모델 및 RK4 시뮬레이션 구현**
    - 입력(스로틀)→출력(고도, 속도, 질량) RK4로 시뮬레이션
    - 함수: simulate_rocket_rk4()
    - 테스트: RK4 시뮬레이션 결과 검증

3. **Phase 3: 다중구간슈팅 최적화 문제 정의 및 비용함수 구현**
    - 구간개수 200, 반복 500, 초기 guide값(모든 구간 스로틀=1)
    - 비용함수: 연료 소모량 최소화(isp 활용)
    - 제약식: 위치/속도 연속성, 목표 도달(t_target, h_target, v_target)
    - 함수: cost_function(), constraint_function(), setup_multiple_shooting()
    - 테스트: 비용함수/제약식 검증

4. **Phase 4: 최적화 솔버 통합 및 DearPyGui 그래프 출력**
    - casadi 기반 최적화 루틴 구현
    - 결과: time, altitude, velocity, throttle 등 영어 표기 그래프 출력(DearPyGui)
    - 함수: solve_1axis_optimal(), plot_result_dearpygui()
    - 테스트: 최적화 결과 검증, 그래프 출력 확인

---

**반영 사항**
- 목표 시간(t_target)은 넉넉하게 설정하여 시뮬레이션 실패 방지
- DearPyGui 플롯에는 위치(altitude), 속도(velocity), 스로틀(throttle)를 시간(time)에 대해 표시
- 초기 guide값은 모든 구간에 대해 스로틀=1로 설정

---

계획은 미리 승인되었습니다. Phase 1부터 순차적으로 진행하겠습니다.
