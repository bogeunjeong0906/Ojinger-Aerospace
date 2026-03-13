"""Control Tower package.

Re-export the UI entrypoint so consumers can do:
    from control_tower import ControlTowerUI

Keep imports minimal and safe; `ui.py` defers heavy GUI
imports so importing this module is acceptable.
"""

from .ui import ControlTowerUI  # re-export safe UI class

__all__ = [
    'ControlTowerUI',
]
"""Control Tower package.

Re-export the UI entrypoint so consumers can do:
    from control_tower import ControlTowerUI

Keep imports minimal and safe; `ui.py` defers heavy GUI
imports so importing this module is acceptable.
"""

from .ui import ControlTowerUI  # re-export safe UI class

__all__ = [
    'ControlTowerUI',
]
