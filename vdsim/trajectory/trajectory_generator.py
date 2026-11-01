"""Maneuver generator: ISO test maneuvers, standard maneuvers, road types and custom test cycles.

Every maneuver is a function registered under the kind "maneuver" that returns a Trajectory.
MANEUVER_INFO holds German labels for the GUI. Speeds in the parameters are in km/h,
everything inside is SI.
"""

import json

import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import lsq_linear

from ..core.registry import register
from .speed_profile import speed_profile
from .trajectory import Trajectory

KMH = 1 / 3.6
MANEUVER_INFO = {}


def maneuver(name, label, category, description, **param_labels):
    def decorator(fn):
        register("maneuver", name)(fn)
        MANEUVER_INFO[name] = {"label": label, "category": category, "description": description,
                               "params": param_labels}
        return fn
    return decorator


class PathBuilder:
    # Path from curvature segments (straight, arc, clothoid, offset); integrated exactly per segment
    def __init__(self, ds=0.25):
        self.ds = ds
        self.segments = []  # (length, kappa_fn(local s), speed or None)

    @property
    def end_curvature(self):
        if not self.segments:
            return 0.0
        length, fn, _ = self.segments[-1]
        return float(fn(np.array([length]))[0])

    def straight(self, length, v=None):
        self.segments.append((length, lambda s: np.zeros_like(s), v))
        return self

    def arc(self, radius, angle_deg, v=None):
        k = np.sign(angle_deg) / radius
        self.segments.append((radius * np.radians(abs(angle_deg)), lambda s, k=k: np.full_like(s, k), v))
        return self

    def clothoid(self, length, k_end, k_start=None, v=None):
        k0 = self.end_curvature if k_start is None else k_start
        self.segments.append((length, lambda s, k0=k0, k1=k_end, L=length: k0 + (k1 - k0) * s / L, v))
        return self

    def turn(self, radius, angle_deg, transition=0.0, v=None):
        # clothoid - arc - clothoid; the clothoids take transition/R of the total angle
        k = np.sign(angle_deg) / radius
        arc_angle = np.degrees(np.radians(abs(angle_deg)) - transition / radius)
        if transition > 0:
            self.clothoid(transition, k, k_start=0.0, v=v)
        self.arc(radius, np.sign(angle_deg) * max(arc_angle, 0.0), v=v)
        if transition > 0:
            self.clothoid(transition, 0.0, k_start=k, v=v)
        return self

    def offset(self, length, lateral, v=None):
        # smooth lateral offset (sinusoidal curvature, zero curvature at both ends)
        amp = 2 * np.pi * lateral / length**2
        self.segments.append((length, lambda s, a=amp, L=length: a * np.sin(2 * np.pi * s / L), v))
        return self

    def build(self, v_default=10.0, name="", x0=0.0, y0=0.0, psi0=0.0, refine=8):
        xs, ys, ps, ks, vs = [np.array([x0])], [np.array([y0])], [np.array([psi0])], [], []
        x, y, psi = x0, y0, psi0
        first_k = None
        for length, fn, v in self.segments:
            n = max(int(np.ceil(length / self.ds)), 2)
            fine = np.linspace(0.0, length, n * refine + 1)
            k = fn(fine)
            first_k = k[0] if first_k is None else first_k
            psi_f = psi + cumulative_trapezoid(k, fine, initial=0.0)
            x_f = x + cumulative_trapezoid(np.cos(psi_f), fine, initial=0.0)
            y_f = y + cumulative_trapezoid(np.sin(psi_f), fine, initial=0.0)
            pick = slice(refine, None, refine)
            xs.append(x_f[pick]); ys.append(y_f[pick]); ps.append(psi_f[pick]); ks.append(k[pick])
            vs.append(np.full(n, v_default if v is None else v))
            x, y, psi = x_f[-1], y_f[-1], psi_f[-1]
        kappa = np.concatenate([[first_k or 0.0]] + ks)
        speed = np.concatenate([vs[0][:1]] + vs) if vs else np.array([v_default])
        traj = Trajectory(np.concatenate(xs), np.concatenate(ys), speed, name)
        if len(traj.x) == len(kappa):
            traj.kappa = kappa
            traj.psi = np.concatenate(ps)
        return traj


