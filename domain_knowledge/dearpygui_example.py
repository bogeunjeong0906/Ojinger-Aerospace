import math
import random

import dearpygui.dearpygui as dpg


MAIN_WINDOW_TAG = "main_window"
STATUS_TEXT_TAG = "status_text"
LOG_TEXT_TAG = "log_text"
GREETING_TEXT_TAG = "greeting_text"
PROGRESS_BAR_TAG = "progress_bar"
ADVANCED_PANEL_TAG = "advanced_panel"
FILE_DIALOG_TAG = "file_dialog"
FILE_RESULT_TAG = "file_result"
MOUSE_TEXT_TAG = "mouse_position_text"
ITEM_HANDLER_TEXT_TAG = "item_handler_text"
NODE_EDITOR_TAG = "node_editor"
PLOT_X_AXIS_TAG = "plot_x_axis"
PLOT_Y_AXIS_TAG = "plot_y_axis"
SINE_SERIES_TAG = "sine_series"
COSINE_SERIES_TAG = "cosine_series"
TELEMETRY_TAGS = {
    "Altitude": "telemetry_altitude",
    "Velocity": "telemetry_velocity",
    "Fuel": "telemetry_fuel",
    "Pitch": "telemetry_pitch",
}

LOG_LIMIT = 22
LOG_ENTRIES: list[str] = []
PLOT_X_DATA = [index * 0.1 for index in range(0, 126)]


def append_log(message: str) -> None:
    LOG_ENTRIES.append(f"[{len(LOG_ENTRIES) + 1:02d}] {message}")
    trimmed_log = "\n".join(LOG_ENTRIES[-LOG_LIMIT:])
    if dpg.does_item_exist(LOG_TEXT_TAG):
        dpg.set_value(LOG_TEXT_TAG, trimmed_log)


def set_status(message: str) -> None:
    if dpg.does_item_exist(STATUS_TEXT_TAG):
        dpg.set_value(STATUS_TEXT_TAG, message)
    append_log(message)


def stop_application(sender=None, app_data=None, user_data=None) -> None:
    set_status("Stopping DearPyGui event loop.")
    dpg.stop_dearpygui()


def clear_log(sender=None, app_data=None, user_data=None) -> None:
    LOG_ENTRIES.clear()
    if dpg.does_item_exist(LOG_TEXT_TAG):
        dpg.set_value(LOG_TEXT_TAG, "")
    set_status("Event log cleared.")


def update_greeting(sender, app_data, user_data) -> None:
    name = (app_data or "Pilot").strip() or "Pilot"
    dpg.set_value(GREETING_TEXT_TAG, f"Hello, {name}! Welcome to DearPyGui.")
    set_status(f"Greeting updated for {name}.")


def update_progress(sender, app_data, user_data) -> None:
    dpg.set_value(PROGRESS_BAR_TAG, app_data)
    dpg.configure_item(PROGRESS_BAR_TAG, overlay=f"{app_data:.0%}")
    set_status(f"Progress bar set to {app_data:.0%}.")


def toggle_quick_reference(sender, app_data, user_data) -> None:
    dpg.configure_item(ADVANCED_PANEL_TAG, show=app_data)
    state = "visible" if app_data else "hidden"
    set_status(f"Quick reference panel is now {state}.")


def report_selection(sender, app_data, user_data) -> None:
    label = user_data or dpg.get_item_label(sender)
    set_status(f"{label} changed to {app_data}.")


def randomize_telemetry(sender=None, app_data=None, user_data=None) -> None:
    telemetry_values = {
        "Altitude": f"{random.uniform(12000, 182000):,.0f} m",
        "Velocity": f"{random.uniform(120, 4250):,.1f} m/s",
        "Fuel": f"{random.uniform(4, 100):.1f} %",
        "Pitch": f"{random.uniform(-15, 90):.1f} deg",
    }

    for key, value in telemetry_values.items():
        dpg.set_value(TELEMETRY_TAGS[key], value)

    set_status("Telemetry table randomized.")


