# Target Formats for 6‑DOF Spacecraft Planning & Control

## Executive Summary
This document defines a concrete, engineering‑grade target data model and conventions for planning and controlling a KSP‑like 6‑DOF spacecraft across changing reference frames (planetary transfers, body‑relative operations, surface/local frames). The goal is a clear, minimal schema and practical guidance for interpolation, transforms, error metrics, uncertainty handling, and safe runtime behavior for real‑time control systems.

## Motivation
Games and simulators with multi‑body dynamics require robust, unambiguous target representations that survive frame switches (inertial ↔ body ↔ surface). Ambiguity in units, quaternion ordering, or frame identifiers causes subtle failures in guidance and rendezvous. A compact, extendable model reduces integration bugs and supports deterministic control.

## Design Goals
- Unambiguous: explicit units, timestamp format, quaternion ordering, coordinate handedness.
- Composable: support both single‑state (instant) and time‑parameterized (trajectory) targets.
- Robust to frame switches: canonical `frame_id` rules and recommended transform timing.
- Practical: small payloads, easy interpolation (pos/orient), and explicit uncertainty/covariance support.
- Safe: built‑in checks for staleness, covariance thresholds, and fallback behaviors.

## Recommended Target Data Model
Top‑level target object fields (types and units):

- `target_id` (string): unique identifier for the target.
- `type` (enum): `"instant"` or `"trajectory"`.
- `reference_frame` (string): canonical frame id (see Frame ID Rule).
- `timestamp` (string, ISO8601 UTC): issuance or sample time (fractional seconds allowed).
- `samples` (array[TargetState]) optional: for `trajectory` targets, time‑ordered.
- `state` (TargetState) optional: for `instant` targets.
- `interpolation` (enum): `"hold" | "linear" | "cubic" | "slerp" | "squad"`.
- `source` (string): origin of target (planner, pilot, user).
- `covariance` (optional): 6x6 covariance matrix mapping (pos,vel,orient,angvel) in the `reference_frame`.
- `metadata` (object) optional: human or system notes.

Unit conventions for fields inside `TargetState`:
- `position`: meters (m)
- `velocity`: meters per second (m/s)
- `orientation`: quaternion [w, x, y, z] (unitless)
- `angular_velocity`: radians per second (rad/s)
- `time`: ISO8601 UTC string
- `acceleration` (optional): m/s^2

Coordinate handedness: right‑handed, Cartesian (X,Y,Z). Clearly document frame axes for each `reference_frame` entry.

### Field Types: `TargetState` (concept)
- `time` (ISO8601 string)
- `position` (3‑tuple float, m)
- `velocity` (3‑tuple float, m/s)
- `orientation` (4‑tuple float, quaternion [w,x,y,z])
- `angular_velocity` (3‑tuple float, rad/s)
- `acceleration` (3‑tuple float, m/s^2) optional

## Frame and Transform Conventions
- Use canonical `frame_id` tokens with deterministic rules (see Frame ID Rule).
- All target samples must include `reference_frame`; if omitted, system rejects the target.
- Transform operations must indicate the source frame and target frame; transforms are applied using the most recent pose of intermediate frames at the requested `time`.
- Coordinate handedness: right‑handed across all frames.
- Quaternion ordering: scalar‑first `[w, x, y, z]`. Normalized quaternions only.
- Timestamp format: ISO8601 UTC with fractional seconds, e.g. `2026-03-13T12:34:56.789Z`. Systems may also store epoch seconds internally for performance.
- Frame ID Rule (recommended):
  - Format: `<SCOPE>:<BODY>:<DETAIL>` where:
    - `<SCOPE>` ∈ {`INERTIAL`, `BODY`, `SURFACE`, `RELATIVE`}
    - `<BODY>` = canonical body name (e.g., `Kerbin`, `Mun`, `VESSEL-<uuid>`)
    - `<DETAIL>` optional (e.g., `LATLON:lat,lon` or `NODE:<node_id>`)
  - Examples: `INERTIAL:Kerbin`, `BODY:VESSEL-1234`, `SURFACE:Kerbin:LATLON:34.12,-118.4`, `RELATIVE:VESSEL-1234:TARGET-AB`.

