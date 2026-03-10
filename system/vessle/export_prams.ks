// export_prams.ks
//
// Practical onboard exporter for the T4 parameter export contract.
// Usage:
//   RUNPATH("export_prams.ks").
//   RUNPATH("export_prams.ks", "0:/exports/parameter_export.json").
//
// Notes:
// - JSON keys are lowercase for operator readability and Linux-safe file workflows.
// - The payload stays mostly flat, but includes simple list summaries for resources/engines.
// - Extra convenience fields such as vertical_speed_mps are included for downstream tooling.
// - All mass fields are exported in kilograms, even though kOS ship/resource masses are ton-based.

DECLARE PARAMETER export_path IS "parameter_export.json".

DECLARE FUNCTION ROUND3 {
	PARAMETER value.
	RETURN ROUND(value, 3).
}.

DECLARE FUNCTION LOWER_SAFE {
	PARAMETER value.
	RETURN (value + ""):TOLOWER().
}.

DECLARE FUNCTION BUILD_RESOURCE_SUMMARY {
	LOCAL resource_items IS LIST().

	FOR resource IN SHIP:RESOURCES {
		LOCAL item IS LEXICON().
		LOCAL fill_ratio IS 0.

		IF resource:CAPACITY > 0 {
			SET fill_ratio TO ROUND(resource:AMOUNT / resource:CAPACITY, 4).
		}.

		SET item["name"] TO LOWER_SAFE(resource:NAME).
		SET item["amount"] TO ROUND3(resource:AMOUNT).
		SET item["capacity"] TO ROUND3(resource:CAPACITY).
		SET item["fill_ratio"] TO fill_ratio.
		SET item["mass_kg"] TO ROUND3(resource:AMOUNT * resource:DENSITY * 1000).

		resource_items:ADD(item).
	}.

	RETURN resource_items.
}.

DECLARE FUNCTION BUILD_ENGINE_SUMMARY {
	LOCAL engine_items IS LIST().

	FOR eng IN SHIP:ENGINES {
		LOCAL item IS LEXICON().
		LOCAL engine_mode IS "single".

		IF eng:MULTIMODE {
			SET engine_mode TO LOWER_SAFE(eng:MODE).
		}.

		SET item["name"] TO LOWER_SAFE(eng:NAME).
		SET item["available_thrust_kn"] TO ROUND3(eng:AVAILABLETHRUST).
		SET item["max_thrust_kn"] TO ROUND3(eng:MAXTHRUST).
		SET item["vacuum_isp_s"] TO ROUND3(eng:VACUUMISP).
		SET item["sea_level_isp_s"] TO ROUND3(eng:SEALEVELISP).
		SET item["thrust_limit_pct"] TO ROUND3(eng:THRUSTLIMIT).
		SET item["ignition"] TO eng:IGNITION.
		SET item["flameout"] TO eng:FLAMEOUT.
		SET item["mode"] TO engine_mode.

		engine_items:ADD(item).
	}.

	RETURN engine_items.
}.

