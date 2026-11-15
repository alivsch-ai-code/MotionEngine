"""English texts of the reports: KPI labels, groups, values, plot labels, stop reasons.

The library labels are German. `english(text)` returns the English text of a known German label and the text
itself otherwise, so a new label appears untranslated instead of failing. `tests/reporting` checks that the labels
of the standard report are covered.
"""

KPI_LABELS_EN = {
    "max_ay": "Max. lateral acceleration",
    "max_ax": "Max. longitudinal acceleration",
    "min_ax": "Max. deceleration",
    "max_yaw_rate": "Max. yaw rate",
    "max_beta": "Max. side-slip angle",
    "max_roll": "Max. roll angle",
    "max_steer": "Max. road-wheel angle",
    "max_lateral_error": "Max. path deviation",
    "rms_lateral_error": "RMS path deviation",
    "max_friction_utilization": "Max. friction utilization",
    "stability_reserve": "Stability reserve (1 - utilization)",
    "mean_speed": "Mean speed",
    "distance": "Distance",
    "duration": "Simulated time",
    "iso2631_aw": "Weighted vertical accel. a_w (ISO 2631)",
    "iso2631_rating": "Comfort rating (ISO 2631)",
    "max_pitch": "Max. pitch angle",
    "rms_ay": "RMS lateral acceleration",
    "rms_lateral_jerk": "RMS lateral jerk",
    "max_lateral_jerk": "Max. lateral jerk",
    "energy_drive": "Energy demand (drive)",
    "energy_regen": "Recuperated energy",
    "consumption": "Consumption",
    "cone_hits": "Lane gate violations",
    "test_passed": "Test passed",
    "entry_speed": "Entry speed",
    "understeer_gradient": "Understeer gradient",
    "understeer_gradient_g": "Understeer gradient",
    "max_ay_steady": "Max. steady-state lateral acceleration",
    "yaw_gain": "Steady-state yaw gain",
    "ay_gain": "Steady-state lateral acceleration gain",
    "response_time": "Yaw rate response time (90 %)",
    "peak_response_time": "Time to yaw rate peak",
    "yaw_overshoot": "Yaw rate overshoot",
    "yaw_ratio_1s": "Yaw rate 1.0 s after steering end",
    "yaw_ratio_175s": "Yaw rate 1.75 s after steering end",
    "lateral_displacement": "Lateral displacement 1.07 s after steering start",
    "stopping_distance": "Stopping distance",
    "brake_speed": "Initial braking speed",
    "mfdd": "Mean fully developed deceleration (MFDD)",
    "max_yaw_deviation": "Max. yaw angle deviation",
    "lap_time": "Lap time",
    "yaw_resonance": "Frequency of max. yaw gain",
    "yaw_gain_peak_ratio": "Yaw gain peak ratio",
    "yaw_gain_1hz_ratio": "Yaw gain 1 Hz / steady state",
    "min_gap": "Min. gap",
    "min_time_gap": "Min. time gap",
    "collision": "Collision",
    "aeb_trigger_ttc": "AEB triggered at TTC",
    "min_distance_to_line": "Min. distance to lane marking",
    "lane_departure": "Lane departure",
    "lka_active_time": "LKA intervention time",
}

KPI_GROUPS_EN = {
    "Fahrdynamik": "Vehicle dynamics", "Bahnführung": "Path tracking", "Allgemein": "General", "Komfort": "Comfort",
    "Energie": "Energy", "Normtest": "Standard test", "Bremsen": "Braking", "Beschleunigen": "Acceleration",
    "Rennstrecke": "Race track", "Frequenzgang": "Frequency response", "Fahrerassistenz": "Driver assistance",
}

KPI_VALUES_EN = {
    "ja": "yes", "nein": "no", "nicht unkomfortabel": "not uncomfortable", "etwas unkomfortabel": "a little uncomfortable",
    "ziemlich unkomfortabel": "fairly uncomfortable", "unkomfortabel": "uncomfortable",
    "sehr unkomfortabel": "very uncomfortable", "extrem unkomfortabel": "extremely uncomfortable",
}

RATINGS_EN = {"OK": "OK", "Hinweis": "note", "nicht erfüllt": "not met"}

