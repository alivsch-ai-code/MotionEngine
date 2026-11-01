"""Configurable multi-objective cost of the trajectory planner (kind="cost_term").

Consistent terms (Werling 2011, (3.4), (3.10), Tab. 3.1): jerk integral, k_tau tau and the
terminal deviation. They define the optimal control problem whose minimizers are exactly the
quintic/quartic polynomials of the candidate sets, so ONLY these terms keep the Bellman
guarantee (temporal consistency, Satz 3).

Additional terms (weight 0 by default) express further objectives:

    separable      computed on the lateral or longitudinal set (cheap, enter the sorting):
                   acceleration, lane_deviation, travel_time, energy
    non-separable  depend on world coordinates or obstacles; they are evaluated in a re-ranking
                   window over the first valid candidates: comfort, curvature, safety_distance,
                   collision_risk

Any additional term changes the selected trajectory w.r.t. the optimal control problem the
function class was derived for, so cyclic replanning is in general no longer exactly consistent.

Total cost (3.2):  J = k_lat * sum(lateral terms) + k_lon * sum(longitudinal terms) + sum(combined terms)
All weights live in parameters (planner config JSON / API), never in the code.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

import numpy as np

from ..core.conventions import AIR_DENSITY, G
from ..core.parameters import param
from ..framework.component import Component
from ..framework.knowledge import ComponentDoc, trace
from ..framework.plugins import component, create_component, get_component
from .constraints import group


def _trapz(values, dx):
    # integral over a uniform grid along the last axis
    v = np.asarray(values, dtype=float)
    if v.shape[-1] < 2:
        return np.zeros(v.shape[:-1])
    return dx * (np.sum(v, axis=-1) - 0.5 * (v[..., 0] + v[..., -1]))


class CostTerm(Component):
    KIND, CATEGORY = "cost_term", "Planer-Kostenterme"
    LABEL = "Kostenterm"
    SCOPE = "separable"          # "separable" (lateral() and/or longitudinal()) or "combined"
    CONSISTENT = False           # True only for the Werling terms (Bellman guarantee)

    def setup(self, vehicle, geometry):
        self.vehicle, self.geometry = vehicle, geometry

    @property
    def active(self):
        if not getattr(self.params, "enabled", True):
            return False
        if self.CONSISTENT:
            return True
        return any(abs(float(getattr(self.params, f.name))) > 0 for f in fields(self.params)
                   if f.name.startswith("weight"))

    # weighted contributions; None = term does not apply to this set
    def lateral(self, lat, ctx):
        return None

    def longitudinal(self, lon, ctx):
        return None

    def combined(self, batch, collision, ctx):
        return None

    def step(self, t, inputs):
        return {}


# ----------------------------------------------------------------------------- consistent (Werling) terms
@dataclass
class JerkCostParams:
    k_lat: float = param(1.0, "-", "Gewicht Querruck d(t)  ∫½ d⃛² dt", min=0.0)
    k_arc: float = param(1000.0, "-", "Gewicht Querruck d(s)  ∫½ d‴² ds", min=0.0)
    k_lon: float = param(1.0, "-", "Gewicht Längsruck ∫½ s⃛² dt", min=0.0)


@component
class JerkCost(CostTerm):
    NAME, VERSION, LABEL = "jerk", "1.0.0", "Ruck (konsistent)"
    PARAMS = JerkCostParams
    CONSISTENT = True
    DOC = ComponentDoc(summary="Ruckintegral ∫½u² dt des Optimalsteuerproblems (3.4), geschlossen ausgewertet.",
                       references=["werling2011"], equations=["werling2011:(3.4)"], concepts=["jerk_integral"])

    def lateral(self, lat, ctx):
        k = self.params.k_arc if lat.mode == "arc" else self.params.k_lat
        return k * 0.5 * lat.jerk

    def longitudinal(self, lon, ctx):
        return self.params.k_lon * 0.5 * lon.jerk


@dataclass
class TerminalTimeParams:
    k_tau_lat: float = param(5.0, "1/s", "k_τ quer (d(t))", min=0.0)
    k_s_arc: float = param(8.0, "1/m", "k_s quer (d(s)): k_s [s(τ) − s(0)]", min=0.0)
    k_tau_lon: float = param(2.0, "1/s", "k_τ längs", min=0.0)


@component
class TerminalTimeCost(CostTerm):
    NAME, VERSION, LABEL = "terminal_time", "1.0.0", "Endzeit k_τ τ (konsistent)"
    PARAMS = TerminalTimeParams
    CONSISTENT = True
    DOC = ComponentDoc(summary="Endkosten k_τ τ (bzw. k_s [s(τ)−s(0)] im d(s)-Modus) gegen langsames Annähern.",
                       references=["werling2011"], equations=["werling2011:(3.10)", "werling2011:Tab. 3.1"])

    def lateral(self, lat, ctx):
        return (self.params.k_s_arc if lat.mode == "arc" else self.params.k_tau_lat) * lat.tau

    def longitudinal(self, lon, ctx):
        return self.params.k_tau_lon * lon.tau


@dataclass
class TerminalDeviationParams:
    k_delta: float = param(200.0, "1/m²", "k_δ Endversatz quer (d(t))", min=0.0)
    k_delta_arc: float = param(600.0, "1/m²", "k_δ Endversatz quer (d(s))", min=0.0)
    k_sigma: float = param(30.0, "1/m²", "k_σ Positionsversatz (Folgen, Einfädeln, Anhalten)", min=0.0)
    k_nu: float = param(20.0, "s²/m²", "k_ν Geschwindigkeitsversatz", min=0.0)


@component
class TerminalDeviationCost(CostTerm):
    NAME, VERSION, LABEL = "terminal_deviation", "1.0.0", "Zielerreichung ½kδ² (konsistent)"
    PARAMS = TerminalDeviationParams
    CONSISTENT = True
    DOC = ComponentDoc(summary="Endabweichung ½kδ δ², ½kσ σ², ½kν ν² von der Referenz (Zielerreichung).",
                       references=["werling2011"], equations=["werling2011:(3.10)", "werling2011:Tab. 3.1"])

    @trace("werling2011", section="3.4.2", equation="Tab. 3.1", concept="continuous_manifold",
           note="k_tau tau_j + 1/2 k_delta delta_i^2 usw.")
    def lateral(self, lat, ctx):
        k = self.params.k_delta_arc if lat.mode == "arc" else self.params.k_delta
        return 0.5 * k * lat.delta ** 2

    def longitudinal(self, lon, ctx):
        k = self.params.k_nu if lon.kind == "velocity" else self.params.k_sigma
        return 0.5 * k * lon.offset ** 2


# ----------------------------------------------------------------------------- separable additional terms
@dataclass
class AccelerationCostParams:
    enabled: bool = param(True, "", "aktiv")
    weight_lat: float = param(0.0, "s³/m²", "Gewicht ∫ d̈² dt (bzw. ∫ d''² ds)", min=0.0)
    weight_lon: float = param(0.0, "s³/m²", "Gewicht ∫ s̈² dt", min=0.0)


@component
class AccelerationCost(CostTerm):
    NAME, VERSION, LABEL = "acceleration", "1.0.0", "Beschleunigung"
    PARAMS = AccelerationCostParams
    DOC = ComponentDoc(summary="Quadratintegral der straßenrelativen Beschleunigungen über den Prüfhorizont.")

    def lateral(self, lat, ctx):
        dx = lat.grid[1] - lat.grid[0] if len(lat.grid) > 1 else 0.0
        return self.params.weight_lat * _trapz(lat.d2 ** 2, dx)

    def longitudinal(self, lon, ctx):
        dx = lon.grid[1] - lon.grid[0] if len(lon.grid) > 1 else 0.0
        return self.params.weight_lon * _trapz(lon.sdd ** 2, dx)


@dataclass
class LaneDeviationParams:
    enabled: bool = param(True, "", "aktiv")
    weight: float = param(0.0, "1/(m² s)", "Gewicht ∫ (d − d_ref)² dt", min=0.0)
    relative_to_d_ref: bool = param(True, "", "Abweichung zu d_ref (sonst zur Spurmitte d = 0)")


@component
class LaneDeviationCost(CostTerm):
    NAME, VERSION, LABEL = "lane_deviation", "1.0.0", "Spurabweichung"
    PARAMS = LaneDeviationParams
    DOC = ComponentDoc(summary="Integrierte Querabweichung zur Referenz über den Prüfhorizont (bzw. die Prüfstrecke).")

    def lateral(self, lat, ctx):
        center = lat.d_ref if self.params.relative_to_d_ref else 0.0
        dx = lat.grid[1] - lat.grid[0] if len(lat.grid) > 1 else 0.0
        return self.params.weight * _trapz((lat.d - center) ** 2, dx)


@dataclass
class TravelTimeParams:
    enabled: bool = param(True, "", "aktiv")
    weight: float = param(0.0, "1/s", "Gewicht Zeitverlust gegenüber Wunschgeschwindigkeit", min=0.0)


@component
class TravelTimeCost(CostTerm):
    NAME, VERSION, LABEL = "travel_time", "1.0.0", "Fahrzeit"
    PARAMS = TravelTimeParams
    DOC = ComponentDoc(summary="Zeitverlust max(0, v_soll T − Δs)/v_soll auf dem Prüfhorizont.")

    def longitudinal(self, lon, ctx):
        horizon = lon.grid[-1] if len(lon.grid) else 0.0
        v_des = max(ctx.target_speed, 0.1)
        progress = lon.s[:, -1] - lon.s[:, 0]
        return self.params.weight * np.maximum(0.0, v_des * horizon - progress) / v_des


@dataclass
class EnergyParams:
    enabled: bool = param(True, "", "aktiv")
    weight: float = param(0.0, "s²/m²", "Gewicht Traktionsenergie je Masse", min=0.0)
    regen_efficiency: float = param(0.0, "-", "Rückgewinnungsgrad beim Verzögern", min=0.0, max=1.0)


@component
class EnergyCost(CostTerm):
    NAME, VERSION, LABEL = "energy", "1.0.0", "Energieeffizienz"
    PARAMS = EnergyParams
    DOC = ComponentDoc(summary="Traktionsenergie je Masse ∫ ṡ (s̈ + c_r g + ρ c_w A ṡ²/(2m)) dt mit Rekuperation.",
                       assumptions=["Bahngeschwindigkeit ≈ ṡ", "ebene Straße"])

    def longitudinal(self, lon, ctx):
        veh = getattr(self.vehicle, "vehicle", None)
        cr = veh.rolling_resistance if veh is not None else 0.012
        drag = (0.5 * AIR_DENSITY * veh.drag_coefficient * veh.frontal_area / veh.mass) if veh is not None else 2e-4
        power = lon.sd * (lon.sdd + cr * G + drag * lon.sd ** 2)
        net = np.maximum(power, 0.0) - self.params.regen_efficiency * np.maximum(-power, 0.0)
        dx = lon.grid[1] - lon.grid[0] if len(lon.grid) > 1 else 0.0
        return self.params.weight * _trapz(net, dx)


# ----------------------------------------------------------------------------- non-separable terms
@dataclass
class ComfortParams:
    enabled: bool = param(True, "", "aktiv")
    weight: float = param(0.0, "s³/m²", "Gewicht ∫ (a_quer² + a_längs²) dt (Weltkoordinaten)", min=0.0)


@component
class ComfortCost(CostTerm):
    NAME, VERSION, LABEL = "comfort", "1.0.0", "Komfort"
    PARAMS = ComfortParams
    SCOPE = "combined"
    DOC = ComponentDoc(summary="Beschleunigungsbelastung der Insassen in Weltkoordinaten (inkl. Straßenkrümmung).")

    def combined(self, batch, collision, ctx):
        return self.params.weight * _trapz(batch.a_lat ** 2 + batch.a ** 2, batch.dt)


@dataclass
class CurvatureCostParams:
    enabled: bool = param(True, "", "aktiv")
    weight: float = param(0.0, "m", "Gewicht ∫ κ² dℓ", min=0.0)


@component
class CurvatureCost(CostTerm):
    NAME, VERSION, LABEL = "curvature", "1.0.0", "Krümmung"
    PARAMS = CurvatureCostParams
    SCOPE = "combined"
    DOC = ComponentDoc(summary="Geometrische Krümmungsenergie ∫ κ² dℓ = ∫ κ² v dt.")

    def combined(self, batch, collision, ctx):
        return self.params.weight * _trapz(batch.kappa ** 2 * np.abs(batch.v), batch.dt)


@dataclass
class SafetyDistanceParams:
    enabled: bool = param(True, "", "aktiv")
    weight: float = param(0.0, "1/(m² s)", "Gewicht ∫ max(0, d_soll − Abstand)² dt", min=0.0)
    distance: float = param(2.0, "m", "Weicher Wunschabstand zu Objekten", min=0.0, max=20.0)


@component
class SafetyDistanceCost(CostTerm):
    NAME, VERSION, LABEL = "safety_distance", "1.0.0", "Sicherheitsabstand"
    PARAMS = SafetyDistanceParams
    SCOPE = "combined"
    DOC = ComponentDoc(summary="Weiche Abstandskosten zusätzlich zur harten Kollisionsrestriktion.")

    def combined(self, batch, collision, ctx):
        if collision is None:
            return np.zeros(len(batch))
        gap = np.maximum(0.0, self.params.distance - np.minimum(collision.clearance, 1e6))
        return self.params.weight * _trapz(gap ** 2, batch.dt)


@dataclass
class CollisionRiskParams:
    enabled: bool = param(True, "", "aktiv")
    weight: float = param(0.0, "1/s", "Gewicht ∫ exp(−Abstand²/(2σ²)) dt", min=0.0)
    sigma: float = param(1.0, "m", "Unsicherheit σ der Objektposition", min=0.05, max=10.0)


@component
class CollisionRiskCost(CostTerm):
    NAME, VERSION, LABEL = "collision_risk", "1.0.0", "Kollisionsrisiko"
    PARAMS = CollisionRiskParams
    SCOPE = "combined"
    DOC = ComponentDoc(summary="Gaußförmiges Risikomaß über den kleinsten Abstand zu den prädizierten Objekten.")

    def combined(self, batch, collision, ctx):
        if collision is None:
            return np.zeros(len(batch))
        c = np.maximum(np.minimum(collision.clearance, 1e3), 0.0)
        return self.params.weight * _trapz(np.exp(-0.5 * (c / self.params.sigma) ** 2), batch.dt)


# ----------------------------------------------------------------------------- settings / model
@dataclass
class CostSettings:
    k_lat: float = param(1.0, "-", "Gewicht Querkosten k_lat (3.2)", min=0.0)
    k_lon: float = param(1.0, "-", "Gewicht Längskosten k_lon = k_s (3.2)", min=0.0)
    rerank_window: int = param(10, "", "Re-Ranking-Fenster für nicht separierbare Terme", min=1, max=500)
    jerk: JerkCostParams = group(JerkCostParams, "Ruck (konsistent)")
    terminal_time: TerminalTimeParams = group(TerminalTimeParams, "Endzeit (konsistent)")
    terminal_deviation: TerminalDeviationParams = group(TerminalDeviationParams, "Zielerreichung (konsistent)")
    acceleration: AccelerationCostParams = group(AccelerationCostParams, "Beschleunigung")
    lane_deviation: LaneDeviationParams = group(LaneDeviationParams, "Spurabweichung")
    travel_time: TravelTimeParams = group(TravelTimeParams, "Fahrzeit")
    energy: EnergyParams = group(EnergyParams, "Energieeffizienz")
    comfort: ComfortParams = group(ComfortParams, "Komfort")
    curvature: CurvatureCostParams = group(CurvatureCostParams, "Krümmung")
    safety_distance: SafetyDistanceParams = group(SafetyDistanceParams, "Sicherheitsabstand")
    collision_risk: CollisionRiskParams = group(CollisionRiskParams, "Kollisionsrisiko")
    custom: list = param([], "", "Weitere Kostenterme [{spec, params}]")


_NON_TERMS = ("k_lat", "k_lon", "rerank_window", "custom")


@trace("werling2011", section="3.3", equation="(3.2)", concept="multi_objective_cost",
       note="J = k_lat J_d + k_lon J_s + nicht separierbare Zusatzterme (Re-Ranking)")
class CostModel:
    """Instantiated cost terms; computes set costs, combined costs and the breakdown."""

    def __init__(self, settings, vehicle=None, geometry=None):
        self.settings = settings
        self.terms = []
        for f in fields(settings):
            if f.name in _NON_TERMS:
                continue
            term = get_component("cost_term", f.name)(getattr(settings, f.name))
            term.setup(vehicle, geometry)
            if term.active:
                self.terms.append(term)
        for entry in settings.custom or []:
            spec = entry["spec"] if isinstance(entry, dict) else str(entry)
            term = create_component(spec, entry.get("params") if isinstance(entry, dict) else None)
            term.setup(vehicle, geometry)
            if term.active:
                self.terms.append(term)

    @property
    def combined_terms(self):
        return [t for t in self.terms if t.SCOPE == "combined"]

    @property
    def consistent_only(self):
        return all(t.CONSISTENT for t in self.terms)

    def _apply(self, cset, method, ctx):
        costs, total = {}, np.zeros(len(cset))
        for term in self.terms:
            if term.SCOPE == "combined":
                continue
            val = getattr(term, method)(cset, ctx)
            if val is None:
                continue
            val = np.broadcast_to(np.asarray(val, dtype=float), (len(cset),))
            costs[term.NAME] = val
            total = total + val
        cset.costs, cset.total = costs, total
        return total

    def lateral(self, lat, ctx):
        return self._apply(lat, "lateral", ctx)

    def longitudinal(self, lon, ctx):
        return self._apply(lon, "longitudinal", ctx)

    def combined(self, batch, collision, ctx):
        costs, total = {}, np.zeros(len(batch))
        for term in self.combined_terms:
            val = term.combined(batch, collision, ctx)
            if val is None:
                continue
            costs[term.NAME] = np.asarray(val, dtype=float)
            total = total + costs[term.NAME]
        return total, costs

    def breakdown(self, lat, i, lon, j, combined=None):
        # weighted cost terms of one selected candidate (PlannerDebug.cost_terms)
        out = {}
        for name, val in lat.costs.items():
            out[f"quer.{name}"] = float(self.settings.k_lat * val[i])
        for name, val in lon.costs.items():
            out[f"laengs.{name}"] = float(self.settings.k_lon * val[j])
        for name, val in (combined or {}).items():
            out[name] = float(val)
        out["gesamt"] = float(sum(out.values()))
        out["konsistent"] = float(sum(v for k, v in out.items() if k.split(".")[-1] in
                                      ("jerk", "terminal_time", "terminal_deviation")))
        return out