def apply_theme(sender, app_data, user_data) -> None:
    dpg.bind_theme(user_data)
    set_status(f"Applied theme: {user_data}.")


def open_metrics(sender=None, app_data=None, user_data=None) -> None:
    dpg.show_metrics()
    set_status("Opened metrics window.")


def open_debug(sender=None, app_data=None, user_data=None) -> None:
    dpg.show_debug()
    set_status("Opened debug window.")


def open_style_editor(sender=None, app_data=None, user_data=None) -> None:
    dpg.show_style_editor()
    set_status("Opened style editor.")


def open_documentation(sender=None, app_data=None, user_data=None) -> None:
    dpg.show_documentation()
    set_status("Opened DearPyGui documentation window.")


def open_item_registry(sender=None, app_data=None, user_data=None) -> None:
    dpg.show_item_registry()
    set_status("Opened item registry.")


def open_about(sender=None, app_data=None, user_data=None) -> None:
    dpg.show_about()
    set_status("Opened about window.")


def open_file_dialog(sender=None, app_data=None, user_data=None) -> None:
    dpg.show_item(FILE_DIALOG_TAG)
    set_status("Opened file dialog.")


def handle_file_selection(sender, app_data, user_data) -> None:
    selections = list(app_data.get("selections", {}).values())
    if selections:
        summary = "\n".join(selections[:6])
        dpg.set_value(FILE_RESULT_TAG, summary)
        set_status(f"Selected {len(selections)} file(s) from the file dialog.")
        return

    selected_path = app_data.get("file_path_name", "No file selected.")
    dpg.set_value(FILE_RESULT_TAG, selected_path)
    set_status("File dialog closed with a single selection.")


def refresh_plot(sender=None, app_data=None, user_data=None) -> None:
    phase = random.uniform(0.0, math.pi)
    scale = random.uniform(0.7, 1.4)
    sine_values = [scale * math.sin(x + phase) for x in PLOT_X_DATA]
    cosine_values = [math.cos((x * 0.7) + phase) for x in PLOT_X_DATA]
    dpg.set_value(SINE_SERIES_TAG, [PLOT_X_DATA, sine_values])
    dpg.set_value(COSINE_SERIES_TAG, [PLOT_X_DATA, cosine_values])
    dpg.fit_axis_data(PLOT_X_AXIS_TAG)
    dpg.fit_axis_data(PLOT_Y_AXIS_TAG)
    set_status("Plot data regenerated and fitted.")


def fit_plot(sender=None, app_data=None, user_data=None) -> None:
    dpg.fit_axis_data(PLOT_X_AXIS_TAG)
    dpg.fit_axis_data(PLOT_Y_AXIS_TAG)
    set_status("Plot axes fitted to the visible series.")


def create_link(sender, app_data, user_data) -> None:
    dpg.add_node_link(app_data[0], app_data[1], parent=sender)
    set_status(f"Created node link from {app_data[0]} to {app_data[1]}.")


def delete_link(sender, app_data, user_data) -> None:
    dpg.delete_item(app_data)
    set_status("Deleted a node link from the editor.")


def update_mouse_position(sender, app_data, user_data) -> None:
    if dpg.does_item_exist(MOUSE_TEXT_TAG):
        mouse_x, mouse_y = app_data
        dpg.set_value(MOUSE_TEXT_TAG, f"Mouse position: {int(mouse_x)}, {int(mouse_y)}")


def report_key_press(sender, app_data, user_data) -> None:
    set_status(f"Key press detected: {app_data}.")


def report_button_hover(sender, app_data, user_data) -> None:
    dpg.set_value(ITEM_HANDLER_TEXT_TAG, "Item handler: hover detected on the tracked button.")


def report_button_click(sender, app_data, user_data) -> None:
    dpg.set_value(ITEM_HANDLER_TEXT_TAG, "Item handler: click detected on the tracked button.")
    set_status("Tracked button activated through an item handler.")


