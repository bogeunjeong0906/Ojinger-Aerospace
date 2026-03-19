## Phase 1 Complete: 기본 변수 및 초기화 루틴 구현

KOS 자동 발사/궤도비행 스크립트의 주요 변수(목표 Apoapsis, 중력턴 시작/종료 고도 등) 선언 및 초기화, 함수 구조 정의, PRINT 기반 테스트를 완료했습니다. TDD 원칙과 KOS 문법을 모두 준수했습니다.

**Files created/changed:**
- launch_orbit.ks

**Functions created/changed:**
- init_variables
- test_function_calls

**Tests created/changed:**
- 변수 선언/초기화 테스트 (PRINT)
- 함수 호출 구조 테스트 (PRINT)

**Review Status:** APPROVED

**Git Commit Message:**
feat: KOS 자동 발사 스크립트 변수 및 초기화

- 목표 Apoapsis, 중력턴 고도 등 주요 변수 선언 및 초기화
- 함수 구조 정의 및 PRINT 기반 테스트 구현
- TDD 원칙에 따라 테스트와 코드 동시 작성
