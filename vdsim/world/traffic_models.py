"""Microscopic traffic models: Intelligent Driver Model and MOBIL lane-change model.

    IDM    Treiber, Hennecke, Helbing (2000):
           a = a_max [1 - (v/v0)^delta - (s*/s)^2],  s* = s0 + max(0, v T + v dv / (2 sqrt(a_max b)))
    MOBIL  Kesting, Treiber, Helbing (2007): incentive  a~_c - a_c + p [(a~_n - a_n) + (a~_o - a_o)] > da_th + a_bias
           safety  a~_n >= -b_safe
Both functions accept numpy arrays (vectorized evaluation for many vehicles).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core.parameters import param
from ..framework.knowledge import trace


@dataclass
class IDMParams:
    v0: float = param(30.0, "m/s", "Wunschgeschwindigkeit v0", min=0.0, max=70.0)
    T: float = param(1.4, "s", "Folgezeitlücke T", min=0.1, max=5.0)
    s0: float = param(2.0, "m", "Mindestabstand s0", min=0.0, max=20.0)
    a: float = param(1.2, "m/s²", "Maximalbeschleunigung a", min=0.1, max=6.0)
    b: float = param(2.0, "m/s²", "komfortable Verzögerung b", min=0.1, max=9.0)
    delta: float = param(4.0, "-", "Beschleunigungsexponent δ", min=1.0, max=10.0)
    b_max: float = param(9.0, "m/s²", "maximale Verzögerung (Begrenzung)", min=1.0, max=12.0)


@dataclass
class MOBILParams:
    politeness: float = param(0.3, "-", "Höflichkeitsfaktor p", min=0.0, max=1.0)
    threshold: float = param(0.2, "m/s²", "Wechselschwelle Δa_th", min=0.0, max=2.0)
    bias_right: float = param(0.3, "m/s²", "Rechtsfahrgebot a_bias", min=0.0, max=2.0)
    b_safe: float = param(4.0, "m/s²", "sichere Verzögerung b_safe", min=0.5, max=9.0)
    interval: float = param(1.0, "s", "Entscheidungsintervall", min=0.1, max=10.0)
    duration: float = param(4.0, "s", "Dauer der Querbewegung", min=1.0, max=10.0)
    cooldown: float = param(4.0, "s", "Sperrzeit nach Spurwechsel", min=0.0, max=30.0)


@trace("treiber2000", section="2", equation="IDM: a = a[1-(v/v0)^δ-(s*/s)^2]", concept="idm",
       note="Intelligent Driver Model, s* = s0 + max(0, vT + vΔv/(2√(ab)))")
def idm_acceleration(v, v0, gap, dv, a=1.2, b=2.0, T=1.4, s0=2.0, delta=4.0, b_max=9.0):
    # v: own speed, v0: desired speed, gap: bumper-to-bumper distance (inf = free road),
    # dv = v - v_leader (approaching rate)
    v = np.asarray(v, dtype=float)
    v0 = np.maximum(np.asarray(v0, dtype=float), 0.1)
    gap = np.maximum(np.asarray(gap, dtype=float), 0.1)
    s_star = s0 + np.maximum(0.0, v * T + v * np.asarray(dv, dtype=float) / (2.0 * np.sqrt(a * b)))
    acc = a * (1.0 - (np.maximum(v, 0.0) / v0) ** delta - (s_star / gap) ** 2)
    acc = np.maximum(acc, -b_max)
    return float(acc) if np.ndim(acc) == 0 else acc


def idm(v, v0, gap, dv, p):
    # convenience wrapper with an IDMParams instance
    return idm_acceleration(v, v0, gap, dv, p.a, p.b, p.T, p.s0, p.delta, p.b_max)


def idm_equilibrium_speed(gap, p, v0=None):
    # steady-state speed for a given gap (dv = 0), solved by bisection (vectorized)
    v0 = p.v0 if v0 is None else v0
    gap = np.atleast_1d(np.asarray(gap, dtype=float))
    lo, hi = np.zeros_like(gap), np.full_like(gap, float(v0))
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        acc = idm_acceleration(mid, v0, gap, 0.0, p.a, p.b, p.T, p.s0, p.delta, p.b_max)
        lo, hi = np.where(acc > 0, mid, lo), np.where(acc > 0, hi, mid)
    return 0.5 * (lo + hi)


@trace("kesting2007", section="3", equation="(3), (4), (8)", concept="mobil",
       note="Anreiz ã_c − a_c + p[(ã_n − a_n) + (ã_o − a_o)] > Δa_th ± a_bias, Sicherheit ã_n ≥ −b_safe")
def mobil_incentive(a_c, a_c_new, a_n, a_n_new, a_o, a_o_new, politeness=0.3, threshold=0.2, bias=0.0, b_safe=4.0):
    # returns (accept, incentive, safe); bias > 0 favors the change (keep-right rule: + for right, - for left)
    incentive = (np.asarray(a_c_new) - a_c) + politeness * ((np.asarray(a_n_new) - a_n) + (np.asarray(a_o_new) - a_o))
    incentive = incentive + bias
    safe = np.asarray(a_n_new) >= -b_safe
    accept = safe & (incentive > threshold)
    if np.ndim(accept) == 0:
        return bool(accept), float(incentive), bool(safe)
    return accept, incentive, safe


def smoothstep5(u):
    # quintic transition 0 -> 1 with zero slope and curvature at both ends (smooth lateral motion)
    u = np.clip(u, 0.0, 1.0)
    return u ** 3 * (10.0 - 15.0 * u + 6.0 * u ** 2)


def smoothstep5_d(u):
    u = np.clip(u, 0.0, 1.0)
    return 30.0 * u ** 2 * (1.0 - u) ** 2
