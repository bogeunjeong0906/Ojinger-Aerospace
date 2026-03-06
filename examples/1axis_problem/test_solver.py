import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import solver

def test_basic():
    sol,X,U,T = solver.solve_rocket_ocp(target=500, N=20)
    # final velocity should be ~0
    v_final = float(sol.value(X[1,-1]))
    assert abs(v_final) < 1e-3, f"final velocity nonzero: {v_final}"
    # positions should reach target
    x_final = float(sol.value(X[0,-1]))
    assert abs(x_final - 500) < 1e-2

if __name__ == '__main__':
    test_basic()
    print('solver test passed')