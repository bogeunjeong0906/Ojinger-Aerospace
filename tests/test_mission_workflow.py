from __future__ import annotations

import json

from system.control_tower import run as control_tower_run
from system.control_tower.backend import MockTelemetryAdapter, RuntimeConfig, build_service_container
from system.control_tower.manager import ControlTowerApplication


def test_manager_workflow_runs_mock_cycle_and_writes_artifacts(tmp_path) -> None:
    config = RuntimeConfig.load(mode="headless")
    services = build_service_container(config)
    application = ControlTowerApplication(config, services=services)

    report = application.run_mock_mission_cycle(
        artifact_root=tmp_path,
        monitor_steps=6,
    )

    payload = report.to_dict()

    assert report.status == "ok"
    assert payload["summary"]["final_state"] == "completed"
    assert payload["summary"]["terminal_state_reached"] is True
    assert payload["summary"]["successful_terminal_state"] is True
    assert payload["summary"]["outcome"] == "ok"
    assert payload["summary"]["state_path"] == [
        "params_exported",
        "optimized",
        "armed",
        "active",
        "completed",
    ]
    assert payload["summary"]["contracts_validated"] == [
        {"contract": "parameter_export", "stage": "export", "status": "ok"},
        {"contract": "optimization_request", "stage": "optimize_request", "status": "ok"},
        {"contract": "flight_plan", "stage": "optimize_plan", "status": "ok"},
        {"contract": "flight_plan", "stage": "dispatch_plan", "status": "ok"},
    ]

    written_names = {artifact["name"] for artifact in payload["artifacts"]}
    assert written_names == {
        "parameter_export",
        "optimization_request",
        "flight_plan.optimized",
        "flight_plan.armed",
        "dispatch_record",
        "telemetry_history",
        "mission_cycle_report",
    }

    report_path = tmp_path / payload["mission_id"] / "mission_cycle_report.json"
    assert report_path.exists()
    disk_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert disk_payload["summary"]["final_state"] == "completed"
    assert disk_payload["transitions"][-1]["to_state"] == "completed"


def test_manager_workflow_marks_aborted_terminal_runs_as_aborted(tmp_path) -> None:
    config = RuntimeConfig.load(mode="headless")
    services = build_service_container(config)
    services.telemetry = MockTelemetryAdapter(
        samples=(
            {
                "snapshot_id": "ts-abort-0001",
                "status": "active",
                "ut": 25000.0,
                "mission_elapsed_s": 2.0,
                "altitude_m": 120.0,
                "vertical_speed_mps": 40.0,
                "surface_speed_mps": 42.0,
                "acceleration_mps2": 11.0,
                "mass_kg": 18000.0,
                "fuel_mass_kg": 5600.0,
                "available_thrust_kn": 420.0,
                "throttle_cmd": 0.8,
                "pitch_deg": 90.0,
                "heading_deg": 90.0,
                "dynamic_pressure_pa": 999999.0,
                "g_force": 1.3,
                "stage_index": 0,
            },
        ),
        loop=False,
    )
    services.telemetry.connect()
    application = ControlTowerApplication(config, services=services)

    report = application.run_mock_mission_cycle(
        artifact_root=tmp_path,
        monitor_steps=3,
    )

    payload = report.to_dict()

    assert report.status == "aborted"
    assert payload["summary"]["final_state"] == "aborted"
    assert payload["summary"]["terminal_state_reached"] is True
    assert payload["summary"]["successful_terminal_state"] is False
    assert payload["summary"]["outcome"] == "aborted"
    assert payload["errors"]
    assert payload["transitions"][-1]["to_state"] == "aborted"


def test_cli_mission_cycle_emits_json_and_artifacts(tmp_path, capsys) -> None:
    exit_code = control_tower_run(
        [
            "--action",
            "mission-cycle",
            "--mode",
            "headless",
            "--artifacts-dir",
            str(tmp_path),
            "--monitor-steps",
            "6",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["mode"] == "mission-cycle"
    assert payload["summary"]["final_state"] == "completed"
    assert payload["summary"]["successful_terminal_state"] is True
    assert (tmp_path / payload["mission_id"] / "telemetry_history.json").exists()


def test_cli_mission_cycle_returns_nonzero_for_incomplete_run(tmp_path, capsys) -> None:
    exit_code = control_tower_run(
        [
            "--action",
            "mission-cycle",
            "--mode",
            "headless",
            "--artifacts-dir",
            str(tmp_path),
            "--monitor-steps",
            "0",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 2
    assert payload["status"] == "incomplete"
    assert payload["summary"]["final_state"] == "armed"
    assert payload["summary"]["terminal_state_reached"] is False
    assert payload["summary"]["successful_terminal_state"] is False
    assert payload["errors"]
