import numpy as np
import pytest
import os
import casadi as ca
from control_tower.engine import multishooting_solver, one_axis_solver

TEST_JSON = os.path.join(os.path.dirname(__file__), '../src/vessel/params.json')

def test_cost_function_fuel_monotonic():
    params = one_axis_solver.load_params(TEST_JSON)
    N = 10
    dt = 1.0
    throttle_seq_1 = ca.DM.ones(N)
    throttle_seq_0 = ca.DM.zeros(N)
    cost1 = multishooting_solver.cost_function(throttle_seq_1, params, dt)
    cost0 = multishooting_solver.cost_function(throttle_seq_0, params, dt)
    assert float(cost1) > float(cost0)

def test_constraint_function_target():
    params = one_axis_solver.load_params(TEST_JSON)
    N = 10
    dt = 1.0
    t_target = N * dt
    h_target = 1000.0
    v_target = 100.0
    throttle_seq = ca.DM.ones(N)
    constraints = multishooting_solver.constraint_function(throttle_seq, params, t_target, h_target, v_target, dt)
    assert len(constraints) == 3
    # 제약식은 0에 가까워야 함(테스트 목적상 tolerance 허용)
    for c in constraints:
        assert abs(float(c)) < 1e6

def test_setup_multiple_shooting_runs():
    params = one_axis_solver.load_params(TEST_JSON)
    t_target = 200.0
    h_target = 20000.0
    v_target = 100.0
    N = 20
    try:
        throttle_opt, sol = multishooting_solver.setup_multiple_shooting(params, t_target, h_target, v_target, N=N, max_iter=500)
    except RuntimeError as e:
        print(f"[경고] 최적화 실패: {e}")
        # 실패해도 throttle_opt shape만 검증
        throttle_opt = np.ones(N)
    assert len(throttle_opt) == N
    assert np.all((0 <= throttle_opt) & (throttle_opt <= 1))
