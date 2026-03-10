from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping

import casadi as cs
import numpy as np

from .contracts import validate_contract_payload


def build_optimization_request_from_parameter_export(
    parameter_export: Mapping[str, Any],
    *,
    defaults: Mapping[str, Any] | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an optimizer request from an exporter-shaped parameter payload."""

    export_payload = dict(parameter_export)
    validate_contract_payload("parameter_export", export_payload)

    request = dict(defaults or {})
    request.update(overrides or {})

    export_id = str(export_payload["export_id"])
    request_id = str(request.get("request_id") or export_id.replace("pe-", "or-", 1))
    min_throttle = export_payload.get("throttle_min", request.get("min_throttle", 0.0))
    max_throttle = export_payload.get("throttle_max", request.get("max_throttle", 1.0))

    request.update(
        {
            "schema_name": "optimization_request",
            "schema_version": "1.0.0",
            "request_id": request_id,
            "source_export_id": export_id,
            "vessel_name": str(export_payload["vessel_name"]),
            "initial_mass_kg": float(export_payload["mass_kg"]),
            "initial_altitude_m": float(export_payload["altitude_m"]),
            "initial_vertical_speed_mps": float(export_payload.get("vertical_speed_mps", 0.0)),
            "gravity_mps2": float(export_payload["surface_gravity_mps2"]),
            "available_thrust_kn": float(export_payload["available_thrust_kn"]),
            "min_throttle": float(min_throttle),
            "max_throttle": float(max_throttle),
        }
    )

    optional_export_mappings = {
        "drag_coefficient": "drag_coefficient",
        "reference_area_m2": "reference_area_m2",
    }
    for export_field, request_field in optional_export_mappings.items():
        value = export_payload.get(export_field)
        if value is not None:
            request[request_field] = float(value)

    validate_contract_payload("optimization_request", request)
    return request


class OptimizationSolveError(RuntimeError):
    """Raised when the optimizer cannot produce a flight plan."""

    def __init__(self, message: str, *, diagnostics: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.diagnostics = dict(diagnostics or {})


@dataclass(slots=True)
class Casadi1AxisOptimizer:
    name: str = "casadi_1axis_optimizer"
    solver_name: str = "ipopt"
    _last_diagnostics: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    @property
    def last_diagnostics(self) -> dict[str, Any]:
        return dict(self._last_diagnostics)

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": "ready",
            "backend": "casadi",
            "solver": self.solver_name,
            "model": "vertical_1d",
            "contracts": {
                "input": "optimization_request",
                "output": "flight_plan",
            },
            "last_status": self._last_diagnostics.get("status", "idle"),
        }

    def solve(self, request: Mapping[str, Any]) -> dict[str, Any]:
        payload = dict(request)
        validate_contract_payload("optimization_request", payload)

        requested_solver = payload.get("solver_name")
        if requested_solver and str(requested_solver).lower() not in {"casadi", self.solver_name}:
            diagnostics = {
                "status": "failed",
                "code": "UNSUPPORTED_SOLVER",
                "request_id": payload.get("request_id"),
                "requested_solver": requested_solver,
                "supported_solvers": ["casadi", self.solver_name],
            }
            self._last_diagnostics = diagnostics
            raise OptimizationSolveError("unsupported solver requested", diagnostics=diagnostics)

        feasibility = self._basic_feasibility(payload)
        if feasibility is not None:
            self._last_diagnostics = feasibility
            raise OptimizationSolveError("request is physically infeasible for the simplified model", diagnostics=feasibility)

        plan = self._solve_opti(payload)
        validate_contract_payload("flight_plan", plan)
        return plan

    def _basic_feasibility(self, request: Mapping[str, Any]) -> dict[str, Any] | None:
        grid_size = int(request["grid_size"])
        if grid_size < 2:
            return {
                "status": "failed",
                "code": "INVALID_GRID",
                "request_id": request.get("request_id"),
                "grid_size": grid_size,
                "detail": "grid_size must be at least 2 for a trajectory solve",
            }

        mass_kg = float(request["initial_mass_kg"])
        gravity_mps2 = float(request["gravity_mps2"])
        thrust_n = float(request["available_thrust_kn"]) * 1000.0
        raw_thrust_acceleration = thrust_n / max(mass_kg, 1e-6)
        max_throttle = float(request["max_throttle"])
        max_net_acceleration = raw_thrust_acceleration * max_throttle - gravity_mps2

        climbing_target = (
            float(request["target_altitude_m"]) > float(request["initial_altitude_m"])
            or float(request["target_vertical_speed_mps"]) > float(request["initial_vertical_speed_mps"])
        )
        if climbing_target and max_net_acceleration <= 0:
            return {
                "status": "failed",
                "code": "OPTIMIZER_INFEASIBLE",
                "request_id": request.get("request_id"),
                "detail": "maximum available thrust cannot overcome gravity for an ascent",
                "raw_max_thrust_acceleration_mps2": raw_thrust_acceleration,
                "max_net_acceleration_mps2": max_net_acceleration,
                "initial_twr": raw_thrust_acceleration / max(gravity_mps2, 1e-6),
            }

        return None

    def _solve_opti(self, request: Mapping[str, Any]) -> dict[str, Any]:
        grid_size = int(request["grid_size"])
        duration_s = float(request["time_horizon_s"])
        sample_period_s = duration_s / float(grid_size - 1)

        initial_altitude_m = float(request["initial_altitude_m"])
        initial_vertical_speed_mps = float(request["initial_vertical_speed_mps"])
        target_altitude_m = float(request["target_altitude_m"])
        target_vertical_speed_mps = float(request["target_vertical_speed_mps"])
        mass_kg = float(request["initial_mass_kg"])
        gravity_mps2 = float(request["gravity_mps2"])
        min_throttle = float(request["min_throttle"])
        max_throttle = float(request["max_throttle"])

        raw_thrust_acceleration = float(request["available_thrust_kn"]) * 1000.0 / max(mass_kg, 1e-6)
        bounded_net_acceleration = float(request.get("max_acceleration_mps2") or max(20.0, gravity_mps2 * 3.5))
        bounded_thrust_acceleration = min(raw_thrust_acceleration, gravity_mps2 + bounded_net_acceleration)

        drag_coefficient = float(request.get("drag_coefficient") or 0.35)
        reference_area_m2 = float(request.get("reference_area_m2") or 0.08)
        scale_height_m = float(request.get("atmosphere_scale_height_m") or 5000.0)
        surface_density_kgpm3 = 1.225

        weight_altitude = float(request["weight_altitude"])
        weight_fuel = float(request["weight_fuel"])
        weight_tracking = float(request["weight_tracking"])
        max_dynamic_pressure_pa = request.get("max_dynamic_pressure_pa")

        opti = cs.Opti()
        altitude = opti.variable(grid_size)
        vertical_speed = opti.variable(grid_size)
        throttle = opti.variable(grid_size)

        opti.subject_to(altitude[0] == initial_altitude_m)
        opti.subject_to(vertical_speed[0] == initial_vertical_speed_mps)
        opti.subject_to(opti.bounded(min_throttle, throttle, max_throttle))
        opti.subject_to(altitude >= 0.0)
        opti.subject_to(vertical_speed >= -150.0)
        opti.subject_to(vertical_speed <= max(350.0, target_vertical_speed_mps + 200.0))

        dynamic_pressures: list[Any] = []
        accelerations: list[Any] = []
        for index in range(grid_size - 1):
            density = surface_density_kgpm3 * cs.exp(-altitude[index] / scale_height_m)
            drag_force = 0.5 * density * drag_coefficient * reference_area_m2 * vertical_speed[index] * cs.fabs(vertical_speed[index])
            drag_acceleration = drag_force / max(mass_kg, 1e-6)
            net_acceleration = throttle[index] * bounded_thrust_acceleration - gravity_mps2 - drag_acceleration

            dynamic_pressures.append(0.5 * density * vertical_speed[index] ** 2)
            accelerations.append(net_acceleration)

            opti.subject_to(altitude[index + 1] == altitude[index] + sample_period_s * vertical_speed[index])
            opti.subject_to(vertical_speed[index + 1] == vertical_speed[index] + sample_period_s * net_acceleration)

        final_altitude_error = altitude[-1] - target_altitude_m
        final_speed_error = vertical_speed[-1] - target_vertical_speed_mps
        throttle_smoothness = cs.sumsqr(throttle[1:] - throttle[:-1])
        fuel_proxy = sample_period_s * cs.sumsqr(throttle)

        objective = (
            weight_altitude * final_altitude_error ** 2
            + weight_tracking * final_speed_error ** 2
            + weight_fuel * fuel_proxy
            + 0.05 * throttle_smoothness
        )

        if max_dynamic_pressure_pa is not None:
            max_dynamic_pressure_value = float(max_dynamic_pressure_pa)
            q_penalty = sum(cs.fmax(0, q - max_dynamic_pressure_value) ** 2 for q in dynamic_pressures)
            objective += 1e-6 * q_penalty

        if accelerations:
            accel_penalty = sum(cs.fmax(0, acc - bounded_net_acceleration) ** 2 for acc in accelerations)
            objective += 0.1 * accel_penalty

        opti.minimize(objective)

        altitude_guess = np.linspace(initial_altitude_m, target_altitude_m, grid_size)
        speed_guess = np.linspace(initial_vertical_speed_mps, target_vertical_speed_mps, grid_size)
        average_required_acceleration = (target_vertical_speed_mps - initial_vertical_speed_mps) / max(duration_s, 1e-6)
        throttle_guess = np.clip(
            (gravity_mps2 + average_required_acceleration) / max(bounded_thrust_acceleration, 1e-6),
            min_throttle,
            max_throttle,
        )
        opti.set_initial(altitude, altitude_guess)
        opti.set_initial(vertical_speed, speed_guess)
        opti.set_initial(throttle, np.full(grid_size, throttle_guess))

        solver_iterations = int(request.get("solver_max_iterations") or 300)
        opti.solver(
            self.solver_name,
            {"expand": True, "print_time": False},
            {
                "max_iter": solver_iterations,
                "print_level": 0,
                "sb": "yes",
                "tol": 1e-6,
            },
        )

        try:
            solution = opti.solve()
        except RuntimeError as exc:
            diagnostics = self._solver_failure_diagnostics(
                opti=opti,
                request=request,
                error=exc,
                bounded_thrust_acceleration=bounded_thrust_acceleration,
                sample_period_s=sample_period_s,
            )
            self._last_diagnostics = diagnostics
            raise OptimizationSolveError("CasADi solver failed to converge", diagnostics=diagnostics) from exc

        throttle_profile = self._rounded_profile(solution.value(throttle), grid_size)
        altitude_profile = self._rounded_profile(solution.value(altitude), grid_size)
        vertical_speed_profile = self._rounded_profile(solution.value(vertical_speed), grid_size)

        diagnostics = {
            "status": "success",
            "code": "OK",
            "request_id": request.get("request_id"),
            "solver": self.solver_name,
            "objective_value": float(solution.value(objective)),
            "raw_max_thrust_acceleration_mps2": raw_thrust_acceleration,
            "bounded_thrust_acceleration_mps2": bounded_thrust_acceleration,
            "terminal_altitude_error_m": altitude_profile[-1] - target_altitude_m,
            "terminal_vertical_speed_error_mps": vertical_speed_profile[-1] - target_vertical_speed_mps,
            "iterations": self._extract_iteration_count(opti.stats()),
            "return_status": opti.stats().get("return_status"),
        }
        self._last_diagnostics = diagnostics

        plan = {
            "schema_name": "flight_plan",
            "schema_version": "1.0.0",
            "plan_id": self._plan_id(str(request["request_id"])),
            "request_id": str(request["request_id"]),
            "vessel_name": str(request["vessel_name"]),
            "generated_at_utc": self._utc_now(),
            "status": "draft",
            "start_ut": 0.0,
            "duration_s": float(duration_s),
            "sample_period_s": float(sample_period_s),
            "sample_count": int(grid_size),
            "steering_mode": "vertical_hold",
            "target_heading_deg": 90.0,
            "target_pitch_deg": 90.0,
            "throttle_profile": throttle_profile,
            "altitude_profile_m": altitude_profile,
            "vertical_speed_profile_mps": vertical_speed_profile,
            "control_kp": 0.9,
            "control_ki": 0.04,
            "control_kd": 0.18,
            "abort_min_twr": round(max(1.02, raw_thrust_acceleration / max(gravity_mps2, 1e-6) * 0.5), 6),
            "abort_max_q_pa": float(max_dynamic_pressure_pa) if max_dynamic_pressure_pa is not None else 35000.0,
            "abort_max_tilt_deg": 8.0,
            "arm_mode": "manual_confirm",
            "guidance_frame": "surface_vertical",
            "note": "Generated by simplified 1-axis CasADi ascent optimizer.",
        }
        plan["checksum"] = self._checksum(plan)
        return plan

    def _solver_failure_diagnostics(
        self,
        *,
        opti: cs.Opti,
        request: Mapping[str, Any],
        error: RuntimeError,
        bounded_thrust_acceleration: float,
        sample_period_s: float,
    ) -> dict[str, Any]:
        stats = dict(opti.stats()) if hasattr(opti, "stats") else {}
        diagnostics = {
            "status": "failed",
            "code": "OPTIMIZER_SOLVER_FAILURE",
            "request_id": request.get("request_id"),
            "solver": self.solver_name,
            "detail": str(error),
            "return_status": stats.get("return_status"),
            "iterations": self._extract_iteration_count(stats),
            "sample_period_s": sample_period_s,
            "bounded_thrust_acceleration_mps2": bounded_thrust_acceleration,
        }

        try:
            diagnostics["debug_objective_value"] = float(opti.debug.value(opti.f))
        except Exception:
            pass

        return diagnostics

    def _checksum(self, plan: Mapping[str, Any]) -> str:
        canonical = json.dumps(plan, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    def _extract_iteration_count(self, stats: Mapping[str, Any]) -> int | None:
        for key in ("iter_count", "iterations"):
            value = stats.get(key)
            if isinstance(value, int):
                return value
        return None

    def _plan_id(self, request_id: str) -> str:
        normalized = request_id.replace("or-", "", 1)
        return f"fp-{normalized}"

    def _rounded_profile(self, values: Any, expected_count: int) -> list[float]:
        array = np.asarray(values, dtype=float).reshape(-1)
        if array.size != expected_count:
            array = np.resize(array, expected_count)
        return [round(float(item), 6) for item in array.tolist()]

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")