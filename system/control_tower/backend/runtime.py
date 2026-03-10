from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Mapping


def _coerce_bool(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _coerce_int(value: Any, *, default: int) -> int:
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


def _load_json_object(config_path: Path | None) -> dict[str, Any]:
    if config_path is None:
        return {}
    if not config_path.exists():
        raise FileNotFoundError(f"config file not found: {config_path}")

    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("control tower config must be a JSON object")
    return data


@dataclass(slots=True)
class RuntimeConfig:
    app_name: str = "Ojinger Control Tower"
    mode: str = "headless"
    log_level: str = "INFO"
    connect_live_services: bool = False
    krpc_address: str = "127.0.0.1"
    krpc_rpc_port: int = 50000
    krpc_stream_port: int = 50001
    config_path: Path | None = None

    @classmethod
    def load(
        cls,
        config_path: str | Path | None = None,
        *,
        mode: str | None = None,
        connect_live_services: bool | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> "RuntimeConfig":
        env = os.environ if environ is None else environ
        resolved_path = Path(config_path).expanduser().resolve() if config_path else None
        file_values = _load_json_object(resolved_path)

        selected_mode = mode or env.get("CONTROL_TOWER_MODE") or file_values.get("mode") or "headless"
        normalized_mode = str(selected_mode).strip().lower()
        if normalized_mode not in {"headless", "ui", "auto"}:
            normalized_mode = "headless"

        live_services = connect_live_services
        if live_services is None:
            live_services = _coerce_bool(
                env.get("CONTROL_TOWER_CONNECT_LIVE", file_values.get("connect_live_services")),
                default=False,
            )

        return cls(
            app_name=str(file_values.get("app_name") or env.get("CONTROL_TOWER_APP_NAME") or "Ojinger Control Tower"),
            mode=normalized_mode,
            log_level=str(file_values.get("log_level") or env.get("CONTROL_TOWER_LOG_LEVEL") or "INFO").upper(),
            connect_live_services=bool(live_services),
            krpc_address=str(file_values.get("krpc_address") or env.get("KRPC_ADDRESS") or "127.0.0.1"),
            krpc_rpc_port=_coerce_int(file_values.get("krpc_rpc_port") or env.get("KRPC_RPC_PORT"), default=50000),
            krpc_stream_port=_coerce_int(file_values.get("krpc_stream_port") or env.get("KRPC_STREAM_PORT"), default=50001),
            config_path=resolved_path,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "app_name": self.app_name,
            "mode": self.mode,
            "log_level": self.log_level,
            "connect_live_services": self.connect_live_services,
            "krpc_address": self.krpc_address,
            "krpc_rpc_port": self.krpc_rpc_port,
            "krpc_stream_port": self.krpc_stream_port,
            "config_path": str(self.config_path) if self.config_path else None,
        }


@dataclass(slots=True)
class RuntimeContext:
    config: RuntimeConfig
    started_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dependency_status: dict[str, dict[str, Any]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config.as_dict(),
            "started_at_utc": self.started_at_utc,
            "dependency_status": self.dependency_status,
            "notes": list(self.notes),
        }
