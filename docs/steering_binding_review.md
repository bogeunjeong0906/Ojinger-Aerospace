# Steering/Throttle Binding for KSP Vessel Control — Review

## Executive Summary
This review evaluates the proposed control abstraction: binding each controllable part in Kerbal Space Program (KSP) to high-level controls (roll, pitch, yaw, throttle) and driving the vessel only via `steering` and `throttle` from kOS scripts. Aligned with the `mission_target_spec` target model, the steering/throttle-only interface simplifies common flight tasks, reduces actuator-level complexity, and enables compact autopilots. However, it is insufficient for coordinated low-level actions (precision translation, asymmetric-engine management, complex RCS burns). The report provides mapping guidance, control architecture options, failure modes, implementation recommendations, a minimal bridging API, example kOS pseudocode, JSON mapping sample, and a testing plan.

## Background & Assumptions
- References: the `mission_target_spec` (docs/mission_target_spec.md) is assumed to define a `TargetState` or trajectory model describing desired position, velocity, attitude, and timing constraints.
- Assumptions:
  - Vessel has SAS, reaction wheels, RCS, and engines with possible gimbals.
  - kOS can set `steering` (3-axis normalized: roll/pitch/yaw) and scalar `throttle`, and toggle auxiliary systems (RCS, SAS, staging).
  - `TargetState` provides at least: desired attitude (quaternion or Euler), desired translational velocity/position, desired acceleration, and optional throttle or thrust-setpoint.
- Goal: map `TargetState` -> {steering, throttle, aux_flags} without direct per-actuator commands.

## Mapping from Target Model to Steering/Throttle
- Core principle: convert high-level errors in the vessel frame to normalized attitude commands and a scalar throttle:
  - Attitude error (Target.attitude vs vessel.attitude) -> normalized `steering` vector representing commanded roll/pitch/yaw torque demand.
  - Translational requests (Target.velocity/position/accel) -> compute required acceleration along body thrust axis and convert to `throttle` by dividing required thrust by current available thrust (accounting for mass).
- Representations in `TargetState`:
  - `attitude`: quaternion + `attitude_mode` (attitude-only vs translation-aligned).
  - `translational_goal`: object with `type` ("velocity", "position", "acceleration"), vector and reference frame.
  - `thrust_hint` (optional): desired thrust fraction or desired delta-v budget.
  - `tolerance` fields for attitude and position control.

## Control Architecture Options
- Open‑loop
  - Use for scripted trajectory playback with deterministic actuators (rarely robust).
  - Simple mapping: set `steering` from precomputed attitude schedule and `throttle` per precomputed thrust profile.
- PID (single-loop attitude & throttle)
  - Attitude PID: compute error axis-angle -> PID -> steering vector. Use yaw as separate loop or combine to 3-axis PID.
  - Throttle PID: target vertical/axial acceleration -> throttle adjustment based on mass & ISP model.
  - Best for typical ascent and cruise.
- Cascaded control
  - Outer loop: trajectory/velocity error -> desired attitude and thrust setpoint.
  - Inner loop: attitude PID (fast) implemented via `steering`, throttle PID (slower).
  - Preferred for robust flight (handles disturbances).
- Model Predictive Control (MPC)
  - Numerically optimize control sequence (steering + throttle) over horizon using vessel model (mass, thrust curve, gimbal limits).
  - Useful for precise burns, gravity-turn optimization, or constrained maneuvers.
  - Cost: computational complexity; may be heavy for kOS on-board.

## Advantages
- Simplifies control logic: single unified interface for attitude and thrust.
- Engine-agnostic: autopilot generalizes across vessel designs.
- Easier to implement and reason about in higher-level mission planners.
- Fits well with `mission_target_spec` when targets are attitude/trajectory-centric.

## Limitations and Failure Modes
- Loss of per-actuator granularity:
  - Cannot coordinate asymmetric engine failures (must detect and escalate to direct actuator control).
  - Fine translational translation (docking using RCS thrusters in translation-only axis) requires direct RCS impulse control.
- Fuel-thrust asymmetries:
  - Varying engine output, throttling capability and staging cause inaccurate thrust estimation unless modeled.
- Gimbal/RCS vs reaction wheels:
  - Reaction wheels provide torque without changing thrust; gimbals change thrust vector and affect translational forces. Steering mixes these effects implicitly—must model available torque vs thrust coupling.
- Staging & discrete thrust events:
  - Discrete staging (engines that start/stop or solid rockets) cannot be smoothly represented by throttle; must use `staging` aux flag and scheduling.

