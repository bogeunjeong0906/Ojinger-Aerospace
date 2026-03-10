from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

JsonPrimitive = str | int | float | bool | None
JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
Validator = Callable[[Mapping[str, Any]], list[str]]

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
_UNSET = object()
_MISSION_LIFECYCLE_STATES = (
    "draft",
    "params_exported",
    "optimized",
    "armed",
    "active",
    "completed",
    "aborted",
)


class ContractValidationError(ValueError):
    """Raised when a payload does not satisfy a contract."""


@dataclass(frozen=True)
class FieldSpec:
    name: str
    json_types: tuple[str, ...]
    description: str
    required: bool = True
    item_json_types: tuple[str, ...] | None = None
    allowed_values: tuple[JsonPrimitive, ...] | None = None
    const: JsonValue | object = _UNSET

    def validate(self, value: Any) -> list[str]:
        errors: list[str] = []
        if not _matches_json_types(value, self.json_types, self.item_json_types):
            errors.append(
                f"field '{self.name}' must be {', '.join(self.json_types)}"
            )
            return errors

        if self.allowed_values is not None and value not in self.allowed_values:
            allowed = ", ".join(repr(item) for item in self.allowed_values)
            errors.append(f"field '{self.name}' must be one of: {allowed}")

        if self.const is not _UNSET and value != self.const:
            errors.append(f"field '{self.name}' must equal {self.const!r}")

        return errors


@dataclass(frozen=True)
class ContractSpec:
    name: str
    version: str
    description: str
    fixture_name: str
    required_fields: tuple[FieldSpec, ...]
    optional_fields: tuple[FieldSpec, ...] = ()
    extra_validators: tuple[Validator, ...] = field(default_factory=tuple)

    @property
    def all_fields(self) -> tuple[FieldSpec, ...]:
        return self.required_fields + self.optional_fields

    @property
    def required_field_names(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.required_fields)

    @property
    def optional_field_names(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.optional_fields)

    def validate(self, payload: Mapping[str, Any], *, allow_unknown: bool = False) -> None:
        errors: list[str] = []
        field_specs = {field.name: field for field in self.all_fields}

        for field_name in self.required_field_names:
            if field_name not in payload:
                errors.append(f"missing required field '{field_name}'")

        for field_name, value in payload.items():
            spec = field_specs.get(field_name)
            if spec is None:
                if not allow_unknown:
                    errors.append(f"unknown field '{field_name}'")
                continue
            errors.extend(spec.validate(value))

        if not errors:
            for validator in self.extra_validators:
                errors.extend(validator(payload))

        if errors:
            joined = "; ".join(errors)
            raise ContractValidationError(f"{self.name} contract invalid: {joined}")


def _matches_json_types(
    value: Any,
    json_types: Iterable[str],
    item_json_types: tuple[str, ...] | None,
) -> bool:
    return any(_matches_json_type(value, json_type, item_json_types) for json_type in json_types)


def _matches_json_type(
    value: Any,
    json_type: str,
    item_json_types: tuple[str, ...] | None,
) -> bool:
    if json_type == "string":
        return isinstance(value, str)
    if json_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if json_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if json_type == "boolean":
        return isinstance(value, bool)
    if json_type == "array":
        if not isinstance(value, list):
            return False
        if item_json_types is None:
            return True
        return all(_matches_json_types(item, item_json_types, None) for item in value)
    if json_type == "object":
        return isinstance(value, dict)
    if json_type == "null":
        return value is None
    return False


def _validate_non_negative(payload: Mapping[str, Any], fields: Iterable[str]) -> list[str]:
    errors: list[str] = []
    for field_name in fields:
        value = payload.get(field_name)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value < 0:
            errors.append(f"field '{field_name}' must be non-negative")
    return errors


