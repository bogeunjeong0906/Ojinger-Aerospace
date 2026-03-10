from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any

from .contracts import contract_manifest
from .optimizer import Casadi1AxisOptimizer
from .runtime import RuntimeConfig, RuntimeContext
from .supervisor import MissionSupervisor
from .telemetry import KrpcTelemetryAdapter, MockTelemetryAdapter, NullTelemetryAdapter


@dataclass(slots=True)
class DependencyState:
    name: str
    available: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.available,
            "detail": self.detail,
        }


def probe_optional_dependency(module_name: str, import_target: str | None = None) -> DependencyState:
    target = import_target or module_name
    try:
        import_module(target)
    except (ImportError, ModuleNotFoundError) as exc:
        return DependencyState(name=module_name, available=False, detail=str(exc))

    return DependencyState(name=module_name, available=True, detail="available")

@dataclass(slots=True)
class PlaceholderOptimizer:
    name: str = "placeholder_optimizer"

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": "stub",
            "detail": "Optimization engine scaffolded for later tasks.",
        }


@dataclass(slots=True)
class ServiceContainer:
    context: RuntimeContext
    dependencies: dict[str, DependencyState]
    telemetry: MockTelemetryAdapter | NullTelemetryAdapter | KrpcTelemetryAdapter
    supervisor: MissionSupervisor
    optimizer: Casadi1AxisOptimizer | PlaceholderOptimizer

    def boot_summary(self) -> dict[str, Any]:
        return {
            "app_name": self.context.config.app_name,
            "mode": self.context.config.mode,
            "contracts": sorted(contract_manifest().keys()),
            "runtime": self.context.to_dict(),
            "dependencies": {
                name: state.to_dict() for name, state in self.dependencies.items()
            },
            "telemetry": self.telemetry.describe(),
            "supervisor": self.supervisor.describe(),
            "optimizer": self.optimizer.describe(),
        }


def build_service_container(config: RuntimeConfig) -> ServiceContainer:
    dependencies = {
        "dearpygui": probe_optional_dependency("dearpygui", "dearpygui.dearpygui"),
        "krpc": probe_optional_dependency("krpc"),
    }

    notes = [
        "Control tower scaffold initialized.",
        "Optional UI/live transport dependencies are soft-gated.",
    ]
    if not config.connect_live_services:
        notes.append("Live telemetry bootstrap is disabled in this run.")

    context = RuntimeContext(
        config=config,
        dependency_status={
            name: state.to_dict() for name, state in dependencies.items()
        },
        notes=notes,
    )

    if config.connect_live_services:
        live_telemetry = KrpcTelemetryAdapter(
            address=config.krpc_address,
            rpc_port=config.krpc_rpc_port,
            stream_port=config.krpc_stream_port,
        )
        if live_telemetry.connect():
            telemetry: MockTelemetryAdapter | NullTelemetryAdapter | KrpcTelemetryAdapter = live_telemetry
        else:
            notes.append(
                "Live telemetry bootstrap failed; continuing with mock telemetry snapshots."
            )
            telemetry = MockTelemetryAdapter(
                note=f"fallback mock stream after live bootstrap failure: {live_telemetry.describe().get('detail', 'unknown error')}",
            )
            telemetry.connect()
    else:
        telemetry = MockTelemetryAdapter(
            note="live transport disabled; using mock telemetry snapshots",
        )
        telemetry.connect()

    supervisor = MissionSupervisor(telemetry=telemetry)

    return ServiceContainer(
        context=context,
        dependencies=dependencies,
        telemetry=telemetry,
        supervisor=supervisor,
        optimizer=Casadi1AxisOptimizer(),
    )