def build_themes() -> None:
    with dpg.theme(tag="theme_ocean"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (15, 23, 42), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (30, 41, 59), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (51, 65, 85), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button, (37, 99, 235), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (59, 130, 246), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (96, 165, 250), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Header, (14, 116, 144), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (30, 64, 175), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, (37, 99, 235), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 6, category=dpg.mvThemeCat_Core)

    with dpg.theme(tag="theme_sunset"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (42, 25, 15), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (68, 42, 24), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (101, 67, 33), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button, (234, 88, 12), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (249, 115, 22), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (251, 146, 60), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Header, (217, 119, 6), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (194, 65, 12), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, (234, 88, 12), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 10, category=dpg.mvThemeCat_Core)

    with dpg.theme(tag="theme_forest"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (10, 27, 21), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (20, 50, 39), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (34, 84, 61), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button, (22, 163, 74), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (34, 197, 94), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (74, 222, 128), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Header, (21, 128, 61), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (22, 101, 52), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, (22, 163, 74), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 12, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 12, category=dpg.mvThemeCat_Core)

    with dpg.theme(tag="theme_button_accent"):
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (168, 85, 247), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (192, 132, 252), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (216, 180, 254), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 14, category=dpg.mvThemeCat_Core)


def build_menu_bar() -> None:
    with dpg.menu_bar():
        with dpg.menu(label="Application"):
            dpg.add_menu_item(label="Open File Dialog", callback=open_file_dialog)
            dpg.add_menu_item(label="Clear Log", callback=clear_log)
            dpg.add_separator()
            dpg.add_menu_item(label="Quit", callback=stop_application)

        with dpg.menu(label="Built-in Tools"):
            dpg.add_menu_item(label="Metrics", callback=open_metrics)
            dpg.add_menu_item(label="Debug", callback=open_debug)
            dpg.add_menu_item(label="Style Editor", callback=open_style_editor)
            dpg.add_menu_item(label="Item Registry", callback=open_item_registry)
            dpg.add_menu_item(label="Documentation", callback=open_documentation)
            dpg.add_menu_item(label="About", callback=open_about)

        with dpg.menu(label="Themes"):
            dpg.add_menu_item(label="Ocean", callback=apply_theme, user_data="theme_ocean")
            dpg.add_menu_item(label="Sunset", callback=apply_theme, user_data="theme_sunset")
            dpg.add_menu_item(label="Forest", callback=apply_theme, user_data="theme_forest")


def build_level_one_tab() -> None:
    with dpg.tab(label="Level 1 · Basics"):
        dpg.add_text("Start here: window, text, button, tooltip, input_text, slider_float, progress_bar, checkbox.")
        dpg.add_separator()

        with dpg.group(horizontal=True):
            with dpg.child_window(width=520, height=430, border=True):
                dpg.add_text("Core widgets")
                dpg.add_spacer(height=4)
                dpg.add_input_text(
                    label="Name",
                    default_value="Flight Director",
                    callback=update_greeting,
                    on_enter=True,
                    width=260,
                )
                dpg.add_text("Hello, Flight Director! Welcome to DearPyGui.", tag=GREETING_TEXT_TAG)
                hero_button = dpg.add_button(label="Trigger greeting callback", callback=report_selection, user_data="Hero button")
                with dpg.tooltip(parent=hero_button):
                    dpg.add_text("Tooltips are lightweight contextual helpers attached to items.")

                dpg.add_spacer(height=8)
                dpg.add_slider_float(
                    label="Mission progress",
                    min_value=0.0,
                    max_value=1.0,
                    default_value=0.35,
                    callback=update_progress,
                    width=280,
                )
                dpg.add_progress_bar(default_value=0.35, overlay="35%", width=330, tag=PROGRESS_BAR_TAG)
                dpg.add_checkbox(
                    label="Show quick reference panel",
                    default_value=True,
                    callback=toggle_quick_reference,
                )
                dpg.add_button(label="Clear event log", callback=clear_log)

            with dpg.child_window(width=520, height=430, border=True, tag=ADVANCED_PANEL_TAG):
                dpg.add_text("Quick reference")
                dpg.add_text("• Use callbacks to react to value changes.")
                dpg.add_text("• Tags let you update widgets anywhere in the app.")
                dpg.add_text("• Child windows create structured dashboard layouts.")
                dpg.add_text("• Tooltips, groups, separators, and spacers improve readability.")
                dpg.add_separator()

                with dpg.tree_node(label="Minimal learning path", default_open=True):
                    dpg.add_text("1. Build containers first.")
                    dpg.add_text("2. Add widgets and give them tags.")
                    dpg.add_text("3. Wire callbacks to update other items.")
                    dpg.add_text("4. Use themes and handlers to scale the UI.")

                with dpg.collapsing_header(label="Common beginner commands", default_open=True):
                    dpg.add_text("create_context, window, add_text, add_button, add_input_text")
                    dpg.add_text("add_slider_float, add_progress_bar, add_checkbox, tooltip")


