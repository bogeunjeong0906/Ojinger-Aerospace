from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Callable, Mapping, Protocol

from .contracts import validate_contract_payload

_G0 = 9.80665
ImportResolver = Callable[[str], Any]


class TelemetryAdapter(Protocol):
    def connect(self) -> bool: ...

    def describe(self) -> dict[str, Any]: ...

    def stream_snapshot(
        self,
        *,
        plan_id: str | None = None,
        vessel_name: str | None = None,
        status: str | None = None,
    ) -> "TelemetrySnapshot": ...


@dataclass(frozen=True, slots=True)
class TelemetrySnapshot:
    schema_name: str
    schema_version: str
    snapshot_id: str
    plan_id: str
    vessel_name: str
    status: str
    ut: float
    mission_elapsed_s: float
    altitude_m: float
    vertical_speed_mps: float
    surface_speed_mps: float
    acceleration_mps2: float
    mass_kg: float
    fuel_mass_kg: float
    available_thrust_kn: float
    throttle_cmd: float
    pitch_deg: float
    heading_deg: float
    dynamic_pressure_pa: float
    g_force: float
    stage_index: int
    apoapsis_altitude_m: float | None = None
    periapsis_altitude_m: float | None = None
    guidance_error_m: float | None = None
    active_mode: str | None = None
    note: str | None = None

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        *,
        defaults: Mapping[str, Any] | None = None,
    ) -> "TelemetrySnapshot":
        normalized = normalize_telemetry_payload(payload, defaults=defaults)
        return cls(**normalized)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "plan_id": self.plan_id,
            "vessel_name": self.vessel_name,
            "status": self.status,
            "ut": self.ut,
            "mission_elapsed_s": self.mission_elapsed_s,
            "altitude_m": self.altitude_m,
            "vertical_speed_mps": self.vertical_speed_mps,
            "surface_speed_mps": self.surface_speed_mps,
            "acceleration_mps2": self.acceleration_mps2,
            "mass_kg": self.mass_kg,
            "fuel_mass_kg": self.fuel_mass_kg,
            "available_thrust_kn": self.available_thrust_kn,
            "throttle_cmd": self.throttle_cmd,
            "pitch_deg": self.pitch_deg,
            "heading_deg": self.heading_deg,
            "dynamic_pressure_pa": self.dynamic_pressure_pa,
            "g_force": self.g_force,
            "stage_index": self.stage_index,
        }
        optional_values = {
            "apoapsis_altitude_m": self.apoapsis_altitude_m,
            "periapsis_altitude_m": self.periapsis_altitude_m,
            "guidance_error_m": self.guidance_error_m,
            "active_mode": self.active_mode,
            "note": self.note,
        }
        for key, value in optional_values.items():
            if value is not None:
                payload[key] = value
        return payload

    def with_status(self, status: str, *, note: str | None = None) -> "TelemetrySnapshot":
        updated = replace(self, status=status, note=note if note is not None else self.note)
        validate_contract_payload("telemetry_snapshot", updated.to_payload())
        return updated


@dataclass(slots=True)
class MockTelemetryAdapter:
    samples: tuple[Mapping[str, Any], ...] = ()
    plan_id: str = "fp-mock-0001"
    vessel_name: str = "ojinger-1"
    loop: bool = True
    note: str = "mock telemetry stream"
    _status: str = field(default="idle", init=False)
    _detail: str = field(default="not connected", init=False)
    _cursor: int = field(default=0, init=False, repr=False)
    _emitted_count: int = field(default=0, init=False, repr=False)
    _last_snapshot: TelemetrySnapshot | None = field(default=None, init=False, repr=False)

    def connect(self) -> bool:
        self._status = "mock"
        self._detail = self.note
        return True

    def describe(self) -> dict[str, Any]:
        return {
            "adapter": "mock",
            "status": self._status,
            "detail": self._detail,
            "emitted_count": self._emitted_count,
            "last_snapshot_id": self._last_snapshot.snapshot_id if self._last_snapshot else None,
        }

    def stream_snapshot(
        self,
        *,
        plan_id: str | None = None,
        vessel_name: str | None = None,
        status: str | None = None,
    ) -> TelemetrySnapshot:
        if self._status == "idle":
            self.connect()

        sample_set = self.samples or _default_mock_samples()
        index = min(self._cursor, len(sample_set) - 1)
        raw_sample = dict(sample_set[index])
        if self.loop:
            self._cursor = (self._cursor + 1) % len(sample_set)
        else:
            self._cursor = min(self._cursor + 1, len(sample_set) - 1)

        snapshot = TelemetrySnapshot.from_mapping(
            raw_sample,
            defaults={
                "plan_id": plan_id or self.plan_id,
                "vessel_name": vessel_name or self.vessel_name,
                "status": status or "draft",
                "note": self.note,
            },
        )
        self._emitted_count += 1
        self._last_snapshot = snapshot
        return snapshot

    def snapshot(self) -> dict[str, Any]:
        return self.stream_snapshot().to_payload()


