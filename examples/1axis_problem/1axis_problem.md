# � 1차원 로켓 제어 최적화 문제 정의서

이 예제에서는 단일 축으로 움직이는 로켓을 대상으로 최적 제어 문제를 정의하고
CasADi를 이용해 솔버를 작성합니다. 이후 DearPyGui 기반 관제탑과 KSP용
KOS/KRPC 임베디드 스크립트를 연결하는 구조를 구현합니다.

---

## 1. 상태 공간 방정식 (Dynamics)
* **위치** $x$ (m)
* **속도** $v$ (m/s)

로켓에 작용하는 제어 $u(t)$는 엔진 추력(가속도)이며,
중력가속도 $g=9.81\,	ext{m/s}^2$를 상쇄합니다:

\[
\dot{x} = v,\qquad
\dot{v} = u - g
\]

(모델 단순화를 위해 질량 변화 및 공기저항은 무시합니다.)

---

## 2. 결정 변수 (Decision Variables)
* **상태 변수:** $X_k = [x_k, v_k]^\top$ at discrete time points $k=0\ldots N$.
* **제어 입력:** $U_k$ (추력 가속도), $0 \le U_k \le U_{\max}$.
* **종료 시간:** 연속 최적화 변수 $T>0$.

---

## 3. 경계 조건 (Boundary Conditions)
* 초기 상태: $x(0)=0$, $v(0)=0$.
* 목표 상태: $x(T)=x_{\mathrm{target}}$ (예: 1000 m), $v(T)=0$.

---

## 4. 제약 조건 (Constraints)
* 제어 범위: $0\le u(t)\le U_{\max}$ (예: 20 m/s²).
* 시간 $T$는 양수.
* 모든 구간에서 위 **Dynamics** 수식을 만족해야 함.

---

## 5. 비용 함수 (Cost Function)
추력 제곱의 적분을 최소화하여 연료 효율을 높이고,
종료 시간에 일정 가중치를 둡니다:

\[
J = \int_{0}^{T} u(t)^2 \,dt + \lambda T,
\qquad \lambda=0.1
\]

---

## 6. 시간 도메인 정의 (Discretization)
* 구간 수 $N$ (기본 100).
* 시간 간격 $\Delta t = T/N$.
* 이산화는 전진 오일러로 처리합니다.

---

## 7. 솔버 스크립트
아래 `solver.py`를 실행하면 CasADi가 IPOPT을 호출해 최적
추력 프로파일을 계산합니다. 기본 호출 예:

```bash
python examples/1axis_problem/solver.py
```

출력으로 계산된 궤적과 제어 신호를 플롯합니다.

## 8. 관제탑(DearPyGui) 사용법
`ground_station/gui.py` 스크립트는 그래픽 인터페이스를 제공하며 다음과
같이 실행합니다:

```bash
python examples/1axis_problem/ground_station/gui.py
```

- **Target (m)**: 목표 거리 입력
- **Max thrust**: 최대 추력(가속도)
- **Discretization N**: 시간 분할 수
- **Run solver**: CasADi 최적화 실행 후 결과 그래프 표시
- **Send to KSP**: 현재 솔루션을 KRPC를 통해 케릭터에게 전송 (KSP가 실행 중이어야 함)

GUI는 궤적(위치·속도)과 제어(추력 프로파일)를 플롯하고 로그 창에 상태를
표시합니다.

자세한 수식과 GUI/KOS 통합은 각 섹션에서 다룹니다.