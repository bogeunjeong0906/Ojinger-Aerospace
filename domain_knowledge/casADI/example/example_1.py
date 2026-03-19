import casadi as ca
import numpy as np
import matplotlib.pyplot as plt

def solve_rocket_optimization():
    # 1. 설정 및 파라미터
    N = 50
    Tf = 10.0
    dt = Tf / N
    g0 = 9.80665
    F_max = 50000.0
    Isp = 300.0
    m_initial = 500.0
    m_empty = 100.0
    h_goal = 100.0
    
    w_fuel = 1.0
    w_smooth = 0.1

    opti = ca.Opti()

    # 2. 결정 변수
    X = opti.variable(3, N + 1)  # [h, v, m]
    U = opti.variable(1, N)      # [throttle]

    # 3. 동역학 및 RK4 적분기
    f = lambda x, u: ca.vertcat(
        x[1],
        (u * F_max / x[2]) - g0,
        -(u * F_max) / (Isp * g0)
    )

    for k in range(N):
        k1 = f(X[:, k],         U[:, k])
        k2 = f(X[:, k] + dt/2 * k1, U[:, k])
        k3 = f(X[:, k] + dt/2 * k2, U[:, k])
        k4 = f(X[:, k] + dt * k3,   U[:, k])
        x_next = X[:, k] + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
        opti.subject_to(X[:, k+1] == x_next)

    # 4. 제약 조건
    opti.subject_to(X[0, 0] == 0)           # 초기 고도
    opti.subject_to(X[1, 0] == 0)           # 초기 속도
    opti.subject_to(X[2, 0] == m_initial)    # 초기 질량
    # 조건 완화: 0.1m, 0.1m/s 오차 허용
    opti.subject_to(opti.bounded(h_goal - 0.1, X[0, N], h_goal + 0.1))  # 종단 고도
    opti.subject_to(opti.bounded(-0.1, X[1, N], 0.1))                   # 종단 속도

    opti.subject_to(opti.bounded(0, U, 1))
    opti.subject_to(opti.bounded(0, X[0, :], 1000))
    opti.subject_to(opti.bounded(m_empty, X[2, :], m_initial))

    # 5. 목적 함수
    fuel_used = m_initial - X[2, N]
    control_effort = ca.sumsqr(U) * dt
    opti.minimize(w_fuel * fuel_used + w_smooth * control_effort)

    # 6. 초기값 설정
    opti.set_initial(X[0, :], np.linspace(0, h_goal, N+1))
    opti.set_initial(X[2, :], m_initial)
    opti.set_initial(U, 0.5)

    # 7. 솔버 설정 (로그 최소화)
    opts = {
        'ipopt.print_level': 0,           # IPOPT 내부 로그 미출력
        'print_time': False,              # 실행 시간 미출력
        'ipopt.sb': 'yes',                # IPOPT 배너 숨기기
        'ipopt.max_iter': 1000,
        'ipopt.nlp_scaling_method': 'gradient-based'
    }
    opti.solver('ipopt', opts)

    # 8. 실행 및 디버깅 결과 출력
    try:
        sol = opti.solve()
        print("-" * 40)
        print("✅ 최적화 성공 (Optimization Solved)")
        print("-" * 40)
        
        # 최종 결과값 추출
        res_h = sol.value(X[0, N])
        res_v = sol.value(X[1, N])
        res_m_final = sol.value(X[2, N])
        res_fuel = m_initial - res_m_final
        
        print(f"1. 목표 고도 도달: {res_h:.4f} m (Goal: {h_goal})")
        print(f"2. 최종 속도: {res_v:.4f} m/s (Goal: 0.0)")
        print(f"3. 초기 질량: {m_initial:.2f} kg")
        print(f"4. 최종 질량: {res_m_final:.2f} kg")
        print(f"5. 총 연료 소모량: {res_fuel:.4f} kg")
        print("-" * 40)

        # 그래프 데이터 반환용 딕셔너리
        results = {
            't': np.linspace(0, Tf, N+1),
            'h': sol.value(X[0, :]),
            'v': sol.value(X[1, :]),
            'm': sol.value(X[2, :]),
            'u': sol.value(U)
        }
        
        # 시각화 실행
        plot_results(results, res_fuel)
        return results

    except Exception as e:
        print("-" * 40)
        print("❌ 최적화 실패 (Optimization Failed)")
        print(f"에러 내용: {e}")
        # 실패 시에도 현재까지 계산된 변수값을 debug용으로 확인 가능
        try:
            h_val = opti.debug.value(X[0, N])
            v_val = opti.debug.value(X[1, N])
            m_val = opti.debug.value(X[2, N])
            u_val = opti.debug.value(U)
            # 제약조건별 상세 로깅
            print(f"[제약조건 상세]")
            # 1. 종단 고도
            h_goal_min = h_goal - 0.1
            h_goal_max = h_goal + 0.1
            h_in_range = h_goal_min <= h_val <= h_goal_max
            print(f"- [종단 고도] 목표: {h_goal_min:.4f} ~ {h_goal_max:.4f} m, 실제: {h_val:.4f} m, {'✅' if h_in_range else '❌'}")
            # 2. 종단 속도
            v_goal_min = -0.1
            v_goal_max = 0.1
            v_in_range = v_goal_min <= v_val <= v_goal_max
            print(f"- [종단 속도] 목표: {v_goal_min:.4f} ~ {v_goal_max:.4f} m/s, 실제: {v_val:.4f} m/s, {'✅' if v_in_range else '❌'}")
            # 3. 최종 질량
            m_in_range = m_val >= m_empty
            print(f"- [최종 질량] 하한: {m_empty:.2f} kg, 실제: {m_val:.2f} kg, {'✅' if m_in_range else '❌'}")
            # 4. 스로틀 제약 (대표 1~2개만)
            if hasattr(u_val, '__len__') and len(u_val) > 0:
                u_min = np.min(u_val)
                u_max = np.max(u_val)
                u_in_range = (u_min >= 0) and (u_max <= 1)
                print(f"- [스로틀] 범위: 0 ~ 1, 실제 min: {u_min:.4f}, max: {u_max:.4f}, {'✅' if u_in_range else '❌'}")
            # 5. 고도/질량 범위 제약 (대표 1~2개만)
            h_all = opti.debug.value(X[0, :])
            m_all = opti.debug.value(X[2, :])
            h_all_in_range = np.all((h_all >= 0) & (h_all <= 1000))
            m_all_in_range = np.all((m_all >= m_empty) & (m_all <= m_initial))
            print(f"- [전체 고도] 범위: 0 ~ 1000, 실제 min: {np.min(h_all):.4f}, max: {np.max(h_all):.4f}, {'✅' if h_all_in_range else '❌'}")
            print(f"- [전체 질량] 범위: {m_empty} ~ {m_initial}, 실제 min: {np.min(m_all):.4f}, max: {np.max(m_all):.4f}, {'✅' if m_all_in_range else '❌'}")
        except Exception as dbg_e:
            print(f"[제약조건 상세 출력 실패]: {dbg_e}")
        print("-" * 40)
        return None

def plot_results(res, fuel_val):
    fig, axs = plt.subplots(4, 1, figsize=(8, 10), sharex=True)
    axs[0].plot(res['t'], res['h'], 'b-', lw=2); axs[0].set_ylabel('Height [m]')
    axs[1].plot(res['t'], res['v'], 'r-', lw=2); axs[1].set_ylabel('Velocity [m/s]')
    axs[2].plot(res['t'], res['m'], 'g-', lw=2); axs[2].set_ylabel('Mass [kg]')
    axs[3].step(res['t'][:-1], res['u'], 'k-', where='post', lw=2); axs[3].set_ylabel('Throttle')
    for ax in axs: ax.grid(True)
    plt.suptitle(f"Rocket Optimization (Total Fuel: {fuel_val:.3f} kg)")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    solve_rocket_optimization()