// controler_1axis.ks
//
// Minimal onboard 1-axis ascent controller skeleton for T7.
// Usage:
//   RUNPATH("controler_1axis.ks").
//   RUNPATH("controler_1axis.ks", "0:/flight_plan.json").
//
// Notes:
// - This is a realistic kOS skeleton that consumes the shared flight_plan contract.
// - It intentionally stays simple/resource-aware: READJSON polling, explicit manual arm,
//   basic PIDLOOP throttle correction, optional steering hold, and conservative aborts.
// - It does NOT claim full live validation against every runtime/environment edge case.

DECLARE PARAMETER plan_path IS "flight_plan.json".
DECLARE PARAMETER log_path IS "controller_1axis.log".
DECLARE PARAMETER auto_arm IS FALSE.
DECLARE PARAMETER status_interval_s IS 2.

SET controller_state TO "idle".
SET active_plan TO LEXICON().
SET active_pid TO PIDLOOP(0.8, 0, 0).
SET throttle_cmd TO 0.
SET steering_is_locked TO FALSE.
SET target_heading_deg TO 90.
SET target_pitch_deg TO 90.
SET plan_started_ut TO 0.
SET control_wait_s TO 0.2.
SET arm_ready TO FALSE.
SET last_status_ut TO -999.
SET last_status_line TO "".
SET consumed_plan_id TO "".
SET consumed_plan_generated_at_utc TO "".
SET consumed_plan_signature TO "".

LOCK THROTTLE TO throttle_cmd.

DECLARE FUNCTION ROUND3 {
	PARAMETER value.
	RETURN ROUND(value, 3).
}.

DECLARE FUNCTION CLAMP {
	PARAMETER value.
	PARAMETER minimum.
	PARAMETER maximum.

	IF value < minimum {
		RETURN minimum.
	}.

	IF value > maximum {
		RETURN maximum.
	}.

	RETURN value.
}.

DECLARE FUNCTION PLAN_HAS {
	PARAMETER key_name.
	RETURN active_plan:HASKEY(key_name).
}.

DECLARE FUNCTION PLAN_NUMBER {
	PARAMETER key_name.
	PARAMETER fallback.

	IF PLAN_HAS(key_name) {
		RETURN active_plan[key_name].
	}.

	RETURN fallback.
}.

DECLARE FUNCTION PLAN_STRING {
	PARAMETER key_name.
	PARAMETER fallback.

	IF PLAN_HAS(key_name) {
		RETURN active_plan[key_name] + "".
	}.

	RETURN fallback + "".
}.

DECLARE FUNCTION SAMPLE_AT {
	PARAMETER values.
	PARAMETER index.
	PARAMETER fallback.

	IF values:LENGTH = 0 {
		RETURN fallback.
	}.

	IF index < 0 {
		RETURN values[0].
	}.

	IF index >= values:LENGTH {
		RETURN values[values:LENGTH - 1].
	}.

	RETURN values[index].
}.

DECLARE FUNCTION PLAN_MAP_STRING {
	PARAMETER plan_map.
	PARAMETER key_name.
	PARAMETER fallback.

	IF plan_map:HASKEY(key_name) {
		RETURN plan_map[key_name] + "".
	}.

	RETURN fallback + "".
}.

DECLARE FUNCTION PLAN_SIGNATURE_FOR {
	PARAMETER plan_map.
	RETURN PLAN_MAP_STRING(plan_map, "plan_id", "unknown")
		+ "|"
		+ PLAN_MAP_STRING(plan_map, "generated_at_utc", "na")
		+ "|"
		+ PLAN_MAP_STRING(plan_map, "checksum", "na").
}.

DECLARE FUNCTION MARK_PLAN_CONSUMED {
	PARAMETER plan_map.

	SET consumed_plan_id TO PLAN_MAP_STRING(plan_map, "plan_id", "").
	SET consumed_plan_generated_at_utc TO PLAN_MAP_STRING(plan_map, "generated_at_utc", "").
	SET consumed_plan_signature TO PLAN_SIGNATURE_FOR(plan_map).
}.

DECLARE FUNCTION PLAN_REUSE_REASON {
	PARAMETER plan_map.

	LOCAL incoming_signature IS PLAN_SIGNATURE_FOR(plan_map).
	LOCAL incoming_plan_id IS PLAN_MAP_STRING(plan_map, "plan_id", "").
	LOCAL incoming_generated_at_utc IS PLAN_MAP_STRING(plan_map, "generated_at_utc", "").

	IF consumed_plan_signature <> "" AND incoming_signature = consumed_plan_signature {
		RETURN "plan instance already consumed; deploy a fresh flight_plan.json before re-arming".
	}.

	IF consumed_plan_id <> "" AND incoming_plan_id = consumed_plan_id {
		IF incoming_generated_at_utc = "" OR incoming_generated_at_utc = consumed_plan_generated_at_utc {
			RETURN "plan_id already consumed; refresh plan_id/generated_at_utc before reusing this file".
		}.
	}.

	RETURN "".
}.