def _constant_speed(traj, speed_kmh, name, **meta):
    traj.v = np.full(len(traj.x), speed_kmh * KMH)
    traj.name = name
    traj.metadata.update(maneuver=name, speed=speed_kmh * KMH, **meta)
    return traj


def _lane_cones(x_start, x_end, y_center, width, spacing=5.0):
    xs = np.linspace(x_start, x_end, max(int(round((x_end - x_start) / spacing)) + 1, 2))
    return [(float(x), float(y_center + side * width / 2)) for x in xs for side in (1, -1)]


def _smooth_step(xi):
    # 0 -> 1 with zero slope and zero curvature at both ends
    xi = np.clip(xi, 0.0, 1.0)
    return xi - np.sin(2 * np.pi * xi) / (2 * np.pi)


def _path_from_sections(sections, pre=30.0, post=60.0, dx=0.25):
    # sections: list of (length, y_center or None for transition); returns x, y and lane geometry
    x_edges = np.concatenate([[0.0], np.cumsum([length for length, _ in sections])]) + pre
    centers = [c for _, c in sections]
    x = np.arange(0.0, x_edges[-1] + post, dx)
    y = np.full_like(x, centers[0])
    for i, (length, center) in enumerate(sections):
        x0, x1 = x_edges[i], x_edges[i + 1]
        inside = (x >= x0) & (x <= x1)
        if center is None:
            y_prev, y_next = centers[i - 1], centers[i + 1]
            y[inside] = y_prev + (y_next - y_prev) * _smooth_step((x[inside] - x0) / length)
        else:
            y[inside] = center
    y[x > x_edges[-1]] = centers[-1]
    return x, y, x_edges


def _gate_line(x, gates, vehicle_width, margin=0.15, free=8.0, knot_spacing=2.0):
    # Minimum-curvature line y(x) through the cone gates (what a good driver drives):
    # minimize sum(y''^2) on a coarse grid with y inside each gate corridor
    # (gate width minus vehicle width), then a C2 cubic spline on the fine grid
    from scipy.interpolate import CubicSpline
    xc = np.arange(x[0], x[-1] + knot_spacing / 2, knot_spacing)
    n = len(xc)
    D2 = (np.eye(n, k=-1)[1:-1] - 2 * np.eye(n)[1:-1] + np.eye(n, k=1)[1:-1]) / knot_spacing**2
    lower, upper = np.full(n, -free), np.full(n, free)
    for x0, x1, center, width in gates:
        half = max(width / 2 - vehicle_width / 2 - margin, 0.02)
        inside = (xc >= x0) & (xc <= x1)
        lower[inside], upper[inside] = center - half, center + half
    first, last = gates[0], gates[-1]
    before = xc <= first[0]
    lower[before] = upper[before] = first[2]          # straight run-in on the entry lane center
    after = xc >= last[1]
    lower[after] = upper[after] = last[2]             # leave on the exit lane center
    res = lsq_linear(D2, np.zeros(n - 2), bounds=(lower - 1e-9, upper + 1e-9), method="bvls")
    return CubicSpline(xc, res.x, bc_type="clamped")(x)


# ----------------------------------------------------------------------------------------------
# ISO and standard closed-loop maneuvers
# ----------------------------------------------------------------------------------------------

@maneuver("straight", "Geradeausfahrt", "Basis", "Gerade Strecke mit konstanter Geschwindigkeit",
          length=("Länge", "m"), speed_kmh=("Geschwindigkeit", "km/h"))
