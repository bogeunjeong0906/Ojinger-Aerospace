// dv.ks
// 목적: MechJeb(addon)의 정보를 사용해 스테이지 Δv를 출력하고,
//        현재 바디 파라미터로 "대기권 밖의 가장 낮은 원궤도(=lowest safe circular orbit)"
//        에 필요한 Δv를 계산한 뒤 MechJeb의 총 Δv와 비교하여 실행 가능성 판정
// 사용법: RUN "0:/dv.ks".

// 참고 문서 (kOS reference)
// - ADDONS:MJ / ADDONS:MJ:INFO — reference_docs/KOS_DOC/kOS.MechJeb2.Addon-main/README.md (lines ~72, 277, 409)
//   예: set info to addons:mj:info.  (MechJeb info items: TOTALDV*, STAGEDELTAV*)
//   (문서 예시: reference_docs/KOS_DOC/kOS.MechJeb2.Addon-main/README.md line 72, 409)
// - ADDONS:AVAILABLE (addon 존재 확인 권장) — reference_docs/KOS_DOC/addons/KAC.html (line ~109)
// - SHIP:DELTAV / SHIP:STAGEDELTAV — reference_docs/KOS_DOC/structures/vessels/deltav.html (lines ~145-160)
// - BODY:MU / BODY:RADIUS / BODY:ATM:HEIGHT — reference_docs/KOS_DOC/structures/celestial_bodies/body.html (lines ~327-334)
// - ORBIT 속성 및 SHIP:VELOCITY:ORBIT:MAGNITUDE — reference_docs/KOS_DOC/language/syntax.html (line ~268)
// - SQRT 함수 — reference_docs/KOS_DOC/math/basic.html (line ~648)

// 기본 손실 마진(사용자 조정 가능)
SET DEFAULT_ATMOSPHERIC_LOSS TO 1500.   // (ascent.ks 관례 — 대기권 손실 보수)
SET DEFAULT_VACUUM_LOSS TO 300.
SET LOSS_MARGIN TO -1.                  // -1이면 자동으로 위 기본값 사용
SET TARGET_ALT_OVERRIDE TO -1.          // >0이면 강제 목표 고도(m)

// --- 헬퍼: 숫자 포맷 ---
FUNCTION fmtms { PARAMETER x. RETURN ROUND(x,0) + " m/s". }.

// MechJeb 사용 가능 여부 확인 (권장 패턴)
// 문서: reference_docs/KOS_DOC/kOS.MechJeb2.Addon-main/README.md line ~72
IF NOT ADDONS:AVAILABLE("MJ") {
    PRINT "경고: MechJeb(ADDONS:MJ) 애드온이 감지되지 않았습니다. 이 스크립트는 MechJeb 정보를 사용하도록 설계되었습니다.".
    PRINT "대신 kOS 내장 DELTAV 값을 사용하여 비교를 시도합니다. (권장: MechJeb 설치 후 재실행)".
    // 계속 실행하되 MJ 정보는 사용하지 않음
    SET useMJ TO FALSE.
} ELSE {
    SET useMJ TO TRUE.
}

// MechJeb info wrapper 준비 (존재하면 사용)
IF useMJ {
    // reference: set info to addons:mj:info.  — reference_docs/KOS_DOC/kOS.MechJeb2.Addon-main/README.md (line ~409)
    SET info TO ADDONS:MJ:INFO.
}

// MechJeb에서 읽어온(또는 kOS에서 계산된) 스테이지/총 Δv 출력
PRINT "--- Stage Δv (MechJeb 우선 표시) ---".
LOCAL topStage TO SHIP:STAGENUM.
LOCAL s TO topStage.
UNTIL s < 0 {
    // kOS 기본 스테이지 Δv (참고): SHIP:STAGEDELTAV(s):CURRENT  — reference_docs/KOS_DOC/structures/vessels/deltav.html (line ~151)
    LOCAL kos_stage_asl TO SHIP:STAGEDELTAV(s):CURRENT.
    LOCAL kos_stage_vac TO SHIP:STAGEDELTAV(s):VACUUM.

    IF useMJ {
        // MechJeb의 'current stage' Δv (문서: info:STAGEDELTAVATM / info:STAGEDELTAVVAC)
        // 참고: reference_docs/KOS_DOC/kOS.MechJeb2.Addon-main/README.md (lines ~396-413)
            LOCAL mj_stage_atm TO -1.
        LOCAL mj_stage_vac TO -1.
        IF info:HASSUFFIX("STAGEDELTAVATM") { SET mj_stage_atm TO info:STAGEDELTAVATM. }.
        IF info:HASSUFFIX("STAGEDELTAVVAC") { SET mj_stage_vac TO info:STAGEDELTAVVAC. }.
        LOCAL mj_asl_str TO "N/A".
        LOCAL mj_vac_str TO "N/A".
        IF mj_stage_atm >= 0 { SET mj_asl_str TO ROUND(mj_stage_atm,0). }.
        IF mj_stage_vac >= 0 { SET mj_vac_str TO ROUND(mj_stage_vac,0). }.
        PRINT "스테이지 " + s + ": MechJeb(ASL=" + mj_asl_str + ", Vac=" + mj_vac_str + ")  |  kOS(ASL=" + ROUND(kos_stage_asl,0) + ", Vac=" + ROUND(kos_stage_vac,0) + ")".
    } ELSE {
        PRINT "스테이지 " + s + ": kOS(ASL=" + ROUND(kos_stage_asl,0) + ", Vac=" + ROUND(kos_stage_vac,0) + ")".
    }.

    SET s TO s - 1.
}.

