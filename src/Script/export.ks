// export.ks: 로켓 조립 직후 실행, 주요 파라미터를 JSON으로 내보내는 부트파일
// KOS 문법 및 KOS_DOC 참조, 문법 무결성 최우선

// 0. 터미널 
CORE:PART:GETMODULE("kOSProcessor"):DOEVENT("Open Terminal").

// 1. 로켓 식별자
SET rocket_name TO SHIP:NAME.

// 2. 천체 파라미터
// body 정의 삭제, ship_body로 대체
SET ship_body TO SHIP:BODY.
SET body_info TO LEXICON().
SET body_info["name"] TO ship_body:NAME.
SET body_info["mass"] TO ship_body:MASS.
SET body_info["radius"] TO ship_body:RADIUS.
SET body_info["mu"] TO ship_body:MU.
SET body_info["atm"] TO ship_body:ATM.
SET body_info["atmHeight"] TO ship_body:ATM:HEIGHT.
SET body_info["atmMolarMass"] TO ship_body:ATM:MOLARMASS.
SET body_info["atmAdiabaticIndex"] TO ship_body:ATM:ADIABATICINDEX.

SET body_info["atmOxygen"] TO ship_body:ATM:OXYGEN.
// DensityASL은 공식 suffix가 없어 주석 처리 (필요시 직접 계산 필요)
SET body_info["atmPressureSeaLevel"] TO ship_body:ATM:SEALEVELPRESSURE.

// --- 고도별 대기압/온도 룩업테이블 생성 ---
SET atm_profile TO LIST().
SET atm_height TO ship_body:ATM:HEIGHT.
SET atm_step TO 1000. // 1km 간격 (필요시 조정)
FOR atm_alt IN RANGE(0, atm_height, atm_step) {
    SET entry TO LEXICON().
    SET entry["alt"] TO atm_alt.
    SET entry["pressure"] TO ship_body:ATM:ALTITUDEPRESSURE(atm_alt).
    SET entry["temperature"] TO ship_body:ATM:ALTITUDETEMPERATURE(atm_alt).
    atm_profile:ADD(entry).
}
// 마지막 고도(대기권 끝)도 추가
SET entry TO LEXICON().
SET entry["alt"] TO atm_height.
SET entry["pressure"] TO ship_body:ATM:ALTITUDEPRESSURE(atm_height).
SET entry["temperature"] TO ship_body:ATM:ALTITUDETEMPERATURE(atm_height).
atm_profile:ADD(entry).
SET body_info["atmProfile"] TO atm_profile.

// 3. 스테이지별 부품/엔진/연료탱크/시뮬레이션 파라미터 수집
SET stages TO LIST().
SET stage_count TO SHIP:stagenum.
SET g0 TO 9.81.
// prev_mass 변수 제거 (사용하지 않음)
FOR stage_num IN RANGE(0, stage_count-1) {
    SET parts_list TO LIST().
    SET engines_list TO LIST().
    SET tanks_list TO LIST().
    SET sim TO LEXICON().
    SET stage_mass TO 0.
    SET stage_thrust TO 0.
    SET stage_isp_sum TO 0.
    SET stage_isp_weight TO 0.
    SET fuel_capacity TO 0.
    SET fuel_amount TO 0.
    // 1. 파트 분류 및 합산
    FOR p IN SHIP:PARTS {
        IF p:STAGE = stage_num {
            parts_list:ADD(p:NAME).
            SET stage_mass TO stage_mass + p:MASS.
            // 엔진
            IF p:HASMODULE("ModuleEngines") {
                SET eng TO LEXICON().
                SET eng["name"] TO p:NAME.
                SET eng["thrust"] TO p:MAXTHRUST.
                SET eng["isp"] TO p:ISP.
                engines_list:ADD(eng).
                SET stage_thrust TO stage_thrust + p:MAXTHRUST.
                SET stage_isp_sum TO stage_isp_sum + (p:MAXTHRUST * p:ISP).
                SET stage_isp_weight TO stage_isp_weight + p:MAXTHRUST.
            }
            // 연료탱크
            IF p:HASMODULE("ModuleFuelTanks") {
                FOR res IN p:RESOURCES {
                    IF res:NAME = "LiquidFuel" {
                        SET tank TO LEXICON().
                        SET tank["name"] TO p:NAME.
                        SET tank["mass"] TO p:MASS.
                        SET tank["fuelType"] TO res:NAME.
                        SET tank["capacity"] TO res:MAX.
                        SET tank["amount"] TO res:AMOUNT.
                        tanks_list:ADD(tank).
                        SET fuel_capacity TO fuel_capacity + res:MAX.
                        SET fuel_amount TO fuel_amount + res:AMOUNT.
                    }
                }
            }
        }
    }
    // 2. 평균 ISP (추력 가중 평균)
    IF stage_isp_weight > 0 {
        SET stage_isp TO stage_isp_sum / stage_isp_weight.
    } ELSE {
        SET stage_isp TO 0.
    }
    // 3. 델타V 계산 (Tsiolkovsky 공식)
    SET m0 TO stage_mass.
    SET m1 TO stage_mass - fuel_amount.
    IF m1 <= 0 { SET m1 TO 0.01. } // 0 division 방지
    IF stage_isp > 0 AND m1 > 0 {
        SET deltav TO stage_isp * g0 * LN(m0 / m1).
    } ELSE {
        SET deltav TO 0.
    }
    // 4. 시뮬레이션 파라미터 저장
    SET sim["stage"] TO stage_num.
    SET sim["mass"] TO stage_mass.
    SET sim["fuel"] TO fuel_amount.
    SET sim["thrust"] TO stage_thrust.
    SET sim["isp"] TO stage_isp.
    SET sim["deltav"] TO deltav.
    SET sim["fuelCap"] TO fuel_capacity.
    // 5. 스테이지 객체 구성
    SET stage_obj TO LEXICON().
    SET stage_obj["stage"] TO stage_num.
    SET stage_obj["parts"] TO parts_list.
    SET stage_obj["engines"] TO engines_list.
    SET stage_obj["tanks"] TO tanks_list.
    SET stage_obj["sim"] TO sim.
    stages:ADD(stage_obj).
}

// 4. 최종 JSON 객체 구성
SET export_obj TO LEXICON().
SET export_obj["rocket"] TO rocket_name.
SET export_obj["body"] TO body_info.
SET export_obj["stages"] TO stages.

// 5. JSON 파일로 내보내기 (Archive와 CPU 디스크 모두)
SET file_path_archive TO "0:/" + rocket_name + ".json".
SET file_path_local TO "1:/" + rocket_name + ".json". // 필요시 1:/을 실제 CPU 디스크 번호로 조정
// JSON 파일로 저장 (공식문서 WRITEJSON 사용)
WRITEJSON(export_obj, file_path_archive).
WRITEJSON(export_obj, file_path_local).
PRINT("[export.ks] Exported to " + file_path_archive + " and " + file_path_local).
