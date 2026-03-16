"""Simple 1-axis (vertical) trajectory/throttle solver.

This module provides a lightweight `OneAxisSolver` class which can be
initialized from a parameter dictionary (as produced by `export.ks` ->
`vessel/params.json`). The solver implements a basic physics model and a
heuristic throttle controller to drive the vehicle to a target altitude.

The intent is not to be a full optimal-control solver yet, but to provide
a well-documented, testable starting point that extracts required
parameters from `params.json`, performs system modeling, and returns a
time-series of throttle commands and a small summary.

Public API:
- OneAxisSolver(params_dict)
- solve(target_altitude, cost_weight=0.5, max_time=300.0, dt=0.5)

Notes on compatibility:
- `params_dict` is expected to follow the rough shape emitted by
  `src/vessel/export.ks`: fields like `mass`, `current_stage`, and
  `stages` (each with `thrust` and optionally `isp`) are used. If `isp`
  is not provided, a sensible default is used.
"""
from typing import Dict, Any, List


class OneAxisSolver:
    """One-axis vertical trajectory/throttle solver.

    The solver models vertical motion under gravity with thrust as the
    only control (scalar throttle in [0,1]). Mass decreases with fuel
    consumption using a simple rocket equation approximation: mdot =
    thrust / (Isp * g0).
    """

    G0 = 9.80665

    def __init__(self, params: Dict[str, Any]):
        """Parse params and build internal model.

        Args:
            params: Dictionary loaded from `vessel/params.json` (export.ks).
        """
        self.raw = params
        # Basic vehicle properties
        self.mass0 = float(params.get("mass", 0.0))
        self.current_stage = int(params.get("current_stage", 0))

        # Extract stage info if available
        stages = params.get("stages", []) or []
        stage_info = None
        if 0 <= self.current_stage < len(stages):
            stage_info = stages[self.current_stage]

        # Stage thrust (N) and initial fuel (kg) defaults
        self.max_thrust = float(stage_info.get("thrust", 0.0)) if stage_info else 0.0
        self.initial_stage_fuel = float(stage_info.get("fuel", 0.0)) if stage_info else 0.0

        # Specific impulse (s) — prefer explicit, otherwise sensible default
        self.isp = float(stage_info.get("isp", 300.0)) if stage_info else 300.0

        # Initial state (altitude m, velocity m/s)
        # export.ks does not currently provide altitude/velocity; default to 0
        self.alt0 = float(params.get("altitude", 0.0))
        self.vel0 = float(params.get("velocity", 0.0))

    def _dynamics_step(self, mass: float, throttle: float) -> Dict[str, float]:
        """Compute acceleration and mass flow for given mass & throttle."""
        thrust = max(0.0, min(1.0, throttle)) * self.max_thrust
        # mass flow (kg/s)
        mdot = 0.0
        if self.isp > 0 and self.G0 > 0:
            mdot = thrust / (self.isp * self.G0)
        # acceleration (m/s^2): a = (thrust / mass) - g
        a = (thrust / mass) - self.G0
        return {"acc": a, "mdot": mdot, "thrust": thrust}

    def simulate(self, throttle_profile: List[float], max_time: float, dt: float):
        """Forward integrate dynamics given a throttle profile.

        Returns a dict containing time-series arrays.
        """
        times: List[float] = []
        alts: List[float] = []
        vels: List[float] = []
        ths: List[float] = []

        mass = self.mass0
        alt = self.alt0
        vel = self.vel0
        fuel = self.initial_stage_fuel

        t = 0.0
        steps = int(max_time / dt)
        for i in range(steps):
            throttle = throttle_profile[i] if i < len(throttle_profile) else throttle_profile[-1]
            dyn = self._dynamics_step(mass, throttle)
            acc = dyn["acc"]
            mdot = dyn["mdot"]

            # integrate
            vel = vel + acc * dt
            alt = alt + vel * dt

            # fuel consumption
            df = mdot * dt
            fuel = max(0.0, fuel - df)
            mass = max(1e-3, mass - df)

            times.append(t)
            alts.append(alt)
            vels.append(vel)
            ths.append(throttle)

            t += dt

        return {"time": times, "altitude": alts, "velocity": vels, "throttle": ths, "fuel_remaining": fuel}

    def solve(self, target_altitude: float, cost_weight: float = 0.5, max_time: float = 300.0, dt: float = 0.5):
        """Heuristic solver: runs a simple feedback throttle controller.

        Args:
            target_altitude: target altitude in meters.
            cost_weight: 0..1 weight blending fuel vs time (1.0 => fuel-only).
            max_time: simulation horizon (s).
            dt: integration timestep (s).

        Returns:
            dict with keys: `time`, `altitude`, `velocity`, `throttle`, `fuel_used`, `time_to_goal`, `cost`, `success`.
        """
        # controller gains (tunable)
        kp = 0.005
        kd = 0.15

        mass = self.mass0
        alt = self.alt0
        vel = self.vel0
        fuel = self.initial_stage_fuel
        initial_fuel = fuel

        times = []
        alts = []
        vels = []
        ths = []

        t = 0.0
        reached = False
        for _ in range(int(max_time / dt)):
            # altitude and velocity errors
            e_alt = target_altitude - alt
            # desired acceleration from PD law
            a_des = kp * e_alt - kd * vel

            # compute required thrust to achieve a_des (include gravity)
            thrust_req = max(0.0, (a_des + self.G0) * mass)
            throttle = 0.0
            if self.max_thrust > 0:
                throttle = max(0.0, min(1.0, thrust_req / self.max_thrust))

            dyn = self._dynamics_step(mass, throttle)
            acc = dyn["acc"]
            mdot = dyn["mdot"]

            # integrate
            vel = vel + acc * dt
            alt = alt + vel * dt

            # consume fuel
            df = mdot * dt
            fuel = max(0.0, fuel - df)
            mass = max(1e-3, mass - df)

            times.append(t)
            alts.append(alt)
            vels.append(vel)
            ths.append(throttle)

            t += dt

            # goal check: near target altitude and near zero velocity
            if abs(e_alt) < 1.0 and abs(vel) < 0.5:
                reached = True
                break

            # out-of-fuel stop
            if fuel <= 0 and self.max_thrust <= 0:
                break

        time_to_goal = t
        fuel_used = initial_fuel - fuel

        # cost: normalized time and fuel
        fuel_term = (fuel_used / initial_fuel) if initial_fuel > 0 else 0.0
        time_term = min(time_to_goal / max_time, 1.0)
        cost = cost_weight * fuel_term + (1.0 - cost_weight) * time_term

        return {
            "time": times,
            "altitude": alts,
            "velocity": vels,
            "throttle": ths,
            "fuel_used": fuel_used,
            "time_to_goal": time_to_goal,
            "cost": cost,
            "success": reached,
        }


def compute_trajectory(params: Dict[str, Any], target_altitude: float = None) -> Dict[str, Any]:
    """Backward-compatible compute entrypoint.

    Args:
        params: solver parameters dictionary.
        target_altitude: explicit target altitude override in meters. If
            not provided, falls back to `params['target_altitude']` or
            a default of 1000.0 m.

    Returns:
        Solver result dictionary (delegates to `OneAxisSolver.solve`).
    """
    solver = OneAxisSolver(params)
    # prefer explicit argument, otherwise fall back to params or default
    used_target = target_altitude if target_altitude is not None else params.get("target_altitude", 1000.0)
    result = solver.solve(target_altitude=used_target, cost_weight=0.5)
    # expose what target was actually used (helpful for testing and introspection)
    result["target_altitude_used"] = used_target
    return result

