from __future__ import annotations

import json

import pytest

from system.control_tower.backend import (
    Casadi1AxisOptimizer,
    OptimizationSolveError,
    build_optimization_request_from_parameter_export,
)
from system.control_tower.backend.contracts import load_golden_fixture, validate_contract_payload


def test_optimizer_solves_sample_request_into_valid_flight_plan() -> None:
    request = load_golden_fixture("optimization_request")
    optimizer = Casadi1AxisOptimizer()

    plan = optimizer.solve(request)

    validate_contract_payload("flight_plan", plan)
    assert plan["request_id"] == request["request_id"]
    assert plan["sample_count"] == request["grid_size"]
    assert len(plan["throttle_profile"]) == request["grid_size"]
    assert plan["altitude_profile_m"][0] == pytest.approx(request["initial_altitude_m"])
    assert plan["altitude_profile_m"][-1] >= request["target_altitude_m"] * 0.9
    assert min(plan["throttle_profile"]) >= request["min_throttle"] - 1e-6
    assert max(plan["throttle_profile"]) <= request["max_throttle"] + 1e-6

    roundtrip_payload = json.loads(json.dumps(plan))
    validate_contract_payload("flight_plan", roundtrip_payload)

    assert optimizer.last_diagnostics["status"] == "success"
    assert optimizer.last_diagnostics["code"] == "OK"


def test_optimizer_reports_diagnostics_for_infeasible_request() -> None:
    request = load_golden_fixture("optimization_request")
    request["available_thrust_kn"] = 0.05
    optimizer = Casadi1AxisOptimizer()

    with pytest.raises(OptimizationSolveError) as exc_info:
        optimizer.solve(request)

    diagnostics = exc_info.value.diagnostics
    assert diagnostics["status"] == "failed"
    assert diagnostics["code"] == "OPTIMIZER_INFEASIBLE"
    assert diagnostics["request_id"] == request["request_id"]
    assert diagnostics["max_net_acceleration_mps2"] < 0
    assert optimizer.last_diagnostics["code"] == "OPTIMIZER_INFEASIBLE"


def test_parameter_export_can_be_adapted_into_optimizer_request_and_solved() -> None:
    parameter_export = load_golden_fixture("parameter_export")
    request_defaults = load_golden_fixture("optimization_request")
    optimizer = Casadi1AxisOptimizer()

    request = build_optimization_request_from_parameter_export(
        parameter_export,
        defaults=request_defaults,
    )

    validate_contract_payload("optimization_request", request)
    assert request["source_export_id"] == parameter_export["export_id"]
    assert request["initial_mass_kg"] == parameter_export["mass_kg"]
    assert request["initial_altitude_m"] == parameter_export["altitude_m"]
    assert request["initial_vertical_speed_mps"] == parameter_export["vertical_speed_mps"]

    plan = optimizer.solve(request)

    validate_contract_payload("flight_plan", plan)
    assert plan["request_id"] == request["request_id"]