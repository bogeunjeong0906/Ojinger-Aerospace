---
name: python-execution-environment
description: "Choose and activate the correct Python environment before running Python scripts, tests, or one-off commands, or when Python execution fails with an import error such as ModuleNotFoundError or ImportError. Prefer a repo-local virtual environment first, then an already active global environment such as base."
argument-hint: "python command or target file"
user-invocable: true
---

# Python Execution Environment

Use this skill whenever TAS needs to run a Python script, test, module, or inline Python command.

Also use this skill when a Python run already failed with an import error and the failure may be caused by the wrong environment selection.

## Goals

- Make Python execution deterministic.
- Prefer the environment that belongs to the current repository.
- Fall back to an already active global environment only when no repo-local environment exists.
- Record which environment path was chosen when it affects reproducibility.
- Recover quickly from `ModuleNotFoundError`, `ImportError`, or similar package-resolution failures by re-checking environment choice first.

## Priority Order

1. Repo-local virtual environment in the repository root.
2. Already active global environment, including `base`.
3. A direct global Python executable only if neither of the above is available.

## Repo-Local Environment Detection

Check the repository root in this order:

1. `.venv`
2. `venv`
3. `env`
4. `.conda`
5. `conda`

Treat a candidate as valid only when it has environment markers.

- For `venv` or `virtualenv`, look for `pyvenv.cfg` and the interpreter under `bin/python` on POSIX.
- For conda, look for `conda-meta/` in the environment prefix.

## Activation Rules

- If a valid repo-local conda environment exists, activate it with `conda activate <path>`.
- If a valid repo-local `venv` or `virtualenv` exists, activate it with `source <path>/bin/activate` on POSIX shells.
- If no repo-local environment exists but `VIRTUAL_ENV` or `CONDA_DEFAULT_ENV` is already set, reuse that active environment.
- If the active conda environment is `base`, it is an acceptable second-priority fallback.
- If no activation mechanism is available, run the environment's Python executable directly and note that activation was skipped.

## Import Error Recovery

- If Python execution fails with `ModuleNotFoundError`, `ImportError`, or an obviously missing installed package, re-run environment detection before assuming the dependency is absent.
- Prefer switching from a global environment to a repo-local environment when one exists.
- If already using the repo-local environment, only then treat the error as a likely missing dependency or broken installation.
- Record whether the issue was caused by wrong environment selection or by a genuinely missing package when that distinction matters.

## Tool Preference

- When Python environment tools are available, prefer them over ad-hoc shell guessing.
- If the task requires a terminal command, activate the chosen environment in the same shell session before running Python.
- Do not silently switch away from a repo-local environment to a global environment.

## Validation

- Confirm that the chosen interpreter belongs to the intended environment before running important commands.
- If execution output depends on packages from the chosen environment, record which environment was used in the active artifact or summary.

## Fallback Notes

- Repo-local environments are the default because they are most likely to match the repository's dependencies.
- Global environments are fallback-only because they are less reproducible across machines.
- If no suitable environment exists, state that Python ran without a repo-local environment.
