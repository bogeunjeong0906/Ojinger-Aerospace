// export.ks: 로켓 조립 직후 실행, 주요 파라미터를 JSON으로 내보내는 부트파일
// KOS 문법 및 KOS_DOC 참조, 문법 무결성 최우선

// 1. 로켓 식별자
SET rocket_name TO SHIP:NAME.

// 2. 천체 파라미터
SET body TO SHIP:BODY.
SET body_info TO LEXICON().
SET body_info["name"] TO body:NAME.
SET body_info["mass"] TO body:MASS.
SET body_info["radius"] TO body:RADIUS.
SET body_info["mu"] TO body:MU.
SET body_info["atm"] TO body:ATM.
SET body_info["atmDensitySeaLevel"] TO body:ATM:DensityASL.
SET body_info["atmPressureSeaLevel"] TO body:ATM:PressureASL.

// 3. 스테이지별 부품/엔진/연료탱크/시뮬레이션 파라미터 수집
SET stages TO LIST().
SET stage_count TO SHIP:STAGE:STAGES.
FOR stage_num IN RANGE(0, stage_count-1) {
    SET parts_list TO LIST().
    SET engines_list TO LIST().
    SET tanks_list TO LIST().
    SET sim_list TO LIST().
    FOR p IN SHIP:PARTS {
        IF p:STAGE = stage_num {
            // 부품
            parts_list:ADD(p:NAME).
            // 엔진
            IF p:HASMODULE("ModuleEngines") {
                SET eng TO LEXICON().
                SET eng["name"] TO p:NAME.
                SET eng["thrust"] TO p:MAXTHRUST.
                SET eng["isp"] TO p:ISP.
                SET eng["fuelFlow"] TO p:ENGINE:FUELFLOW.
                engines_list:ADD(eng).
            }
            // 연료탱크
            IF p:HASRESOURCE("LiquidFuel") OR p:HASRESOURCE("Oxidizer") {
                SET tank TO LEXICON().
                SET tank["name"] TO p:NAME.
                SET tank["mass"] TO p:MASS.
                IF p:HASRESOURCE("LiquidFuel") {
                    SET tank["fuelType"] TO "LiquidFuel".
                    SET tank["capacity"] TO p:RESOURCES["LiquidFuel"]:MAX.
                    SET tank["amount"] TO p:RESOURCES["LiquidFuel"]:AMOUNT.
                } ELSE {
                    SET tank["fuelType"] TO "Oxidizer".
                    SET tank["capacity"] TO p:RESOURCES["Oxidizer"]:MAX.
                    SET tank["amount"] TO p:RESOURCES["Oxidizer"]:AMOUNT.
                }
                tanks_list:ADD(tank).
            }
        }
    }
    // 시뮬레이션 파라미터(예시: 질량, 연료량, 추력, TWR, ISP, 연소시간)
    SET sim TO LEXICON().
    SET sim["stage"] TO stage_num.
    SET sim["mass"] TO SHIP:MASS.
    SET sim["fuel"] TO SHIP:RESOURCES["LiquidFuel"].
    SET sim["thrust"] TO SHIP:MAXTHRUST.
    SET sim["twr"] TO SHIP:MAXTHRUST / (SHIP:MASS * body:MU / (body:RADIUS^2)).
    SET sim["isp"] TO SHIP:ISP.
    IF SHIP:MAXTHRUST > 0 AND SHIP:ISP > 0 {
        SET sim["burntime"] TO SHIP:RESOURCES["LiquidFuel"] / (SHIP:MAXTHRUST / (9.81 * SHIP:ISP)).
    } ELSE {
        SET sim["burntime"] TO 0.
    }
    sim_list:ADD(sim).
    // 스테이지 객체 구성
    SET stage_obj TO LEXICON().
    SET stage_obj["stage"] TO stage_num.
    SET stage_obj["parts"] TO parts_list.
    SET stage_obj["engines"] TO engines_list.
    SET stage_obj["tanks"] TO tanks_list.
    SET stage_obj["sim"] TO sim_list.
    stages:ADD(stage_obj).
}

// 4. 최종 JSON 객체 구성
SET export_obj TO LEXICON().
SET export_obj["rocket"] TO rocket_name.
SET export_obj["body"] TO body_info.
SET export_obj["stages"] TO stages.

// 5. JSON 파일로 내보내기 (KOS Volume 0)
SET file_path TO "/0/" + rocket_name + ".json".
SET f TO OPEN(file_path, "w").
// JSON 문자열로 변환 (간단화, 실제로는 더 복잡한 조립 필요)
CLEARSCREEN.
f:WRITE(export_obj:TOJSON).
f:CLOSE().
PRINT("[export.ks] Exported to " + file_path).