// 목표 원궤도에 필요한 Δv 계산 (ascent.ks와 동일한 규칙 사용)
// - 목표 고도: BODY:ATM:HEIGHT + 1000 (대기 존재 시), 아니면 1000m
// - 이상적 Δv = max(0, v_circ_target - v_current)
// - 필요 Δv = 이상적 Δv + LOSS_MARGIN(기본값 자동 적용)

// BODY 파라미터 읽기 — reference_docs/KOS_DOC/structures/celestial_bodies/body.html (lines ~327-334)
SET curBody TO SHIP:BODY.
SET mu TO curBody:MU.
SET radius TO curBody:RADIUS.

SET atm_height TO 0.
IF curBody:ATM:EXISTS { SET atm_height TO curBody:ATM:HEIGHT. }.

// 현재 속도(궤도/준궤도 상태인 경우) — SHIP:VELOCITY:ORBIT:MAGNITUDE 참고 (language syntax + orbit structures)
SET ship_status TO SHIP:STATUS.
SET v_current TO 0.
IF ship_status = "ORBITING" OR ship_status = "SUB_ORBITAL" { SET v_current TO SHIP:VELOCITY:ORBIT:MAGNITUDE. }.

// target_alt은 inline IF 대신 명시적 분기문으로 설정합니다 (kOS는 SET 내부 IF를 허용하지 않음)
SET target_alt TO 1000.
IF atm_height > 0 {
    SET target_alt TO atm_height + 1000.
}.
IF TARGET_ALT_OVERRIDE > 0 { SET target_alt TO TARGET_ALT_OVERRIDE. }.

SET r_target TO radius + target_alt.
// 원형 속도: v = sqrt(mu / r)  — SQRT 참조: reference_docs/KOS_DOC/math/basic.html (line ~648)
SET v_circ_target TO SQRT(mu / r_target).

SET ideal_delta_v TO 0.
IF v_circ_target > v_current { SET ideal_delta_v TO v_circ_target - v_current. }.

IF LOSS_MARGIN < 0 {
    IF curBody:ATM:EXISTS { SET used_loss TO DEFAULT_ATMOSPHERIC_LOSS. } ELSE { SET used_loss TO DEFAULT_VACUUM_LOSS. }.
} ELSE { SET used_loss TO LOSS_MARGIN. }.
SET required_delta_v TO ideal_delta_v + used_loss.

PRINT "--- 목표 원궤도 요약 ---".
PRINT "바디: " + curBody:NAME + "    목표 고도(안전): " + ROUND(target_alt,0) + " m".
PRINT "목표 원형 속도: " + ROUND(v_circ_target,1) + " m/s".
PRINT "이상적 Δv (손실 무시): " + ROUND(ideal_delta_v,0) + " m/s".
PRINT "사용 손실 마진: " + ROUND(used_loss,0) + " m/s".
PRINT "요구 Δv (마진 포함): " + ROUND(required_delta_v,0) + " m/s".

// MechJeb 총 Δv 읽기(가능하면 MJ 사용, 없으면 kOS SHIP:DELTAV 사용)
LOCAL total_mj_asl TO -1.
LOCAL total_mj_vac TO -1.
LOCAL kos_total_asl TO SHIP:DELTAV:ASL.
LOCAL kos_total_vac TO SHIP:DELTAV:VACUUM.

IF useMJ {
    // MechJeb 문서에 따르면 info:TOTALDVATM / info:TOTALDVVAC 존재 — reference_docs/KOS_DOC/kOS.MechJeb2.Addon-main/README.md (lines ~402-404)
    IF info:HASSUFFIX("TOTALDVATM") { SET total_mj_asl TO info:TOTALDVATM. }.
    IF info:HASSUFFIX("TOTALDVVAC") { SET total_mj_vac TO info:TOTALDVVAC. }.
}

PRINT "--- 총 Δv 비교 ---".
IF useMJ {
    // PRINT 내부의 inline IF 대신 문자열을 미리 준비
    LOCAL total_mj_asl_str TO "N/A".
    LOCAL total_mj_vac_str TO "N/A".
    IF total_mj_asl >= 0 { SET total_mj_asl_str TO ROUND(total_mj_asl,0). }.
    IF total_mj_vac >= 0 { SET total_mj_vac_str TO ROUND(total_mj_vac,0). }.
    PRINT "MechJeb 총 Δv (ASL): " + total_mj_asl_str + "   (Vac): " + total_mj_vac_str + ".".
} ELSE {
    PRINT "kOS 총 Δv (ASL): " + ROUND(kos_total_asl,0) + "   (Vac): " + ROUND(kos_total_vac,0) + ".".
}

// 실행 가능성 판단: MechJeb 기준 우선, 없으면 kOS 기준 사용
PRINT "--- 실행 가능성 판단 ---".
IF useMJ AND total_mj_asl >= 0 {
    IF total_mj_asl >= required_delta_v {
        PRINT "가능 (MechJeb ASL 총 Δv " + ROUND(total_mj_asl,0) + " m/s >= 요구 " + ROUND(required_delta_v,0) + " m/s) ✅".
    } ELSE {
        PRINT "불가능 (MechJeb ASL 총 Δv " + ROUND(total_mj_asl,0) + " m/s < 요구 " + ROUND(required_delta_v,0) + " m/s) ⚠️".
    }.
} ELSE {
    IF kos_total_asl >= required_delta_v {
        PRINT "가능 (kOS ASL 총 Δv " + ROUND(kos_total_asl,0) + " m/s >= 요구 " + ROUND(required_delta_v,0) + " m/s) ✅".
    } ELSE {
        PRINT "불가능 (kOS ASL 총 Δv " + ROUND(kos_total_asl,0) + " m/s < 요구 " + ROUND(required_delta_v,0) + " m/s) ⚠️".
    }.
}.

PRINT "dv.ks 완료.".