DECLARE FUNCTION REPORT_STATUS {
	PARAMETER message.
	PARAMETER force.

	LOCAL line IS "[ctrl-1axis][" + controller_state + "] " + message.

	IF force OR line <> last_status_line OR TIME:SECONDS - last_status_ut >= status_interval_s {
		PRINT line.
		LOG ROUND3(TIME:SECONDS) + " " + line TO log_path.
		SET last_status_line TO line.
		SET last_status_ut TO TIME:SECONDS.
	}.
}.

DECLARE FUNCTION CURRENT_G {
	LOCAL altitude_m IS MAX(0, SHIP:ALTITUDE).
	RETURN SHIP:BODY:MU / ((SHIP:BODY:RADIUS + altitude_m) ^ 2).
}.

DECLARE FUNCTION CURRENT_TWR {
	LOCAL g_now IS CURRENT_G().

	IF g_now <= 0 {
		RETURN 0.
	}.

	RETURN SHIP:AVAILABLETHRUST / (MAX(0.001, SHIP:MASS) * g_now).
}.

DECLARE FUNCTION CURRENT_TILT_DEG {
	RETURN VANG(SHIP:FACING:FOREVECTOR, UP:FOREVECTOR).
}.

DECLARE FUNCTION CURRENT_Q_PA {
	IF SHIP:HASSUFFIX("Q") {
		RETURN MAX(0, SHIP:Q).
	}.

	RETURN 0.
}.

DECLARE FUNCTION CLEAR_PLAN_STATE {
	SET active_plan TO LEXICON().
	SET arm_ready TO FALSE.
	SET plan_started_ut TO 0.
	SET control_wait_s TO 0.2.
}.

DECLARE FUNCTION ENTER_SAFE_IDLE {
	PARAMETER reason.

	SET throttle_cmd TO 0.
	SET controller_state TO "idle".

	IF steering_is_locked {
		UNLOCK STEERING.
		SET steering_is_locked TO FALSE.
	}.

	REPORT_STATUS(reason, TRUE).
}.

DECLARE FUNCTION LOAD_PLAN_IF_AVAILABLE {
	PARAMETER source_path.

	IF NOT EXISTS(source_path) {
		RETURN FALSE.
	}.

	LOCAL loaded_plan IS LEXICON(READJSON(source_path)).
	LOCAL required_keys IS LIST(
		"schema_name",
		"schema_version",
		"plan_id",
		"duration_s",
		"sample_period_s",
		"sample_count",
		"throttle_profile",
		"altitude_profile_m",
		"vertical_speed_profile_mps",
		"control_kp",
		"control_ki",
		"control_kd",
		"abort_min_twr",
		"abort_max_q_pa",
		"abort_max_tilt_deg"
	).

	FOR key_name IN required_keys {
		IF NOT loaded_plan:HASKEY(key_name) {
			REPORT_STATUS("plan rejected: missing key " + key_name, TRUE).
			RETURN FALSE.
		}.
	}.

	IF loaded_plan["schema_name"] <> "flight_plan" {
		REPORT_STATUS("plan rejected: schema_name != flight_plan", TRUE).
		RETURN FALSE.
	}.

	IF loaded_plan["schema_version"] <> "1.0.0" {
		REPORT_STATUS("plan rejected: schema_version != 1.0.0", TRUE).
		RETURN FALSE.
	}.

	IF loaded_plan:HASKEY("status") {
		LOCAL incoming_status IS loaded_plan["status"] + "".

		IF incoming_status = "completed" OR incoming_status = "aborted" {
			REPORT_STATUS("plan rejected: terminal-status plan file cannot be re-flown", TRUE).
			RETURN FALSE.
		}.
	}.

	IF loaded_plan:HASKEY("vessel_name") AND loaded_plan["vessel_name"] + "" <> SHIP:NAME + "" {
		REPORT_STATUS("plan rejected: vessel_name does not match active ship", TRUE).
		RETURN FALSE.
	}.

	LOCAL reuse_reason IS PLAN_REUSE_REASON(loaded_plan).
	IF reuse_reason <> "" {
		REPORT_STATUS("plan rejected: " + reuse_reason, TRUE).
		RETURN FALSE.
	}.

	IF loaded_plan["sample_count"] <= 0 {
		REPORT_STATUS("plan rejected: sample_count must be positive", TRUE).
		RETURN FALSE.
	}.

	IF loaded_plan["throttle_profile"]:LENGTH <> loaded_plan["sample_count"] {
		REPORT_STATUS("plan rejected: throttle profile length mismatch", TRUE).
		RETURN FALSE.
	}.

	IF loaded_plan["altitude_profile_m"]:LENGTH <> loaded_plan["sample_count"] {
		REPORT_STATUS("plan rejected: altitude profile length mismatch", TRUE).
		RETURN FALSE.
	}.

	IF loaded_plan["vertical_speed_profile_mps"]:LENGTH <> loaded_plan["sample_count"] {
		REPORT_STATUS("plan rejected: vertical speed profile length mismatch", TRUE).
		RETURN FALSE.
	}.

	SET active_plan TO loaded_plan.
	SET active_pid TO PIDLOOP(PLAN_NUMBER("control_kp", 0.8), PLAN_NUMBER("control_ki", 0), PLAN_NUMBER("control_kd", 0)).
	SET control_wait_s TO CLAMP(PLAN_NUMBER("sample_period_s", 0.5) / 2, 0.05, 0.25).
	SET arm_ready TO NOT AG1.
	SET controller_state TO "holding".

	REPORT_STATUS("plan loaded via READJSON: " + PLAN_STRING("plan_id", "unknown") + " / arm_mode=" + PLAN_STRING("arm_mode", "manual_confirm"), TRUE).
	RETURN TRUE.
}.