def build_level_two_tab() -> None:
    with dpg.tab(label="Level 2 · Inputs and Selection"):
        dpg.add_text("Explore selection widgets, drags, color tools, and value callbacks.")
        dpg.add_separator()

        with dpg.group(horizontal=True):
            with dpg.child_window(width=500, height=520, border=True):
                dpg.add_combo(
                    label="Render mode",
                    items=["Wireframe", "Solid", "Hybrid", "Debug"],
                    default_value="Hybrid",
                    callback=report_selection,
                    width=220,
                    user_data="Render mode",
                )
                dpg.add_listbox(
                    label="Panel focus",
                    items=["Telemetry", "Navigation", "Propulsion", "Diagnostics", "Plots"],
                    default_value="Telemetry",
                    callback=report_selection,
                    num_items=5,
                    width=220,
                    user_data="Panel focus",
                )
                dpg.add_slider_int(
                    label="Sample count",
                    default_value=32,
                    min_value=8,
                    max_value=256,
                    callback=report_selection,
                    width=250,
                    user_data="Sample count",
                )
                dpg.add_drag_float(
                    label="Control gain",
                    default_value=0.8,
                    speed=0.01,
                    min_value=0.0,
                    max_value=5.0,
                    callback=report_selection,
                    width=250,
                    user_data="Control gain",
                )
                dpg.add_input_int(
                    label="Packet ID",
                    default_value=42,
                    callback=report_selection,
                    width=180,
                    user_data="Packet ID",
                )
                dpg.add_selectable(label="Selectable telemetry overlay", callback=report_selection, user_data="Selectable overlay")

            with dpg.child_window(width=540, height=520, border=True):
                dpg.add_color_edit(
                    label="Accent color",
                    default_value=(64, 156, 255, 255),
                    callback=report_selection,
                    user_data="Accent color",
                )
                dpg.add_spacer(height=8)
                dpg.add_color_picker(
                    label="Full color picker",
                    default_value=(86, 180, 211, 255),
                    alpha_bar=True,
                    callback=report_selection,
                    user_data="Color picker",
                )


