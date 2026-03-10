from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from ..backend import MissionSupervisor, ServiceContainer, build_optimization_request_from_parameter_export
from ..backend.contracts import load_golden_fixture, validate_contract_payload


_SUCCESS_TERMINAL_STATE = "completed"
_FAILURE_TERMINAL_STATE = "aborted"
_TERMINAL_STATES = {_SUCCESS_TERMINAL_STATE, _FAILURE_TERMINAL_STATE}


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    name: str
    path: str
    contract_name: str | None = None
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "path": self.path,
        }
        if self.contract_name is not None:
            payload["contract_name"] = self.contract_name
        if self.detail is not None:
            payload["detail"] = self.detail
        return payload


@dataclass(frozen=True, slots=True)
class MissionStateTransition:
    sequence: int
    phase: str
    from_state: str
    to_state: str
    reason: str
    at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "phase": self.phase,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "reason": self.reason,
            "at_utc": self.at_utc,
        }


@dataclass(slots=True)
class MissionCycleReport:
    status: str
    mode: str
    mission_id: str
    artifact_dir: str
    summary: dict[str, Any]
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    transitions: list[MissionStateTransition] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "mission_id": self.mission_id,
            "artifact_dir": self.artifact_dir,
            "summary": self.summary,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "transitions": [transition.to_dict() for transition in self.transitions],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


