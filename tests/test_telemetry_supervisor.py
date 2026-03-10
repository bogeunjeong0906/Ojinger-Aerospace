from __future__ import annotations

from typing import Any

from system.control_tower.backend import KrpcTelemetryAdapter, MissionSupervisor, MockTelemetryAdapter
from system.control_tower.backend.contracts import load_golden_fixture, validate_contract_payload


def test_mock_adapter_normalizes_alias_fields_into_contract_snapshot() -> None:
    adapter = MockTelemetryAdapter(
        samples=(
            {
                "ut": 12000.0,
                "mission_elapsed": 3.5,
                "altitude": 125.0,
                "vertical_speed": 42.0,
                "surface_speed": 43.5,
                "acceleration": 12.4,
                "mass": 18000.0,
                "fuel_mass": 5800.0,
                "available_thrust": 420.0,
                "throttle": 0.74,
                "pitch": 89.5,
                "heading": 90.0,
                "dynamic_pressure": 8200.0,
                "g_force": 1.38,
                "stage": 1,
                "active_mode": "closed_loop",
            },
        ),
        loop=False,
    )

    snapshot = adapter.stream_snapshot(plan_id="fp-test-0001", vessel_name="ojinger-1", status="active")

    payload = snapshot.to_payload()
    validate_contract_payload("telemetry_snapshot", payload)
    assert payload["plan_id"] == "fp-test-0001"
    assert payload["vessel_name"] == "ojinger-1"
    assert payload["status"] == "active"
    assert payload["altitude_m"] == 125.0
    assert payload["throttle_cmd"] == 0.74
    assert payload["stage_index"] == 1


def test_supervisor_loop_tracks_active_then_aborted_state() -> None:
    flight_plan = load_golden_fixture("flight_plan")
    flight_plan["status"] = "optimized"
    flight_plan["abort_max_q_pa"] = 15000.0

    adapter = MockTelemetryAdapter(
        samples=(
            {
                "snapshot_id": "ts-seq-0001",
                "status": "armed",
                "ut": 20000.0,
                "mission_elapsed_s": 0.0,
                "altitude_m": 0.0,
                "vertical_speed_mps": 0.0,
                "surface_speed_mps": 0.0,
                "acceleration_mps2": 0.0,
                "mass_kg": 18000.0,
                "fuel_mass_kg": 5900.0,
                "available_thrust_kn": 420.0,
                "throttle_cmd": 0.0,
                "pitch_deg": 90.0,
                "heading_deg": 90.0,
                "dynamic_pressure_pa": 0.0,
                "g_force": 1.0,
                "stage_index": 0,
            },
            {
                "snapshot_id": "ts-seq-0002",
                "status": "active",
                "ut": 20003.0,
                "mission_elapsed_s": 3.0,
                "altitude_m": 160.0,
                "vertical_speed_mps": 55.0,
                "surface_speed_mps": 57.0,
                "acceleration_mps2": 13.0,
                "mass_kg": 17500.0,
                "fuel_mass_kg": 5400.0,
                "available_thrust_kn": 420.0,
                "throttle_cmd": 0.82,
                "pitch_deg": 89.2,
                "heading_deg": 90.0,
                "dynamic_pressure_pa": 12000.0,
                "g_force": 1.42,
                "stage_index": 0,
            },
            {
                "snapshot_id": "ts-seq-0003",
                "status": "active",
                "ut": 20006.0,
                "mission_elapsed_s": 6.0,
                "altitude_m": 400.0,
                "vertical_speed_mps": 70.0,
                "surface_speed_mps": 73.0,
                "acceleration_mps2": 14.0,
                "mass_kg": 17000.0,
                "fuel_mass_kg": 4900.0,
                "available_thrust_kn": 420.0,
                "throttle_cmd": 0.88,
                "pitch_deg": 89.0,
                "heading_deg": 90.0,
                "dynamic_pressure_pa": 18000.0,
                "g_force": 1.5,
                "stage_index": 0,
            },
        ),
        loop=False,
    )

    supervisor = MissionSupervisor(telemetry=adapter, flight_plan=flight_plan)
    records = supervisor.run_steps(steps=3, arm_if_needed=True, stop_on_terminal=True)

    assert [record.state for record in records] == ["armed", "active", "aborted"]
    assert records[-1].reason == "dynamic_pressure_limit_exceeded"
    assert records[-1].snapshot.status == "aborted"


def test_live_adapter_reports_unavailable_without_krpc_dependency() -> None:
    def missing_import(_: str) -> Any:
        raise ModuleNotFoundError("No module named 'krpc'")

    adapter = KrpcTelemetryAdapter(
        address="127.0.0.1",
        rpc_port=50000,
        stream_port=50001,
        import_resolver=missing_import,
    )

    assert adapter.connect() is False
    assert adapter.describe()["status"] == "unavailable"