def build_level_three_tab() -> None:
    with dpg.tab(label="Level 3 · Layout and Tables"):
        dpg.add_text("Combine groups, child windows, tables, tree nodes, and buttons to build dashboards.")
        dpg.add_separator()

        with dpg.group(horizontal=True):
            with dpg.child_window(width=560, height=500, border=True):
                dpg.add_text("Command catalog")
                with dpg.table(
                    header_row=True,
                    resizable=True,
                    row_background=True,
                    borders_innerH=True,
                    borders_outerH=True,
                    borders_innerV=True,
                    borders_outerV=True,
                    policy=dpg.mvTable_SizingStretchProp,
                ):
                    dpg.add_table_column(label="Level")
                    dpg.add_table_column(label="Representative commands")

                    rows = [
                        ("Beginner", "window, add_text, add_button, add_input_text"),
                        ("Intermediate", "group, child_window, combo, listbox, table"),
                        ("Advanced", "plot, drawlist, theme, handler_registry"),
                        ("Expert", "node_editor, item_registry, metrics, debug"),
                    ]
                    for level, commands in rows:
                        with dpg.table_row():
                            dpg.add_text(level)
                            dpg.add_text(commands)

                dpg.add_separator()
                with dpg.tree_node(label="Nested layout example", default_open=True):
                    dpg.add_text("Tree nodes are ideal for hierarchical configuration panels.")
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Left action", callback=report_selection, user_data="Left action")
                        dpg.add_button(label="Right action", callback=report_selection, user_data="Right action")

            with dpg.child_window(width=480, height=500, border=True):
                dpg.add_text("Telemetry table")
                with dpg.table(
                    header_row=True,
                    row_background=True,
                    borders_innerH=True,
                    borders_outerH=True,
                    borders_innerV=True,
                    borders_outerV=True,
                    policy=dpg.mvTable_SizingStretchProp,
                ):
                    dpg.add_table_column(label="Metric")
                    dpg.add_table_column(label="Value")

                    for key, tag in TELEMETRY_TAGS.items():
                        with dpg.table_row():
                            dpg.add_text(key)
                            dpg.add_text("--", tag=tag)

                dpg.add_spacer(height=10)
                dpg.add_button(label="Randomize telemetry", callback=randomize_telemetry)
                dpg.add_spacer(height=12)
                with dpg.collapsing_header(label="Why tables matter", default_open=True):
                    dpg.add_text("• Tables support dashboards, inspectors, and data-heavy tools.")
                    dpg.add_text("• Stretch sizing helps tables fill available width cleanly.")
                    dpg.add_text("• Row backgrounds improve scanability for operators.")


def build_level_four_tab() -> None:
    with dpg.tab(label="Level 4 · Themes and Styling"):
        dpg.add_text("Themes scale visual consistency across a full application.")
        dpg.add_separator()

        with dpg.group(horizontal=True):
            with dpg.child_window(width=520, height=500, border=True):
                dpg.add_text("Global themes")
                dpg.add_button(label="Apply Ocean theme", callback=apply_theme, user_data="theme_ocean")
                dpg.add_button(label="Apply Sunset theme", callback=apply_theme, user_data="theme_sunset")
                dpg.add_button(label="Apply Forest theme", callback=apply_theme, user_data="theme_forest")
                dpg.add_spacer(height=12)
                dpg.add_text("Built-in DearPyGui tooling")
                dpg.add_button(label="Open Style Editor", callback=open_style_editor)
                dpg.add_button(label="Open Documentation", callback=open_documentation)
                dpg.add_button(label="Open Item Registry", callback=open_item_registry)

            with dpg.child_window(width=520, height=500, border=True):
                dpg.add_text("Item-specific theme binding")
                themed_button = dpg.add_button(label="Accent themed button", callback=report_selection, user_data="Accent themed button")
                dpg.bind_item_theme(themed_button, "theme_button_accent")
                dpg.add_spacer(height=12)
                dpg.add_text("Theme notes")
                dpg.add_text("• Use global themes with bind_theme for broad styling.")
                dpg.add_text("• Use bind_item_theme when only one widget needs a different look.")
                dpg.add_text("• Combine colors and style variables for strong visual systems.")