@dataclass(slots=True)
class NullTelemetryAdapter:
    reason: str

    def connect(self) -> bool:
        return False

    def describe(self) -> dict[str, Any]:
        return {
            "adapter": "null",
            "status": "offline",
            "reason": self.reason,
        }

    def stream_snapshot(
        self,
        *,
        plan_id: str | None = None,
        vessel_name: str | None = None,
        status: str | None = None,
    ) -> TelemetrySnapshot:
        raise RuntimeError(self.reason)

    def snapshot(self) -> dict[str, Any]:
        return {
            "status": "offline",
            "reason": self.reason,
        }


@dataclass(slots=True)
class KrpcTelemetryAdapter:
    address: str
    rpc_port: int
    stream_port: int
    plan_id: str = "fp-live-0001"
    vessel_name: str = "active-vessel"
    import_resolver: ImportResolver = import_module
    _client: Any | None = field(default=None, init=False, repr=False)
    _status: str = field(default="idle", init=False)
    _detail: str = field(default="not connected", init=False)
    _emitted_count: int = field(default=0, init=False, repr=False)
    _last_snapshot: TelemetrySnapshot | None = field(default=None, init=False, repr=False)

    def connect(self) -> bool:
        try:
            krpc = self.import_resolver("krpc")
        except (ImportError, ModuleNotFoundError) as exc:
            self._status = "unavailable"
            self._detail = str(exc)
            return False

        try:
            self._client = krpc.connect(
                name="ojinger-control-tower",
                address=self.address,
                rpc_port=self.rpc_port,
                stream_port=self.stream_port,
            )
        except Exception as exc:  # pragma: no cover - network availability is environment-specific
            self._status = "connection_failed"
            self._detail = str(exc)
            return False

        self._status = "connected"
        self._detail = f"connected to {self.address}:{self.rpc_port}/{self.stream_port}"
        return True

    def describe(self) -> dict[str, Any]:
        return {
            "adapter": "krpc",
            "status": self._status,
            "detail": self._detail,
            "endpoint": {
                "address": self.address,
                "rpc_port": self.rpc_port,
                "stream_port": self.stream_port,
            },
            "emitted_count": self._emitted_count,
            "last_snapshot_id": self._last_snapshot.snapshot_id if self._last_snapshot else None,
        }

    def stream_snapshot(
        self,
        *,
        plan_id: str | None = None,
        vessel_name: str | None = None,
        status: str | None = None,
    ) -> TelemetrySnapshot:
        if self._client is None:
            raise RuntimeError("kRPC client is not connected")

        payload = self._read_live_payload(
            plan_id=plan_id or self.plan_id,
            vessel_name=vessel_name or self.vessel_name,
            status=status or "active",
        )
        snapshot = TelemetrySnapshot.from_mapping(payload)
        self._emitted_count += 1
        self._last_snapshot = snapshot
        return snapshot

    def snapshot(self) -> dict[str, Any]:
        return self.stream_snapshot().to_payload()

    def _read_live_payload(self, *, plan_id: str, vessel_name: str, status: str) -> dict[str, Any]:
        assert self._client is not None
        space_center = getattr(self._client, "space_center", None)
        vessel = getattr(space_center, "active_vessel", None)
        if vessel is None:
            raise RuntimeError("kRPC active vessel is unavailable")

        flight = _resolve_flight(vessel)
        control = getattr(vessel, "control", None)
        orbit = getattr(vessel, "orbit", None)

        mass_kg = _coerce_float(getattr(vessel, "mass", 0.0))
        dry_mass_kg = _coerce_float(getattr(vessel, "dry_mass", mass_kg), default=mass_kg)
        fuel_mass_kg = max(mass_kg - dry_mass_kg, 0.0)
        g_force = _coerce_float(getattr(flight, "g_force", 0.0))
        pitch_deg = _coerce_float(getattr(flight, "pitch", 90.0), default=90.0)
        heading_deg = _coerce_float(getattr(flight, "heading", 90.0), default=90.0)
        dynamic_pressure_pa = _coerce_float(getattr(flight, "dynamic_pressure", 0.0))
        vertical_speed_mps = _coerce_float(getattr(flight, "vertical_speed", 0.0))
        surface_speed_mps = _coerce_float(
            getattr(flight, "speed", getattr(flight, "horizontal_speed", 0.0)),
        )

        return normalize_telemetry_payload(
            {
                "plan_id": plan_id,
                "vessel_name": str(getattr(vessel, "name", vessel_name)),
                "status": status,
                "ut": _coerce_float(getattr(space_center, "ut", 0.0)),
                "mission_elapsed_s": _coerce_float(getattr(vessel, "met", 0.0)),
                "altitude_m": _coerce_float(getattr(flight, "mean_altitude", getattr(flight, "surface_altitude", 0.0))),
                "vertical_speed_mps": vertical_speed_mps,
                "surface_speed_mps": surface_speed_mps,
                "acceleration_mps2": g_force * _G0,
                "mass_kg": mass_kg,
                "fuel_mass_kg": fuel_mass_kg,
                "available_thrust_kn": _coerce_float(getattr(vessel, "available_thrust", 0.0)) / 1000.0,
                "throttle_cmd": _coerce_float(getattr(control, "throttle", 0.0)),
                "pitch_deg": pitch_deg,
                "heading_deg": heading_deg,
                "dynamic_pressure_pa": dynamic_pressure_pa,
                "g_force": g_force,
                "stage_index": _coerce_int(getattr(control, "current_stage", 0)),
                "apoapsis_altitude_m": _optional_float(getattr(orbit, "apoapsis_altitude", None)),
                "periapsis_altitude_m": _optional_float(getattr(orbit, "periapsis_altitude", None)),
                "active_mode": "live_krpc",
                "note": self._detail,
            }
        )