def straight(length=300.0, speed_kmh=50.0):
    traj = PathBuilder().straight(length).build()
    return _constant_speed(traj, speed_kmh, "straight")


@maneuver("lane_change", "Spurwechsel", "Basis",
          "Einfacher Spurwechsel mit sinusförmiger Krümmung (Kurswinkel am Ende 0)",
          speed_kmh=("Geschwindigkeit", "km/h"), width=("Querversatz", "m"), duration=("Dauer", "s"),
          pre_length=("Vorlauf", "m"), post_length=("Nachlauf", "m"))
def lane_change(speed_kmh=120.0, width=3.5, duration=6.0, pre_length=40.0, post_length=150.0):
    length = speed_kmh * KMH * duration
    traj = PathBuilder().straight(pre_length).offset(length, width).straight(post_length).build()
    traj.boundaries = _lane_lines(traj, width)
    return _constant_speed(traj, speed_kmh, "lane_change", width=width, lane_change_duration=duration)


def _lane_lines(traj, lane_width, n_lanes=2):
    x_max = traj.x.max() + 10
    ys = [-lane_width / 2 + i * lane_width for i in range(n_lanes + 1)]
    return [(np.array([traj.x.min() - 10, x_max]), np.array([y, y])) for y in ys]


@maneuver("iso_double_lane_change", "ISO-Doppelspurwechsel (ISO 3888-1)", "ISO",
          "Doppelter Spurwechsel mit Pylonengassen nach ISO 3888-1 (Versatz 3,5 m)",
          speed_kmh=("Geschwindigkeit", "km/h"), vehicle_width=("Fahrzeugbreite", "m"))
def iso_double_lane_change(speed_kmh=80.0, vehicle_width=1.85):
    b = vehicle_width
    w1, w3, w5 = 1.1 * b + 0.25, 1.2 * b + 0.25, 1.3 * b + 0.25
    sections = [(15.0, 0.0), (30.0, None), (25.0, 3.5), (25.0, None), (15.0, 0.0), (15.0, 0.0)]
    x, y, edges = _path_from_sections(sections, dx=0.5)
    gates = [(edges[0], edges[1], 0.0, w1), (edges[2], edges[3], 3.5, w3), (edges[4], edges[5], 0.0, w5)]
    traj = Trajectory(x, _gate_line(x, gates, b), speed_kmh * KMH)
    traj.cones = (_lane_cones(edges[0], edges[1], 0.0, w1) + _lane_cones(edges[2], edges[3], 3.5, w3)
                  + _lane_cones(edges[4], edges[5], 0.0, w5))
    return _constant_speed(traj, speed_kmh, "iso_double_lane_change", gates=gates, vehicle_width=b)


@maneuver("iso_obstacle_avoidance", "ISO-Ausweichtest (ISO 3888-2)", "ISO",
          "Ausweichmanöver nach ISO 3888-2 (\"Elchtest\")",
          speed_kmh=("Einfahrgeschwindigkeit", "km/h"), vehicle_width=("Fahrzeugbreite", "m"))
def iso_obstacle_avoidance(speed_kmh=60.0, vehicle_width=1.85):
    b = vehicle_width
    w1, w3, w5 = 1.1 * b + 0.25, b + 1.0, max(1.3 * b + 0.25, 3.0)
    c3 = w1 / 2 + 1.0 + w3 / 2
    c5 = -w1 / 2 + w5 / 2
    sections = [(12.0, 0.0), (13.5, None), (11.0, c3), (12.5, None), (12.0, c5), (10.0, c5)]
    x, y, edges = _path_from_sections(sections, dx=0.5)
    gates = [(edges[0], edges[1], 0.0, w1), (edges[2], edges[3], c3, w3), (edges[4], edges[5], c5, w5)]
    traj = Trajectory(x, _gate_line(x, gates, b), speed_kmh * KMH)
    traj.cones = (_lane_cones(edges[0], edges[1], 0.0, w1, 4.0) + _lane_cones(edges[2], edges[3], c3, w3, 3.7)
                  + _lane_cones(edges[4], edges[5], c5, w5, 4.0))
    return _constant_speed(traj, speed_kmh, "iso_obstacle_avoidance", gates=gates, vehicle_width=b)


