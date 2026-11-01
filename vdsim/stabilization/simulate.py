"""Lightweight closed-loop runners for tests and examples (independent of the graph executor).

run_closed_loop   tracking controller -> vehicle_dynamics/split_range -> actuator/steering_powertrain
                  -> vehicle_plant/vehicle_model (contracts.md section 1), optional trajectory provider
                  (stands in for the planner, e.g. re-initialization on status.reinit_request)
run_design_loop   controller directly on its design model (werling_kesm: delta_dot, F_l; werling_desm:
                  delta_dot, F_vl, F_hl), without resistances, steering lag and actuators
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import numpy as np

from ..core.parameters import VehicleConfig
from ..core.registry import create
from ..framework.context import RunContext
from ..framework.plugins import create_component
from ..framework.types import EgoState

LOG_KEYS = ("t", "x", "y", "psi", "vx", "vy", "r", "ax", "ay", "delta", "steer_rate_cmd", "steer_angle_cmd",
            "force_cmd", "accel_cmd", "e_t", "e_n", "e_theta", "e_v", "e_t_dot", "e_n_dot", "reinit",
            "lookahead", "ref_x", "ref_y", "compute_time", "drive_torque", "brake_torque", "integrator")


def _instance(spec, params, kind):
    if isinstance(spec, str):
        return create_component(spec if "/" in spec else f"{kind}/{spec}", params or {})
    return spec


def make_context(config=None, environment=None, ego_initial=None, dt=0.01, seed=0):
    services = {"environment": environment} if environment is not None else {}
    scen = SimpleNamespace(ego_initial=ego_initial) if ego_initial is not None else None
    return RunContext(dt=dt, seed=seed, vehicle=config or VehicleConfig(), scenario=scen, services=services)


def run_closed_loop(controller, trajectory, config=None, duration=10.0, dt=0.01, plant="werling_desm",
                    plant_params=None, dynamics_params=None, actuator_params=None, controller_params=None,
                    environment=None, ego_initial=None, provider=None, on_step=None):
    """Simulate the full chain; returns (log dict of arrays, components dict).

    provider(t, ego, status, trajectory) -> trajectory  (optional replanning / switching of trajectories)
    on_step(t, components)                                (optional hook, e.g. impulse disturbances)
    """
    ctx = make_context(config, environment, ego_initial, dt)
    ctl = _instance(controller, controller_params, "tracking_controller")
    dyn = _instance("vehicle_dynamics/split_range", dynamics_params, "vehicle_dynamics")
    act = _instance("actuator/steering_powertrain", actuator_params, "actuator")
    pl = _instance("vehicle_plant/vehicle_model", {"model": plant, **(plant_params or {})}, "vehicle_plant")
    for c in (ctl, dyn, act, pl):
        c.reset(ctx)
    comps = {"controller": ctl, "dynamics": dyn, "actuator": act, "plant": pl, "context": ctx}
    log = {k: [] for k in LOG_KEYS}
    traj, status = trajectory, None
    n = int(round(duration / dt))
    for k in range(n):
        t = k * dt
        if on_step is not None:
            on_step(t, comps)
        ego = pl.output(t)["ego"]
        if provider is not None:
            traj = provider(t, ego, status, traj)
        start = time.perf_counter()
        out = ctl.step(t, {"ego": ego, "trajectory": traj})
        ct = time.perf_counter() - start
        cmd, status = out["command"], out["status"]
        demand = dyn.step(t, {"command": cmd, "ego": ego})["demand"]
        control = act.step(t, {"demand": demand, "ego": ego})["control"]
        pl.update(t, {"control": control}, dt)
        ref = traj.sample(t) if traj is not None else None
        row = {"t": t, "x": ego.x, "y": ego.y, "psi": ego.psi, "vx": ego.vx, "vy": ego.vy, "r": ego.r, "ax": ego.ax,
               "ay": ego.ay, "delta": ego.delta,
               "steer_rate_cmd": np.nan if cmd.steer_rate is None else cmd.steer_rate,
               "steer_angle_cmd": np.nan if cmd.steer_angle is None else cmd.steer_angle,
               "force_cmd": np.nan if cmd.force is None else cmd.force,
               "accel_cmd": np.nan if cmd.accel is None else cmd.accel,
               "e_t": status.e_t, "e_n": status.e_n, "e_theta": status.e_theta, "e_v": status.e_v,
               "e_t_dot": status.e_t_dot, "e_n_dot": status.e_n_dot, "reinit": float(status.reinit_request),
               "lookahead": status.lookahead, "ref_x": ref.x if ref else np.nan, "ref_y": ref.y if ref else np.nan,
               "compute_time": ct, "drive_torque": float(np.sum(demand.drive_torque)),
               "brake_torque": float(np.sum(demand.brake_torque)), "integrator": demand.info.get("integrator", 0.0)}
        for key, value in row.items():
            log[key].append(value)
        log.setdefault("active", []).append(status.active_controller)
        log.setdefault("status", []).append(status)
    out = {k: np.asarray(v) if k not in ("active", "status") else v for k, v in log.items()}
    return out, comps


def run_design_loop(controller, trajectory, config=None, duration=10.0, dt=0.01, model="werling_kesm", x0=None,
                    controller_params=None, environment=None):
    """Controller on its design model (RK4, zero-order hold); returns the log dict."""
    config = config or VehicleConfig()
    ctx = make_context(config, environment, None, dt)
    ctl = _instance(controller, controller_params, "tracking_controller")
    ctl.reset(ctx)
    m = create("vehicle_model", model, config)
    p0 = trajectory.sample(trajectory.t_start)
    if x0 is None:
        if model == "werling_kesm":
            x0 = np.array([p0.x, p0.y, p0.psi, np.arctan(m.P.l * p0.direction * p0.kappa), p0.direction * p0.v])
        else:
            x0 = np.array([p0.x, p0.y, p0.theta, p0.v, 0.0, 0.0, 0.0])
    x = np.array(x0, dtype=float)
    log = {k: [] for k in ("t", "e_t", "e_n", "e_theta", "e_v", "delta", "steer_rate", "force", "V", "v", "x", "y",
                           "psi", "active", "compute_time")}
    for k in range(int(round(duration / dt))):
        t = trajectory.t_start + k * dt
        ego = _design_ego(model, m, x, t)
        start = time.perf_counter()
        out = ctl.step(t, {"ego": ego, "trajectory": trajectory})
        ct = time.perf_counter() - start
        cmd, st = out["command"], out["status"]
        g = cmd.info.get("gamma", 0.0)
        if model == "werling_kesm":
            f = lambda xx: m.design_rhs(xx, cmd.steer_rate, cmd.force, g)  # noqa: E731
        else:
            f = lambda xx: m.design_rhs(xx, cmd.steer_rate, g * cmd.force, (1 - g) * cmd.force)  # noqa: E731
        k1 = f(x)
        k2 = f(x + dt / 2 * k1)
        k3 = f(x + dt / 2 * k2)
        k4 = f(x + dt * k3)
        x = x + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        for key, val in (("t", t), ("e_t", st.e_t), ("e_n", st.e_n), ("e_theta", st.e_theta), ("e_v", st.e_v),
                         ("delta", ego.delta), ("steer_rate", cmd.steer_rate), ("force", cmd.force),
                         ("V", st.info.get("V", np.nan)), ("v", ego.vx), ("x", ego.x), ("y", ego.y), ("psi", ego.psi),
                         ("active", st.active_controller), ("compute_time", ct)):
            log[key].append(val)
    return {k: (np.asarray(v) if k != "active" else v) for k, v in log.items()}


def _design_ego(model, m, x, t):
    if model == "werling_kesm":
        x1, x2, psi, delta, v = x
        lh = m.P.lh
        r = v * np.tan(delta) / m.P.l
        return EgoState(t=t, x=x1 + lh * np.cos(psi), y=x2 + lh * np.sin(psi), psi=psi, vx=v, vy=lh * r, r=r,
                        delta=delta, gear=1 if v >= 0 else -1)
    xx, yy, psi, vx, vy, r, delta = x
    return EgoState(t=t, x=xx, y=yy, psi=psi, vx=vx, vy=vy, r=r, delta=delta)


def max_abs(a, mask=None):
    a = np.asarray(a, dtype=float)
    if mask is not None:
        a = a[mask]
    return float(np.max(np.abs(a))) if a.size else 0.0
