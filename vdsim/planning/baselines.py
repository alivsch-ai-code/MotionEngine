"""Comparison planners for planner benchmarks (Werling 2011, 3.1, 3.2, Abb. 3.2).

    trajectory_planner/frenet_naive   relative end time grid tau_j = j dtau and replanning from the
                                      measured state in every cycle (high-level stabilization only,
                                      no composition with the old trajectory): the classic sampling
                                      planner without temporal consistency
    trajectory_planner/sequential     longitudinal motion optimized first without knowledge of the lateral
                                      motion, lateral motion afterwards for the given longitudinal one
                                      (decoupled "bi-level optimization" criticized in 3.1)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..framework.knowledge import ComponentDoc
from ..framework.plugins import component
from .combination import CandidateEvaluator
from .longitudinal import build_longitudinal_set
from .planner import StabilizationParams, TimingParams, WerlingPlanner, WerlingPlannerParams
from .sampling import SamplingParams
from .selection import select_mode


def _naive_sampling():
    s = SamplingParams()
    s.absolute_grid = False
    s.lat_tau_min, s.lon_tau_min = 0.5, 0.5
    return s


def _naive_timing():
    t = TimingParams()
    t.t_comp = 0.0
    return t


def _naive_stabilization():
    s = StabilizationParams()
    s.strategy = "high_level"
    return s


@dataclass
class FrenetNaiveParams(WerlingPlannerParams):
    sampling: SamplingParams = field(default_factory=_naive_sampling,
                                     metadata={"label": "Sampling (relatives Raster)", "unit": ""})
    timing: TimingParams = field(default_factory=_naive_timing, metadata={"label": "Zeitverhalten", "unit": ""})
    stabilization: StabilizationParams = field(default_factory=_naive_stabilization,
                                               metadata={"label": "Stabilisierung (immer vom Messzustand)", "unit": ""})


@component
class FrenetNaivePlanner(WerlingPlanner):
    NAME, VERSION = "frenet_naive", "1.0.0"
    LABEL = "Frenet-Planer (naiv, ohne Konsistenz)"
    PARAMS = FrenetNaiveParams
    DOC = ComponentDoc(
        summary="Vergleichsplaner: Frenet-Sampling mit relativem Endzeitraster und Neuplanung vom Messzustand.",
        purpose="Zeigt den Nutzen der zeitlichen Konsistenz (Werling Abb. 3.2) in Planer-Vergleichen.",
        limitations=["keine zeitliche Konsistenz: Ergebnis hängt von der Neuplanungsfrequenz ab",
                     "Regelfehler werden in jedem Zyklus zu Null gesetzt (keine Low-level-Robustheit)"],
        references=["werling2011", "werling2010icra"], equations=["werling2011:Tab. 3.1"],
        concepts=["absolute_time_grid", "bellman_principle"])


@component
class SequentialPlanner(WerlingPlanner):
    NAME, VERSION = "sequential", "1.0.0"
    LABEL = "Sequentieller Planer (erst längs, dann quer)"
    DOC = ComponentDoc(
        summary="Vergleichsplaner: Längsbewegung ohne Kenntnis der Querbewegung, danach Querbewegung (Werling 3.1).",
        purpose="Zeigt den Vorteil der kombinierten Quer-/Längsoptimierung (Ausweichen mit abgestimmtem Bremsen).",
        limitations=["Längskandidaten lexikographisch vor Querkandidaten sortiert"],
        references=["werling2011"])

    def _run_mode(self, label, target, start, t_s, keep_lon, lon_limits, lat, ctx, sel):
        p = self.params
        lon = build_longitudinal_set(start.frenet, target, t_s, p.sampling, ctx.t_grid, keep_lon, lon_limits, label)
        self.cost_model.longitudinal(lon, ctx)
        # lexicographic order: the longitudinal decision dominates every lateral cost
        rank = np.empty(len(lon), dtype=float)
        rank[np.argsort(np.where(lon.feasible, lon.total, np.inf), kind="stable")] = np.arange(len(lon))
        lat_span = float(np.max(lat.total) - np.min(lat.total) + 1.0) * max(p.cost.k_lat, 1e-9)
        lon.total = rank * lat_span / max(p.cost.k_lon, 1e-9)
        evaluator = CandidateEvaluator(ctx.reference_line, lat, lon, ctx)
        res = select_mode(label, lat, lon, evaluator, self.cost_model, self.constraint_set, self.checker, ctx, sel,
                          p.cost.k_lat, p.cost.k_lon)
        res.target = target
        return res