## Implementation Recommendations
- Binding rules:
  - Bind `steering` to attitude control only; do not use `steering` to command lateral translation. Keep `throttle` as propulsion scalar along main thrust vector.
  - Create vessel capability metadata: `max_thrust`, `thrust_vector_offset`, `gimbal_limits`, `rcs_available`, `reaction_wheels_torque`.
- Frame considerations:
  - Maintain all `TargetState` entries with explicit reference frames (vessel-body, inertial, surface). Convert externally before mapping.
  - Use body-frame axial thrust assumption: throttle produces acceleration along the current net thrust axis; account for off-center thrust by adding moment compensation via steering.
- Latency compensation:
  - Implement feedforward terms: predict vessel state after command latency and compute steering/throttle to correct predicted error.
  - Use actuator response models (engine spool-up time, SAS reaction) in inner-loop controllers.
- Safety fallbacks:
  - Monitor yaw/pitch/roll rates, g forces, structural stress, and engine health.
  - If asymmetric thrust or actuator fault detected, escalate to direct actuator control or enable RCS translation mode.
  - Define `safe_mode` that reduces throttle and attempts controlled attitude hold.

## When Steering/Throttle Abstraction Is Insufficient
- Coordinated multi-engine asymmetry handling (failed engine requiring per-engine throttle trim).
- Precision translation/docking where lateral RCS impulses are needed.
- Complex RCS burn sequences that require specific thruster groups.
- Emergency control where engine vectoring is needed to counteract off-axis torque.

## Minimal Bridging API Design
Signature:
- `map_target_to_control(target: TargetState, vessel_state: VesselState) -> ControlCommand`
Where:
- `ControlCommand = {steering: [roll, pitch, yaw], throttle: float, aux_flags: AuxFlags}`
- AuxFlags example:
  - `rcs_on`: bool
  - `staging`: "none" | "stage_now" | "schedule_at_T+..."
  - `gimbal_mode`: "auto" | "disabled" | "limit:<deg>"
  - `sas_mode`: "stability" | "off" | "prograde" | "retrograde"
  - `engine_trim`: float (for coarse per-side trim)
  - `abort`: bool

Behavior:
- `map_target_to_control` should detect when abstraction cannot satisfy the `TargetState` and either return an `aux_flags.abort` or `aux_flags.require_direct_control` with diagnostics.

## Example kOS Pseudocode (<=20 lines)
```kos
// compute steering & throttle from mapped command
function applyControl(cmd) {
  set steering to cmd.steering.
  set throttle to cmd.throttle.
  if (cmd.aux_flags.rcs_on) { set rcson on. } else { set rcson off. }
  if (cmd.aux_flags.staging = "stage_now") { stage. }
  if (cmd.aux_flags.gimbal_mode = "disabled") { togglegimbal(false). }
}
```

## Example JSON (mapped target -> steering+throttle)
```json
{
  "target_id": "burn_123",
  "target_summary": {"type":"prograde_burn","delta_v":250.0},
  "mapped_command": {
    "steering": [0.0, 0.007, -0.002],
    "throttle": 0.62,
    "aux_flags": {
      "rcs_on": false,
      "staging": "none",
      "gimbal_mode": "auto",
      "sas_mode": "stability"
    }
  }
}
```

## Testing & Validation Plan
- Unit tests:
  - Validate `map_target_to_control` for attitude-only targets vs full-6DOF targets.
  - Simulate mass variation and engine-thrust-table to verify throttle conversion.
- Integration tests in KSP:
  - Ascent profile: run cascaded controller; verify trajectory tolerance.
  - Simulate engine-out: introduce asymmetric thrust and detect escalation behavior.
  - Docking test: verify that translation-only targets trigger direct-RCS-required flag.
- Validation metrics:
  - Attitude error RMS, positional error at burn completion, overshoot, fuel usage deviation from expected.
- Hardware-in-the-loop-like: run on representative vessel designs to capture gimbal/offset effects.

## Recommended Next Steps
- Implement `vessel_capabilities` metadata and extend `mission_target_spec` with `thrust_hint`, `attitude_mode`, and `tolerance`.
- Prototype `map_target_to_control` with cascaded PID (outer velocity -> inner attitude PID) and test in-sim.
- Add fault detection hooks to transition to actuator-level control automatically.
- If precision burns or coordinated trims are frequent, plan for a fallback interface to expose per-actuator commands.

Task ID: task_review_steering_binding_009