@maneuver("slalom", "Slalom", "Fahrmanöver", "Slalom um Pylonen in gleichem Abstand",
          speed_kmh=("Geschwindigkeit", "km/h"), spacing=("Pylonenabstand", "m"),
          n_cones=("Anzahl Pylonen", "-"), amplitude=("Seitlicher Abstand", "m"))
def slalom(speed_kmh=45.0, spacing=18.0, n_cones=8, amplitude=1.3):
    # cones at x_i = pre + spacing * (i + 0.5); full lateral amplitude from half a spacing before the
    # first to half a spacing after the last cone, smooth ramps outside
    n = int(n_cones)
    pre, post = 50.0, 60.0
    x = np.arange(0.0, pre + n * spacing + post, 0.25)
    ramp_in = _smooth_step((x - (pre - spacing)) / spacing)
    ramp_out = 1.0 - _smooth_step((x - (pre + n * spacing)) / spacing)
    y = amplitude * np.sin(np.pi * (x - pre) / spacing) * ramp_in * ramp_out
    traj = Trajectory(x, y, speed_kmh * KMH)
    traj.cones = [(pre + spacing * (i + 0.5), 0.0) for i in range(n)]
    return _constant_speed(traj, speed_kmh, "slalom", spacing=spacing)


@maneuver("circle", "Kreisfahrt (ISO 4138)", "ISO",
          "Stationäre Kreisfahrt mit langsam steigender Geschwindigkeit (Eigenlenkgradient)",
          radius=("Radius", "m"), laps=("Runden", "-"), speed_start_kmh=("Startgeschwindigkeit", "km/h"),
          speed_end_kmh=("Endgeschwindigkeit", "km/h"))
def circle(radius=40.0, laps=3.0, speed_start_kmh=20.0, speed_end_kmh=70.0):
    builder = PathBuilder().straight(20.0).turn(radius, 360.0 * laps, transition=10.0)
    traj = builder.build(name="circle")
    traj.v = np.interp(traj.s, [0, traj.length], [speed_start_kmh * KMH, speed_end_kmh * KMH])
    traj.name = "circle"
    traj.metadata.update(maneuver="circle", radius=radius)
    return traj


@maneuver("figure_eight", "Acht", "Fahrmanöver", "Liegende Acht aus zwei Kreisen",
          radius=("Radius", "m"), speed_kmh=("Geschwindigkeit", "km/h"), laps=("Durchgänge", "-"))
def figure_eight(radius=20.0, speed_kmh=30.0, laps=1):
    builder = PathBuilder().straight(10.0)
    for _ in range(int(laps)):
        builder.turn(radius, 360.0, transition=5.0).turn(radius, -360.0, transition=5.0)
    builder.straight(20.0)
    return _constant_speed(builder.build(), speed_kmh, "figure_eight", radius=radius)


@maneuver("emergency_evasion", "Notausweichen", "Fahrmanöver",
          "Schnelles Ausweichen um ein Hindernis und Rückkehr in die Spur",
          speed_kmh=("Geschwindigkeit", "km/h"), offset=("Ausweichversatz", "m"),
          evade_length=("Ausweichstrecke", "m"), hold_length=("Haltestrecke", "m"),
          return_length=("Rückkehrstrecke", "m"))
def emergency_evasion(speed_kmh=60.0, offset=3.0, evade_length=22.0, hold_length=8.0, return_length=28.0):
    builder = PathBuilder().straight(40.0).offset(evade_length, offset).straight(hold_length)
    builder.offset(return_length, -offset).straight(60.0)
    traj = builder.build()
    obstacle_x = 40.0 + evade_length + hold_length / 2
    traj.cones = [(obstacle_x + dx, dy) for dx in (-2.0, 0.0, 2.0) for dy in (-0.9, 0.0, 0.9)]
    return _constant_speed(traj, speed_kmh, "emergency_evasion", offset=offset)


