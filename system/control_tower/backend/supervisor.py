from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from .contracts import validate_contract_payload
from .telemetry import TelemetrySnapshot

_SUPPORTED_STATES = {
    "draft",
    "params_exported",
    "optimized",
    "armed",
    "active",
    "completed",
    "aborted",
}
_PRELAUNCH_STATES = {"draft", "params_exported", "optimized"}
_TERMINAL_STATES = {"completed", "aborted"}


class TelemetryStream(Protocol):
    def describe(self) -> dict[str, Any]: ...

    def stream_snapshot(
        self,
        *,
        plan_id: str | None = None,
        vessel_name: str | None = None,
        status: str | None = None,
    ) -> TelemetrySnapshot: ...


@dataclass(slots=True)
class SupervisorRecord:
    iteration: int
    state: str
    reason: str
    snapshot: TelemetrySnapshot

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "state": self.state,
            "reason": self.reason,
            "snapshot": self.snapshot.to_payload(),
        }


@dataclass(slots=True)
class MissionSupervisor:
    telemetry: TelemetryStream
    flight_plan: Mapping[str, Any] | None = None
    gravity_mps2: float = 9.81
    state: str = "draft"
    history: list[SupervisorRecord] = field(default_factory=list)
    _last_snapshot: TelemetrySnapshot | None = field(default=None, init=False, repr=False)
    _last_reason: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.flight_plan is not None:
            validate_contract_payload("flight_plan", self.flight_plan)
            plan_state = str(self.flight_plan.get("status") or self.state)
            if plan_state in _SUPPORTED_STATES:
                self.state = plan_state

    @property
    def plan_id(self) -> str:
        if self.flight_plan is None:
            return "fp-unknown"
        return str(self.flight_plan.get("plan_id") or "fp-unknown")

    @property
    def vessel_name(self) -> str:
        if self.flight_plan is None:
            return "unknown-vessel"
        return str(self.flight_plan.get("vessel_name") or "unknown-vessel")

    def arm(self) -> str:
        if self.state in _PRELAUNCH_STATES:
            self.state = "armed"
            self._last_reason = "armed_for_monitoring"
        return self.state

    def poll_once(self) -> SupervisorRecord:
        snapshot = self.telemetry.stream_snapshot(
            plan_id=self.plan_id,
            vessel_name=self.vessel_name,
            status=self.state,
        )
        next_state, reason = self._resolve_transition(snapshot)
        if snapshot.status != next_state or (reason and snapshot.note != reason):
            snapshot = snapshot.with_status(next_state, note=reason)

        record = SupervisorRecord(
            iteration=len(self.history) + 1,
            state=next_state,
            reason=reason,
            snapshot=snapshot,
        )
        self.history.append(record)
        self.state = next_state
        self._last_snapshot = snapshot
        self._last_reason = reason
        return record

    def run_steps(
        self,
        steps: int,
        *,
        arm_if_needed: bool = False,
        stop_on_terminal: bool = True,
    ) -> list[SupervisorRecord]:
        if arm_if_needed and self.state in _PRELAUNCH_STATES:
            self.arm()

        records: list[SupervisorRecord] = []
        for _ in range(max(steps, 0)):
            if stop_on_terminal and self.state in _TERMINAL_STATES:
                break
            records.append(self.poll_once())
        return records

    def describe(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "plan_id": self.plan_id,
            "vessel_name": self.vessel_name,
            "history_length": len(self.history),
            "last_reason": self._last_reason,
            "last_snapshot_id": self._last_snapshot.snapshot_id if self._last_snapshot else None,
            "telemetry": self.telemetry.describe(),
        }

    def _resolve_transition(self, snapshot: TelemetrySnapshot) -> tuple[str, str]:
        if self.state in _TERMINAL_STATES:
            return self.state, "terminal_state"

        if snapshot.status in _TERMINAL_STATES:
            return snapshot.status, f"adapter_reported_{snapshot.status}"

        abort_reason = self._abort_reason(snapshot)
        if abort_reason is not None:
            return "aborted", abort_reason

        if snapshot.status in _SUPPORTED_STATES and snapshot.status != self.state:
            if snapshot.status in {"params_exported", "optimized", "armed", "active"}:
                return snapshot.status, f"adapter_reported_{snapshot.status}"

        if self.state in _PRELAUNCH_STATES:
            reasons = {
                "draft": "awaiting_param_export",
                "params_exported": "awaiting_optimization",
                "optimized": "awaiting_arm",
            }
            return self.state, reasons[self.state]

        if self.state == "armed":
            if snapshot.status == "active":
                return "active", "adapter_reported_active"
            if snapshot.mission_elapsed_s > 0 or snapshot.throttle_cmd > 0.05:
                return "active", "vehicle_motion_detected"
            return "armed", "awaiting_liftoff"

        if self.state == "active" and self._is_complete(snapshot):
            return "completed", "profile_complete"

        return self.state, "monitoring"

    def _abort_reason(self, snapshot: TelemetrySnapshot) -> str | None:
        if self.flight_plan is None:
            return None

        abort_max_q_pa = self.flight_plan.get("abort_max_q_pa")
        if isinstance(abort_max_q_pa, (int, float)) and snapshot.dynamic_pressure_pa > float(abort_max_q_pa):
            return "dynamic_pressure_limit_exceeded"

        abort_max_tilt_deg = self.flight_plan.get("abort_max_tilt_deg")
        if isinstance(abort_max_tilt_deg, (int, float)):
            tilt_deg = abs(90.0 - snapshot.pitch_deg)
            if tilt_deg > float(abort_max_tilt_deg):
                return "tilt_limit_exceeded"

        abort_min_twr = self.flight_plan.get("abort_min_twr")
        if isinstance(abort_min_twr, (int, float)) and snapshot.mass_kg > 0:
            twr = snapshot.available_thrust_kn * 1000.0 / (snapshot.mass_kg * self.gravity_mps2)
            if twr < float(abort_min_twr):
                return "twr_below_abort_threshold"

        return None

    def _is_complete(self, snapshot: TelemetrySnapshot) -> bool:
        if self.flight_plan is None:
            return snapshot.status == "completed"

        duration_s = self.flight_plan.get("duration_s")
        if isinstance(duration_s, (int, float)) and snapshot.mission_elapsed_s >= float(duration_s):
            return True

        return snapshot.status == "completed"
