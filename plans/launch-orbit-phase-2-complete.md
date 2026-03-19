## Phase 2 Complete: 자동 발사 및 중력턴 로직 구현

KOS 자동 발사/궤도비행 스크립트에 gravity_turn 함수로 자동 발사 및 중력턴(Ascent & Gravity Turn) 로직을 구현하고, PRINT 기반 테스트를 완료했습니다. TDD 원칙과 KOS 문법을 모두 준수했습니다.

**Files created/changed:**
- launch_orbit.ks

**Functions created/changed:**
- gravity_turn
- test_gravity_turn

**Tests created/changed:**
- 발사 시퀀스 테스트 (PRINT)
- 중력턴 각도 변화 테스트 (PRINT)

**Review Status:** APPROVED

**Git Commit Message:**
feat: KOS 자동 발사/중력턴 로직 구현

- gravity_turn 함수로 자동 발사 및 중력턴 시퀀스 구현
- 스로틀/스티어링 제어, 각도 변화, PRINT 기반 테스트 추가
- TDD 원칙에 따라 테스트와 코드 동시 작성