def _validate_parameter_export(payload: Mapping[str, Any]) -> list[str]:
    errors = _validate_non_negative(
        payload,
        (
            "mass_kg",
            "dry_mass_kg",
            "fuel_mass_kg",
            "available_thrust_kn",
            "max_thrust_kn",
            "isp_vac_s",
            "isp_atm_s",
            "altitude_m",
            "surface_gravity_mps2",
        ),
    )
    mass = payload.get("mass_kg")
    dry_mass = payload.get("dry_mass_kg")
    fuel_mass = payload.get("fuel_mass_kg")
    if isinstance(mass, (int, float)) and isinstance(dry_mass, (int, float)) and dry_mass > mass:
        errors.append("field 'dry_mass_kg' must be less than or equal to 'mass_kg'")
    if isinstance(mass, (int, float)) and isinstance(fuel_mass, (int, float)) and fuel_mass > mass:
        errors.append("field 'fuel_mass_kg' must be less than or equal to 'mass_kg'")
    return errors


def _validate_optimization_request(payload: Mapping[str, Any]) -> list[str]:
    errors = _validate_non_negative(
        payload,
        (
            "initial_mass_kg",
            "initial_altitude_m",
            "target_altitude_m",
            "time_horizon_s",
            "weight_altitude",
            "weight_fuel",
            "weight_tracking",
        ),
    )
    min_throttle = payload.get("min_throttle")
    max_throttle = payload.get("max_throttle")
    if isinstance(min_throttle, (int, float)) and not 0 <= min_throttle <= 1:
        errors.append("field 'min_throttle' must be within [0, 1]")
    if isinstance(max_throttle, (int, float)) and not 0 <= max_throttle <= 1:
        errors.append("field 'max_throttle' must be within [0, 1]")
    if (
        isinstance(min_throttle, (int, float))
        and isinstance(max_throttle, (int, float))
        and min_throttle > max_throttle
    ):
        errors.append("field 'min_throttle' must be less than or equal to 'max_throttle'")
    grid_size = payload.get("grid_size")
    if isinstance(grid_size, int) and grid_size <= 0:
        errors.append("field 'grid_size' must be greater than zero")
    return errors


def _validate_flight_plan(payload: Mapping[str, Any]) -> list[str]:
    errors = _validate_non_negative(payload, ("duration_s", "sample_period_s", "control_kp", "control_ki", "control_kd"))
    sample_count = payload.get("sample_count")
    expected_fields = ("throttle_profile", "altitude_profile_m", "vertical_speed_profile_mps")
    if isinstance(sample_count, int):
        for field_name in expected_fields:
            value = payload.get(field_name)
            if isinstance(value, list) and len(value) != sample_count:
                errors.append(
                    f"field '{field_name}' length must equal 'sample_count' ({sample_count})"
                )
    return errors


def _validate_telemetry_snapshot(payload: Mapping[str, Any]) -> list[str]:
    errors = _validate_non_negative(
        payload,
        (
            "mission_elapsed_s",
            "altitude_m",
            "surface_speed_mps",
            "acceleration_mps2",
            "mass_kg",
            "fuel_mass_kg",
            "available_thrust_kn",
            "dynamic_pressure_pa",
            "g_force",
        ),
    )
    throttle_cmd = payload.get("throttle_cmd")
    if isinstance(throttle_cmd, (int, float)) and not 0 <= throttle_cmd <= 1:
        errors.append("field 'throttle_cmd' must be within [0, 1]")
    return errors


