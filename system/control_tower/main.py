from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

try:
	from .backend import RuntimeConfig
	from .manager import ControlTowerApplication
except ImportError:  # pragma: no cover - supports direct script execution
	from system.control_tower.backend import RuntimeConfig
	from system.control_tower.manager import ControlTowerApplication


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Ojinger control tower bootstrap entrypoint")
	parser.add_argument(
		"--action",
		choices=("boot", "mission-cycle"),
		default="boot",
		help="Select either a plain bootstrap report or the mock mission workflow.",
	)
	parser.add_argument(
		"--mode",
		choices=("headless", "ui", "auto"),
		default="headless",
		help="Select the boot path. 'headless' is safe without optional dependencies.",
	)
	parser.add_argument(
		"--config",
		type=Path,
		default=None,
		help="Optional path to a JSON runtime config file.",
	)
	parser.add_argument(
		"--artifacts-dir",
		type=Path,
		default=None,
		help="Optional root directory for mission workflow artifacts.",
	)
	parser.add_argument(
		"--parameter-export",
		type=Path,
		default=None,
		help="Optional parameter export JSON payload to seed the mission workflow.",
	)
	parser.add_argument(
		"--request-defaults",
		type=Path,
		default=None,
		help="Optional optimization request JSON defaults for the mission workflow.",
	)
	parser.add_argument(
		"--monitor-steps",
		type=int,
		default=6,
		help="Maximum supervisor polling steps during the mission workflow.",
	)
	parser.add_argument(
		"--connect-live",
		action="store_true",
		help="Attempt a live kRPC bootstrap if the optional dependency is available.",
	)
	parser.add_argument(
		"--json",
		action="store_true",
		help="Emit the boot report as JSON.",
	)
	return parser


def run(argv: Sequence[str] | None = None) -> int:
	parser = build_parser()
	args = parser.parse_args(list(argv) if argv is not None else None)

	try:
		config = RuntimeConfig.load(
			args.config,
			mode=args.mode,
			connect_live_services=args.connect_live,
		)
		application = ControlTowerApplication(config)
		if args.action == "mission-cycle":
			report = application.run_mock_mission_cycle(
				artifact_root=args.artifacts_dir,
				parameter_export=args.parameter_export,
				request_defaults=args.request_defaults,
				monitor_steps=args.monitor_steps,
			)
		else:
			report = application.boot()
	except Exception as exc:
		failure_payload = {
			"status": "error",
			"mode": args.action if args.action == "mission-cycle" else args.mode,
			"summary": {},
			"warnings": [],
			"errors": [str(exc)],
		}
		print(json.dumps(failure_payload, indent=2, sort_keys=True))
		return 1

	payload = report.to_dict()
	print(json.dumps(payload, indent=2, sort_keys=True))

	if args.action == "mission-cycle":
		final_state = str(payload.get("summary", {}).get("final_state") or "")
		if payload.get("status") == "ok" and final_state == "completed" and not report.errors:
			return 0
		if payload.get("status") in {"aborted", "incomplete"} or final_state != "completed":
			return 2

	return 0 if not report.errors else 1


def main() -> int:
	return run()


if __name__ == "__main__":
	raise SystemExit(main())