@maneuver("braking", "Bremsen (Geradeaus)", "Fahrmanöver", "Bremsung aus konstanter Geschwindigkeit",
          speed_kmh=("Anfangsgeschwindigkeit", "km/h"), deceleration=("Verzögerung", "m/s²"),
          brake_time=("Bremsbeginn", "s"))
def braking(speed_kmh=100.0, deceleration=10.0, brake_time=1.0):
    v0 = speed_kmh * KMH
    traj = PathBuilder().straight(v0 * brake_time + v0**2 / 2 + 100.0).build()
    traj = _constant_speed(traj, speed_kmh, "braking", deceleration=deceleration)
    traj.accel_table = (np.array([0.0, brake_time, brake_time + 0.15, 1e3]),
                        np.array([0.0, 0.0, -abs(deceleration), -abs(deceleration)]))
    return traj


@maneuver("acceleration", "Beschleunigen (0-100 km/h)", "Fahrmanöver", "Volllastbeschleunigung aus dem Stand",
          target_kmh=("Zielgeschwindigkeit", "km/h"), request=("Angeforderte Beschleunigung", "m/s²"))
def acceleration(target_kmh=100.0, request=12.0):
    traj = PathBuilder().straight(600.0).build()
    traj = _constant_speed(traj, target_kmh, "acceleration", initial_speed=0.0, target=target_kmh * KMH)
    traj.accel_table = (np.array([0.0, 0.3, 1e3]), np.array([0.0, request, request]))
    return traj


@maneuver("brake_in_turn", "Bremsen in der Kurve (ISO 7975)", "ISO",
          "Stationäre Kreisfahrt, dann Bremsung mit konstanter Verzögerung",
          radius=("Radius", "m"), speed_kmh=("Geschwindigkeit", "km/h"),
          deceleration=("Verzögerung", "m/s²"), brake_time=("Bremsbeginn", "s"))
def brake_in_turn(radius=100.0, speed_kmh=80.0, deceleration=4.0, brake_time=6.0):
    traj = PathBuilder().straight(30.0).turn(radius, 300.0, transition=15.0).build()
    traj = _constant_speed(traj, speed_kmh, "brake_in_turn", radius=radius)
    traj.accel_table = (np.array([0.0, brake_time, brake_time + 0.3, 1e3]),
                        np.array([0.0, 0.0, -abs(deceleration), -abs(deceleration)]))
    return traj


# ----------------------------------------------------------------------------------------------
# Open-loop steering maneuvers (straight reference path for plots, steering from a table)
# ----------------------------------------------------------------------------------------------

def _open_loop(name, speed_kmh, duration, t, steer_wheel_deg, steering_ratio, **meta):
    v = speed_kmh * KMH
    traj = PathBuilder().straight(v * duration + 50.0).build()
    traj = _constant_speed(traj, speed_kmh, name, steering_ratio=steering_ratio, **meta)
    traj.steer_table = (np.asarray(t, dtype=float), np.radians(np.asarray(steer_wheel_deg, dtype=float)) / steering_ratio)
    traj.metadata["duration"] = duration
    return traj


@maneuver("step_steer", "Lenkwinkelsprung (ISO 7401)", "ISO", "Sprungförmige Lenkeingabe bei konstanter Geschwindigkeit",
          speed_kmh=("Geschwindigkeit", "km/h"), steering_wheel_deg=("Lenkradwinkel", "°"),
          rise_time=("Anstiegszeit", "s"), duration=("Dauer", "s"), steering_ratio=("Lenkübersetzung", "-"))
