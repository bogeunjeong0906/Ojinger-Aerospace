
import numpy as np
import pytest
import os
from control_tower.engine import one_axis_solver as axis_solver
TEST_JSON = os.path.join(os.path.dirname(__file__), '../src/vessel/params.json')

def test_simulate_rocket_rk4_all_throttle_one():
    params = axis_solver.load_params(TEST_JSON)
    # thrust를 충분히 크게 보정 (실제 상승 보장)
    params['stages'][params['current_stage']]['thrust'] = 2_000_000
    N = 100
    throttle_seq = np.ones(N)
    result = axis_solver.simulate_rocket_rk4(throttle_seq, params, dt=0.5)
    assert len(result['time']) >= 2
    assert result['altitude'][-1] > result['altitude'][0]
    assert result['mass'][-1] < result['mass'][0]
    assert np.all(result['mass'] >= 0)
    assert np.all(result['altitude'] >= 0)

def test_simulate_rocket_rk4_varying_throttle():
    params = axis_solver.load_params(TEST_JSON)
    N = 50
    throttle_seq = np.linspace(0, 1, N)
    result = axis_solver.simulate_rocket_rk4(throttle_seq, params, dt=0.2)
    assert len(result['time']) >= 2
    assert result['mass'][-1] <= result['mass'][0]
    assert np.all(result['mass'] >= 0)

def test_simulate_rocket_rk4_invalid_throttle():
    params = axis_solver.load_params(TEST_JSON)
    throttle_seq = -np.ones(10)
    with pytest.raises(ValueError):
        axis_solver.simulate_rocket_rk4(throttle_seq, params)
    throttle_seq = np.ones(10) * 1.5
    with pytest.raises(ValueError):
        axis_solver.simulate_rocket_rk4(throttle_seq, params)
    throttle_seq = np.array([])
    with pytest.raises(ValueError):
        axis_solver.simulate_rocket_rk4(throttle_seq, params)


def test_solve_1axis_optimal_runs():
    params = axis_solver.load_params(TEST_JSON)
    t_target = 200.0
    h_target = 20000.0
    v_target = 100.0
    # 입력 검증 통과용 키 추가
    params['t_target'] = t_target
    params['h_target'] = h_target
    params['v_target'] = v_target
    result = axis_solver.solve_1axis_optimal(params, t_target, h_target, v_target, N=50, max_iter=100)
    assert 'time' in result and 'altitude' in result and 'velocity' in result and 'throttle' in result
    assert len(result['time']) >= 2
    assert len(result['throttle']) == 50
    assert np.all((0 <= result['throttle']) & (result['throttle'] <= 1))
    assert np.all(result['altitude'] >= 0)
    assert np.all(result['time'] >= 0)


def test_plot_result_dearpygui_runs(monkeypatch):
    # 그래프 함수가 DearPyGui context에서 예외 없이 실행되는지 확인 (실제 창은 뜨지 않음)
    params = axis_solver.load_params(TEST_JSON)
    t_target = 10.0
    h_target = 1000.0
    v_target = 100.0
    params['t_target'] = t_target
    params['h_target'] = h_target
    params['v_target'] = v_target
    result = axis_solver.solve_1axis_optimal(params, t_target, h_target, v_target, N=10, max_iter=10)
    # DearPyGui의 start_dearpygui를 무시하여 창 실행 방지
    monkeypatch.setattr("dearpygui.dearpygui.start_dearpygui", lambda: None)
    try:
        axis_solver.plot_result_dearpygui(result)
    except Exception as e:
        pytest.fail(f"plot_result_dearpygui 예외 발생: {e}")
