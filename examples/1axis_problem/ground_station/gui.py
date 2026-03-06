import dearpygui.dearpygui as dpg
import numpy as np
from solver import solve_rocket_ocp

# global storage for last solution
_last_sol = None


def run_solver_callback(sender, data):
    global _last_sol
    target = dpg.get_value("target_input")
    umax = dpg.get_value("umax_input")
    N = int(dpg.get_value("n_input"))
    sol, X, U, T = solve_rocket_ocp(target=target, umax=umax, N=N)
    _last_sol = (sol, X, U, T)
    plot_solution(sol, X, U, T)
    dpg.log_info(f"Solved OCP: T={sol.value(T):.2f}")


def plot_solution(sol, X, U, T):
    tvals = np.linspace(0, sol.value(T), X.shape[1])
    xvals = np.array(sol.value(X[0,:])).flatten()
    vvals = np.array(sol.value(X[1,:])).flatten()
    uvals = np.array(sol.value(U)).flatten()
    # create or update plots
    if not dpg.does_item_exist("trajectory_plot"):
        with dpg.plot(label="States", height=300, tag="trajectory_plot"):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="t")
            dpg.add_plot_axis(dpg.mvYAxis, label="value", tag="traj_y")
    # clear existing series by deleting children
    for child in dpg.get_item_children("traj_y", 1) or []:
        dpg.delete_item(child)
    dpg.add_line_series(tvals, xvals, label="position", parent="traj_y")
    dpg.add_line_series(tvals, vvals, label="velocity", parent="traj_y")
    if not dpg.does_item_exist("control_plot"):
        with dpg.plot(label="Control", height=200, tag="control_plot"):
            dpg.add_plot_axis(dpg.mvXAxis, label="t")
            dpg.add_plot_axis(dpg.mvYAxis, label="thrust", tag="ctrl_y")
    for child in dpg.get_item_children("ctrl_y", 1) or []:
        dpg.delete_item(child)
    dpg.add_line_series(tvals[:-1], uvals, label="thrust", parent="ctrl_y")


def send_to_ksp_callback(sender, data):
    # placeholder for KRPC interface
    if _last_sol is None:
        dpg.log_error("No solution to send")
        return
    try:
        import krpc
        conn = krpc.connect(name='1axis control')
        vessel = conn.space_center.active_vessel
        sol, X, U, T = _last_sol
        thrusts = list(np.array(sol.value(U)).flatten())
        dpg.log_info(f"Sent {len(thrusts)} thrust points to KSP vessel")
    except Exception as e:
        dpg.log_error(f"KSP send failed: {e}")


def main():
    dpg.create_context()
    with dpg.window(label="Rocket Control Ground Station", tag="main_window"):
        dpg.add_input_float(label="Target (m)", default_value=1000.0, tag="target_input")
        dpg.add_input_float(label="Max thrust (m/s^2)", default_value=20.0, tag="umax_input")
        dpg.add_input_int(label="Discretization N", default_value=100, tag="n_input")
        dpg.add_button(label="Run solver", callback=run_solver_callback)
        dpg.add_button(label="Send to KSP", callback=send_to_ksp_callback)
        dpg.add_logger(tag="log")
    dpg.create_viewport(title="Rocket Control GS", width=800, height=600)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == '__main__':
    main()