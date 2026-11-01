"""Parameters of the rule-based behavior planner (flat dataclass, German labels for the GUI)."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.parameters import param


@dataclass
class RuleBasedParams:
    # target speed
    a_lat_max: float = param(2.0, "m/s²", "max. Querbeschleunigung (Kurvengeschwindigkeit)", min=0.5, max=8.0)
    b_comf: float = param(1.5, "m/s²", "Vorausschau-Verzögerung (Tempolimit, Kurven)", min=0.3, max=5.0)
    speed_lookahead: float = param(250.0, "m", "Vorausschau Geschwindigkeit", min=20.0, max=1000.0)
    # following (Werling 3.5.2)
    k0: float = param(5.0, "m", "Folgen: Mindestabstand k0 (Stoßstange)", min=0.5, max=30.0)
    kv: float = param(1.2, "s", "Folgen: Zeitlücke kv", min=0.2, max=4.0)
    lead_lookahead_time: float = param(6.0, "s", "Vorausschau Vorderfahrzeug", min=1.0, max=20.0)
    lead_lookahead_min: float = param(60.0, "m", "min. Vorausschau Vorderfahrzeug", min=10.0, max=300.0)
    lateral_margin: float = param(0.3, "m", "Querzuschlag Fahrschlauch", min=0.0, max=2.0)
    intrusion_time: float = param(2.0, "s", "Prädiktionszeit für Einscherer", min=0.0, max=6.0)
    clearance_vru: float = param(1.5, "m", "Seitenabstand Rad/Fußgänger (StVO §5)", min=0.3, max=3.0)
    clearance_static: float = param(0.5, "m", "Seitenabstand stehende Objekte", min=0.1, max=3.0)
    max_pass_offset: float = param(1.5, "m", "max. Versatz d_ref zum Vorbeifahren", min=0.0, max=4.0)
    # lane change (MOBIL-like)
    lc_politeness: float = param(0.2, "-", "Spurwechsel: Höflichkeit p", min=0.0, max=1.0)
    lc_threshold: float = param(0.3, "m/s²", "Spurwechsel: Schwelle Δa_th", min=0.0, max=3.0)
    lc_bias_right: float = param(0.25, "m/s²", "Spurwechsel: Rechtsfahrgebot", min=0.0, max=2.0)
    lc_b_safe: float = param(3.0, "m/s²", "Spurwechsel: zumutbare Verzögerung des Hintermanns", min=0.5, max=9.0)
    lc_safety_horizon: float = param(4.0, "s", "Spurwechsel: Prüfhorizont der Prädiktion", min=0.5, max=10.0)
    lc_gap_min: float = param(3.0, "m", "Spurwechsel: Mindestlücke", min=0.0, max=30.0)
    lc_front_time: float = param(0.6, "s", "Spurwechsel: Zeitlücke nach vorn", min=0.0, max=3.0)
    lc_rear_time: float = param(0.8, "s", "Spurwechsel: Zeitlücke nach hinten", min=0.0, max=3.0)
    lc_cooldown: float = param(4.0, "s", "Spurwechsel: Sperrzeit", min=0.0, max=30.0)
    lc_done_d: float = param(0.4, "m", "Spurwechsel abgeschlossen bei |d| <", min=0.05, max=2.0)
    lc_abort_unsafe: bool = param(True, "", "unsicheren Spurwechsel vor Spurgrenze abbrechen")
    lc_min_speed: float = param(5.0, "m/s", "min. Geschwindigkeit für Spurwechsel", min=0.0, max=30.0)
    exit_prepare_distance: float = param(800.0, "m", "Ausfahrt: Vorbereitungsstrecke je Spur", min=50.0, max=5000.0)
    adopt_time: float = param(1.0, "s", "Spurübernahme nach Ausweichen", min=0.1, max=10.0)
    idm_a: float = param(1.5, "m/s²", "Ego-IDM: Beschleunigung", min=0.1, max=5.0)
    idm_b: float = param(2.0, "m/s²", "Ego-IDM: komfortable Verzögerung", min=0.1, max=9.0)
    idm_T: float = param(1.2, "s", "Ego-IDM: Zeitlücke", min=0.1, max=5.0)
    idm_s0: float = param(3.0, "m", "Ego-IDM: Mindestabstand", min=0.0, max=20.0)
    # overtaking on the oncoming lane
    overtake_min_dv: float = param(3.0, "m/s", "Überholen: min. Geschwindigkeitsvorteil", min=0.5, max=20.0)
    overtake_margin_time: float = param(3.0, "s", "Überholen: Sicherheitszeit Gegenverkehr", min=0.0, max=20.0)
    overtake_return_gap: float = param(10.0, "m", "Überholen: Abstand vor dem Wiedereinscheren", min=0.0, max=100.0)
    overtake_max_distance: float = param(600.0, "m", "Überholen: max. Überholweg", min=50.0, max=3000.0)
    # merging (Werling 5.3.2, eq. 3.15)
    merge_horizon: float = param(8.0, "s", "Einfädeln: max. Planungshorizont", min=1.0, max=30.0)
    merge_margin: float = param(3.0, "m", "Einfädeln: Sicherheitsabstand in der Lücke", min=0.0, max=20.0)
    merge_time_gap: float = param(0.6, "s", "Einfädeln: Zeitlücke je Seite", min=0.0, max=3.0)
    merge_a_max: float = param(3.0, "m/s²", "Einfädeln: max. Beschleunigung", min=0.1, max=5.0)
    merge_a_min: float = param(-3.0, "m/s²", "Einfädeln: max. Verzögerung", min=-9.0, max=0.0)
    merge_switch_time: float = param(2.0, "s", "Einfädeln: Vorausschau für Referenzwechsel", min=0.0, max=10.0)
    merge_hysteresis: float = param(0.5, "m/s²", "Einfädeln: Hysterese Lückenwahl", min=0.0, max=5.0)
    # stopping
    stop_margin: float = param(1.0, "m", "Anhalten: Abstand vor der Haltelinie", min=0.0, max=10.0)
    yield_gap_time: float = param(2.0, "s", "Vorfahrt: Zeitreserve der Lücke", min=0.0, max=10.0)
    stop_hold: float = param(1.0, "s", "Stoppschild: Haltezeit", min=0.0, max=10.0)
    yellow_decel: float = param(3.0, "m/s²", "Gelb: max. Verzögerung zum Anhalten", min=0.5, max=9.0)
    standstill_v: float = param(0.1, "m/s", "Stillstandsschwelle", min=0.01, max=1.0)
    end_of_lane_margin: float = param(5.0, "m", "Anhalten vor Spurende", min=0.0, max=50.0)
    # parking
    park_hold: float = param(0.5, "s", "Einparken: Haltezeit vor Richtungswechsel", min=0.0, max=10.0)
    park_tol: float = param(0.6, "m", "Einparken: Positionstoleranz", min=0.05, max=3.0)
    # corridor (box restriction)
    box_lookahead_time: float = param(2.0, "s", "Korridor: Vorausschau", min=0.0, max=10.0)
    use_opposite_lane: bool = param(True, "", "Gegenfahrbahn bei gestrichelter Linie im Korridor")
    use_parking_lane: bool = param(True, "", "Parkstreifen im Korridor")
    # hazard indicator (Werling 3.6)
    hazard_cost_threshold: float = param(1e6, "-", "Gefahrenindikator: Kostenschwelle", min=0.0)
    hazard_on_invalid: bool = param(True, "", "Gefahrenindikator: ungültige Trajektorie")
    hazard_hold: float = param(1.0, "s", "Gefahrenindikator: Spurwechselsperre", min=0.0, max=10.0)
    route_ahead: float = param(1500.0, "m", "Länge der Referenzkurve voraus", min=100.0, max=10000.0)
