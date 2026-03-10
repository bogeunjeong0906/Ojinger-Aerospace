"""Generate as-built architecture artifacts using pyreverse when available.

This wrapper is intentionally small and mechanical. It does not invent
architecture; it only drives a generator and writes provenance metadata.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def find_pyreverse() -> list[str] | None:
    direct = shutil.which("pyreverse")
    if direct:
        return [direct]

    try:
        import pylint  # noqa: F401
    except Exception:
        return None

    return [sys.executable, "-m", "pylint.pyreverse.main"]


def build_command(pyreverse_cmd: list[str], module_path: str, output_dir: Path) -> list[str]:
    return [
        *pyreverse_cmd,
        module_path,
        "-o",
        "dot",
        "-p",
        Path(module_path).name.replace("/", "_").replace(".", "_"),
        "--output-directory",
        str(output_dir),
    ]


def write_manifest(output_dir: Path, module_path: str, command: list[str]) -> None:
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "pyreverse",
        "module_path": module_path,
        "command": command,
        "artifacts": sorted(path.name for path in output_dir.glob("*.dot")),
    }
    (output_dir / "generation_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate as-built architecture artifacts.")
    parser.add_argument("module_path", help="Python package/module path to analyze")
    parser.add_argument("--output-dir", required=True, help="Directory where generated artifacts will be written")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pyreverse_cmd = find_pyreverse()
    if pyreverse_cmd is None:
        print("pyreverse is not available. Install pylint/pyreverse or provide it in PATH.", file=sys.stderr)
        return 2

    command = build_command(pyreverse_cmd, args.module_path, output_dir)
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        return completed.returncode

    write_manifest(output_dir, args.module_path, command)
    print(json.dumps({"status": "completed", "output_dir": str(output_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())