def normalize_telemetry_payload(
    payload: Mapping[str, Any],
    *,
    defaults: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    merged = dict(defaults or {})
    merged.update(payload)

    normalized: dict[str, Any] = {
        "schema_name": "telemetry_snapshot",
        "schema_version": "1.0.0",
        "snapshot_id": _coerce_str(_alias(merged, "snapshot_id", "id"), default=_next_snapshot_id()),
        "plan_id": _coerce_str(_alias(merged, "plan_id", "flight_plan_id"), default="fp-unknown"),
        "vessel_name": _coerce_str(_alias(merged, "vessel_name", "vessel"), default="unknown-vessel"),
        "status": _coerce_str(_alias(merged, "status", "state"), default="draft"),
        "ut": _coerce_float(_alias(merged, "ut", "time", "universal_time")),
        "mission_elapsed_s": _coerce_float(_alias(merged, "mission_elapsed_s", "mission_elapsed", "met")),
        "altitude_m": _coerce_float(_alias(merged, "altitude_m", "altitude", "mean_altitude")),
        "vertical_speed_mps": _coerce_float(_alias(merged, "vertical_speed_mps", "vertical_speed", "vertical_speed_ms")),
        "surface_speed_mps": _coerce_float(
            _alias(merged, "surface_speed_mps", "surface_speed", "speed"),
            default=abs(_coerce_float(_alias(merged, "vertical_speed_mps", "vertical_speed", "vertical_speed_ms"))),
        ),
        "acceleration_mps2": _coerce_float(_alias(merged, "acceleration_mps2", "acceleration", "acceleration_ms2")),
        "mass_kg": _coerce_float(_alias(merged, "mass_kg", "mass")),
        "fuel_mass_kg": _coerce_float(_alias(merged, "fuel_mass_kg", "fuel_mass", "propellant_mass_kg")),
        "available_thrust_kn": _coerce_float(_alias(merged, "available_thrust_kn", "available_thrust", "thrust_kn")),
        "throttle_cmd": _coerce_float(_alias(merged, "throttle_cmd", "throttle", "throttle_command")),
        "pitch_deg": _coerce_float(_alias(merged, "pitch_deg", "pitch"), default=90.0),
        "heading_deg": _coerce_float(_alias(merged, "heading_deg", "heading"), default=90.0),
        "dynamic_pressure_pa": _coerce_float(_alias(merged, "dynamic_pressure_pa", "dynamic_pressure", "q")),
        "g_force": _coerce_float(_alias(merged, "g_force", "gee_force", "g")),
        "stage_index": _coerce_int(_alias(merged, "stage_index", "stage")),
    }

    optional_values = {
        "apoapsis_altitude_m": _optional_float(_alias(merged, "apoapsis_altitude_m", "apoapsis_altitude")),
        "periapsis_altitude_m": _optional_float(_alias(merged, "periapsis_altitude_m", "periapsis_altitude")),
        "guidance_error_m": _optional_float(_alias(merged, "guidance_error_m", "guidance_error")),
        "active_mode": _optional_str(_alias(merged, "active_mode", "mode")),
        "note": _optional_str(merged.get("note")),
    }
    for key, value in optional_values.items():
        if value is not None:
            normalized[key] = value

    validate_contract_payload("telemetry_snapshot", normalized)
    return normalized


def _default_mock_samples() -> tuple[dict[str, Any], ...]:
    return (
        {
            "snapshot_id": "ts-mock-0001",
            "status": "armed",
            "ut": 10000.0,
            "mission_elapsed_s": 0.0,
            "altitude": 0.0,
            "vertical_speed": 0.0,
            "surface_speed": 0.0,
            "acceleration": 0.0,
            "mass": 18500.0,
            "fuel_mass": 6200.0,
            "available_thrust": 420.0,
            "throttle": 0.0,
            "pitch": 90.0,
            "heading": 90.0,
            "dynamic_pressure": 0.0,
            "g_force": 1.0,
            "stage": 0,
            "active_mode": "awaiting_arm",
        },
        {
            "snapshot_id": "ts-mock-0002",
            "status": "active",
            "ut": 10005.0,
            "mission_elapsed_s": 5.0,
            "altitude": 250.0,
            "vertical_speed": 58.0,
            "surface_speed": 60.0,
            "acceleration": 14.2,
            "mass": 17200.0,
            "fuel_mass": 5100.0,
            "available_thrust": 420.0,
            "throttle": 0.82,
            "pitch": 90.0,
            "heading": 90.0,
            "dynamic_pressure": 8500.0,
            "g_force": 1.45,
            "stage": 0,
            "active_mode": "closed_loop",
        },
        {
            "snapshot_id": "ts-mock-0003",
            "status": "completed",
            "ut": 10018.0,
            "mission_elapsed_s": 18.0,
            "altitude": 1350.0,
            "vertical_speed": 0.2,
            "surface_speed": 0.4,
            "acceleration": 0.4,
            "mass": 15800.0,
            "fuel_mass": 3700.0,
            "available_thrust": 410.0,
            "throttle": 0.0,
            "pitch": 90.0,
            "heading": 90.0,
            "dynamic_pressure": 100.0,
            "g_force": 1.0,
            "stage": 0,
            "active_mode": "coast",
        },
    )


def _resolve_flight(vessel: Any) -> Any:
    flight_fn = getattr(vessel, "flight", None)
    if not callable(flight_fn):
        return vessel
    try:
        reference_frame = getattr(vessel, "surface_reference_frame")
        return flight_fn(reference_frame)
    except Exception:
        return flight_fn()


def _alias(payload: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in payload:
            return payload[name]
    return None


def _coerce_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def _coerce_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default


def _coerce_str(value: Any, *, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return _coerce_float(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _next_snapshot_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"ts-{timestamp}"
