// export.ks: 로켓 조립 직후 실행, 주요 파라미터를 JSON으로 내보내는 부트파일
// KOS 문법 및 KOS_DOC 참조, 문법 무결성 최우선

// 0. 터미널 
CORE:PART:GETMODULE("kOSProcessor"):DOEVENT("Open Terminal").

// 1. 로켓 식별자
SET rocket_name TO SHIP:NAME.
SET rocket_info TO LEXICON().
SET rocket_info["name"] TO rocket_name.
SET rocket_info["vesselType"] TO SHIP:TYPE.
SET rocket_info["wetMass"] TO SHIP:WETMASS.
SET rocket_info["dryMass"] TO SHIP:DRYMASS.
SET rocket_info["stageNum"] TO SHIP:STAGENUM.
SET rocket_info["partCount"] TO SHIP:PARTS:LENGTH.
SET rocket_info["engineCount"] TO SHIP:ENGINES:LENGTH.

// 2. 천체 파라미터
SET ship_body TO SHIP:BODY.
SET body_info TO LEXICON().
SET atmosphere_exists TO ship_body:ATM:EXISTS.
SET launch_latitude TO SHIP:LATITUDE.
SET launch_longitude TO SHIP:LONGITUDE.
SET launch_altitude TO SHIP:ALTITUDE.
SET launch_terrain_height TO SHIP:GEOPOSITION:TERRAINHEIGHT.
SET local_g TO ship_body:MU / ((ship_body:RADIUS + launch_altitude) ^ 2).

SET body_info["name"] TO ship_body:NAME.
SET body_info["mass"] TO ship_body:MASS.
SET body_info["radius"] TO ship_body:RADIUS.
SET body_info["mu"] TO ship_body:MU.
SET body_info["hasOcean"] TO ship_body:HASOCEAN.
SET body_info["hasSolidSurface"] TO ship_body:HASSOLIDSURFACE.
SET body_info["rotationPeriod"] TO ship_body:ROTATIONPERIOD.
SET body_info["soiRadius"] TO ship_body:SOIRADIUS.
SET body_info["atmosphereExists"] TO atmosphere_exists.
SET body_info["launchLatitude"] TO launch_latitude.
SET body_info["launchLongitude"] TO launch_longitude.
SET body_info["launchAltitude"] TO launch_altitude.
SET body_info["launchTerrainHeight"] TO launch_terrain_height.
SET body_info["localGravity"] TO local_g.

// --- 고도별 대기압/온도 룩업테이블 생성 ---
SET atm_profile TO LIST().
SET atm_step TO 1000. // 1km 간격 (필요시 조정)
IF atmosphere_exists {
    SET atm_height TO ship_body:ATM:HEIGHT.
    SET body_info["atmHeight"] TO atm_height.
    SET body_info["atmMolarMass"] TO ship_body:ATM:MOLARMASS.
    SET body_info["atmAdiabaticIndex"] TO ship_body:ATM:ADIABATICINDEX.
    SET body_info["atmOxygen"] TO ship_body:ATM:OXYGEN.
    SET body_info["atmPressureSeaLevel"] TO ship_body:ATM:SEALEVELPRESSURE.
    SET body_info["launchPressure"] TO ship_body:ATM:ALTITUDEPRESSURE(launch_altitude).
    SET body_info["launchTemperature"] TO ship_body:ATM:ALTITUDETEMPERATURE(launch_altitude).

    SET atm_alt TO 0.
    UNTIL atm_alt >= atm_height {
        SET entry TO LEXICON().
        SET entry["alt"] TO atm_alt.
        SET entry["pressure"] TO ship_body:ATM:ALTITUDEPRESSURE(atm_alt).
        SET entry["temperature"] TO ship_body:ATM:ALTITUDETEMPERATURE(atm_alt).
        atm_profile:ADD(entry).
        SET atm_alt TO atm_alt + atm_step.
    }

    SET entry TO LEXICON().
    SET entry["alt"] TO atm_height.
    SET entry["pressure"] TO ship_body:ATM:ALTITUDEPRESSURE(atm_height).
    SET entry["temperature"] TO ship_body:ATM:ALTITUDETEMPERATURE(atm_height).
    atm_profile:ADD(entry).
} ELSE {
    SET body_info["atmHeight"] TO 0.
    SET body_info["atmMolarMass"] TO 0.
    SET body_info["atmAdiabaticIndex"] TO 0.
    SET body_info["atmOxygen"] TO FALSE.
    SET body_info["atmPressureSeaLevel"] TO 0.
    SET body_info["launchPressure"] TO 0.
    SET body_info["launchTemperature"] TO 0.
}
SET body_info["atmProfile"] TO atm_profile.