STOP_REASONS_EN = {
    "Simulationsdauer erreicht": "simulation time reached", "Ende der Trajektorie": "end of the trajectory",
    "Fahrzeug steht": "vehicle at standstill", "Zielgeschwindigkeit erreicht": "target speed reached",
    "Kollision mit vorausfahrendem Fahrzeug": "collision with the leading vehicle",
    "numerisch instabil (NaN)": "numerically unstable (NaN)",
    "Fahrzeug instabil (Schleudern/Überschlag)": "vehicle unstable (spin or rollover)",
    "Rechenzeitlimit": "computing time limit",
}

PLOT_LABELS_EN = {
    "Anforderung": "request", "Antrieb mechanisch": "drive, mechanical", "Aufbaubewegung": "Body motion",
    "Bahnabweichung": "Path deviation", "Batterie/Kraftstoff": "battery / fuel", "Beschleunigungen": "Accelerations",
    "Betrag (dB)": "Magnitude (dB)", "Bode-Diagramm (lineares Einspurmodell)": "Bode diagram (linear single-track model)",
    "Energie": "Energy", "Energiebedarf": "Energy demand", "Fahrzeug": "vehicle", "Fahrzeugpfad": "Vehicle path",
    "Federwege (+ = Einfedern)": "Suspension travel (+ = compression)",
    "Federwege nur im Mehrkörpermodell": "Suspension travel only in the multibody model", "GGV-Diagramm": "GGV diagram",
    "Geschwindigkeit": "Speed", "Gierrate": "Yaw rate", "Gierrate (°/s)": "yaw rate (°/s)",
    "Gierrate / Radlenkwinkel": "Yaw rate / road-wheel angle",
    "Gierrate, Schwimm- und Wankwinkel": "Yaw rate, side-slip and roll angle", "Hub (mm)": "heave (mm)",
    "Leistung": "Power", "Lenkwinkel": "Steering angle", "Längsschlupf": "Longitudinal slip",
    "Längsschlupf (%)": "Longitudinal slip (%)", "Nicken (°)": "pitch (°)", "Phase (°)": "Phase (°)",
    "Phasenebene Schwimmwinkel": "Phase plane of the side-slip angle", "Pylonen": "cones",
    "Querbeschleunigung": "Lateral acceleration", "Querbeschleunigung / Radlenkwinkel": "Lateral acceleration / road-wheel angle",
    "Radlasten": "Wheel loads", "Radlasten (Linkskurve)": "Wheel loads (left turn)",
    "Radlenkwinkel vorne": "road-wheel angle, front", "Referenz": "reference", "Reibwertausnutzung": "Friction utilization",
    "Reifen": "Tires", "Reifenbelastung (Radlast)": "Tire load (wheel load)", "Rekuperiert": "recuperated",
    "Schräglaufwinkel": "Slip angle", "Schräglaufwinkel (°)": "Slip angle (°)", "Schwimmwinkel (°)": "side-slip angle (°)",
    "Stabilitätsreserve (1 - max. Ausnutzung)": "Stability reserve (1 - max. utilization)",
    "Sturz zur Fahrbahn (kurvenaußen)": "Camber to the road (outside of the turn)",
    "Vergleich der Simulationsläufe": "Comparison of the simulation runs", "Wanken (°)": "roll (°)",
    "Wankwinkel (°)": "roll angle (°)", "hinten": "rear", "hinten außen": "rear, outside", "vorne außen": "front, outside",
    "mm bzw. °": "mm or °", "°/s bzw. °": "°/s or °",
}

_ALL = {**KPI_GROUPS_EN, **KPI_VALUES_EN, **RATINGS_EN, **STOP_REASONS_EN, **PLOT_LABELS_EN}


def english(text):
    """English text of a German label of the library; unknown texts are returned unchanged."""
    return _ALL.get(text, text) if isinstance(text, str) else text


def translate_figure(fig):
    """Replace the German labels of a matplotlib figure (titles, axis labels, legends) by the English ones."""
    import matplotlib.text as mtext

    for item in fig.findobj(mtext.Text):
        text = item.get_text()
        if text in PLOT_LABELS_EN:
            item.set_text(PLOT_LABELS_EN[text])
    return fig
