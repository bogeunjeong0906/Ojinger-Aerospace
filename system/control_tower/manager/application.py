from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..backend import RuntimeConfig, ServiceContainer, build_service_container
from ..ui import create_ui_shell
from .workflow import MissionCycleReport, MissionWorkflow


@dataclass(slots=True)
class ApplicationReport:
    status: str
    mode: str
    summary: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "summary": self.summary,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


class ControlTowerApplication:
    def __init__(
        self,
        config: RuntimeConfig,
        services: ServiceContainer | None = None,
    ) -> None:
        self.config = config
        self.services = services or build_service_container(config)

    def boot(self) -> ApplicationReport:
        if self.config.mode == "ui":
            return self.run_ui()
        if self.config.mode == "auto":
            shell = create_ui_shell(self.config.app_name)
            if shell.is_available:
                return self.run_ui(shell=shell)
            report = self.run_headless()
            report.status = "degraded"
            report.mode = "auto"
            report.warnings.append(shell.describe()["detail"])
            return report
        return self.run_headless()

    def run_headless(self) -> ApplicationReport:
        warnings: list[str] = []
        telemetry_status = self.services.telemetry.describe().get("status")
        if telemetry_status == "mock":
            warnings.append("Live telemetry unavailable; running in mock telemetry mode.")
        elif telemetry_status != "connected":
            warnings.append("Live telemetry is not connected; running in scaffold/headless mode.")

        return ApplicationReport(
            status="ok",
            mode="headless",
            summary=self.services.boot_summary(),
            warnings=warnings,
        )

    def run_ui(self, shell: Any | None = None) -> ApplicationReport:
        resolved_shell = shell or create_ui_shell(self.config.app_name)
        if not resolved_shell.is_available:
            report = self.run_headless()
            report.status = "degraded"
            report.warnings.append(resolved_shell.describe()["detail"])
            return report

        summary = self.services.boot_summary()
        summary["ui"] = resolved_shell.describe()
        return ApplicationReport(
            status="ok",
            mode="ui",
            summary=summary,
            warnings=["UI shell is scaffolded; interactive views are deferred to later tasks."],
        )

    def run_mock_mission_cycle(
        self,
        *,
        artifact_root: str | Path | None = None,
        parameter_export: dict[str, Any] | str | Path | None = None,
        request_defaults: dict[str, Any] | str | Path | None = None,
        monitor_steps: int = 6,
    ) -> MissionCycleReport:
        workflow = MissionWorkflow(self.services)
        return workflow.run_mock_mission_cycle(
            artifact_root=artifact_root,
            parameter_export=parameter_export,
            request_defaults=request_defaults,
            monitor_steps=monitor_steps,
        )