import pytest

from src.control_tower.engine.solver_1axis_1 import compute_trajectory


def test_target_override():
    # minimal params to construct solver
    params = {
        "mass": 1000.0,
        "stages": [{"thrust": 20000.0, "fuel": 500.0, "isp": 300.0}],
        "current_stage": 0,
    }

    result = compute_trajectory(params, target_altitude=1234.5)
    assert result.get("target_altitude_used") == 1234.5