CONTRACTS: dict[str, ContractSpec] = {
    "parameter_export": ContractSpec(
        name="parameter_export",
        version="1.0.0",
        description="Scalar vehicle and environment export emitted by kOS WRITEJSON.",
        fixture_name="parameter_export.sample.json",
        required_fields=(
            FieldSpec("schema_name", ("string",), "Contract identifier.", const="parameter_export"),
            FieldSpec("schema_version", ("string",), "Contract version.", const="1.0.0"),
            FieldSpec("export_id", ("string",), "Unique export identifier."),
            FieldSpec("vessel_name", ("string",), "Active vessel name."),
            FieldSpec("body_name", ("string",), "Reference celestial body."),
            FieldSpec("situation", ("string",), "Flight situation label."),
            FieldSpec("ut", ("number",), "Universal time in seconds."),
            FieldSpec("mass_kg", ("number",), "Current vessel mass in kilograms."),
            FieldSpec("dry_mass_kg", ("number",), "Dry mass in kilograms."),
            FieldSpec("fuel_mass_kg", ("number",), "Propellant mass in kilograms."),
            FieldSpec("available_thrust_kn", ("number",), "Current available thrust in kilonewtons."),
            FieldSpec("max_thrust_kn", ("number",), "Maximum thrust in kilonewtons."),
            FieldSpec("isp_vac_s", ("number",), "Vacuum specific impulse in seconds."),
            FieldSpec("isp_atm_s", ("number",), "Sea-level specific impulse in seconds."),
            FieldSpec("altitude_m", ("number",), "Current altitude in meters."),
            FieldSpec("surface_gravity_mps2", ("number",), "Surface gravity in meters per second squared."),
        ),
        optional_fields=(
            FieldSpec("stage_index", ("integer",), "Current stage index.", required=False),
            FieldSpec("throttle_min", ("number",), "Minimum stable throttle command.", required=False),
            FieldSpec("throttle_max", ("number",), "Maximum throttle command.", required=False),
            FieldSpec("pressure_pa", ("number",), "Ambient pressure in pascals.", required=False),
            FieldSpec("temperature_k", ("number",), "Ambient temperature in kelvin.", required=False),
            FieldSpec("vertical_speed_mps", ("number",), "Current vertical speed in meters per second.", required=False),
            FieldSpec("reference_area_m2", ("number",), "Reference drag area in square meters.", required=False),
            FieldSpec("drag_coefficient", ("number",), "Drag coefficient proxy.", required=False),
            FieldSpec(
                "resource_summary",
                ("array",),
                "Flat per-resource summary emitted by the onboard exporter.",
                required=False,
                item_json_types=("object",),
            ),
            FieldSpec(
                "engine_summary",
                ("array",),
                "Flat per-engine summary emitted by the onboard exporter.",
                required=False,
                item_json_types=("object",),
            ),
            FieldSpec("note", ("string",), "Human-readable export note.", required=False),
        ),
        extra_validators=(_validate_parameter_export,),
    ),
    "optimization_request": ContractSpec(
        name="optimization_request",
        version="1.0.0",
        description="Flat solver input derived from exported parameters and mission targets.",
        fixture_name="optimization_request.sample.json",
        required_fields=(
            FieldSpec("schema_name", ("string",), "Contract identifier.", const="optimization_request"),
            FieldSpec("schema_version", ("string",), "Contract version.", const="1.0.0"),
            FieldSpec("request_id", ("string",), "Unique request identifier."),
            FieldSpec("source_export_id", ("string",), "Parameter export used as source."),
            FieldSpec("vessel_name", ("string",), "Target vessel name."),
            FieldSpec(
                "objective_mode",
                ("string",),
                "Optimization mode.",
                allowed_values=("min_fuel_to_altitude", "track_profile"),
            ),
            FieldSpec("initial_mass_kg", ("number",), "Initial mass in kilograms."),
            FieldSpec("initial_altitude_m", ("number",), "Initial altitude in meters."),
            FieldSpec("initial_vertical_speed_mps", ("number",), "Initial vertical speed in meters per second."),
            FieldSpec("target_altitude_m", ("number",), "Terminal target altitude in meters."),
            FieldSpec("target_vertical_speed_mps", ("number",), "Terminal target vertical speed in meters per second."),
            FieldSpec("gravity_mps2", ("number",), "Gravity model value."),
            FieldSpec("available_thrust_kn", ("number",), "Available thrust in kilonewtons."),
            FieldSpec("min_throttle", ("number",), "Minimum throttle command."),
            FieldSpec("max_throttle", ("number",), "Maximum throttle command."),
            FieldSpec("time_horizon_s", ("number",), "Optimization horizon in seconds."),
            FieldSpec("grid_size", ("integer",), "Number of solver grid samples."),
            FieldSpec("weight_altitude", ("number",), "Altitude tracking weight."),
            FieldSpec("weight_fuel", ("number",), "Fuel usage penalty weight."),
            FieldSpec("weight_tracking", ("number",), "Vertical-speed tracking weight."),
        ),
        optional_fields=(
            FieldSpec("max_dynamic_pressure_pa", ("number",), "Dynamic pressure soft limit.", required=False),
            FieldSpec("max_acceleration_mps2", ("number",), "Acceleration soft limit.", required=False),
            FieldSpec("drag_coefficient", ("number",), "Drag coefficient proxy.", required=False),
            FieldSpec("reference_area_m2", ("number",), "Reference drag area.", required=False),
            FieldSpec("atmosphere_scale_height_m", ("number",), "Exponential atmosphere scale height.", required=False),
            FieldSpec("solver_name", ("string",), "Requested optimizer backend.", required=False),
            FieldSpec("solver_max_iterations", ("integer",), "Maximum solver iterations.", required=False),
            FieldSpec("note", ("string",), "Human-readable request note.", required=False),
        ),
        extra_validators=(_validate_optimization_request,),
    ),
    "flight_plan": ContractSpec(
        name="flight_plan",
        version="1.0.0",
        description="Time-indexed ascent plan consumable by a kOS control loop.",
        fixture_name="flight_plan.sample.json",
        required_fields=(
            FieldSpec("schema_name", ("string",), "Contract identifier.", const="flight_plan"),
            FieldSpec("schema_version", ("string",), "Contract version.", const="1.0.0"),
            FieldSpec("plan_id", ("string",), "Unique plan identifier."),
            FieldSpec("request_id", ("string",), "Source optimization request identifier."),
            FieldSpec("vessel_name", ("string",), "Target vessel name."),
            FieldSpec("generated_at_utc", ("string",), "UTC timestamp for plan generation."),
            FieldSpec(
                "status",
                ("string",),
                "Lifecycle state for the plan.",
                allowed_values=_MISSION_LIFECYCLE_STATES,
            ),
            FieldSpec("start_ut", ("number",), "Planned universal-time start."),
            FieldSpec("duration_s", ("number",), "Planned duration in seconds."),
            FieldSpec("sample_period_s", ("number",), "Sampling period in seconds."),
            FieldSpec("sample_count", ("integer",), "Number of profile samples."),
            FieldSpec(
                "steering_mode",
                ("string",),
                "Attitude guidance mode.",
                allowed_values=("vertical_hold", "pitch_program"),
            ),
            FieldSpec("target_heading_deg", ("number",), "Heading setpoint in degrees."),
            FieldSpec("target_pitch_deg", ("number",), "Pitch setpoint in degrees."),
            FieldSpec("throttle_profile", ("array",), "Throttle samples.", item_json_types=("number",)),
            FieldSpec("altitude_profile_m", ("array",), "Altitude reference samples.", item_json_types=("number",)),
            FieldSpec(
                "vertical_speed_profile_mps",
                ("array",),
                "Vertical speed reference samples.",
                item_json_types=("number",),
            ),
            FieldSpec("control_kp", ("number",), "Proportional gain."),
            FieldSpec("control_ki", ("number",), "Integral gain."),
            FieldSpec("control_kd", ("number",), "Derivative gain."),
            FieldSpec("abort_min_twr", ("number",), "Abort threshold for TWR."),
            FieldSpec("abort_max_q_pa", ("number",), "Abort threshold for dynamic pressure."),
            FieldSpec("abort_max_tilt_deg", ("number",), "Abort threshold for tilt."),
        ),
        optional_fields=(
            FieldSpec("arm_mode", ("string",), "Arming policy.", required=False),
            FieldSpec("guidance_frame", ("string",), "Reference frame label.", required=False),
            FieldSpec("checksum", ("string",), "Payload checksum.", required=False),
            FieldSpec("note", ("string",), "Human-readable plan note.", required=False),
        ),
        extra_validators=(_validate_flight_plan,),
    ),
    "telemetry_snapshot": ContractSpec(
        name="telemetry_snapshot",
        version="1.0.0",
        description="Flat runtime snapshot for supervisory monitoring and logging.",
        fixture_name="telemetry_snapshot.sample.json",
        required_fields=(
            FieldSpec("schema_name", ("string",), "Contract identifier.", const="telemetry_snapshot"),
            FieldSpec("schema_version", ("string",), "Contract version.", const="1.0.0"),
            FieldSpec("snapshot_id", ("string",), "Unique snapshot identifier."),
            FieldSpec("plan_id", ("string",), "Active flight-plan identifier."),
            FieldSpec("vessel_name", ("string",), "Active vessel name."),
            FieldSpec(
                "status",
                ("string",),
                "Supervisor state.",
                allowed_values=_MISSION_LIFECYCLE_STATES,
            ),
            FieldSpec("ut", ("number",), "Universal time in seconds."),
            FieldSpec("mission_elapsed_s", ("number",), "Mission elapsed time in seconds."),
            FieldSpec("altitude_m", ("number",), "Current altitude in meters."),
            FieldSpec("vertical_speed_mps", ("number",), "Vertical speed in meters per second."),
            FieldSpec("surface_speed_mps", ("number",), "Surface speed in meters per second."),
            FieldSpec("acceleration_mps2", ("number",), "Acceleration magnitude in meters per second squared."),
            FieldSpec("mass_kg", ("number",), "Current mass in kilograms."),
            FieldSpec("fuel_mass_kg", ("number",), "Remaining propellant mass in kilograms."),
            FieldSpec("available_thrust_kn", ("number",), "Available thrust in kilonewtons."),
            FieldSpec("throttle_cmd", ("number",), "Last commanded throttle."),
            FieldSpec("pitch_deg", ("number",), "Pitch angle in degrees."),
            FieldSpec("heading_deg", ("number",), "Heading angle in degrees."),
            FieldSpec("dynamic_pressure_pa", ("number",), "Dynamic pressure in pascals."),
            FieldSpec("g_force", ("number",), "Current g-force."),
            FieldSpec("stage_index", ("integer",), "Current stage index."),
        ),
        optional_fields=(
            FieldSpec("apoapsis_altitude_m", ("number",), "Current apoapsis altitude.", required=False),
            FieldSpec("periapsis_altitude_m", ("number",), "Current periapsis altitude.", required=False),
            FieldSpec("guidance_error_m", ("number",), "Scalar tracking error metric.", required=False),
            FieldSpec("active_mode", ("string",), "Runtime controller mode.", required=False),
            FieldSpec("note", ("string",), "Human-readable telemetry note.", required=False),
        ),
        extra_validators=(_validate_telemetry_snapshot,),
    ),
}


def load_golden_fixture(contract_name: str) -> dict[str, JsonValue]:
    contract = CONTRACTS[contract_name]
    fixture_path = _FIXTURES_DIR / contract.fixture_name
    with fixture_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ContractValidationError(f"fixture '{fixture_path.name}' must contain a JSON object")
    return payload


def validate_contract_payload(contract_name: str, payload: Mapping[str, Any], *, allow_unknown: bool = False) -> None:
    CONTRACTS[contract_name].validate(payload, allow_unknown=allow_unknown)


def contract_manifest() -> dict[str, dict[str, Any]]:
    manifest: dict[str, dict[str, Any]] = {}
    for name, contract in CONTRACTS.items():
        manifest[name] = {
            "version": contract.version,
            "description": contract.description,
            "fixture_name": contract.fixture_name,
            "required_fields": list(contract.required_field_names),
            "optional_fields": list(contract.optional_field_names),
        }
    return manifest