def step_steer(speed_kmh=80.0, steering_wheel_deg=40.0, rise_time=0.15, duration=6.0, steering_ratio=15.0):
    t = [0.0, 1.0, 1.0 + rise_time, duration]
    return _open_loop("step_steer", speed_kmh, duration, t, [0, 0, steering_wheel_deg, steering_wheel_deg],
                      steering_ratio, step_time=1.0 + rise_time / 2)


@maneuver("ramp_steer", "Lenkwinkelrampe (ISO 4138)", "ISO", "Langsam steigender Lenkwinkel bei konstanter Geschwindigkeit",
          speed_kmh=("Geschwindigkeit", "km/h"), steer_rate_deg=("Lenkradwinkelgeschwindigkeit", "°/s"),
          duration=("Dauer", "s"), steering_ratio=("Lenkübersetzung", "-"))
def ramp_steer(speed_kmh=80.0, steer_rate_deg=8.0, duration=20.0, steering_ratio=15.0):
    t = [0.0, 1.0, duration]
    return _open_loop("ramp_steer", speed_kmh, duration, t, [0, 0, steer_rate_deg * (duration - 1.0)], steering_ratio)


@maneuver("sine_with_dwell", "Sinus mit Haltezeit (FMVSS 126)", "ISO", "ESC-Prüfmanöver: 0,7-Hz-Sinus mit 500 ms Haltezeit",
          speed_kmh=("Geschwindigkeit", "km/h"), amplitude_deg=("Lenkradamplitude", "°"),
          frequency=("Frequenz", "Hz"), dwell=("Haltezeit", "s"), steering_ratio=("Lenkübersetzung", "-"))
def sine_with_dwell(speed_kmh=80.0, amplitude_deg=180.0, frequency=0.7, dwell=0.5, steering_ratio=15.0):
    t0, period = 1.0, 1.0 / frequency
    t1 = np.linspace(0, 0.75 * period, 60)
    t3 = np.linspace(0.75 * period, period, 20)
    t = np.concatenate([[0.0], t0 + t1, t0 + 0.75 * period + dwell + (t3 - 0.75 * period), [t0 + period + dwell + 4.0]])
    angle = np.concatenate([[0.0], amplitude_deg * np.sin(2 * np.pi * frequency * t1),
                            amplitude_deg * np.sin(2 * np.pi * frequency * t3), [0.0]])
    t = np.insert(t, 1, t0)
    angle = np.insert(angle, 1, 0.0)
    return _open_loop("sine_with_dwell", speed_kmh, float(t[-1]), t, angle, steering_ratio)


@maneuver("frequency_sweep", "Frequenzgang (Sinus-Sweep)", "ISO", "Lenk-Sweep zur Bestimmung des Frequenzgangs (ISO 7401)",
          speed_kmh=("Geschwindigkeit", "km/h"), amplitude_deg=("Lenkradamplitude", "°"),
          f_start=("Startfrequenz", "Hz"), f_end=("Endfrequenz", "Hz"), duration=("Dauer", "s"),
          steering_ratio=("Lenkübersetzung", "-"))
def frequency_sweep(speed_kmh=80.0, amplitude_deg=20.0, f_start=0.1, f_end=3.0, duration=30.0, steering_ratio=15.0):
    t = np.linspace(0.0, duration, int(duration * 200))
    phase = 2 * np.pi * (f_start * t + (f_end - f_start) * t**2 / (2 * duration))
    angle = amplitude_deg * np.sin(phase) * np.clip(t / 1.0, 0, 1)
    return _open_loop("frequency_sweep", speed_kmh, duration, t, angle, steering_ratio, f_start=f_start, f_end=f_end)


# ----------------------------------------------------------------------------------------------
# Roads and tracks
# ----------------------------------------------------------------------------------------------

@maneuver("highway", "Autobahnfahrt", "Strecke", "Autobahn mit Klothoiden-Kurven und Spurwechsel",
          speed_kmh=("Richtgeschwindigkeit", "km/h"), ay_max=("Max. Querbeschleunigung", "m/s²"))
