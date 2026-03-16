# Architecture ↔ Files Alignment Report

Date: 2026-03-16

## Overview
This report analyzes how the repository's documented architecture (file: `architecture_map.md`) maps to the actual files in the workspace. It summarizes matches, highlights mismatches with severity, and provides concrete recommendations to align documentation and implementation.

## Sources inspected
- `architecture_map.md`
- `main.py`
- `src/control_tower/ui.py`
- `docs/mission_target_spec.md`
- `docs/steering_binding_review.md`
- `environment.yaml`

## Summary — key findings
- Partial match: The project contains a functioning UI implementation (`src/control_tower/ui.py`) and a runnable entrypoint (`main.py`) that imports from `src`. Documentation in `docs/` (mission target spec and steering review) is present and consistent with design intent.
- Major mismatch: `architecture_map.md` documents a top-level `control_tower/` directory with `ui.py`, `manager.py`, and `engine.py` as peer files, and shows `vessel/export.ks` and `params.json` interactions. The workspace does not contain these top-level `control_tower/*.py` files or the `vessel/export.ks` file at the expected paths — instead, UI lives under `src/control_tower/` and kOS scripts are not present at the expected vessel path.

## Detailed mapping

- Documented: `control_tower/ui.py` (top-level)  
  Actual: `src/control_tower/ui.py` — IMPLEMENTED (UI class present).  
  Severity: Low (file exists but under `src/` package). Recommendation: update `architecture_map.md` to reference `src/control_tower/ui.py` or add a top-level wrapper to preserve the documented layout.

- Documented: `control_tower/manager.py`, `control_tower/engine.py`  
  Actual: Not found at `/control_tower/manager.py` or `/control_tower/engine.py`. No equivalent modules were detected under `src/control_tower/` other than `ui.py`.  
  Severity: High (missing components referenced in architecture). Recommendation: either (A) restore the missing modules, (B) update the architecture diagram and documentation to reflect current design (e.g., move conceptual manager/engine roles into `src/control_tower/*` modules and document their absence/presence), or (C) create lightweight stubs that re-export behavior from new locations.

- Documented: `vessel/export.ks` and `params.json` interaction  
  Actual: `vessel/export.ks` not found at expected path. No `params.json` producer in repository root was detected.  
  Severity: Medium (kOS artifacts and I/O paths are part of the deployment flow). Recommendation: add a `vessel/` folder with `export.ks` (or update architecture to point to actual kOS script locations), and document where `params.json` is written/read in the current layout.

- Documented: `main.py` entrypoint interacting with `ControlTowerUI`  
  Actual: `main.py` exists at project root and imports `src/control_tower.ui.ControlTowerUI` — IMPLEMENTED and consistent.  
  Severity: None.

- Documented: `docs/*` references and mission target model  
  Actual: `docs/mission_target_spec.md` and `docs/steering_binding_review.md` present — IMPLEMENTED and consistent with the mission planning design.  
  Severity: None.

## Risk & Impact Assessment
- Missing manager/engine modules: If the architecture expects an optimization engine and a manager hub (for scheduling and planning), their absence is a functional gap — either the functionality was not implemented yet, or it moved to a different module. Impact: medium-to-high for features depending on automated planning.
- Mismatched paths: Documentation referencing top-level scripts while code lives under `src/` can confuse new contributors and automated tooling (CI, packaging). Impact: low-to-medium.
- Missing kOS scripts: If mission deployment relies on kOS scripts (`export.ks`), their absence prevents the end-to-end workflow demonstrated in the architecture diagram. Impact: medium for mission export/test workflows.

## Recommendations (concrete)
1. Short-term (documentation-only, low effort)
   - Update `architecture_map.md` to reflect `src/` package layout (replace `control_tower/` references with `src/control_tower/`). This will remove confusion for contributors and align the diagram with `main.py` behavior.

2. Short-term (developer ergonomics)
   - Add a `control_tower/__init__.py` at project root that re-exports `src/control_tower` APIs (or add a thin top-level `control_tower/` package) if the documented layout must be preserved for existing scripts or developer expectations. Example content:
     ```python
     # control_tower/__init__.py (thin shim)
     from src.control_tower.ui import ControlTowerUI
     __all__ = ["ControlTowerUI"]
     ```
   - Or update `main.py` import paths and `architecture_map.md` to be consistent — prefer updating docs to `src/` if `src/` is intended layout.

3. Mid-term (feature parity)
   - If `manager.py` and `engine.py` are planned features, either add them under `src/control_tower/` or document where their responsibilities currently live. If code exists under different names, add cross-references in `architecture_map.md`.

4. kOS workflow
   - Restore or add `vessel/export.ks` and clarify `params.json` path. If kOS scripts live out-of-repo (e.g., in a player-side KSP save), add a README section describing deployment steps and expected file locations.

5. CI & onboarding
   - Add a short `CONTRIBUTING.md` or README update noting the canonical import path (`src/`) and mapping to the architecture diagram.

## Suggested Quick Patches
- Patch A: update `architecture_map.md` node labels to `src/control_tower/ui.py` and note `manager/engine` status as "planned" or point to existing modules.
- Patch B: add a top-level `control_tower/__init__.py` shim if preserving the original documented layout is preferable.

## Next Steps (proposed)
1. Confirm intended canonical layout with maintainers: `src/`-first (current) vs top-level package (documented).  
2. Apply either Patch A (documentation update) or Patch B (shim) as agreed.  
3. If planning features exist for `manager`/`engine`, open issues or add TODOs mapping responsibilities and required interfaces.  

---
If you want, I can (pick one):
- implement Patch A and update `architecture_map.md` to reflect `src/` paths, or
- create a top-level `control_tower/__init__.py` shim (Patch B), or
- create skeletons for `manager.py` and `engine.py` under `src/control_tower/` with TODO stubs.
