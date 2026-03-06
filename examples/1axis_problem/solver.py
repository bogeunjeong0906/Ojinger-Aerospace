import casadi as ca
import numpy as np


def solve_rocket_ocp(target=1000, g=9.81, umax=20, N=100):
    opti = ca.Opti()
    # decision variables: x (position) and v (velocity)
    X = opti.variable(2, N+1)  # [x,v]
    U = opti.variable(1, N)
    T = opti.variable()  # final time
    dt = T/N
    # dynamics with simple acceleration u - g
    for k in range(N):
        xk = X[:,k]
        xk1 = X[:,k+1]
        uk = U[:,k]
        xdot = ca.vertcat(xk[1], uk - g)
        opti.subject_to(xk1 == xk + dt*xdot)
    # boundary conditions
    opti.subject_to(X[0,0]==0)
    opti.subject_to(X[1,0]==0)
    opti.subject_to(X[0,-1]==target)
    opti.subject_to(X[1,-1]==0)
    # control bounds
    opti.subject_to(opti.bounded(0, U, umax))
    opti.subject_to(T>=0.1)
    # objective minimize integral u^2 (effort) plus time penalty
    opti.minimize(ca.sumsqr(U)*dt + 0.1*T)
    # initial guesses
    opti.set_initial(T, target/10)
    opti.set_initial(X[0,:], ca.linspace(0,target,N+1))
    opti.set_initial(X[1,:], 0)
    opti.set_initial(U, umax/2)
    # solve
    p_opts = {"expand":True}
    s_opts = {"max_iter":1000}
    opti.solver("ipopt", p_opts, s_opts)
    sol = opti.solve()
    return sol, X, U, T


if __name__=="__main__":
    sol,X,U,T = solve_rocket_ocp()
    import matplotlib.pyplot as plt
    t = np.linspace(0, sol.value(T), X.shape[1])
    x = np.array(sol.value(X[0,:])).flatten()
    v = np.array(sol.value(X[1,:])).flatten()
    m = np.array(sol.value(X[2,:])).flatten()
    u = np.array(sol.value(U)).flatten()
    plt.figure()
    plt.plot(np.linspace(0,sol.value(T),len(x)),x,label='x')
    plt.plot(np.linspace(0,sol.value(T),len(v)),v,label='v')
    plt.plot(np.linspace(0,sol.value(T),len(m)),m,label='m')
    plt.legend()
    plt.show()