class MissionWorkflow:
    def __init__(self, services: ServiceContainer) -> None:
        self.services = services

    def run_mock_mission_cycle(
        self,
        *,
        artifact_root: str | Path | None = None,
        parameter_export: Mapping[str, Any] | str | Path | None = None,
        request_defaults: Mapping[str, Any] | str | Path | None = None,
        monitor_steps: int = 6,
    ) -> MissionCycleReport:
        warnings: list[str] = []
        validations: list[dict[str, Any]] = []
        artifacts: list[ArtifactRecord] = []
        transitions: list[MissionStateTransition] = []

        telemetry_description = self.services.telemetry.describe()
        if telemetry_description.get("status") == "mock":
            warnings.append("Mission cycle is running against mock telemetry samples.")
        elif telemetry_description.get("status") != "connected":
            warnings.append("Telemetry is not live-connected; dispatch remains abstracted.")

        export_payload = self._resolve_contract_payload(
            parameter_export,
            fallback_contract="parameter_export",
        )
        self._validate_contract(
            "parameter_export",
            export_payload,
            stage="export",
            validations=validations,
        )

        request_defaults_payload = self._resolve_contract_payload(
            request_defaults,
            fallback_contract="optimization_request",
        )
        request_payload = build_optimization_request_from_parameter_export(
            export_payload,
            defaults=request_defaults_payload,
        )
        self._validate_contract(
            "optimization_request",
            request_payload,
            stage="optimize_request",
            validations=validations,
        )

        optimized_plan = dict(self.services.optimizer.solve(request_payload))
        optimized_plan["status"] = "optimized"
        self._validate_contract(
            "flight_plan",
            optimized_plan,
            stage="optimize_plan",
            validations=validations,
        )

        mission_id = str(optimized_plan["plan_id"])
        artifact_dir = self._prepare_artifact_dir(artifact_root, mission_id)

        export_path = self._write_json_artifact(artifact_dir / "parameter_export.json", export_payload)
        artifacts.append(
            ArtifactRecord(
                name="parameter_export",
                path=str(export_path),
                contract_name="parameter_export",
            )
        )
        transitions.append(
            self._transition(
                sequence=len(transitions) + 1,
                phase="export",
                from_state="draft",
                to_state="params_exported",
                reason="parameter_export_validated",
            )
        )

        request_path = self._write_json_artifact(artifact_dir / "optimization_request.json", request_payload)
        artifacts.append(
            ArtifactRecord(
                name="optimization_request",
                path=str(request_path),
                contract_name="optimization_request",
            )
        )

        optimized_plan_path = self._write_json_artifact(
            artifact_dir / "flight_plan.optimized.json",
            optimized_plan,
        )
        artifacts.append(
            ArtifactRecord(
                name="flight_plan.optimized",
                path=str(optimized_plan_path),
                contract_name="flight_plan",
            )
        )
        transitions.append(
            self._transition(
                sequence=len(transitions) + 1,
                phase="optimize",
                from_state="params_exported",
                to_state="optimized",
                reason="flight_plan_generated",
            )
        )

        armed_plan = dict(optimized_plan)
        armed_plan["status"] = "armed"
        self._validate_contract(
            "flight_plan",
            armed_plan,
            stage="dispatch_plan",
            validations=validations,
        )
        armed_plan_path = self._write_json_artifact(
            artifact_dir / "flight_plan.armed.json",
            armed_plan,
        )
        artifacts.append(
            ArtifactRecord(
                name="flight_plan.armed",
                path=str(armed_plan_path),
                contract_name="flight_plan",
                detail="Abstract dispatch-ready plan; live file handoff is intentionally deferred.",
            )
        )

        dispatch_record = {
            "dispatch_id": f"dispatch-{mission_id}",
            "plan_id": mission_id,
            "request_id": request_payload["request_id"],
            "status": "armed",
            "dispatch_mode": "abstract_file_handoff",
            "source_plan_path": str(armed_plan_path),
            "target_hint": "kOS volume/file copy remains abstract until live path is verified.",
            "telemetry_adapter": telemetry_description.get("adapter"),
            "issued_at_utc": self._utc_now(),
            "note": "Headless/mock-first dispatch stub only; no live vessel upload performed.",
        }
        dispatch_path = self._write_json_artifact(artifact_dir / "dispatch_record.json", dispatch_record)
        artifacts.append(
            ArtifactRecord(
                name="dispatch_record",
                path=str(dispatch_path),
                detail="Abstract dispatch metadata for the armed plan handoff.",
            )
        )
        transitions.append(
            self._transition(
                sequence=len(transitions) + 1,
                phase="dispatch",
                from_state="optimized",
                to_state="armed",
                reason="abstract_dispatch_recorded",
            )
        )

        supervisor = MissionSupervisor(
            telemetry=self.services.telemetry,
            flight_plan=armed_plan,
        )
        monitor_records = supervisor.run_steps(
            max(monitor_steps, 0),
            arm_if_needed=True,
            stop_on_terminal=True,
        )
        monitor_history = [record.to_dict() for record in monitor_records]
        telemetry_log_path = self._write_json_artifact(
            artifact_dir / "telemetry_history.json",
            monitor_history,
        )
        artifacts.append(
            ArtifactRecord(
                name="telemetry_history",
                path=str(telemetry_log_path),
                detail="Supervisor polling history captured during the mock mission cycle.",
            )
        )

        previous_state = "armed"
        for record in monitor_records:
            if record.state == previous_state:
                continue
            transitions.append(
                self._transition(
                    sequence=len(transitions) + 1,
                    phase="monitor",
                    from_state=previous_state,
                    to_state=record.state,
                    reason=record.reason,
                )
            )
            previous_state = record.state

        final_state = supervisor.state
        status = self._mission_status_for_state(final_state)
        terminal_state_reached = final_state in _TERMINAL_STATES
        successful_terminal_state = final_state == _SUCCESS_TERMINAL_STATE
        errors = self._mission_errors_for_state(final_state)
        summary = {
            "mission_id": mission_id,
            "final_state": final_state,
            "terminal_state_reached": terminal_state_reached,
            "successful_terminal_state": successful_terminal_state,
            "outcome": status,
            "state_path": [transition.to_state for transition in transitions],
            "contracts_validated": validations,
            "artifacts_written": len(artifacts),
            "monitor_iterations": len(monitor_records),
            "telemetry": telemetry_description,
            "optimizer": self.services.optimizer.describe(),
            "optimizer_diagnostics": getattr(self.services.optimizer, "last_diagnostics", {}),
            "dispatch": dispatch_record,
            "monitor_history": monitor_history,
        }

        report = MissionCycleReport(
            status=status,
            mode="mission-cycle",
            mission_id=mission_id,
            artifact_dir=str(artifact_dir),
            summary=summary,
            artifacts=artifacts,
            transitions=transitions,
            warnings=warnings,
            errors=errors,
        )

        report_path = self._write_json_artifact(
            artifact_dir / "mission_cycle_report.json",
            report.to_dict(),
        )
        report.artifacts.append(
            ArtifactRecord(
                name="mission_cycle_report",
                path=str(report_path),
                detail="Top-level report for the headless mission workflow run.",
            )
        )
        report.summary["artifacts_written"] = len(report.artifacts)
        return report

    def _resolve_contract_payload(
        self,
        source: Mapping[str, Any] | str | Path | None,
        *,
        fallback_contract: str,
    ) -> dict[str, Any]:
        if source is None:
            return dict(load_golden_fixture(fallback_contract))
        if isinstance(source, Mapping):
            return dict(source)

        source_path = Path(source).expanduser().resolve()
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{source_path} must contain a JSON object")
        return payload

    def _validate_contract(
        self,
        contract_name: str,
        payload: Mapping[str, Any],
        *,
        stage: str,
        validations: list[dict[str, Any]],
    ) -> None:
        validate_contract_payload(contract_name, payload)
        validations.append(
            {
                "contract": contract_name,
                "stage": stage,
                "status": "ok",
            }
        )

    def _prepare_artifact_dir(self, artifact_root: str | Path | None, mission_id: str) -> Path:
        root = Path(artifact_root).expanduser().resolve() if artifact_root else (Path.cwd() / "artifacts" / "control_tower")
        artifact_dir = root / mission_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir

    def _write_json_artifact(self, path: Path, payload: Any) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def _mission_status_for_state(self, final_state: str) -> str:
        if final_state == _SUCCESS_TERMINAL_STATE:
            return "ok"
        if final_state == _FAILURE_TERMINAL_STATE:
            return "aborted"
        return "incomplete"

    def _mission_errors_for_state(self, final_state: str) -> list[str]:
        if final_state == _FAILURE_TERMINAL_STATE:
            return [
                "Mission cycle ended in aborted state; inspect telemetry_history and dispatch metadata before retrying.",
            ]
        if final_state != _SUCCESS_TERMINAL_STATE:
            return [
                "Mission cycle ended before reaching a successful terminal state; increase monitor_steps or verify dispatch/telemetry progress.",
            ]
        return []

    def _transition(
        self,
        *,
        sequence: int,
        phase: str,
        from_state: str,
        to_state: str,
        reason: str,
    ) -> MissionStateTransition:
        return MissionStateTransition(
            sequence=sequence,
            phase=phase,
            from_state=from_state,
            to_state=to_state,
            reason=reason,
            at_utc=self._utc_now(),
        )

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
