"""Main entry point.

This script bootstraps the  package onto `sys.path` and runs
the `ControlTowerUI` defined in . It no
longer imports or calls DearPyGui directly; the UI wrapper manages
DearPyGui usage internally.
"""

import logging
import os
import sys

# Ensure  is importable when running this script from the repository root.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from control_tower.ui import ControlTowerUI


def main():
    logging.basicConfig(level=logging.INFO)
    ui = ControlTowerUI()
    try:
        ui.start()
    finally:
        ui.stop()


if __name__ == "__main__":
    main()