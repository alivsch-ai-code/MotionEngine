"""Linear lateral MPC on the path-error dynamics of the single-track model (Rajamani, ch. 2.5).

States e = [lateral error, its rate, heading error, its rate], input delta, measured disturbance
psi_dot_des = v * kappa (preview from the reference path). The condensed QP with steering
bounds is solved as a bounded least-squares problem (scipy.optimize.lsq_linear).
"""

import numpy as np
from scipy.linalg import expm
from scipy.optimize import lsq_linear

from ..core.interfaces import LateralController
from ..core.registry import register
from ..tire_models import create_tires
from ..vehicle_models.common import axle_cornering_stiffness
from .path_tracking import clip_steer, wrap


@register("lateral_controller", "mpc")
class MPCController(LateralController):
    label = "MPC"

    def __init__(self, config, horizon=25, dt=0.05, q_lateral=10.0, q_heading=5.0, r_steer=1.0,
                 r_rate=20.0, update_period=0.01):
        self.config = config
        self.N, self.dt = int(horizon), dt
        self.Q = np.diag([q_lateral, 0.0, q_heading, 0.0])
        self.r, self.s_rate = r_steer, r_rate
        self.update_period = update_period
        p = config.vehicle
        tire_f, tire_r = create_tires(config.tires)
        fz_f, fz_r = p.static_axle_loads
        self.c_f = axle_cornering_stiffness(tire_f, fz_f / 2)
        self.c_r = axle_cornering_stiffness(tire_r, fz_r / 2)
        self._cache_v = None
        self.reset()

    def reset(self):
        self.u_prev = 0.0
        self._last_t = -1e9
        self._u = 0.0
        self.signals = {}
        self._hint = 0

    def _matrices(self, vx):
        p, cf, cr = self.config.vehicle, self.c_f, self.c_r
        m, iz, lf, lr = p.mass, p.inertia_z, p.cg_to_front, p.cg_to_rear
        A = np.array([[0, 1, 0, 0],
                      [0, -(cf + cr) / (m * vx), (cf + cr) / m, (-cf * lf + cr * lr) / (m * vx)],
                      [0, 0, 0, 1],
                      [0, -(cf * lf - cr * lr) / (iz * vx), (cf * lf - cr * lr) / iz,
                       -(cf * lf**2 + cr * lr**2) / (iz * vx)]])
        B = np.array([0, cf / m, 0, cf * lf / iz])
        E = np.array([0, -(cf * lf - cr * lr) / (m * vx) - vx, 0, -(cf * lf**2 + cr * lr**2) / (iz * vx)])
        # exact zero-order-hold discretization of [A | B E]
        M = np.zeros((6, 6))
        M[:4, :4], M[:4, 4], M[:4, 5] = A, B, E
        Md = expm(M * self.dt)
        return Md[:4, :4], Md[:4, 4], Md[:4, 5]

    def _prediction(self, vx):
        if self._cache_v is not None and abs(vx - self._cache_v) < 0.5:
            return self._cache
        Ad, Bd, Ed = self._matrices(vx)
        n, N = 4, self.N
        Phi = np.zeros((n * N, n))
        Gam = np.zeros((n * N, N))
        Psi = np.zeros((n * N, N))
        Ak = np.eye(n)
        powers = [np.eye(n)]
        for k in range(N):
            Ak = Ad @ Ak
            powers.append(Ak)
            Phi[n * k:n * k + n] = Ak
        for k in range(N):
            for j in range(k + 1):
                Gam[n * k:n * k + n, j] = powers[k - j] @ Bd
                Psi[n * k:n * k + n, j] = powers[k - j] @ Ed
        self._cache_v, self._cache = vx, (Phi, Gam, Psi)
        return self._cache

    def steer(self, t, state, ref):
        if t - self._last_t < self.update_period - 1e-9:
            return self._u
        self._last_t = t
        vx = max(state.vx, 2.0)
        proj = ref.project(state.x, state.y, hint=self._hint)
        self._hint = proj.index
        e_psi = wrap(state.psi - proj.heading)
        x0 = np.array([proj.lateral_error, state.vy + vx * np.sin(e_psi), e_psi, state.r - vx * proj.kappa])
        s_preview = proj.s + vx * self.dt * np.arange(self.N)
        w = vx * np.interp(s_preview, ref.s, ref.kappa)

        Phi, Gam, Psi = self._prediction(vx)
        N = self.N
        qh = np.kron(np.eye(N), np.sqrt(self.Q))
        D = np.eye(N) - np.eye(N, k=-1)
        d0 = np.zeros(N)
        d0[0] = self.u_prev
        A_ls = np.vstack([qh @ Gam, np.sqrt(self.r) * np.eye(N), np.sqrt(self.s_rate) * D])
        b_ls = np.concatenate([-qh @ (Phi @ x0 + Psi @ w), np.zeros(N), np.sqrt(self.s_rate) * d0])
        limit = self.config.vehicle.max_steer_angle
        res = lsq_linear(A_ls, b_ls, bounds=(-limit, limit), method="bvls")
        self._u = clip_steer(res.x[0], self.config)
        self.u_prev = self._u
        self.signals = {"lateral_error": proj.lateral_error, "heading_error": e_psi, "s": proj.s,
                        "mpc_cost": float(res.cost)}
        return self._u
