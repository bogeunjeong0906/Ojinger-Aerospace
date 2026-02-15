import casadi as ca
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# [6] 시간 정의 (Discretization)
# ---------------------------------------------------------
N = 1000  # 구간 수

# 1. 최적화 도구 상자(Opti) 생성
opti = ca.Opti()

# ---------------------------------------------------------
# [3] 결정 변수 정의 (Decision Variables)
# ---------------------------------------------------------
X = opti.variable(1, N+1)  # 위치 x
V = opti.variable(1, N+1)  # 속도 v
U = opti.variable(1, N)    # 제어 입력 u (브레이크)
T = opti.variable()        # 종료 시간 T (자유 시간)

# ---------------------------------------------------------
# [4] 비용 함수 (Cost Function)
# J = integral( (1000*u)^2 ) dt + lambda * T
# ---------------------------------------------------------
dt = T / N  # 미소 시간 정의
lambda_T = 1.0  # 시간 가중치 (원하는 대로 조절 가능)

# 에너지 소모(열 발생) 항 + 시간 최소화 항
fuel_cost = ca.sumsqr(1000 * U) * dt
time_cost = lambda_T * T
opti.minimize(fuel_cost + time_cost)

# ---------------------------------------------------------
# [1] 운동방정식 (Dynamics) & [5] 제약조건 (Constraints)
# ---------------------------------------------------------
for k in range(N):
    # 다음 스텝 상태 = 현재 상태 + 변화량 * dt (Euler integration)
    # x_dot = v, v_dot = -10 * u
    opti.subject_to(X[k+1] == X[k] + V[k] * dt)
    opti.subject_to(V[k+1] == V[k] + (-10 * U[k]) * dt)

# 제어 제약 (브레이크 0~1 사이)
opti.subject_to(opti.bounded(0, U, 1))
# 시간 제약 (시간은 양수여야 함)
opti.subject_to(T >= 0)

# ---------------------------------------------------------
# [2] 경계 조건 (Boundary Conditions)
# ---------------------------------------------------------
opti.subject_to(X[0] == 0)       # 초기 위치 0
opti.subject_to(V[0] == 1000)    # 초기 속도 1000
opti.subject_to(X[N] == 500000)  # 최종 위치 500,000
opti.subject_to(V[N] == 0)       # 최종 속도 0 (정지)

# ---------------------------------------------------------
# [7] 초기 추측값 (Initial Guess)
# ---------------------------------------------------------
opti.set_initial(T, 1000)
opti.set_initial(X, np.linspace(0, 500000, N+1))
opti.set_initial(V, np.linspace(1000, 0, N+1))
opti.set_initial(U, 0.5)

# ---------------------------------------------------------
# 솔버 설정 및 실행 (IPOPT)
# ---------------------------------------------------------
opti.solver('ipopt')
sol = opti.solve()

# 결과 값 추출
t_opt = sol.value(T)
x_opt = sol.value(X)
v_opt = sol.value(V)
u_opt = sol.value(U)
time_axis = np.linspace(0, t_opt, N+1)

print(f"최적 주행 시간: {t_opt:.2f} 초")

# ---------------------------------------------------------
# 결과 시각화
# ---------------------------------------------------------
plt.figure(figsize=(10, 8))

plt.subplot(3, 1, 1)
plt.plot(time_axis, x_opt, 'b', lw=2)
plt.ylabel('Position (m)')
plt.grid(True)

plt.subplot(3, 1, 2)
plt.plot(time_axis, v_opt, 'g', lw=2)
plt.ylabel('Velocity (m/s)')
plt.grid(True)

plt.subplot(3, 1, 3)
plt.step(time_axis[:-1], u_opt, 'r', where='post', lw=2)
plt.ylabel('Brake Input (u)')
plt.xlabel('Time (s)')
plt.grid(True)

plt.tight_layout()
plt.show()