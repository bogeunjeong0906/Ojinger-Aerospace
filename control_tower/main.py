#!/home/wjdqhrms/Ojinger-Aerospace/.venv/bin/python
"""Entry point for the Control Tower application.

This module initializes a basic DearPyGui user interface with a main
window and placeholder callbacks. Future components such as optimization
controls, telemetry displays, and mission configuration panels will be
added here.

All comments are written in English per project standards.
"""

import sys
import os

# add the root of the repo (two levels up) to sys.path so imports work
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from dearpygui.core import *
from dearpygui.simple import *


# ---------------------------------------------------------------------------
# Callback placeholders
# ---------------------------------------------------------------------------

def on_start_button(sender, data):
    """Placeholder for start button callback."""
    log_info("Start button pressed - callback not implemented yet")


def on_exit_button(sender, data):
    """Placeholder for exit button callback."""
    log_info("Exit button pressed - closing application")
    stop_dearpygui()


# ---------------------------------------------------------------------------
# Main UI setup
# ---------------------------------------------------------------------------

def setup_ui():
    """Create the main window and UI elements."""
    with window("Control Tower"):
        add_text("Welcome to the Rocket Mission Control Tower")
        add_spacing(count=2)
        add_button("Start Mission", callback=on_start_button)
        add_same_line()
        add_button("Exit", callback=on_exit_button)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Initialize the UI and start the DearPyGui event loop."""
    setup_ui()
    start_dearpygui()


if __name__ == "__main__":
    main()
