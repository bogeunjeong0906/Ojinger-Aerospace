## Plan: KOS 기반 KSP 자동 발사 및 궤도비행 스크립트

KOS(.ks) 언어로 KSP 로켓의 자동 발사, 중력턴, 목표 궤도 진입, 순환화까지 자동화하는 스크립트를 루트 경로에 작성합니다. 도메인 지식의 공식 예제와 표준 구문을 정확히 반영합니다.

**Phases 4**
1. **Phase 1: 기본 변수 및 초기화 루틴 구현**
    - **Objective:** 발사, 중력턴, 궤도 목표 등 주요 변수 선언 및 초기화, 기본 함수 구조 정의
    - **Files/Functions to Modify/Create:** /launch_orbit.ks (신규), 변수 및 초기 함수
    - **Tests to Write:** 변수 선언/초기화 테스트, 함수 호출 구조 테스트
    - **Steps:**
        1. 주요 변수(목표 Apoapsis, 중력턴 시작/종료 고도 등) 선언 테스트 작성
        2. 변수 및 함수 선언/초기화 코드 작성
        3. 테스트 실행 및 통과 확인

2. **Phase 2: 자동 발사 및 중력턴(Ascent & Gravity Turn) 로직 구현**
    - **Objective:** 자동 발사, 스로틀/스티어링 제어, 중력턴 구간 구현
    - **Files/Functions to Modify/Create:** /launch_orbit.ks, gravity_turn 함수
    - **Tests to Write:** 발사 시퀀스, 중력턴 각도 변화 테스트
    - **Steps:**
        1. 발사 및 중력턴 함수 테스트 작성
        2. LOCK, STAGE, WAIT 등 명령어로 발사/중력턴 로직 구현
        3. 테스트 실행 및 통과 확인

3. **Phase 3: 목표 궤도 진입 및 엔진 컷오프 로직 구현**
    - **Objective:** 목표 Apoapsis 도달 감지, 스로틀 컷오프, 순환화 준비
    - **Files/Functions to Modify/Create:** /launch_orbit.ks, orbit_insertion 함수
    - **Tests to Write:** Apoapsis 도달/스로틀 컷오프 테스트
    - **Steps:**
        1. Apoapsis 도달/컷오프 테스트 작성
        2. WAIT UNTIL, LOCK THROTTLE TO 0 등 로직 구현
        3. 테스트 실행 및 통과 확인

4. **Phase 4: 순환화(Orbit Circularization) 및 전체 시퀀스 통합**
    - **Objective:** Apoapsis 근처에서 순환화 점화, 전체 자동 시퀀스 통합
    - **Files/Functions to Modify/Create:** /launch_orbit.ks, circularize 함수 및 메인 시퀀스
    - **Tests to Write:** 순환화 성공/실패, 전체 시나리오 통합 테스트
    - **Steps:**
        1. 순환화 함수/테스트 작성
        2. 전체 시퀀스 통합 및 테스트
        3. 최종 통합 테스트 및 검증

---

**Open Questions**
1. 목표 Apoapsis(예: 80,000m)는 기본값으로 둘까요, 파라미터로 받을까요?
2. MechJeb2 Addon 연동(고급 자동화)도 포함할까요, 순수 KOS 명령만 사용할까요?
3. 스크립트 파일명은 launch_orbit.ks로 진행해도 될까요?
4. 테스트는 실제 KSP 환경에서 수동 확인, 또는 코드 내 출력(PRINT)로 대체할까요?
