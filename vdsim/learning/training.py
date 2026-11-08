"""Train a vehicle dynamics surrogate and evaluate it against its physics teacher.

Offline metrics on a held-out test set: RMSE and R^2 per target. Closed loop: the same maneuver with
the same controllers, once with the teacher and once with the neural model; reported are the largest
position and yaw-rate differences and the KPI deviations - the error that matters to a planner.
"""

from __future__ import annotations

import time

import numpy as np

from ..core.parameters import load_vehicle_preset
from .dataset import FEATURES, TARGETS, sample_dataset
from .mlp import MLP


def _metrics(y_true, y_pred):
    out = {}
    for k, name in enumerate(TARGETS):
        err = y_pred[:, k] - y_true[:, k]
        var = float(np.var(y_true[:, k]))
        out[name] = {"rmse": float(np.sqrt(np.mean(err ** 2))), "max_abs": float(np.max(np.abs(err))),
                     "r2": float(1.0 - np.mean(err ** 2) / var) if var > 0 else None}
    return out


def train_surrogate(vehicle="mid_size_sedan", teacher="bicycle_nonlinear", n_samples=20000, hidden=(64, 64),
                    epochs=150, lr=2e-3, batch=256, seed=0, progress=None, should_stop=None):
    """Returns (net, meta). progress(phase, fraction, info) is called during sampling and training."""
    cfg = load_vehicle_preset(vehicle)
    tic = time.perf_counter()
    if progress:
        progress("sampling", 0.0, {})
    x, y = sample_dataset(cfg, teacher, n_samples + n_samples // 5, seed)
    x_test, y_test = x[n_samples:], y[n_samples:]
    x, y = x[:n_samples], y[:n_samples]
    t_data = time.perf_counter() - tic
    net = MLP(len(FEATURES), len(TARGETS), hidden, seed)

    def on_epoch(epoch, total, train, val):
        if progress:
            progress("training", epoch / total, {"epoch": epoch, "train": train, "val": val})

    history = net.fit(x, y, epochs=epochs, batch=batch, lr=lr, seed=seed, progress=on_epoch, should_stop=should_stop)
    metrics = _metrics(y_test, net.predict(x_test))
    meta = {"backend": "mlp", "kind": "vehicle_dynamics", "vehicle": vehicle, "teacher": teacher,
            "features": list(FEATURES), "targets": list(TARGETS), "hidden": list(hidden), "n_samples": n_samples,
            "epochs_run": len(history), "history": history, "test_metrics": metrics,
            "time_data_s": t_data, "time_total_s": time.perf_counter() - tic,
            "n_parameters": int(sum(w.size for w in net.W) + sum(b.size for b in net.b))}
    return net, meta


def evaluate_closed_loop(model_name, teacher="bicycle_nonlinear", vehicle="mid_size_sedan",
                         maneuver="iso_double_lane_change", maneuver_params=None, duration=None, max_points=400):
    from ..reporting import evaluate
    from ..simulation.scenario import Scenario
    from ..simulation.simulator import Simulator

    runs = {}
    for label, model in (("physics", teacher), ("neural", model_name)):
        sc = Scenario(name=label, vehicle=vehicle, model=model, maneuver=maneuver,
                      maneuver_params=dict(maneuver_params or {}), duration=duration or 0.0)
        sim = Simulator.from_scenario(sc)
        tic = time.perf_counter()
        res = sim.run(max_wall_time=60.0)
        runs[label] = (res, time.perf_counter() - tic, {k.key: k.value for k in evaluate(res)})
    a, b = runs["physics"][0], runs["neural"][0]
    n = min(len(a["t"]), len(b["t"]))
    pos = np.hypot(a["x"][:n] - b["x"][:n], a["y"][:n] - b["y"][:n])
    idx = np.unique(np.linspace(0, n - 1, min(n, max_points)).round().astype(int))
    kp, kn = runs["physics"][2], runs["neural"][2]
    kpi = {k: {"physics": kp[k], "neural": kn[k]} for k in ("max_ay", "max_yaw_rate", "max_beta",
                                                             "max_lateral_error") if k in kp and k in kn}
    return {"maneuver": maneuver, "max_position_error": float(np.max(pos)),
            "max_yaw_rate_error": float(np.max(np.abs(a["r"][:n] - b["r"][:n]))),
            "wall_time": {"physics": runs["physics"][1], "neural": runs["neural"][1]},
            "kpis": kpi,
            "series": {"t": a["t"][:n][idx].tolist(),
                       "physics_y": a["y"][:n][idx].tolist(), "neural_y": b["y"][:n][idx].tolist(),
                       "physics_r": a["r"][:n][idx].tolist(), "neural_r": b["r"][:n][idx].tolist(),
                       "physics_x": a["x"][:n][idx].tolist(), "neural_x": b["x"][:n][idx].tolist()}}