DECLARE FUNCTION BUILD_PAYLOAD {
	LOCAL body_ref IS SHIP:BODY.
	LOCAL altitude_m IS ROUND3(SHIP:ALTITUDE).
	LOCAL current_mass_kg IS ROUND3(SHIP:MASS * 1000).
	LOCAL dry_mass_kg IS ROUND3(SHIP:DRYMASS * 1000).
	LOCAL fuel_mass_kg IS ROUND3(MAX(0, (SHIP:MASS - SHIP:DRYMASS) * 1000)).
	LOCAL surface_gravity_mps2 IS ROUND((body_ref:MU / (body_ref:RADIUS ^ 2)), 6).
	LOCAL pressure_atm IS 0.
	LOCAL pressure_pa IS 0.
	LOCAL temperature_k IS 0.
	LOCAL total_isp_weight IS 0.
	LOCAL total_vac_isp_weighted IS 0.
	LOCAL total_sl_isp_weighted IS 0.
	LOCAL resources IS BUILD_RESOURCE_SUMMARY().
	LOCAL engines IS BUILD_ENGINE_SUMMARY().
	LOCAL payload_map IS LEXICON().

	IF body_ref:ATM:EXISTS {
		SET pressure_atm TO body_ref:ATM:ALTITUDEPRESSURE(altitude_m).
		SET pressure_pa TO ROUND3(pressure_atm * CONSTANT:AtmToKPa * 1000).
		SET temperature_k TO ROUND3(body_ref:ATM:ALTITUDETEMPERATURE(altitude_m)).
	}.

	FOR eng IN SHIP:ENGINES {
		LOCAL weight IS 0.

		IF eng:AVAILABLETHRUST > 0 {
			SET weight TO eng:AVAILABLETHRUST.
		} ELSE IF eng:MAXTHRUST > 0 {
			SET weight TO eng:MAXTHRUST.
		}.

		IF weight > 0 {
			SET total_isp_weight TO total_isp_weight + weight.
			SET total_vac_isp_weighted TO total_vac_isp_weighted + (eng:VACUUMISP * weight).
			SET total_sl_isp_weighted TO total_sl_isp_weighted + (eng:SEALEVELISP * weight).
		}.
	}.

	SET payload_map["schema_name"] TO "parameter_export".
	SET payload_map["schema_version"] TO "1.0.0".
	SET payload_map["export_id"] TO "pe-" + ROUND(TIME:SECONDS, 0) + "-s" + STAGE:NUMBER.
	SET payload_map["vessel_name"] TO LOWER_SAFE(SHIP:NAME).
	SET payload_map["body_name"] TO LOWER_SAFE(body_ref:NAME).
	SET payload_map["situation"] TO LOWER_SAFE(SHIP:STATUS).
	SET payload_map["ut"] TO ROUND3(TIME:SECONDS).
	SET payload_map["mass_kg"] TO current_mass_kg.
	SET payload_map["dry_mass_kg"] TO dry_mass_kg.
	SET payload_map["fuel_mass_kg"] TO fuel_mass_kg.
	SET payload_map["available_thrust_kn"] TO ROUND3(SHIP:AVAILABLETHRUST).
	SET payload_map["max_thrust_kn"] TO ROUND3(SHIP:MAXTHRUST).

	IF total_isp_weight > 0 {
		SET payload_map["isp_vac_s"] TO ROUND3(total_vac_isp_weighted / total_isp_weight).
		SET payload_map["isp_atm_s"] TO ROUND3(total_sl_isp_weighted / total_isp_weight).
	} ELSE {
		SET payload_map["isp_vac_s"] TO 0.
		SET payload_map["isp_atm_s"] TO 0.
	}.

	SET payload_map["altitude_m"] TO altitude_m.
	SET payload_map["surface_gravity_mps2"] TO surface_gravity_mps2.
	SET payload_map["stage_index"] TO STAGE:NUMBER.
	SET payload_map["pressure_pa"] TO pressure_pa.
	SET payload_map["temperature_k"] TO temperature_k.
	SET payload_map["vertical_speed_mps"] TO ROUND3(SHIP:VERTICALSPEED).
	SET payload_map["resource_summary"] TO resources.
	SET payload_map["engine_summary"] TO engines.
	SET payload_map["note"] TO "export_prams.ks scalar snapshot with simple engine/resource summaries".

	RETURN payload_map.
}.

PRINT "================================".
PRINT " ojinger parameter export start ".
PRINT "================================".
PRINT "target path     : " + export_path.
PRINT "vessel          : " + SHIP:NAME.
PRINT "body            : " + SHIP:BODY:NAME.
PRINT "gathering state...".

LOCAL payload IS BUILD_PAYLOAD().

PRINT "mass_kg         : " + payload["mass_kg"].
PRINT "available_thrust: " + payload["available_thrust_kn"] + " kN".
PRINT "altitude_m      : " + payload["altitude_m"].
PRINT "vertical_speed  : " + payload["vertical_speed_mps"] + " m/s".
PRINT "resources found : " + payload["resource_summary"]:LENGTH.
PRINT "engines found   : " + payload["engine_summary"]:LENGTH.
PRINT "writing json...".

WRITEJSON(payload, export_path).

PRINT "export complete.".
PRINT "saved to        : " + export_path.
PRINT "================================".
