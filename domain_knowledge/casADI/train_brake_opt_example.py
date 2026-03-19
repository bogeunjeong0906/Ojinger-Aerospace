"""
CasADi 1차원 최적화 예제: 기차 제동 문제 (최단 시간 정지)

빠르게 달리는 기차가 브레이크를 제어하여 정확한 위치에서 정지하도록 하는 최적화 문제.
목적: 최단 시간(T) 내에 목표 위치(p_goal)에서 정지(v=0)
"""
import casadi as ca
import numpy as np
import matplotlib.pyplot as plt
import sys

# 파라미터
v0 = 30.0         # 초기 속도 (m/s)
a_max = 3.0       # 최대 감속 (m/s^2)
N = 50            # 구간 수
# brake_limit와 p_goal을 먼저 계산
brake_limit = v0**2 / (2*a_max)
p_goal = brake_limit + 200.0  # 항상 여유 있게 설정

# 변수 선언
opti = ca.Opti()
T = opti.variable()           # 총 시간 (최적화 대상)
X = opti.variable(2, N+1)     # 상태: [위치, 속도]
U = opti.variable(1, N)       # 제어: 브레이크 (0~1)

# 동역학 함수, RK4는 dt를 반드시 ca.MX로 전달
def f(x, u):
    p, v = x[0], x[1]
    return ca.vertcat(v, -a_max * u)

# RK4 적분
def rk4(x, u, dt):
    k1 = f(x, u)
    k2 = f(x + 0.5*dt*k1, u)
    k3 = f(x + 0.5*dt*k2, u)
    k4 = f(x + dt*k3, u)
    return x + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

# 초기조건
opti.subject_to(X[0,0] == 0)      # 위치 0
opti.subject_to(X[1,0] == v0)     # 속도 v0

# 경계조건
opti.subject_to(X[0,-1] == p_goal) # 목표 위치
opti.subject_to(X[1,-1] == 0)      # 정지

# 동역학 연속성
for k in range(N):
    xk = X[:,k]
    uk = U[:,k]
    dt_sym = T / N  # 반복문 내에서 매번 symbolic dt 사용
    x_next = rk4(xk, uk, dt_sym)
    opti.subject_to(X[:,k+1] == x_next)

# 제약조건
opti.subject_to(U >= 0)
opti.subject_to(U <= 1)
opti.subject_to(X[1,:] >= 0)   # 역주행 금지
opti.subject_to(T >= 0.1)

# 목적함수: 총 시간 최소화
opti.minimize(T)

# 초기 guess 개선
T_guess = (p_goal / v0) * 4.0  # 매우 넉넉하게
opti.set_initial(T, T_guess)
time_guess = np.linspace(0, T_guess, N+1)
opti.set_initial(X[0,:], np.linspace(0, p_goal, N+1))
opti.set_initial(X[1,:], np.linspace(v0, 0, N+1))
# U: 앞부분 0, 뒷부분 1로 계단형
U_guess = np.zeros(N)
U_guess[int(N*0.3):] = 1.0
opti.set_initial(U, U_guess)

# 솔버 옵션
s_opts = {"ipopt.print_level": 5, "print_time": 0, "ipopt.tol": 1e-4, "ipopt.max_iter": 2000}
opti.solver('ipopt', s_opts)

# 제동 한계 거리 계산 및 안내
brake_limit = v0**2 / (2*a_max)
p_goal = brake_limit + 200.0  # 항상 여유 있게 설정
print(f"[INFO] 제동 한계 거리: {brake_limit:.2f} m, 목표 위치(p_goal): {p_goal:.2f} m (항상 여유있게 설정)")

def plot_trajectory(time, pos, vel, u, p_goal, title_suffix=""):
    plt.figure(figsize=(10,7))
    plt.suptitle(f'Train Braking Optimization Result (CasADi){title_suffix}')
    plt.subplot(3,1,1)
    plt.plot(time, pos, label='Position p')
    plt.axhline(p_goal, color='gray', linestyle='--', label='Target Position')
    plt.ylabel('Position (m)')
    plt.legend()
    plt.grid(True)

    plt.subplot(3,1,2)
    plt.plot(time, vel, label='Velocity v')
    plt.ylabel('Velocity (m/s)')
    plt.legend()
    plt.grid(True)

    plt.subplot(3,1,3)
    plt.step(time[:-1], u, where='post', label='Brake u')
    plt.ylabel('Brake')
    plt.xlabel('Time (s)')
    plt.ylim(-0.05, 1.05)
    plt.legend()
    plt.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()

# 최적화 실행
try:
    sol = opti.solve()
    T_opt = float(sol.value(T))
    X_opt = sol.value(X)
    U_opt = sol.value(U)
    time = np.linspace(0, T_opt, N+1)

    print(f"최적 제동 시간: {T_opt:.2f}초")
    plot_trajectory(time, X_opt[0], X_opt[1], np.squeeze(U_opt), p_goal, title_suffix=" (성공)")
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    # 디버깅용: infeasible 시 guess trajectory 플롯
    try:
        T_dbg = float(opti.debug.value(T))
        X_dbg = opti.debug.value(X)
        U_dbg = opti.debug.value(U)
        time_dbg = np.linspace(0, T_dbg, N+1)
        print("[DEBUG] T guess:", T_dbg)
        print("[DEBUG] X guess (위치):", X_dbg[0])
        print("[DEBUG] X guess (속도):", X_dbg[1])
        print("[DEBUG] U guess:", U_dbg)
        plot_trajectory(time_dbg, X_dbg[0], X_dbg[1], np.squeeze(U_dbg), p_goal, title_suffix=" (초기 guess)")
    except Exception as e2:
        print(f"[DEBUG] opti.debug.value 실패: {e2}")
    sys.exit(1)
