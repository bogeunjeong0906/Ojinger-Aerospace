## Phase 4 Complete: 순환화 및 전체 시퀀스 통합

KOS 자동 발사/궤도비행 스크립트에 circularize 함수와 전체 시퀀스 통합 함수, PRINT 기반 테스트를 완료했습니다. TDD 원칙과 KOS 문법을 모두 준수했습니다.

**Files created/changed:**
- launch_orbit.ks

**Functions created/changed:**
- circularize
- test_circularize_success
- test_circularize_failure
- launch_to_orbit_sequence
- test_full_sequence

**Tests created/changed:**
- 순환화 성공/실패 테스트 (PRINT)
- 전체 시나리오 통합 테스트 (PRINT)

**Review Status:** APPROVED

**Git Commit Message:**
feat: KOS 순환화 및 전체 시퀀스 통합

- circularize 함수 및 순환화 성공/실패 테스트 구현
- 전체 자동 시퀀스 통합 및 PRINT 기반 검증
- TDD 원칙에 따라 테스트와 코드 동시 작성