## Trajectory vs Instant Targets
- `instant`: single desired state at time `t` (common for hold or manual setpoint).
- `trajectory`: time‑parameterized sequence of `TargetState` samples used by a planner. Samples must be strictly time‑ordered. Trajectories are authoritative for the times they cover; outside that interval the controller may hold or extrapolate according to `interpolation`.

## Interpolation Methods
Position:
- `linear`: piecewise linear interpolation between samples (cheap, continuous pos).
- `cubic` / `hermite` / `bezier`: preserves smooth velocity and acceleration; use when feedforward accel matters.

Orientation:
- `slerp`: spherical linear interpolation between quaternions; preserves constant angular speed behavior.
- `squad` (spherical cubic): for smooth angular acceleration (recommended for docking maneuvers).

Velocity/Angular velocity:
- Interpolate velocities linearly or with cubic splines consistent with position/orientation interpolation to avoid jerk.

Interpolation recommendations:
- For low sample rates or large attitude changes, use `slerp` for orientation and cubic position splines with velocity constraints.
- Always interpolate to the control loop's commanded time (see Implementation Considerations).

## Error Definitions for Control
- Position error: e_p = p_target - p_actual (3×1 vector, meters).
- Velocity error: e_v = v_target - v_actual (3×1 vector, m/s).
- Orientation error: compute delta quaternion q_err = q_target * q_actual^{-1}; convert to angle‑axis or rotation vector: angle = 2 * acos(clamp(q_err.w, -1, 1)), axis = normalize(q_err.xyz).
  - Small‑angle approximation: orientation error vector ≈ 2 * q_err.xyz (radians).
- Angular velocity error: e_ω = ω_target - ω_actual (3×1 rad/s).
- Combined state error can be packaged as [e_p, e_v, e_θ, e_ω] with units (m, m/s, rad, rad/s).

## Uncertainty and Covariance
- Support optional 6×6 or 12×12 covariance aligned to state ordering (pos, vel, orient, angvel). Use SI units: position in m^2, velocity in (m/s)^2, orientation in rad^2.
- Provide `covariance` in the `reference_frame`. If covariance missing, controllers should treat the target as high‑uncertainty unless `source` is trusted.
- Use covariance to gate controller gains and safety checks (e.g., reduce approach speed if cross‑track uncertainty large).

## Example JSON Payloads

Time‑parameterized trajectory (abridged):
```json
{
  "target_id": "TRAJ-20260313-001",
  "type": "trajectory",
  "reference_frame": "INERTIAL:Kerbin",
  "interpolation": "cubic",
  "samples": [
    {
      "time": "2026-03-13T12:00:00.000Z",
      "position": [700000.0, 0.0, 0.0],
      "velocity": [0.0, 7600.0, 0.0],
      "orientation": [0.9999, 0.0, 0.0045, 0.0],
      "angular_velocity": [0.0, 0.0, 0.0001]
    },
    {
      "time": "2026-03-13T12:05:00.000Z",
      "position": [900000.0, 110000.0, -20000.0],
      "velocity": [100.0, 7400.0, 10.0],
      "orientation": [0.9996, 0.01, 0.01, 0.0],
      "angular_velocity": [0.0, 0.0, 0.0002]
    }
  ]
}
```

Single‑state instant target:
```json
{
  "target_id": "HOLD-BASE",
  "type": "instant",
  "reference_frame": "BODY:VESSEL-1234",
  "state": {
    "time": "2026-03-13T12:10:00.500Z",
    "position": [0.0, 0.0, 5.0],
    "velocity": [0.0, 0.0, 0.0],
    "orientation": [1.0, 0.0, 0.0, 0.0],
    "angular_velocity": [0.0, 0.0, 0.0]
  },
  "interpolation": "hold"
}
```

