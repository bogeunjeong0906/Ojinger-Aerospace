import numpy as np
import casadi as ca

# 기존 simulate_rocket_rk4, load_params, validate_inputs 함수는 그대로 사용
# 다중구간슈팅 최적화용 함수 및 비용/제약 함수 구현

def cost_function(throttle_seq, params, dt=0.1):
    """
    연료 소모량 최소화 비용함수 (최종 mass 최대화)
    throttle_seq: (N,) casadi SX/DM
    params: dict
    dt: float
    return: casadi SX/DM (cost)
    """
    g0 = 9.80665
    stage = params['stages'][params['current_stage']]
    F_max = stage['thrust']
    Isp = stage.get('isp', 300)
    m = params['mass']
    cost = 0
    N = int(throttle_seq.size1())
    for i in range(N):
        u = throttle_seq[i]
        dm = -(u * F_max) / (Isp * g0) * dt
        m = m + dm
        m = ca.fmax(m, 0)
    # 연료 소모량 = 초기질량 - 최종질량
    return params['mass'] - m


def constraint_function(throttle_seq, params, t_target, h_target, v_target, dt=0.1):
    """
    위치/속도 연속성, 목표 도달 제약식
    return: list of casadi SX/DM (constraints)
    """
    stage = params['stages'][params['current_stage']]
    F_max = stage['thrust']
    Isp = stage.get('isp', 300)
    g = 9.80665
    g0 = 9.80665
    h = params.get('altitude', 0.0)
    v = params.get('velocity', 0.0)
    m = params['mass']
    N = int(throttle_seq.size1())
    x = ca.vertcat(h, v, m)
    for i in range(N):
        u = throttle_seq[i]
        dh = x[1]
        dv = (u * F_max / x[2]) - g
        dm = -(u * F_max) / (Isp * g0)
        x = x + dt * ca.vertcat(dh, dv, dm)
        x[2] = ca.fmax(x[2], 0)
        x[0] = ca.fmax(x[0], 0)
    # 목표 도달 제약 (최종 시각, 고도, 속도)
    constraints = [
        (N*dt) - t_target,  # 시간 일치
        x[0] - h_target,    # 고도 일치
        x[1] - v_target     # 속도 일치
    ]
    return constraints


def setup_multiple_shooting(params, t_target, h_target, v_target, N=200, max_iter=500, dt=None):
    """
    casadi 기반 다중구간슈팅 최적화 문제 정의 및 풀이
    """
    if dt is None:
        dt = t_target / N
    opti = ca.Opti()
    throttle_seq = opti.variable(N)
    opti.subject_to(throttle_seq >= 0)
    opti.subject_to(throttle_seq <= 1)
    # 비용함수
    opti.minimize(cost_function(throttle_seq, params, dt))
    # 제약식
    constraints = constraint_function(throttle_seq, params, t_target, h_target, v_target, dt)
    opti.subject_to(ca.vertcat(*constraints) == 0)
    # 초기값: 모든 구간 스로틀=1
    opti.set_initial(throttle_seq, 1)
    p_opts = {"expand":True}
    s_opts = {"max_iter": max_iter}
    opti.solver('ipopt', p_opts, s_opts)
    sol = opti.solve()
    throttle_opt = sol.value(throttle_seq)
    return throttle_opt, sol