def highway(speed_kmh=130.0, ay_max=2.0):
    b = PathBuilder(ds=0.5)
    b.straight(400).turn(1200, 25, transition=150).straight(300).offset(200, 3.75).straight(300)
    b.turn(900, -30, transition=180).straight(400).turn(1500, 15, transition=150).straight(300)
    traj = b.build()
    traj.v = speed_profile(traj.s, traj.kappa, speed_kmh * KMH, ay_max, 1.5, -2.0, v_start=speed_kmh * KMH)
    traj.name = "highway"
    traj.metadata.update(maneuver="highway", speed=speed_kmh * KMH)
    return traj


@maneuver("city", "Stadtverkehr", "Strecke", "Innerstädtischer Rundkurs mit Abbiegevorgängen",
          speed_kmh=("Höchstgeschwindigkeit", "km/h"), ay_max=("Max. Querbeschleunigung", "m/s²"))
def city(speed_kmh=50.0, ay_max=2.5):
    b = PathBuilder(ds=0.25)
    b.straight(120).turn(12, 90, transition=4).straight(80).turn(15, -90, transition=4).straight(150)
    b.turn(12, 90, transition=4).straight(60).turn(10, 90, transition=3).straight(200)
    b.turn(25, -45, transition=6).straight(80).turn(25, 45, transition=6).straight(100)
    traj = b.build()
    traj.v = speed_profile(traj.s, traj.kappa, speed_kmh * KMH, ay_max, 1.5, -2.5,
                           v_start=speed_kmh * KMH * 0.6)
    traj.name = "city"
    traj.metadata.update(maneuver="city")
    return traj


def _track_centerline():
    # Closed circuit: oval with a chicane and a double-apex corner (counter-clockwise)
    b = PathBuilder(ds=1.0)
    main = 450.0
    chicane_r, chicane_deg = 40.0, 20.0
    chicane_dx = 4 * chicane_r * np.sin(np.radians(chicane_deg))
    b.straight(main).turn(50.0, 180.0)
    back = (main - chicane_dx) / 2
    b.straight(back).arc(chicane_r, chicane_deg).arc(chicane_r, -2 * chicane_deg).arc(chicane_r, chicane_deg)
    b.straight(back).arc(40.0, 90.0).straight(20.0).arc(40.0, 90.0)
    return b.build()


def racing_line(center, width, margin=1.0, iterations=3):
    # Minimum-curvature line inside the track (linearized least squares with bounds)
    s = np.linspace(0.0, center.length, int(center.length / 3.0), endpoint=False)
    cx, cy = np.interp(s, center.s, center.x), np.interp(s, center.s, center.y)
    psi = np.interp(s, center.s, center.psi)
    nx, ny = -np.sin(psi), np.cos(psi)
    n = len(s)
    h = s[1] - s[0]
    D2 = (np.roll(np.eye(n), 1, axis=1) - 2 * np.eye(n) + np.roll(np.eye(n), -1, axis=1)) / h**2
    D1 = (np.roll(np.eye(n), -1, axis=1) - np.roll(np.eye(n), 1, axis=1)) / (2 * h)
    offset = np.zeros(n)
    bound = width / 2 - margin
    for _ in range(iterations):
        px, py = cx + offset * nx, cy + offset * ny
        dx, dy = D1 @ px, D1 @ py
        norm = np.maximum(dx**2 + dy**2, 1e-9) ** 1.5
        # curvature = (x' y'' - y' x'') / |r'|^3, linear in the offset for fixed x', y'
        A = (dx[:, None] * D2 * ny[None, :] - dy[:, None] * D2 * nx[None, :]) / norm[:, None]
        kappa_c = (dx * (D2 @ cx) - dy * (D2 @ cy)) / norm
        res = lsq_linear(A, -kappa_c, bounds=(-bound, bound))
        offset = res.x
    x, y = cx + offset * nx, cy + offset * ny
    return np.append(x, x[0]), np.append(y, y[0])


