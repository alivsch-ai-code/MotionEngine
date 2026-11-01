"""Motion prediction of the perceived objects (absolute time base t0 ... t0 + horizon).

predictor/constant_acceleration  Werling 3.5.2: s_v(t) = s_v(0) + s_dot_v(0) t + 1/2 s_ddot_v(0) t^2 along
                                 the lane (Frenet), lateral offset d constant, clamped at standstill;
                                 objects without lane (pedestrians, off-road) Cartesian along psi
predictor/constant_velocity      Cartesian straight line (optionally constant yaw rate, CTRV)
predictor/lane_following         constant speed along the lane sequence, lateral offset converging
                                 (critically damped) to the lane center the object is heading for
PredictedObject.s / s_dot refer to the lane chain starting at PredictedObject.lane_id (s = lane s).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core.parameters import param
from ..framework.knowledge import ComponentDoc, trace
from ..framework.layers import PredictionBase
from ..framework.types import PredictedObject, Prediction
from ..geometry.reference_line import wrap_angle

LANE_TYPES_FRENET = ("car", "truck", "cyclist", "unknown")


@dataclass
class PredictorParams:
    horizon: float = param(6.0, "s", "Prädiktionshorizont", min=0.1, max=20.0)
    dt: float = param(0.1, "s", "Zeitschritt", min=0.01, max=1.0)
    v_max: float = param(70.0, "m/s", "max. prädizierte Geschwindigkeit", min=1.0, max=100.0)
    max_heading_error_deg: float = param(60.0, "°", "max. Winkel zur Spur für Frenet-Prädiktion", min=0.0, max=90.0)
    use_lanes: bool = param(True, "", "spurbasierte Prädiktion (falls Spur bekannt)")
    chain_length: float = param(400.0, "m", "Länge der Spurfolge", min=50.0, max=3000.0)


@dataclass
class LaneFollowingParams(PredictorParams):
    tau_lateral: float = param(1.2, "s", "Zeitkonstante Querbewegung", min=0.1, max=10.0)
    lateral_intent_speed: float = param(0.35, "m/s", "Quergeschwindigkeit für Spurwechselabsicht", min=0.0, max=3.0)
    use_acceleration: bool = param(False, "", "Längsbeschleunigung berücksichtigen")


@dataclass
class ConstantVelocityParams(PredictorParams):
    use_yaw_rate: bool = param(False, "", "konstante Gierrate (CTRV)")


@trace("werling2011", section="3.5.2", equation="s_v(t) = s_v(0) + ṡ_v(0) t + ½ s̈_v(0) t²", concept="ca_prediction",
       note="konstante Beschleunigung, Klemmung bei Stillstand und bei v_max")
def ca_motion(s0, v0, a0, tau, v_max=np.inf):
    # 1d motion with constant acceleration, clamped at standstill (no reversing) and at v_max
    tau = np.asarray(tau, dtype=float)
    v0 = float(v0)
    a0 = float(a0)
    if v0 <= 0.0 and a0 <= 0.0:
        return np.full_like(tau, float(s0)), np.zeros_like(tau)
    v = v0 + a0 * tau
    s = s0 + v0 * tau + 0.5 * a0 * tau ** 2
    if a0 < 0.0:
        t_stop = -v0 / a0
        m = tau >= t_stop
        s = np.where(m, s0 + 0.5 * v0 * t_stop, s)
        v = np.where(m, 0.0, v)
    elif a0 > 0.0 and np.isfinite(v_max) and v0 < v_max:
        t_m = (v_max - v0) / a0
        m = tau >= t_m
        s = np.where(m, s0 + v0 * t_m + 0.5 * a0 * t_m ** 2 + v_max * (tau - t_m), s)
        v = np.where(m, v_max, v)
    return s, np.maximum(v, 0.0)


@trace("werling2011", section="3.5.2", concept="lateral_intent",
       note="kritisch gedämpfte Konvergenz d(t) -> d_ziel mit d(0), d'(0)")
def lateral_convergence(d0, d_dot0, d_target, tau, T):
    # critically damped lateral motion with initial value and slope (closed form)
    T = np.asarray(T, dtype=float)
    e0 = d0 - d_target
    return d_target + (e0 + (d_dot0 + e0 / tau) * T) * np.exp(-T / tau)


class _BasePredictor(PredictionBase):
    PARAMS = PredictorParams
    PERIOD = None

    def reset(self, context):
        super().reset(context)
        self._last = None

    def time_grid(self, t0):
        p = self.params
        n = int(round(p.horizon / p.dt))
        return t0 + p.dt * np.arange(n + 1)

    def _road(self, inputs):
        world = inputs.get("world")
        road = world.road if world is not None and world.road is not None else getattr(self.context, "road", None)
        return road if self.params.use_lanes else None

    def lane_line(self, road, lane_id):
        chain = road.chain(lane_id, ahead=self.params.chain_length)
        return road.route_line(chain)

    def frenet_ok(self, road, o):
        if road is None or o.lane_id is None or o.lane_id not in road.lanes or o.type not in LANE_TYPES_FRENET:
            return False
        th = road.lanes[o.lane_id].center.evaluate(o.s if o.s is not None else 0.0)[2]
        return abs(float(wrap_angle(o.psi - th))) <= np.radians(self.params.max_heading_error_deg)

    def frenet_start(self, road, o):
        line = self.lane_line(road, o.lane_id)
        if o.s is None or o.d is None:
            s, d = line.project(o.x, o.y)
        else:
            s, d = o.s, o.d
        _, _, th, k, _ = line.evaluate(s)
        dpsi = float(wrap_angle(o.psi - th))
        scale = max(1.0 - k * d, 0.1)
        return line, float(s), float(d), o.v * np.cos(dpsi) / scale, o.a * np.cos(dpsi) / scale, o.v * np.sin(dpsi)

    def predict_object(self, o, t, road):
        raise NotImplementedError

    def step(self, t, inputs):
        objs = inputs.get("objects")
        if objs is None:
            return {"prediction": Prediction(t0=t, objects=[])}
        road = self._road(inputs)
        tt = self.time_grid(float(objs.t))
        out = [self.predict_object(o, tt, road) for o in objs.objects]
        self.signals["n_predicted"] = float(len(out))
        return {"prediction": Prediction(t0=float(objs.t), objects=out)}


def _cartesian_ca(o, tt, v_max):
    tau = tt - tt[0]
    s, v = ca_motion(0.0, o.v, o.a, tau, v_max)
    c, sn = np.cos(o.psi), np.sin(o.psi)
    return PredictedObject(id=o.id, type=o.type, length=o.length, width=o.width, t=tt, x=o.x + c * s, y=o.y + sn * s,
                           psi=np.full_like(tt, o.psi), v=v, lane_id=o.lane_id)


class ConstantAccelerationPredictor(_BasePredictor):
    NAME, VERSION = "constant_acceleration", "1.0.0"
    LABEL = "Konstante Beschleunigung (Frenet, Werling 3.5.2)"
    DOC = ComponentDoc(
        summary="Prädiziert Objekte mit konstanter Beschleunigung entlang ihrer Spur in Frenet-Koordinaten.",
        purpose="Prädiktion der Vorder- und Lückenfahrzeuge für Folge- und Einfädelmodus nach Werling 3.5.2.",
        theory="$s_v(t) = s_v(0) + \\dot s_v(0) t + \\tfrac12 \\ddot s_v(0) t^2$, $d(t) = d(0)$; bei "
               "$\\dot s_v(t) \\le 0$ wird der Stillstand gehalten. Objekte ohne Spur werden kartesisch entlang "
               "ihrer Orientierung prädiziert.",
        assumptions=["Beschleunigung über den Horizont konstant", "keine Querbewegung relativ zur Spur",
                     "an Verzweigungen folgt das Objekt der Standardfortsetzung der Spur"],
        limitations=["Spurwechsel und Abbiegen anderer Verkehrsteilnehmer werden nicht vorhergesagt"],
        references=["werling2011"],
        equations=["werling2011:3.5.2"],
        concepts=["ca_prediction", "frenet_frame"],
        validation=["tests/prediction/test_prediction_predictors.py"],
    )

    def predict_object(self, o, tt, road):
        p = self.params
        if not self.frenet_ok(road, o):
            return _cartesian_ca(o, tt, p.v_max)
        line, s0, d0, sd0, sdd0, _ = self.frenet_start(road, o)
        s, sd = ca_motion(s0, sd0, sdd0, tt - tt[0], p.v_max)
        x, y = line.point(s, d0)
        _, _, th, k, _ = line.evaluate(s)
        return PredictedObject(id=o.id, type=o.type, length=o.length, width=o.width, t=tt, x=np.asarray(x),
                               y=np.asarray(y), psi=np.asarray(th), v=sd * (1.0 - k * d0), lane_id=o.lane_id, s=s,
                               s_dot=sd)


class ConstantVelocityPredictor(_BasePredictor):
    NAME, VERSION = "constant_velocity", "1.0.0"
    LABEL = "Konstante Geschwindigkeit (kartesisch)"
    PARAMS = ConstantVelocityParams
    DOC = ComponentDoc(
        summary="Geradlinige Prädiktion mit konstanter Geschwindigkeit (optional konstanter Gierrate).",
        purpose="Einfache, kartenunabhängige Referenzprädiktion, z. B. für Fußgänger oder ohne Straßenkarte.",
        theory="$x(t) = x_0 + v \\cos\\psi\\, t$, $y(t) = y_0 + v \\sin\\psi\\, t$; mit CTRV "
               "$\\psi(t) = \\psi_0 + \\dot\\psi t$.",
        concepts=["cv_prediction"],
        validation=["tests/prediction/test_prediction_predictors.py"],
    )

    def predict_object(self, o, tt, road):
        tau = tt - tt[0]
        r = o.yaw_rate if getattr(self.params, "use_yaw_rate", False) else 0.0
        if abs(r) < 1e-6:
            x, y = o.x + o.v * np.cos(o.psi) * tau, o.y + o.v * np.sin(o.psi) * tau
            psi = np.full_like(tau, o.psi)
        else:
            psi = o.psi + r * tau
            x = o.x + o.v / r * (np.sin(psi) - np.sin(o.psi))
            y = o.y - o.v / r * (np.cos(psi) - np.cos(o.psi))
        return PredictedObject(id=o.id, type=o.type, length=o.length, width=o.width, t=tt, x=x, y=y, psi=psi,
                               v=np.full_like(tau, o.v), lane_id=o.lane_id)


class LaneFollowingPredictor(_BasePredictor):
    NAME, VERSION = "lane_following", "1.0.0"
    LABEL = "Spurfolge mit Querabsicht"
    PARAMS = LaneFollowingParams
    DOC = ComponentDoc(
        summary="Konstante Geschwindigkeit entlang der Spurfolge, Querablage konvergiert zur Zielspurmitte.",
        purpose="Erkennt Spurwechsel (Einscherer) frühzeitig aus der Quergeschwindigkeit relativ zur Spur.",
        theory="Längs: $s(t) = s_0 + \\dot s_0 t$ (optional mit $\\ddot s_0$). Quer: kritisch gedämpft "
               "$d(t) = d_z + (e_0 + (\\dot d_0 + e_0/\\tau) t) e^{-t/\\tau}$ mit $e_0 = d_0 - d_z$. Die Zielablage "
               "$d_z$ ist die Mitte der Nachbarspur, wenn $|\\dot d_0|$ die Absichtsschwelle überschreitet und das "
               "Objekt auf sie zuläuft, sonst die eigene Spurmitte.",
        assumptions=["Objekte folgen der Standardfortsetzung der Spur"],
        limitations=["Abbiegeabsichten an Kreuzungen werden nicht geschätzt"],
        references=["werling2011"],
        concepts=["lane_following_prediction", "lateral_intent"],
        validation=["tests/prediction/test_prediction_predictors.py"],
    )

    def predict_object(self, o, tt, road):
        p = self.params
        if not self.frenet_ok(road, o):
            return _cartesian_ca(o, tt, p.v_max) if o.type == "pedestrian" else \
                ConstantVelocityPredictor.predict_object(self, o, tt, road)
        line, s0, d0, sd0, sdd0, d_dot0 = self.frenet_start(road, o)
        tau = tt - tt[0]
        s, sd = ca_motion(s0, sd0, sdd0 if p.use_acceleration else 0.0, tau, p.v_max)
        lane = road.lanes[o.lane_id]
        d_target = 0.0
        if abs(d_dot0) > p.lateral_intent_speed:
            side = "left" if d_dot0 > 0 else "right"
            nb = lane.neighbor(side, s0)
            if nb is not None and not lane.opposite(side, s0):
                off = 0.5 * (lane.width + road.lanes[nb].width)
                d_target = off if side == "left" else -off
        d = lateral_convergence(d0, d_dot0, d_target, p.tau_lateral, tau)
        x, y = line.point(s, d)
        _, _, th, k, _ = line.evaluate(s)
        dd_dt = np.gradient(d, tau) if len(tau) > 1 else np.zeros_like(tau)
        v_long = sd * (1.0 - k * d)
        psi = th + np.arctan2(dd_dt, np.maximum(v_long, 0.5))
        return PredictedObject(id=o.id, type=o.type, length=o.length, width=o.width, t=tt, x=np.asarray(x),
                               y=np.asarray(y), psi=np.asarray(psi), v=np.hypot(v_long, dd_dt), lane_id=o.lane_id,
                               s=s, s_dot=sd)
