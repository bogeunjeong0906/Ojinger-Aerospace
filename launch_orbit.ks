// launch_orbit.ks
// Phase 1: 주요 변수 선언 및 초기화, 함수 구조 정의, 테스트 포함

clearscreen.

// 1. 주요 변수 선언 및 초기화
set target_apoapsis to 80000. // 목표 Apoapsis (m)
set turn_start_altitude to 1000. // 중력턴 시작 고도 (m)
set turn_end_altitude to 45000. // 중력턴 종료 고도 (m)
set turn_angle to 0. // 중력턴 각도 (deg)

// 변수 선언/초기화 테스트
print "[TEST] 목표 Apoapsis: " + target_apoapsis.
print "[TEST] 중력턴 시작 고도: " + turn_start_altitude.
print "[TEST] 중력턴 종료 고도: " + turn_end_altitude.
print "[TEST] 중력턴 각도: " + turn_angle.

// 2. 함수 구조 정의 (기본 틀)
function init_variables {
  set target_apoapsis to 80000.
  set turn_start_altitude to 1000.
  set turn_end_altitude to 45000.
  set turn_angle to 0.
  print "[init_variables] 변수 초기화 완료".
}.

function test_function_calls {
  print "[TEST] 함수 호출 테스트: init_variables()".
  init_variables().
  print "[TEST] 함수 호출 테스트 완료".
}.

// 3. 테스트 실행
print "[TEST] 함수 호출 구조 테스트 시작".
test_function_calls().

print "[TEST] 모든 테스트 완료".

// Phase 2: 자동 발사 및 중력턴(Ascent & Gravity Turn) 로직 구현

function gravity_turn {
  print "[gravity_turn] 자동 발사 및 중력턴 시퀀스 시작".
  clearscreen.
  lock throttle to 1.0.
  print "[gravity_turn] 카운트다운 시작".
  from { local countdown is 5. } until countdown = 0 step { set countdown to countdown - 1. } do {
    print "..." + countdown.
    wait 1.
  }.
  print "[gravity_turn] 발사!".
  stage.
  wait 1.
  set mysteer to heading(90, 90).
  lock steering to mysteer.
  print "[gravity_turn] 중력턴 루프 진입".
  until ship:apoapsis > target_apoapsis {
    if ship:altitude < turn_start_altitude {
      set turn_angle to 90.
    } else if ship:altitude >= turn_start_altitude and ship:altitude < turn_end_altitude {
      set turn_angle to 90 - ((ship:altitude - turn_start_altitude) / (turn_end_altitude - turn_start_altitude)) * 80.
    } else {
      set turn_angle to 10.
    }.
    set mysteer to heading(90, turn_angle).
    print "[gravity_turn] ALT: " + round(ship:altitude,0) + " | 각도: " + round(turn_angle,1) at(0,15).
    print "[gravity_turn] APO: " + round(ship:apoapsis,0) at(0,16).
    wait 0.2.
  }.
  print "[gravity_turn] 목표 Apoapsis 도달, 스로틀 컷".
  lock throttle to 0.
}.

function test_gravity_turn {
  print "[TEST] gravity_turn 함수 테스트 시작".
  gravity_turn().
  print "[TEST] gravity_turn 함수 테스트 완료".
}.

// Phase 2 테스트 실행
print "[TEST] gravity_turn 함수 테스트 호출".
test_gravity_turn().
print "[TEST] Phase 2 테스트 완료".

// Phase 3: 목표 궤도 진입 및 엔진 컷오프 로직 구현

function orbit_insertion {
  print "[orbit_insertion] 목표 Apoapsis 도달 감지 대기...".
  // 목표 Apoapsis 도달까지 대기
  wait until ship:apoapsis >= target_apoapsis.
  print "[orbit_insertion] 목표 Apoapsis 도달! 스로틀 컷오프".
  lock throttle to 0.
  print "[orbit_insertion] 순환화 준비 완료 (엔진 컷오프)".
}.

function test_orbit_insertion {
  print "[TEST] orbit_insertion 함수 테스트 시작".
  orbit_insertion().
  print "[TEST] orbit_insertion 함수 테스트 완료".
}.

// Phase 3 테스트 실행
print "[TEST] orbit_insertion 함수 테스트 호출".
test_orbit_insertion().
print "[TEST] Phase 3 테스트 완료".


// Phase 4: 순환화(Orbit Circularization) 및 전체 시퀀스 통합

function circularize {
  print "[circularize] 순환화 시퀀스 시작".
  // Apoapsis 근처까지 대기
  wait until ship:periapsis > 0 and ship:apoapsis > 0.
  print "[circularize] ETA:APOAPSIS = " + round(ship:eta:apoapsis,1).
  wait until ship:eta:apoapsis < 10.
  print "[circularize] Apoapsis 근처 도달, 순환화 점화 준비".
  lock steering to prograde.
  lock throttle to 1.
  print "[circularize] 순환화 점화!".
  // 순환화 점화: Periapsis가 목표 Apoapsis 근처에 도달할 때까지
  until ship:periapsis >= target_apoapsis - 500 {
    print "[circularize] PERI: " + round(ship:periapsis,0) + " | APO: " + round(ship:apoapsis,0) at(0,18).
    wait 0.2.
  }.
  print "[circularize] 순환화 완료, 스로틀 컷".
  lock throttle to 0.
}.

function test_circularize_success {
  print "[TEST] circularize 함수 성공 시나리오 테스트 시작".
  circularize().
  if ship:periapsis >= target_apoapsis - 500 {
    print "[TEST] 순환화 성공: PERI = " + round(ship:periapsis,0).
  } else {
    print "[TEST] 순환화 실패: PERI = " + round(ship:periapsis,0).
  }.
  print "[TEST] circularize 함수 성공 시나리오 테스트 완료".
}.

function test_circularize_failure {
  print "[TEST] circularize 함수 실패 시나리오 테스트 시작".
  // 실패 조건: 임의로 목표 Apoapsis를 높게 설정
  set target_apoapsis to 200000.
  circularize().
  if ship:periapsis < target_apoapsis - 500 {
    print "[TEST] 순환화 실패 검증: PERI = " + round(ship:periapsis,0).
  } else {
    print "[TEST] 순환화 실패 검증 실패: PERI = " + round(ship:periapsis,0).
  }.
  print "[TEST] circularize 함수 실패 시나리오 테스트 완료".
  // 원래 목표 Apoapsis 복구
  set target_apoapsis to 80000.
}.

function launch_to_orbit_sequence {
  print "[launch_to_orbit_sequence] 전체 자동 시퀀스 시작 (발사→중력턴→궤도진입→순환화)".
  init_variables().
  gravity_turn().
  orbit_insertion().
  circularize().
  print "[launch_to_orbit_sequence] 전체 시퀀스 완료".
}.

function test_full_sequence {
  print "[TEST] 전체 시나리오 통합 테스트 시작".
  launch_to_orbit_sequence().
  if ship:periapsis >= target_apoapsis - 500 {
    print "[TEST] 전체 시퀀스 성공: PERI = " + round(ship:periapsis,0).
  } else {
    print "[TEST] 전체 시퀀스 실패: PERI = " + round(ship:periapsis,0).
  }.
  print "[TEST] 전체 시나리오 통합 테스트 완료".
}.

// Phase 4 테스트 실행
print "[TEST] circularize 함수 성공/실패 테스트 호출".
test_circularize_success().
test_circularize_failure().
print "[TEST] 전체 시퀀스 통합 테스트 호출".
test_full_sequence().
print "[TEST] Phase 4 테스트 완료".
