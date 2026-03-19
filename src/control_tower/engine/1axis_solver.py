## 이 파일을 one_axis_solver.py로 복사/이동 필요 (테스트 호환성)
import numpy as np

def simulate_rocket_rk4(throttle_seq, params, dt=0.1):
    """
    1차원 로켓 플랜트 모델을 RK4로 시뮬레이션한다.
    입력:
        throttle_seq: (N,) shape, 각 step별 스로틀(0~1)
        params: params.json dict
        dt: 타임스텝 (초)
    출력:
        trajectory: dict { 'time':[], 'altitude':[], 'velocity':[], 'mass':[] }
    """
    # 입력 유효성 검사
    throttle_seq = np.asarray(throttle_seq)
    if throttle_seq.ndim != 1 or throttle_seq.size == 0:
        raise ValueError("throttle_seq must be a non-empty 1D array")
    if np.any(throttle_seq < 0) or np.any(throttle_seq > 1):
        raise ValueError("throttle_seq values must be in [0, 1]")

    # 상수
    g = 9.80665
    g0 = 9.80665
    stage = params['stages'][params['current_stage']]
    F_max = stage['thrust']
    Isp = stage.get('isp', 300)  # 없으면 300초 기본값

    # 초기 상태
    h = params.get('altitude', 0.0)
    v = params.get('velocity', 0.0)
    m = params['mass']

    N = len(throttle_seq)
    time_hist = [0.0]
    h_hist = [h]
    v_hist = [v]
    m_hist = [m]

    def dynamics(x, u):
        h, v, m = x
        # u: throttle (0~1)
        dh = v
        dv = (u * F_max / m) - g
        dm = -(u * F_max) / (Isp * g0)
        return np.array([dh, dv, dm])

    x = np.array([h, v, m], dtype=float)
    for i in range(N):
        u = float(throttle_seq[i])
        # RK4 적분
        k1 = dynamics(x, u)
        k2 = dynamics(x + 0.5*dt*k1, u)
        k3 = dynamics(x + 0.5*dt*k2, u)
        k4 = dynamics(x + dt*k3, u)
        x_next = x + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        # 음수 질량/고도 방지
        x_next[2] = max(x_next[2], 0.0)
        x_next[0] = max(x_next[0], 0.0)
        x = x_next
        time_hist.append(time_hist[-1] + dt)
        h_hist.append(x[0])
        v_hist.append(x[1])
        m_hist.append(x[2])
        # 연료 고갈 시 thrust 0 처리
        if x[2] <= 0.0:
            break

    return {
        'time': np.array(time_hist),
        'altitude': np.array(h_hist),
        'velocity': np.array(v_hist),
        'mass': np.array(m_hist)
    }
import json
import os
import casadi as ca
import dearpygui.dearpygui as dpg

def load_params(json_path):
    """
    params.json 파일을 로딩하여 dict로 반환합니다.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            params = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 오류: {e}")
    return params


def validate_inputs(params, t_target, h_target, v_target):
    """
    입력 인수(t_target, h_target, v_target)와 params.json의 값 검증
    """
    errors = []
    # 필수 키 존재 여부
    for key in ['t_target', 'h_target', 'v_target']:
        if key not in params:
            errors.append(f"params.json에 '{key}' 키가 없습니다.")
    # 타입 및 값 검증
    for name, value in [('t_target', t_target), ('h_target', h_target), ('v_target', v_target)]:
        if not isinstance(value, (int, float)):
            errors.append(f"입력값 {name}는 숫자여야 합니다. 현재 타입: {type(value).__name__}")
        elif value <= 0:
            errors.append(f"입력값 {name}는 0보다 커야 합니다. 현재 값: {value}")
    if errors:
        for err in errors:
            print(f"[경고] {err}")
        raise ValueError("입력 검증 실패. 자세한 내용은 경고 메시지를 확인하세요.")
    return True

def solve_1axis_optimal(params, t_target, h_target, v_target, N=200, max_iter=500, dt=None):
    """
    Phase 3까지 구현된 최적화/시뮬레이션/입력 검증을 통합하여 1축 최적화 문제를 풀고 결과 반환
    """
    # 입력 검증
    validate_inputs(params, t_target, h_target, v_target)
    if dt is None:
        dt = t_target / N
    # 다중구간슈팅 최적화 호출
    from . import multishooting_solver
    try:
        throttle_opt, sol = multishooting_solver.setup_multiple_shooting(
            params, t_target, h_target, v_target, N=N, max_iter=max_iter, dt=dt)
    except Exception as e:
        print(f"[경고] 최적화 실패: {e}")
        throttle_opt = np.ones(N)
    # 시뮬레이션
    result = simulate_rocket_rk4(throttle_opt, params, dt=dt)
    # 결과 dict에 throttle 추가
    result['throttle'] = np.array(throttle_opt)
    return result

def plot_result_dearpygui(result):
    """
    DearPyGui로 time, altitude, velocity, throttle 그래프를 영어 표기로 출력
    """
    time = result['time']
    altitude = result['altitude']
    velocity = result['velocity']
    throttle = result['throttle']

    dpg.create_context()
    with dpg.window(label="1-Axis Rocket Optimization Result", width=900, height=700):
        with dpg.plot(label="Trajectory", height=350, width=850):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="x_axis")
            dpg.add_plot_axis(dpg.mvYAxis, label="Altitude (m)", tag="y_axis1")
            dpg.add_line_series(time, altitude, label="Altitude", parent="y_axis1")
            dpg.add_plot_axis(dpg.mvYAxis, label="Velocity (m/s)", tag="y_axis2", axis_side=dpg.mvAxisSide_Right)
            dpg.add_line_series(time, velocity, label="Velocity", parent="y_axis2")
        with dpg.plot(label="Throttle Profile", height=200, width=850):
            dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="x_axis2")
            dpg.add_plot_axis(dpg.mvYAxis, label="Throttle", tag="y_axis3")
            dpg.add_line_series(time[:len(throttle)], throttle, label="Throttle", parent="y_axis3")
    dpg.create_viewport(title="1-Axis Rocket Optimization Result", width=950, height=800)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(dpg.last_container(), True)
    dpg.start_dearpygui()
    dpg.destroy_context()