## Example Python dataclass
```python
from dataclasses import dataclass
from typing import Optional, Sequence, List, Tuple

Vector3 = Tuple[float, float, float]
Quat = Tuple[float, float, float, float]  # [w, x, y, z]

@dataclass
class TargetState:
    """A single 6-DOF state sample. Times are ISO8601 UTC strings."""
    time: str
    position: Vector3
    velocity: Vector3
    orientation: Quat
    angular_velocity: Vector3
    acceleration: Optional[Vector3] = None
```

## Implementation Considerations
- When to transform: perform frame transforms as late as possible, at the controller timestep, using the target's requested `time`. This avoids transform drift from stale intermediate frames.
- Measurement timing: timestamp all sensor reads and frame poses in ISO8601 or epoch seconds. Use the timestamp to interpolate both the target and the current state to the same temporal point before computing errors.
- Latency compensation: controllers should account for input latency by interpolating the target forward by expected control pipeline delay or using model‑predictive feedforward.
- Rendering to control loop: output control setpoints in the *actuator frame* (typically vehicle body frame) as pose (position/orientation) and twist (velocity/angular_velocity) with units matching the controller.
- Gravity fields: for planetary transfers, include gravity compensation in desired accelerations or use the planner to embed gravitational effects into the trajectory. For approximated maneuvers near bodies, compute gravity vector in the `reference_frame` and supply feedforward acceleration.
- Frame switching: when switching frames (e.g., INERTIAL → BODY), convert the active target into the new frame at the switch instant; if conversion not possible (missing transforms), reject switch.

## Safety and Fallback Strategies
- Staleness check: reject targets older than `max_age` (configurable). If stale, enter hold or safe‑stop mode.
- Covariance gating: if covariance trace > threshold, reduce approach velocity or abort rendezvous.
- Fallback targets: maintain a prioritized fallback stack (e.g., safe hover, coast, retroburn). On transform failure or frame ambiguity, switch to highest priority fallback.
- Soft limits: enforce velocity and acceleration bounds derived from vehicle capabilities and mission phase.
- Sanity checks: verify quaternion normalization and finite numeric values; reject or normalize before use.

## Practical Advice for KSP‑like Environments
- Use `RELATIVE` frames for rendezvous (e.g., RELATIVE:VESSEL‑A:VESSEL‑B) and express relative pose as the target; avoids global navigation errors during close ops.
- For transfers: plan trajectories in `INERTIAL` or patched conic inertial frames; at planetary approach, convert to `SURFACE` or `BODY` frames and replan locally.
- Surface operations: `SURFACE` frames should include a well‑defined origin (e.g., geodetic coordinates) and local up vector; specify whether altitudes are above mean radius or terrain.
- Planetary gravity: during low thrust or maneuver execution, include gravity in feedforward acceleration or let the guidance produce trajectory samples that implicitly contain gravitational dynamics.

## Appendix

**Recommended API endpoints / function signatures**
- `publish_target(target_json: dict) -> ack`
- `get_active_target(target_id: str) -> dict`
- `transform_state(state: TargetState, from_frame: str, to_frame: str, at_time: str) -> TargetState`
- `interpolate_trajectory(samples: List[TargetState], at_time: str, method: str) -> TargetState`
- `compute_state_error(target: TargetState, actual: TargetState) -> dict`

**References**
- ROS tf2 conventions (frames & transforms)
- Shoemake, K. "Quaternion Calculus for Animation" (quaternion interpolation concepts)
- Common guidance literature on state error representation (angle‑axis / quaternion delta)
- KSP modding references for body names and coordinate axes (project specific)

## Next Steps (recommended)
- 1) Implement `TargetState` serialization/parsing + canonical `frame_id` resolver in the flight stack.
- 2) Add `interpolate_trajectory` utilities (slerp, cubic pos spline) and unit tests with frame transform mocks.
- 3) Instrument control loop to compute errors at commanded time, including covariance gating and fallback behavior.
