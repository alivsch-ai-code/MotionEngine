"""Discretization of the target manifolds (Werling 2011, 3.4.2, Satz 3, Tab. 3.1).

The end times are NOT chosen relative to the start time t0 but on an absolute grid
T_k = k * dtau, tau_j = T_k - t0. The remainder of the previously selected trajectory (which
ends at some T_k*) is therefore again part of the next candidate set, which is the
precondition of the temporal consistency (Bellman principle). The end offsets delta_i,
sigma_i, nu_i are relative to the reference d_ref, s_ref(tau_j), s_dot_ref.

In the arc-length mode d(s) (slow driving, 3.5.1) the same idea applies to an absolute grid
of end positions S_k = k * ds on the reference curve.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core.parameters import param
from ..framework.knowledge import trace

_EPS = 1e-9


@dataclass
class EndGrid:
    # discretized end "times" (or arc positions) of one candidate set
    tau: np.ndarray            # duration relative to the start (s or m)
    k: np.ndarray              # integer index on the absolute grid (-1 = relative / not on the grid)
    absolute: bool = True


@trace("werling2011", section="3.4.2", equation="Satz 3", concept="absolute_time_grid",
       note="Endzeitpunkte auf absolutem Raster T_k = k*dtau, tau_j = T_k - t0; Rest der alten Optimallösung bleibt verfügbar")
def end_grid(start, step, tau_min, tau_max, absolute=True, keep_k=None):
    # End times tau_j for a start time/position `start`.
    #   absolute: tau_j = k*step - start for all k with tau_min <= tau_j <= tau_max
    #   relative: tau_j = j*step (frenet_naive baseline, violates the consistency)
    # keep_k: grid index of the previously selected end time. It is added even if its remaining
    # duration fell below tau_min, so that the rest of the old optimal trajectory stays available
    # (consistency guard for the "sinking" smallest tau, see theory.md).
    step = float(step)
    if not absolute:
        j = np.arange(max(int(np.ceil(tau_min / step - _EPS)), 1), int(np.floor(tau_max / step + _EPS)) + 1)
        tau = j * step
        tau = tau[tau >= tau_min - _EPS]
        return EndGrid(tau.astype(float), -np.ones(len(tau), dtype=np.int64), False)
    k0 = int(np.ceil((start + tau_min) / step - _EPS))
    k1 = int(np.floor((start + tau_max) / step + _EPS))
    k = np.arange(k0, k1 + 1, dtype=np.int64)
    if keep_k is not None:
        kk = int(keep_k)
        if kk * step - start > 1e-6 and kk not in set(k.tolist()):
            k = np.sort(np.append(k, kk))
    tau = k * step - start
    keep = tau > 1e-6
    return EndGrid(tau[keep], k[keep], True)


def offsets(step, lower, upper, include=()):
    # symmetric grid i*step (i integer) within [lower, upper]; 0 is always part of the grid
    step = float(step)
    if step <= 0:
        vals = np.array([0.0])
    else:
        i0 = int(np.ceil(lower / step - _EPS))
        i1 = int(np.floor(upper / step + _EPS))
        vals = np.arange(i0, i1 + 1) * step
    vals = np.concatenate([vals, np.asarray(include, dtype=float)])
    return np.unique(np.round(vals, 9))


@dataclass
class SamplingParams:
    absolute_grid: bool = param(True, "", "Absolutes Endzeitraster (zeitliche Konsistenz, Satz 3)")
    # lateral d(t)
    lat_tau_step: float = param(0.5, "s", "Raster Endzeit quer Δτ", min=0.05, max=2.0)
    lat_tau_min: float = param(0.05, "s", "Kleinste Endzeit quer τ_min", min=0.0, max=2.0)
    lat_tau_max: float = param(5.0, "s", "Größte Endzeit quer τ_max", min=0.5, max=15.0)
    lat_d_step: float = param(0.5, "m", "Raster Querversatz δ", min=0.05, max=2.0)
    lat_d_range: float = param(3.5, "m", "Max. Querversatz |δ| relativ zu d_ref", min=0.0, max=10.0)
    # lateral d(s) (slow driving)
    arc_s_step: float = param(1.0, "m", "Raster Endposition d(s) Δs", min=0.1, max=10.0)
    arc_s_min: float = param(0.05, "m", "Kleinste Bogenlänge d(s)", min=0.0, max=10.0)
    arc_s_max: float = param(20.0, "m", "Größte Bogenlänge d(s)", min=1.0, max=100.0)
    # longitudinal s(t) / s_dot(t)
    lon_tau_step: float = param(1.0, "s", "Raster Endzeit längs Δτ", min=0.05, max=2.0)
    lon_tau_min: float = param(0.05, "s", "Kleinste Endzeit längs τ_min", min=0.0, max=2.0)
    lon_tau_max: float = param(8.0, "s", "Größte Endzeit längs τ_max", min=0.5, max=20.0)
    lon_sigma_step: float = param(1.0, "m", "Raster Positionsversatz σ", min=0.05, max=10.0)
    lon_sigma_range: float = param(3.0, "m", "Max. Positionsversatz |σ|", min=0.0, max=30.0)
    stop_allow_overshoot: bool = param(False, "", "Anhalten: σ > 0 (hinter der Haltelinie) zulassen")
    lon_nu_step: float = param(1.0, "m/s", "Raster Geschwindigkeitsversatz ν", min=0.05, max=10.0)
    lon_nu_range: float = param(4.0, "m/s", "Max. Geschwindigkeitsversatz |ν|", min=0.0, max=30.0)
    include_stop_candidates: bool = param(True, "", "Geschwindigkeitsmodus: Anhaltekandidaten (Endgeschw. 0) ergänzen")
    lon_nu_coarse_step: float = param(2.0, "m/s", "Grobes ν-Raster unterhalb von −|ν|max bis Stillstand (0 = aus)",
                                      min=0.0, max=10.0)
    # Frenet pre-filter (grey trajectories of Fig. 3.6-3.8, algorithm step 3)
    prefilter: bool = param(True, "", "Vorfilter straßenrelativer Beschleunigungen (Schritt 3)")
    prefilter_factor: float = param(1.25, "-", "Vorfilter: Faktor auf die Restriktionsgrenzen", min=1.0, max=5.0)