@maneuver("race_track", "Rennstrecke (Ideallinie)", "Strecke",
          "Rundkurs mit berechneter Ideallinie (minimale Krümmung) und GGV-Geschwindigkeitsprofil",
          track_width=("Streckenbreite", "m"), ay_max=("Max. Querbeschleunigung", "m/s²"),
          ax_max=("Max. Längsbeschleunigung", "m/s²"), ax_min=("Max. Verzögerung", "m/s²"),
          v_max_kmh=("Höchstgeschwindigkeit", "km/h"), laps=("Runden", "-"))
def race_track(track_width=12.0, ay_max=7.0, ax_max=3.5, ax_min=-6.5, v_max_kmh=230.0, laps=1):
    center = _track_centerline()
    x, y = racing_line(center, track_width)
    x, y = np.tile(x[:-1], int(laps)), np.tile(y[:-1], int(laps))
    x, y = np.append(x, x[0]), np.append(y, y[0])
    traj = Trajectory(x, y).resample(1.0)
    traj.kappa = _smooth(traj.kappa, 7)
    traj.v = speed_profile(traj.s, traj.kappa, v_max_kmh * KMH, ay_max, ax_max, ax_min)
    left = (center.x - track_width / 2 * np.sin(center.psi), center.y + track_width / 2 * np.cos(center.psi))
    right = (center.x + track_width / 2 * np.sin(center.psi), center.y - track_width / 2 * np.cos(center.psi))
    traj.boundaries = [left, right]
    traj.name = "race_track"
    traj.metadata.update(maneuver="race_track", track_width=track_width)
    return traj


def _smooth(values, window):
    kernel = np.ones(window) / window
    pad = window // 2
    return np.convolve(np.pad(values, pad, mode="edge"), kernel, mode="valid")[:len(values)]


@maneuver("custom", "Kundenspezifischer Testzyklus", "Strecke",
          "Segmentliste als JSON: [[\"straight\", L, v_kmh], [\"arc\", R, Winkel°, v_kmh], "
          "[\"clothoid\", L, kappa_end, v_kmh], [\"offset\", L, Versatz, v_kmh]]",
          segments=("Segmente (JSON)", ""), ay_max=("Max. Querbeschleunigung", "m/s²"))
def custom(segments='[["straight", 100, 50], ["turn", 30, 90, 40], ["straight", 80, 50], ["offset", 60, 3.5, 50], '
                    '["straight", 100, 70]]', ay_max=4.0):
    items = json.loads(segments) if isinstance(segments, str) else segments
    b = PathBuilder()
    speeds = []
    for item in items:
        kind, args = item[0], list(item[1:])
        speed = None
        if kind == "straight":
            speed = args[1] if len(args) > 1 else None
            b.straight(args[0], v=speed and speed * KMH)
        elif kind in ("arc", "turn"):
            speed = args[2] if len(args) > 2 else None
            b.turn(args[0], args[1], transition=min(args[0] * 0.3, 15.0), v=speed and speed * KMH)
        elif kind == "clothoid":
            speed = args[2] if len(args) > 2 else None
            b.clothoid(args[0], args[1], v=speed and speed * KMH)
        elif kind == "offset":
            speed = args[2] if len(args) > 2 else None
            b.offset(args[0], args[1], v=speed and speed * KMH)
        else:
            raise ValueError(f"unknown segment type '{kind}'")
        speeds.append(speed or 50.0)
    traj = b.build(v_default=max(speeds) * KMH)
    traj.v = speed_profile(traj.s, traj.kappa, traj.v, ay_max, 2.0, -3.0)  # segment speeds as upper limit
    traj.name = "custom"
    traj.metadata.update(maneuver="custom")
    return traj


def generate(name, **params):
    from ..core.registry import get
    return get("maneuver", name)(**params)