DECLARE FUNCTION APPLY_STEERING_TARGET {
	SET target_heading_deg TO PLAN_NUMBER("target_heading_deg", 90).

	IF PLAN_STRING("steering_mode", "vertical_hold") = "pitch_program" {
		SET target_pitch_deg TO CLAMP(PLAN_NUMBER("target_pitch_deg", 90), 0, 90).
	} ELSE {
		SET target_pitch_deg TO 90.
	}.

	IF NOT steering_is_locked {
		SAS OFF.
		LOCK STEERING TO HEADING(target_heading_deg, target_pitch_deg).
		SET steering_is_locked TO TRUE.
	}.
}.

DECLARE FUNCTION SHOULD_ARM_NOW {
	IF auto_arm {
		RETURN TRUE.
	}.

	IF PLAN_STRING("arm_mode", "manual_confirm") <> "manual_confirm" {
		RETURN TRUE.
	}.

	IF NOT arm_ready {
		IF NOT AG1 {
			SET arm_ready TO TRUE.
			REPORT_STATUS("manual arm ready: toggle AG1 ON to begin", TRUE).
		}.

		RETURN FALSE.
	}.

	RETURN AG1.
}.

DECLARE FUNCTION START_ACTIVE_CONTROL {
	SET controller_state TO "active".
	SET plan_started_ut TO TIME:SECONDS.
	SET active_pid:SETPOINT TO SAMPLE_AT(active_plan["vertical_speed_profile_mps"], 0, 0).
	SET throttle_cmd TO CLAMP(SAMPLE_AT(active_plan["throttle_profile"], 0, 0), 0, 1).
	APPLY_STEERING_TARGET().

	REPORT_STATUS("controller armed -> active; stage/liftoff remains operator-managed", TRUE).
}.

DECLARE FUNCTION CURRENT_ABORT_REASON {
	IF ABORT {
		RETURN "operator_abort_group".
	}.

	IF CURRENT_Q_PA() > PLAN_NUMBER("abort_max_q_pa", 999999) {
		RETURN "dynamic_pressure_limit_exceeded".
	}.

	IF CURRENT_TILT_DEG() > PLAN_NUMBER("abort_max_tilt_deg", 90) {
		RETURN "tilt_limit_exceeded".
	}.

	IF CURRENT_TWR() < PLAN_NUMBER("abort_min_twr", 0) {
		RETURN "twr_below_abort_threshold".
	}.

	IF SHIP:AVAILABLETHRUST <= 0 AND throttle_cmd > 0.05 {
		RETURN "no_available_thrust".
	}.

	RETURN "".
}.

DECLARE FUNCTION HANDLE_ABORT {
	PARAMETER reason.

	SET controller_state TO "aborted".
	SET throttle_cmd TO 0.
	MARK_PLAN_CONSUMED(active_plan).

	IF steering_is_locked {
		LOCK STEERING TO "kill".
	}.

	REPORT_STATUS("abort: " + reason, TRUE).
	WAIT 0.5.

	IF steering_is_locked {
		UNLOCK STEERING.
		SET steering_is_locked TO FALSE.
	}.

	CLEAR_PLAN_STATE().
	ENTER_SAFE_IDLE("abort handled; controller reset and waiting for next plan").
}.

