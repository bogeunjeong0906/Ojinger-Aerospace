# KSP 1-axis control tower runbook

_Last updated: 2026-03-10_

## 1. Current implemented scope

This runbook describes the currently implemented developer/operator path:

- headless control tower bootstrap and mock mission cycle
- stable JSON contracts plus golden fixtures
- offline `parameter_export -> optimization_request -> flight_plan` generation
- mock/live telemetry adapter layer and supervisor state tracking
- onboard kOS scripts for parameter export and a manual-arm controller skeleton

Current confidence is highest for offline/headless runs. The workspace test baseline is:

- `pytest tests -q` -> 13 passed

## 2. Entry points

### Control tower

Use the local environment Python interpreter and run one of these modes:

- bootstrap only:
  - `python -m system.control_tower.main --mode headless --json`
- mock/headless mission cycle:
  - `python -m system.control_tower.main --action mission-cycle --mode headless --artifacts-dir <dir> --monitor-steps 6 --json`
- optional live bootstrap attempt:
  - `python -m system.control_tower.main --mode headless --connect-live --json`

Notes:

- `--connect-live` only attempts kRPC bootstrap. It does not upload files to KSP or arm the vessel.
- `ui` and `auto` modes are scaffolded only. Headless remains the supported operating path.

### Onboard kOS

Available scripts under `system/vessle/`:

- `export_prams.ks`: emits a contract-shaped `parameter_export.json`
- `controler_1axis.ks`: reads a `flight_plan.json`, waits for manual arming, then applies simple throttle/steering control

## 3. Mock/headless mission cycle

Recommended developer validation path:

1. Run tests.
2. Run the control tower mission cycle in headless mode.
3. Inspect the written artifacts.
4. Confirm the final report reaches `completed` in mock mode.

The mission workflow currently performs these phases:

1. load or synthesize `parameter_export`
2. build `optimization_request`
3. solve `flight_plan` with the CasADi 1-axis optimizer
4. write an `armed` copy of the plan
5. record an abstract dispatch record
6. poll telemetry through the supervisor using mock samples unless live kRPC connected

## 4. File contracts and artifacts

### Stable contracts

Canonical contract definitions and fixtures live in `system/control_tower/backend/contracts/`.

Contracts:

- `parameter_export`
- `optimization_request`
- `flight_plan`
- `telemetry_snapshot`

Golden fixtures:

- `system/control_tower/backend/contracts/fixtures/parameter_export.sample.json`
- `system/control_tower/backend/contracts/fixtures/optimization_request.sample.json`
- `system/control_tower/backend/contracts/fixtures/flight_plan.sample.json`
- `system/control_tower/backend/contracts/fixtures/telemetry_snapshot.sample.json`

### Mission-cycle artifact set

A mission-cycle run writes one directory per `plan_id` under the supplied `--artifacts-dir`, or under `artifacts/control_tower/<plan_id>/` by default.

Expected files:

- `parameter_export.json`: exported or fixture-backed vehicle snapshot
- `optimization_request.json`: normalized optimizer request derived from the export
- `flight_plan.optimized.json`: validated optimized plan with status `optimized`
- `flight_plan.armed.json`: dispatch-ready copy with status `armed`
- `dispatch_record.json`: abstract file-handoff record only
- `telemetry_history.json`: supervisor polling history for the run
- `mission_cycle_report.json`: top-level summary, transitions, warnings, and errors

### Current contract ownership

- tower/offline side produces and validates all four contracts
- kOS exporter produces `parameter_export`
- kOS controller consumes `flight_plan`
- live KSP telemetry is expected to normalize into `telemetry_snapshot`

## 5. Planned live KSP steps

These are the intended live steps for the next integration pass. They are not yet fully automated.

1. Start KSP with kRPC and kOS available.
2. Confirm the kRPC server is listening on the configured address/ports.
3. Place or expose a writable kOS volume/file path for JSON exchange.
4. In kOS, run `export_prams.ks` to write `parameter_export.json`.
5. Copy the export JSON to the host-side workspace or artifact directory.
6. Run the control tower mission cycle or optimizer path on the host.
7. Copy the generated `flight_plan.armed.json` into the vessel-accessible kOS path, typically renamed to `flight_plan.json`.
8. In kOS, run `controler_1axis.ks` against that plan file.
9. Manually arm and stage the vehicle.
10. Observe console/log output and abort manually if the vehicle diverges.

Until the live path is verified, treat all host-to-vessel file movement as a manual operator step.

## 6. Manual arming expectations

`controler_1axis.ks` is intentionally conservative.

Expected behavior:

- boot state is `idle`
- controller waits for the plan file to exist
- after successful `READJSON`, state becomes `holding`
- default `arm_mode` is `manual_confirm`
- operator should leave AG1 OFF at least once after plan load so the script can mark itself arm-ready
- operator turns AG1 ON to transition into active control
- operator remains responsible for staging/liftoff timing
- the kOS `ABORT` action group cancels the run and forces safe idle

Optional behavior:

- `auto_arm` parameter can bypass manual arming for experiments
- steering defaults to `vertical_hold`
- `pitch_program` is only a simple constant target-pitch mode, not a full guidance program

## 7. Known limitations

- headless/mock flow is the only verified end-to-end workflow
- dispatch is an abstract JSON record; no automatic copy/upload to kOS volume exists yet
- live kRPC connection is optional and soft-gated; runtime success depends on local game/mod state
- DearPyGui UI is scaffold-only and not an operational control surface yet
- onboard controller validation is still limited to code review and contract assumptions, not real-flight evidence
- controller logging and state handling exist, but no automated replay or HIL validation exists yet
- the optimizer uses a simplified vertical 1D model and should be treated as a planning baseline, not final flight truth
- supervisor terminal states are driven by simplified telemetry/abort rules and mock samples
- no host-side workflow currently launches kOS scripts remotely or confirms file delivery/consumption

## 8. Minimum operator safety checklist

Before any live attempt:

- verify the generated plan belongs to the intended vessel and stage setup
- verify abort thresholds in the plan are sane for the vehicle
- confirm AG1 and ABORT bindings are understood before liftoff
- keep throttle authority/operator override available
- keep the first live attempt to a low-risk vertical ascent only
- preserve all generated JSON and controller log files for post-run review