// 3. 스테이지별 부품/엔진/연료탱크/시뮬레이션 파라미터 수집
SET stages TO LIST().
SET stage_num TO SHIP:STAGENUM.
UNTIL stage_num < 0 {
    SET parts_list TO LIST().
    SET part_details TO LIST().
    SET engines_list TO LIST().
    SET tanks_list TO LIST().
    SET stage_resource_amounts TO LEXICON().
    SET stage_resource_capacities TO LEXICON().
    SET stage_resource_masses TO LEXICON().
    SET stage_resource_capacity_masses TO LEXICON().
    SET sim TO LEXICON().
    SET stage_current_mass TO 0.
    SET stage_dry_mass TO 0.
    SET stage_wet_mass TO 0.
    SET stage_max_thrust TO 0.
    SET stage_max_mass_flow TO 0.
    SET stage_max_fuel_flow TO 0.
    SET stage_vacuum_isp_weighted TO 0.
    SET stage_sea_isp_weighted TO 0.
    SET stage_fuel_mass TO 0.
    SET stage_oxidizer_mass TO 0.
    SET stage_engine_count TO 0.

    FOR p IN SHIP:PARTS {
        IF p:STAGE = stage_num {
            parts_list:ADD(p:NAME).
            SET stage_current_mass TO stage_current_mass + p:MASS.
            SET stage_dry_mass TO stage_dry_mass + p:DRYMASS.
            SET stage_wet_mass TO stage_wet_mass + p:WETMASS.

            SET part_obj TO LEXICON().
            SET part_obj["name"] TO p:NAME.
            SET part_obj["title"] TO p:TITLE.
            SET part_obj["uid"] TO p:UID.
            SET part_obj["tag"] TO p:TAG.
            SET part_obj["stage"] TO p:STAGE.
            SET part_obj["currentMass"] TO p:MASS.
            SET part_obj["dryMass"] TO p:DRYMASS.
            SET part_obj["wetMass"] TO p:WETMASS.
            SET part_obj["modules"] TO p:MODULES.
            part_details:ADD(part_obj).

            IF p:RESOURCES:LENGTH > 0 {
                SET tank TO LEXICON().
                SET tank["partName"] TO p:NAME.
                SET tank["partTitle"] TO p:TITLE.
                SET tank["partUid"] TO p:UID.
                SET tank["stage"] TO p:STAGE.
                SET tank["partMassCurrent"] TO p:MASS.
                SET tank["partMassDry"] TO p:DRYMASS.
                SET tank["partMassWet"] TO p:WETMASS.
                SET tank_resources TO LIST().

                FOR res IN p:RESOURCES {
                    SET resource_mass TO res:AMOUNT * res:DENSITY.
                    SET resource_capacity_mass TO res:CAPACITY * res:DENSITY.
                    SET resource_name TO res:NAME.

                    IF NOT stage_resource_amounts:HASKEY(resource_name) {
                        SET stage_resource_amounts[resource_name] TO 0.
                        SET stage_resource_capacities[resource_name] TO 0.
                        SET stage_resource_masses[resource_name] TO 0.
                        SET stage_resource_capacity_masses[resource_name] TO 0.
                    }

                    SET stage_resource_amounts[resource_name] TO stage_resource_amounts[resource_name] + res:AMOUNT.
                    SET stage_resource_capacities[resource_name] TO stage_resource_capacities[resource_name] + res:CAPACITY.
                    SET stage_resource_masses[resource_name] TO stage_resource_masses[resource_name] + resource_mass.
                    SET stage_resource_capacity_masses[resource_name] TO stage_resource_capacity_masses[resource_name] + resource_capacity_mass.

                    IF resource_name = "LiquidFuel" {
                        SET stage_fuel_mass TO stage_fuel_mass + resource_mass.
                    }
                    IF resource_name = "Oxidizer" {
                        SET stage_oxidizer_mass TO stage_oxidizer_mass + resource_mass.
                    }

                    SET tank_resource TO LEXICON().
                    SET tank_resource["name"] TO resource_name.
                    SET tank_resource["amount"] TO res:AMOUNT.
                    SET tank_resource["capacity"] TO res:CAPACITY.
                    SET tank_resource["density"] TO res:DENSITY.
                    SET tank_resource["mass"] TO resource_mass.
                    SET tank_resource["capacityMass"] TO resource_capacity_mass.
                    tank_resources:ADD(tank_resource).
                }

                SET tank["resources"] TO tank_resources.
                tanks_list:ADD(tank).
            }
        }
    }

    FOR eng IN SHIP:ENGINES {
        IF eng:STAGE = stage_num {
            SET propellant_mix TO LIST().
            FOR consumed_resource IN eng:CONSUMEDRESOURCES:VALUES {
                SET mix_entry TO LEXICON().
                SET mix_entry["name"] TO consumed_resource:NAME.
                SET mix_entry["ratio"] TO consumed_resource:RATIO.
                SET mix_entry["density"] TO consumed_resource:DENSITY.
                propellant_mix:ADD(mix_entry).
            }

            SET eng_obj TO LEXICON().
            SET eng_obj["name"] TO eng:NAME.
            SET eng_obj["title"] TO eng:TITLE.
            SET eng_obj["uid"] TO eng:UID.
            SET eng_obj["stage"] TO eng:STAGE.
            SET eng_obj["currentMass"] TO eng:MASS.
            SET eng_obj["dryMass"] TO eng:DRYMASS.
            SET eng_obj["wetMass"] TO eng:WETMASS.
            SET eng_obj["maxThrust"] TO eng:MAXTHRUST.
            SET eng_obj["vacuumIsp"] TO eng:VACUUMISP.
            SET eng_obj["seaLevelIsp"] TO eng:SEALEVELISP.
            SET eng_obj["maxMassFlow"] TO eng:MAXMASSFLOW.
            SET eng_obj["maxFuelFlow"] TO eng:MAXFUELFLOW.
            SET eng_obj["propellantMix"] TO propellant_mix.
            engines_list:ADD(eng_obj).

            SET stage_engine_count TO stage_engine_count + 1.
            SET stage_max_thrust TO stage_max_thrust + eng:MAXTHRUST.
            SET stage_max_mass_flow TO stage_max_mass_flow + eng:MAXMASSFLOW.
            SET stage_max_fuel_flow TO stage_max_fuel_flow + eng:MAXFUELFLOW.
            SET stage_vacuum_isp_weighted TO stage_vacuum_isp_weighted + (eng:MAXTHRUST * eng:VACUUMISP).
            SET stage_sea_isp_weighted TO stage_sea_isp_weighted + (eng:MAXTHRUST * eng:SEALEVELISP).
        }
    }

    IF stage_max_thrust > 0 {
        SET stage_vacuum_isp TO stage_vacuum_isp_weighted / stage_max_thrust.
        SET stage_sea_isp TO stage_sea_isp_weighted / stage_max_thrust.
    } ELSE {
        SET stage_vacuum_isp TO 0.
        SET stage_sea_isp TO 0.
    }

    IF stage_wet_mass > 0 AND local_g > 0 {
        SET stage_twr_wet TO stage_max_thrust / (stage_wet_mass * local_g).
    } ELSE {
        SET stage_twr_wet TO 0.
    }

    IF stage_current_mass > 0 AND local_g > 0 {
        SET stage_twr_current TO stage_max_thrust / (stage_current_mass * local_g).
    } ELSE {
        SET stage_twr_current TO 0.
    }

    SET sim["stage"] TO stage_num.
    SET sim["currentMass"] TO stage_current_mass.
    SET sim["dryMass"] TO stage_dry_mass.
    SET sim["wetMass"] TO stage_wet_mass.
    SET sim["engineCount"] TO stage_engine_count.
    SET sim["maxThrust"] TO stage_max_thrust.
    SET sim["maxMassFlow"] TO stage_max_mass_flow.
    SET sim["maxFuelFlow"] TO stage_max_fuel_flow.
    SET sim["vacuumIsp"] TO stage_vacuum_isp.
    SET sim["seaLevelIsp"] TO stage_sea_isp.
    SET sim["fuelMass"] TO stage_fuel_mass.
    SET sim["oxidizerMass"] TO stage_oxidizer_mass.
    SET sim["localGravity"] TO local_g.
    SET sim["twrSurfaceWet"] TO stage_twr_wet.
    SET sim["twrSurfaceCurrent"] TO stage_twr_current.
    SET sim["resourceAmounts"] TO stage_resource_amounts.
    SET sim["resourceCapacities"] TO stage_resource_capacities.
    SET sim["resourceMasses"] TO stage_resource_masses.
    SET sim["resourceCapacityMasses"] TO stage_resource_capacity_masses.

    SET stage_obj TO LEXICON().
    SET stage_obj["stage"] TO stage_num.
    SET stage_obj["parts"] TO parts_list.
    SET stage_obj["partDetails"] TO part_details.
    SET stage_obj["engines"] TO engines_list.
    SET stage_obj["tanks"] TO tanks_list.
    SET stage_obj["sim"] TO sim.
    stages:ADD(stage_obj).

    SET stage_num TO stage_num - 1.
}

// 4. 최종 JSON 객체 구성
SET export_obj TO LEXICON().
SET export_obj["rocket"] TO rocket_name.
SET export_obj["rocketInfo"] TO rocket_info.
SET export_obj["body"] TO body_info.
SET export_obj["stages"] TO stages.

// 5. JSON 파일로 내보내기 (Archive와 CPU 디스크 모두)
SET file_path_archive TO "0:/" + rocket_name + ".json".
SET file_path_local TO "1:/" + rocket_name + ".json". // 필요시 1:/을 실제 CPU 디스크 번호로 조정
// JSON 파일로 저장 (공식문서 WRITEJSON 사용)
WRITEJSON(export_obj, file_path_archive).
WRITEJSON(export_obj, file_path_local).
PRINT("[export.ks] Exported to " + file_path_archive + " and " + file_path_local).