DECLARE FUNCTION HANDLE_COMPLETE {
	SET controller_state TO "completed".
	SET throttle_cmd TO 0.
	MARK_PLAN_CONSUMED(active_plan).

	IF steering_is_locked {
		LOCK STEERING TO "kill".
	}.

	REPORT_STATUS("plan duration reached; returning to safe idle", TRUE).
	WAIT 0.5.

	IF steering_is_locked {
		UNLOCK STEERING.
		SET steering_is_locked TO FALSE.
	}.

	CLEAR_PLAN_STATE().
	ENTER_SAFE_IDLE("controller ready for next plan").
}.

DECLARE FUNCTION UPDATE_ACTIVE_CONTROL {
	LOCAL elapsed_s IS MAX(0, TIME:SECONDS - plan_started_ut).
	LOCAL sample_period_s IS MAX(PLAN_NUMBER("sample_period_s", 1), 0.1).
	LOCAL sample_index IS FLOOR(elapsed_s / sample_period_s).
	LOCAL ref_throttle IS SAMPLE_AT(active_plan["throttle_profile"], sample_index, 0).
	LOCAL ref_altitude_m IS SAMPLE_AT(active_plan["altitude_profile_m"], sample_index, SHIP:ALTITUDE).
	LOCAL ref_vertical_speed_mps IS SAMPLE_AT(active_plan["vertical_speed_profile_mps"], sample_index, SHIP:VERTICALSPEED).
	LOCAL altitude_error_m IS ref_altitude_m - SHIP:ALTITUDE.
	LOCAL vertical_speed_bias IS CLAMP(altitude_error_m * 0.02, -15, 15).
	LOCAL pid_delta IS 0.

	SET active_pid:SETPOINT TO ref_vertical_speed_mps + vertical_speed_bias.
	SET pid_delta TO active_pid:UPDATE(TIME:SECONDS, SHIP:VERTICALSPEED).
	SET throttle_cmd TO CLAMP(ref_throttle + pid_delta, 0, 1).

	IF PLAN_STRING("steering_mode", "vertical_hold") = "pitch_program" {
		SET target_pitch_deg TO CLAMP(PLAN_NUMBER("target_pitch_deg", 90), 0, 90).
	} ELSE {
		SET target_pitch_deg TO 90.
	}.

	REPORT_STATUS(
		"sample=" + sample_index
		+ " throttle=" + ROUND3(throttle_cmd)
		+ " vs=" + ROUND3(SHIP:VERTICALSPEED)
		+ " ref_vs=" + ROUND3(active_pid:SETPOINT)
		+ " alt=" + ROUND3(SHIP:ALTITUDE),
		FALSE
	).

	IF elapsed_s >= PLAN_NUMBER("duration_s", 0) {
		HANDLE_COMPLETE().
	}.
}.

PRINT "================================".
PRINT " ojinger 1-axis controller start ".
PRINT "================================".
PRINT "plan path       : " + plan_path.
PRINT "log path        : " + log_path.
PRINT "auto arm        : " + auto_arm.
PRINT "manual arm note : AG1 ON to arm, ABORT to cancel".
PRINT "validation note : contract-compatible skeleton only".

SAS OFF.
ENTER_SAFE_IDLE("boot complete; waiting for plan file").

UNTIL FALSE {
	IF controller_state = "idle" {
		IF EXISTS(plan_path) {
			LOAD_PLAN_IF_AVAILABLE(plan_path).
		} ELSE {
			REPORT_STATUS("idle: waiting for " + plan_path + " (deploy then RUNPATH)", FALSE).
			WAIT 0.5.
		}.
	} ELSE IF controller_state = "holding" {
		SET throttle_cmd TO 0.

		IF ABORT {
			REPORT_STATUS("holding: clear ABORT to continue", FALSE).
			WAIT 0.25.
		} ELSE IF SHOULD_ARM_NOW() {
			START_ACTIVE_CONTROL().
		} ELSE {
			REPORT_STATUS("holding: AG1 arms, ABORT cancels, throttle remains idle", FALSE).
			WAIT 0.25.
		}.
	} ELSE IF controller_state = "active" {
		LOCAL abort_reason IS CURRENT_ABORT_REASON().

		IF abort_reason <> "" {
			HANDLE_ABORT(abort_reason).
		} ELSE {
			UPDATE_ACTIVE_CONTROL().
			WAIT control_wait_s.
		}.
	} ELSE {
		ENTER_SAFE_IDLE("unexpected state recovered to idle").
		WAIT 0.5.
	}.
}.
