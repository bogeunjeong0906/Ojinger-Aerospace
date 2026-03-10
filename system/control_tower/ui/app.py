from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any


@dataclass(slots=True)
class UIShell:
    application_name: str
    dependency_error: str | None = None

    @property
    def is_available(self) -> bool:
        return self.dependency_error is None

    def describe(self) -> dict[str, Any]:
        if not self.is_available:
            return {
                "backend": "dearpygui",
                "status": "unavailable",
                "detail": self.dependency_error,
            }

        return {
            "backend": "dearpygui",
            "status": "ready",
            "detail": f"{self.application_name} UI dependencies resolved.",
        }


def create_ui_shell(application_name: str) -> UIShell:
    try:
        import_module("dearpygui.dearpygui")
    except (ImportError, ModuleNotFoundError) as exc:
        return UIShell(application_name=application_name, dependency_error=str(exc))

    return UIShell(application_name=application_name)