"""Control Tower UI wrapper for DearPyGui.

This module provides the  class which encapsulates
DearPyGui usage so the GUI is not created on import. All DearPyGui
imports and calls happen inside methods so the module is safe to
import in headless environments or during unit tests.

English inline comments and PEP8-compliant code.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class ControlTowerUI:
    """Encapsulate DearPyGui UI lifecycle for the control tower.

    This class does not import or call DearPyGui on module import.
    Call  to create and run the UI (no-op in headless mode),
    and  to tear down any created DearPyGui context.
    """

    def __init__(self, title: str = "Ojinger Aerospace", width: int = 400, height: int = 200, headless: Optional[bool] = None):
        """Initialize the UI controller.

        Args:
            title: Window title for the viewport.
            width: Viewport width in pixels.
            height: Viewport height in pixels.
            headless: If None, detect headless via the DISPLAY environment
                variable. If True, UI operations are skipped.
        """
        self.title = title
        self.width = width
        self.height = height
        if headless is None:
            # If DISPLAY is unset or empty, assume headless environment.
            display = os.environ.get("DISPLAY")
            self.headless = display in (None, "")
        else:
            self.headless = bool(headless)

        self._context_created = False
        # In-memory mapping of tab label -> list of tab id/tags created in DearPyGui
        self._tabs = {}
        # Per-label counters to generate unique tab names
        self._tab_counters = {}
        # Mission window counters to allow multiple windows per mission
        self._mission_window_counters = {}
        # Track mission window tags (mission id -> list of tags)
        self._mission_windows = {}
        # In-memory mission store: list of mission dicts
        self._missions = []
        # Next mission id (incremental integer starting at 1)
        self._next_mission_id = 1

    def create_viewport(self) -> None:
        """Create DearPyGui context, viewport and a simple window with text.

        This method imports DearPyGui locally so importing this module
        doesn't require DearPyGui to be installed or available.
        """
        if self.headless:
            logger.info("Headless mode active; skipping viewport creation.")
            return

        if self._context_created:
            logger.debug("DearPyGui context already created; skipping.")
            return

        try:
            import dearpygui.dearpygui as dpg
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.exception("Failed to import DearPyGui: %s", exc)
            raise

        # Create context and viewport
        dpg.create_context()
        # Hardcode viewport larger to avoid clipping; use 3x configured size
        dpg.create_viewport(title=self.title, width=self.width * 3, height=self.height * 3)

        # Create a main window containing a prominent title and two
        # side-by-side panels: left = Manage list, right = Create form.
        with dpg.window(label="Main Window", width=max(0, self.width - 20), height=max(0, self.height - 40)):
            # Prominent title at the top (plain text)
            dpg.add_text(self.title)

            # Row with two side-by-side buttons that focus the panels
            def _on_button_focus(sender, app_data, user_data=None):
                # user_data will be one of: "create" or "manage"
                target = user_data
                # Try to focus the appropriate item, if supported.
                try:
                    if target == "create":
                        if hasattr(dpg, "set_item_focus"):
                            dpg.set_item_focus("main_create_name")
                        elif hasattr(dpg, "focus_item"):
                            dpg.focus_item("main_create_name")
                    elif target == "manage":
                        if hasattr(dpg, "set_item_focus"):
                            dpg.set_item_focus("main_manage_container")
                        elif hasattr(dpg, "focus_item"):
                            dpg.focus_item("main_manage_container")
                except Exception:
                    # Ignore focus errors; focusing is best-effort.
                    pass

            with dpg.group(horizontal=True):
                dpg.add_button(label="Create Mission", callback=_on_button_focus, user_data="create")
                dpg.add_button(label="Manage Missions", callback=_on_button_focus, user_data="manage")

            # Main two-column layout: left = manage list, right = create form
            with dpg.group(horizontal=True):
                # Left column: manage missions container (scrollable)
                with dpg.child_window(width=260, height=300, tag="main_manage_container"):
                    dpg.add_text("Manage created missions")
                    dpg.add_separator()
                    # The dynamic mission list will be populated by
                    #  into this child window.

                # Right column: create mission form
                with dpg.group(width=260):
                    dpg.add_text("Create a new mission")
                    dpg.add_input_text(label="Mission Name", tag="main_create_name")
                    dpg.add_input_text(label="Description", tag="main_create_description", multiline=True, height=120)

                    def _save_create(sender, app_data, user_data=None):
                        name = dpg.get_value("main_create_name") or ""
                        description = dpg.get_value("main_create_description") or ""
                        if name.strip():
                            mission = {
                                "id": self._next_mission_id,
                                "name": name.strip(),
                                "description": description.strip(),
                                "planned": False,
                            }
                            self._missions.append(mission)
                            self._next_mission_id += 1
                            # Update manage list
                            self._rebuild_manage_content()
                            # Clear inputs
                            dpg.set_value("main_create_name", "")
                            dpg.set_value("main_create_description", "")

                    def _reset_create(sender, app_data, user_data=None):
                        # Clear inputs
                        dpg.set_value("main_create_name", "")
                        dpg.set_value("main_create_description", "")

                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Save", callback=_save_create)
                        dpg.add_button(label="Reset", callback=_reset_create)

        dpg.setup_dearpygui()
        dpg.show_viewport()
        # Attempt measured auto-resize: measure left/right containers after first show
        # Use get_item_rect_size if available; perform a best-effort single resize.
        try:
            if hasattr(dpg, "get_item_rect_size"):
                # read measured sizes for left and right panels
                left_rect = dpg.get_item_rect_size("main_manage_container") or [0, 0]
                # measure a right-side representative item (description field)
                right_rect = dpg.get_item_rect_size("main_create_description") or [0, 0]

                left_w, left_h = int(left_rect[0]), int(left_rect[1])
                right_w, right_h = int(right_rect[0]), int(right_rect[1])

                # Compute target size with padding and header space
                padding_h = 60
                padding_w = 80
                target_w = left_w + right_w + padding_w
                target_h = max(left_h, right_h) + padding_h

                # Ensure minimums
                target_w = max(target_w, int(self.width * 1.5))
                target_h = max(target_h, int(self.height * 1.5))

                try:
                    dpg.configure_item("Main Window", width=target_w, height=target_h)
                except Exception:
                    # Fallback to viewport resize if available
                    if hasattr(dpg, "set_viewport_width") and hasattr(dpg, "set_viewport_height"):
                        try:
                            dpg.set_viewport_width(target_w)
                            dpg.set_viewport_height(target_h)
                        except Exception:
                            logger.exception("Failed to set viewport size in auto-resize fallback.")
        except Exception:
            logger.exception("Measured auto-resize failed; skipping.")

        self._context_created = True
        logger.info("DearPyGui viewport created for %s", self.title)

    def start(self) -> None:
        """Start the DearPyGui event loop unless running headless.

        If headless, this method logs and returns immediately.
        """
        if self.headless:
            logger.info("Running in headless mode; UI start skipped.")
            return

        # Ensure the viewport is created then start the main loop.
        self.create_viewport()
        try:
            import dearpygui.dearpygui as dpg
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.exception("Failed to import DearPyGui for start: %s", exc)
            raise

        logger.info("Starting DearPyGui main loop.")
        dpg.start_dearpygui()

    def stop(self) -> None:
        """Destroy the DearPyGui context if it was created.

        Safe to call multiple times.
        """
        if not self._context_created:
            logger.debug("No DearPyGui context to destroy.")
            return

        try:
            import dearpygui.dearpygui as dpg
        except Exception:  # pragma: no cover - environment dependent
            # If import fails at shutdown, there's nothing we can do.
            logger.exception("DearPyGui import failed during stop; skipping destroy.")
            self._context_created = False
            return

        try:
            dpg.destroy_context()
            logger.info("DearPyGui context destroyed.")
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.exception("Error while destroying DearPyGui context: %s", exc)
        finally:
            self._context_created = False

    def is_running(self) -> bool:
        """Return True if a DearPyGui context was created and we're not headless.

        This is a lightweight indicator rather than probing DearPyGui internals.
        """
        return bool(self._context_created and not self.headless)

    # ---- Internal UI helpers for window-based mission management ----
    def _open_create_window(self) -> None:
        """Open (or focus) the single Create Mission window.

        This UI no longer uses a separate Create window. Keep a small
        compatibility stub that focuses the embedded create panel when
        possible.
        """
        if self.headless:
            return

        try:
            import dearpygui.dearpygui as dpg
        except Exception:  # pragma: no cover - environment dependent
            logger.exception("Failed to import DearPyGui for create stub.")
            return

        # Best-effort: focus the create input in the embedded panel
        try:
            if hasattr(dpg, "set_item_focus"):
                dpg.set_item_focus("main_create_name")
            elif hasattr(dpg, "focus_item"):
                dpg.focus_item("main_create_name")
        except Exception:
            pass

    def _open_manage_window(self) -> None:
        """Compatibility stub for the previous manage window.

        The manage list is now embedded in the main window under the
        tag `main_manage_container`. This stub attempts to focus that
        container when called.
        """
        if self.headless:
            return

        try:
            import dearpygui.dearpygui as dpg
        except Exception:  # pragma: no cover - environment dependent
            logger.exception("Failed to import DearPyGui for manage stub.")
            return

        try:
            if hasattr(dpg, "set_item_focus"):
                dpg.set_item_focus("main_manage_container")
            elif hasattr(dpg, "focus_item"):
                dpg.focus_item("main_manage_container")
        except Exception:
            pass

    def _rebuild_manage_content(self) -> None:
        """Rebuild the contents of the Manage Missions window.

        This clears and repopulates the `main_manage_container` with the
        current missions and their control buttons.
        """
        if self.headless:
            return

        try:
            import dearpygui.dearpygui as dpg
        except Exception:  # pragma: no cover - environment dependent
            logger.exception("Failed to import DearPyGui for rebuilding manage content.")
            return

        container = "main_manage_container"
        try:
            # If the container does not exist yet, nothing to do
            if not dpg.does_item_exist(container):
                return

            # Clear current children
            try:
                children = dpg.get_item_children(container, 1) or []
                for child in list(children):
                    try:
                        dpg.delete_item(child)
                    except Exception:
                        pass
            except Exception:
                # Fall back: attempt to delete all items by tag prefix
                pass

            # Populate container with current missions
            for mission in list(self._missions):
                mid = mission["id"]
                name = mission["name"]
                desc = mission.get("description", "")
                planned = mission.get("planned", False)

                label = f"{name}"
                if planned:
                    label = f"{label} (Planned)"

                # Use a unique group per mission so we can layout buttons
                grp_tag = f"mission_group_{mid}"
                with dpg.group(parent=container, horizontal=False, tag=grp_tag):
                    dpg.add_text(label)
                    dpg.add_text(desc)
                    def _plan_cb(sender, app_data, user_data=None):
                        # Open a dedicated mission window for planning (multiple allowed)
                        self._open_mission_window(mid)

                    def _del_cb(sender, app_data, user_data=None):
                        # Remove mission from store
                        self._missions[:] = [m for m in self._missions if m["id"] != mid]
                        self._rebuild_manage_content()

                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Plan", callback=_plan_cb)
                        dpg.add_button(label="Delete", callback=_del_cb)

            # No separate manage window exists in the integrated layout.

        except Exception:
            logger.exception("Failed to rebuild manage missions content.")

    def _open_mission_window(self, mid: int) -> None:
        """Open a dedicated mission window for the given mission id.

        Multiple mission windows (even for the same mission) are allowed.
        The window provides Plan and Delete actions for the mission.
        """
        if self.headless:
            return

        try:
            import dearpygui.dearpygui as dpg
        except Exception:  # pragma: no cover - environment dependent
            logger.exception("Failed to import DearPyGui for mission window.")
            return

        # Find mission by id
        mission = None
        for m in self._missions:
            if m["id"] == mid:
                mission = m
                break
        if mission is None:
            return

        name = mission["name"]
        desc = mission.get("description", "")

        # Create a unique tag for this mission window instance
        count = self._mission_window_counters.get(mid, 0) + 1
        self._mission_window_counters[mid] = count
        tag = f"mission_window_{mid}_{count}"
        self._mission_windows.setdefault(mid, []).append(tag)

        try:
            with dpg.window(label=f"Mission {mid}: {name}", tag=tag, width=420, height=260):
                dpg.add_text(f"Name: {name}")
                dpg.add_text(f"Description: {desc}")

                def _plan_cb(sender, app_data, user_data=None):
                    # Toggle planned state for this mission
                    for m in self._missions:
                        if m["id"] == mid:
                            m["planned"] = not bool(m.get("planned", False))
                            break
                    self._rebuild_manage_content()

                def _del_cb(sender, app_data, user_data=None):
                    # Delete mission and close this window
                    self._missions[:] = [m for m in self._missions if m["id"] != mid]
                    try:
                        if dpg.does_item_exist(tag):
                            dpg.delete_item(tag)
                    except Exception:
                        pass
                    self._rebuild_manage_content()

                def _close_cb(sender, app_data, user_data=None):
                    try:
                        if dpg.does_item_exist(tag):
                            dpg.delete_item(tag)
                    except Exception:
                        pass

                with dpg.group(horizontal=True):
                    dpg.add_button(label="Plan", callback=_plan_cb)
                    dpg.add_button(label="Delete", callback=_del_cb)
                    dpg.add_button(label="Close", callback=_close_cb)

        except Exception:
            logger.exception("Failed to open mission window for %s", mid)


def handle_user_input(input_data):
    """Compatibility entrypoint for user input handling.

    This function preserves the previous API and explicitly signals
    that a real implementation is required by raising
    .
    """
    raise NotImplementedError()