def build_level_five_tab() -> None:
    with dpg.tab(label="Level 5 · Plots and Drawing"):
        dpg.add_text("Plots and drawlists unlock technical visualization and custom rendering.")
        dpg.add_separator()

        with dpg.group(horizontal=True):
            with dpg.child_window(width=580, height=560, border=True):
                dpg.add_button(label="Regenerate plot", callback=refresh_plot)
                dpg.add_same_line()
                dpg.add_button(label="Fit axes", callback=fit_plot)

                with dpg.plot(label="Signal explorer", height=470, width=550):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag=PLOT_X_AXIS_TAG)
                    dpg.add_plot_axis(dpg.mvYAxis, label="Value", tag=PLOT_Y_AXIS_TAG)
                    dpg.add_line_series(
                        PLOT_X_DATA,
                        [math.sin(x) for x in PLOT_X_DATA],
                        label="sin(x)",
                        parent=PLOT_Y_AXIS_TAG,
                        tag=SINE_SERIES_TAG,
                    )
                    dpg.add_scatter_series(
                        PLOT_X_DATA,
                        [math.cos(x) for x in PLOT_X_DATA],
                        label="cos(x)",
                        parent=PLOT_Y_AXIS_TAG,
                        tag=COSINE_SERIES_TAG,
                    )

            with dpg.child_window(width=460, height=560, border=True):
                dpg.add_text("Drawlist canvas")
                with dpg.drawlist(width=430, height=500):
                    dpg.draw_rectangle((10, 10), (420, 490), color=(148, 163, 184, 255), fill=(15, 23, 42, 255), thickness=2)
                    dpg.draw_text((24, 28), "Custom draw commands", color=(255, 255, 255, 255), size=20)
                    dpg.draw_line((40, 90), (390, 90), color=(59, 130, 246, 255), thickness=3)
                    dpg.draw_circle((110, 180), 48, color=(34, 197, 94, 255), fill=(34, 197, 94, 60), thickness=3)
                    dpg.draw_triangle((220, 235), (290, 120), (360, 235), color=(249, 115, 22, 255), fill=(249, 115, 22, 70), thickness=3)
                    dpg.draw_polyline(
                        [(36, 360), (100, 300), (180, 340), (250, 260), (330, 320), (392, 250)],
                        color=(168, 85, 247, 255),
                        thickness=4,
                        closed=False,
                    )
                    dpg.draw_text((38, 420), "Use drawlists for overlays, HUDs, and custom visual tools.", color=(226, 232, 240, 255), size=16)


def build_level_six_tab() -> None:
    with dpg.tab(label="Level 6 · Node Editor and Debugging"):
        dpg.add_text("The node editor is powerful for visual scripting, pipelines, and graph-based tools.")
        dpg.add_separator()

        with dpg.group(horizontal=True):
            with dpg.child_window(width=730, height=560, border=True):
                with dpg.node_editor(tag=NODE_EDITOR_TAG, callback=create_link, delink_callback=delete_link, minimap=True):
                    with dpg.node(label="Input Node", pos=(30, 60)):
                        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                            dpg.add_text("Generate telemetry")
                            dpg.add_input_float(label="Throttle", default_value=0.75, width=140)
                        with dpg.node_attribute(tag="node_output_a", attribute_type=dpg.mvNode_Attr_Output):
                            dpg.add_text("Telemetry Out")

                    with dpg.node(label="Processor Node", pos=(320, 120)):
                        with dpg.node_attribute(tag="node_input_b", attribute_type=dpg.mvNode_Attr_Input):
                            dpg.add_text("Telemetry In")
                        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                            dpg.add_slider_float(label="Gain", default_value=1.15, min_value=0.0, max_value=2.0, width=160)
                        with dpg.node_attribute(tag="node_output_b", attribute_type=dpg.mvNode_Attr_Output):
                            dpg.add_text("Command Out")

                    with dpg.node(label="Output Node", pos=(600, 200)):
                        with dpg.node_attribute(tag="node_input_c", attribute_type=dpg.mvNode_Attr_Input):
                            dpg.add_text("Command In")
                        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                            dpg.add_checkbox(label="Armed", default_value=True)

            with dpg.child_window(width=310, height=560, border=True):
                dpg.add_text("Expert tooling")
                dpg.add_button(label="Open Metrics", callback=open_metrics)
                dpg.add_button(label="Open Debug", callback=open_debug)
                dpg.add_button(label="Open About", callback=open_about)
                dpg.add_separator()
                dpg.add_text("Node editor notes")
                dpg.add_text("• Drag between node attributes to create links.")
                dpg.add_text("• delink_callback lets you manage graph cleanup.")
                dpg.add_text("• Built-in debug windows help inspect complex applications.")


