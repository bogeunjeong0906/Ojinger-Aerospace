from __future__ import annotations

import json

from system.control_tower import run as control_tower_run
from system.control_tower.backend import RuntimeConfig, build_service_container
from system.control_tower.manager import ControlTowerApplication
from system.control_tower.ui import UIShell
from system.control_tower.ui import create_ui_shell


def test_scaffold_modules_import_and_wire_without_optional_dependencies() -> None:
    config = RuntimeConfig.load(mode="headless")
    services = build_service_container(config)
    application = ControlTowerApplication(config, services=services)
    shell = create_ui_shell(config.app_name)

    assert application.boot().status in {"ok", "degraded"}
    assert services.optimizer.describe()["status"] == "ready"
    assert services.telemetry.describe()["status"] == "mock"
    assert services.supervisor.describe()["state"] == "draft"
    assert shell.describe()["backend"] == "dearpygui"


def test_headless_cli_boot_emits_json_report(capsys) -> None:
    exit_code = control_tower_run(["--mode", "headless", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["mode"] == "headless"
    assert "summary" in payload
    assert payload["summary"]["telemetry"]["status"] in {"mock", "connected", "connection_failed", "unavailable"}
    assert payload["summary"]["supervisor"]["state"] == "draft"


def test_auto_mode_boot_reports_degraded_when_ui_shell_is_unavailable(monkeypatch) -> None:
    config = RuntimeConfig.load(mode="auto")
    services = build_service_container(config)
    application = ControlTowerApplication(config, services=services)

    monkeypatch.setattr(
        "system.control_tower.manager.application.create_ui_shell",
        lambda app_name: UIShell(application_name=app_name, dependency_error="forced missing dearpygui"),
    )

    report = application.boot()

    assert report.status == "degraded"
    assert report.mode == "auto"
    assert "forced missing dearpygui" in report.warnings
    assert report.summary["telemetry"]["status"] == "mock"