def build_level_seven_tab() -> None:
    with dpg.tab(label="Level 7 · Handlers and File Dialog"):
        dpg.add_text("Event handlers and dialogs make apps feel like full desktop tools.")
        dpg.add_separator()

        with dpg.group(horizontal=True):
            with dpg.child_window(width=520, height=520, border=True):
                tracked_button = dpg.add_button(label="Tracked button", width=180, callback=report_selection, user_data="Tracked button")
                dpg.add_spacer(height=8)
                dpg.add_text("Item handler: waiting for hover or click.", tag=ITEM_HANDLER_TEXT_TAG)
                dpg.add_spacer(height=12)
                dpg.add_text("Mouse position: --", tag=MOUSE_TEXT_TAG)
                dpg.add_text("Press any key while the viewport is focused to generate events.")

                with dpg.item_handler_registry(tag="tracked_button_handlers"):
                    dpg.add_item_hover_handler(callback=report_button_hover)
                    dpg.add_item_clicked_handler(callback=report_button_click)

                dpg.bind_item_handler_registry(tracked_button, "tracked_button_handlers")

            with dpg.child_window(width=520, height=520, border=True):
                dpg.add_button(label="Open file dialog", callback=open_file_dialog)
                dpg.add_spacer(height=8)
                dpg.add_input_text(
                    label="Selected files",
                    default_value="No file selected yet.",
                    multiline=True,
                    readonly=True,
                    width=490,
                    height=380,
                    tag=FILE_RESULT_TAG,
                )


def build_status_area() -> None:
    dpg.add_separator()
    with dpg.group(horizontal=True):
        with dpg.child_window(width=560, height=180, border=True):
            dpg.add_text("Status")
            dpg.add_input_text(
                default_value="Ready. Explore the tabs from beginner to expert.",
                readonly=True,
                multiline=True,
                width=530,
                height=120,
                tag=STATUS_TEXT_TAG,
            )

        with dpg.child_window(width=500, height=180, border=True):
            dpg.add_text("Event log")
            dpg.add_input_text(default_value="", readonly=True, multiline=True, width=470, height=120, tag=LOG_TEXT_TAG)


def build_file_dialog() -> None:
    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        callback=handle_file_selection,
        tag=FILE_DIALOG_TAG,
        width=760,
        height=480,
        modal=True,
    ):
        dpg.add_file_extension(".*")
        dpg.add_file_extension(".py", color=(86, 180, 211, 255))
        dpg.add_file_extension(".md", color=(253, 203, 110, 255))
        dpg.add_file_extension(".ks", color=(231, 111, 81, 255))


def build_global_handlers() -> None:
    with dpg.handler_registry():
        dpg.add_mouse_move_handler(callback=update_mouse_position)
        dpg.add_key_press_handler(callback=report_key_press)


def build_interface() -> None:
    build_themes()
    build_file_dialog()
    build_global_handlers()

    with dpg.window(tag=MAIN_WINDOW_TAG, label="DearPyGui Command Atlas", width=1120, height=960):
        build_menu_bar()

        dpg.add_text("DearPyGui Command Atlas")
        dpg.add_text("A single-file playground that moves from beginner widgets to expert tooling.")

        with dpg.collapsing_header(label="How to use this example", default_open=True):
            dpg.add_text("• Explore the tabs in order.")
            dpg.add_text("• Read the command summaries in each section.")
            dpg.add_text("• Interact with widgets and inspect the status log below.")
            dpg.add_text("• Open DearPyGui's built-in tools to study runtime behavior.")

        with dpg.tab_bar():
            build_level_one_tab()
            build_level_two_tab()
            build_level_three_tab()
            build_level_four_tab()
            build_level_five_tab()
            build_level_six_tab()
            build_level_seven_tab()

        build_status_area()


def initialize_demo_state() -> None:
    dpg.bind_theme("theme_ocean")
    dpg.bind_item_theme("main_window", "theme_ocean")
    dpg.add_node_link("node_output_a", "node_input_b", parent=NODE_EDITOR_TAG)
    dpg.add_node_link("node_output_b", "node_input_c", parent=NODE_EDITOR_TAG)
    randomize_telemetry()
    refresh_plot()
    set_status("DearPyGui Command Atlas initialized.")


def main() -> None:
    dpg.create_context()
    build_interface()

    dpg.create_viewport(title="DearPyGui Command Atlas", width=1180, height=1040)
    dpg.setup_dearpygui()
    initialize_demo_state()
    dpg.show_viewport()
    dpg.set_primary_window(MAIN_WINDOW_TAG, True)
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
