"""Rule-based behavior planner "behavior_planner/rule_based" (Werling 2011, 3.5 / 3.6 / 5.3).

Finite state machine over the maneuvers
    lane_keeping -> lane_change_left / lane_change_right -> lane_keeping
    lane_keeping -> merging (acceleration lane, gap selection eq. 3.15, simultaneous move of the
                    reference curve to the target lane, Werling 5.3.2) -> lane_keeping
    lane_keeping -> overtaking (oncoming lane via d_ref, rural road) -> lane_keeping
    park_approach -> park_hold -> park_reverse (direction = -1, reversed reference) -> parked
and the longitudinal modes for the trajectory planner (Werling Tab. 3.1): velocity always,
following (lead_id, k0, kv), merging (front_id, rear_id), stopping (s_stop at stop lines, red
lights, yield without gap, mission goal, end of lane). The box restriction d_min/d_max comes from
the lane markings and neighbor lanes (Werling 5.3.1, footnote 8). The last planned trajectory
(feedback port "trajectory") is the hazard indicator of Werling 3.6: high cost or an invalid
trajectory postpone lane changes.

Conventions: the reference line is the concatenated lane chain starting at BehaviorCommand.lane_id
(s = Frenet coordinate of that lane, consistent with PredictedObject.s); s_stop is the position the
leading bumper must not pass; k0 is a bumper-to-bumper distance.
"""

from __future__ import annotations

import numpy as np

from ..framework.knowledge import ComponentDoc, trace
from ..framework.layers import BehaviorPlannerBase
from ..framework.types import BehaviorCommand, LongitudinalMode
from ..geometry.reference_line import wrap_angle
from ..world.traffic_models import idm_acceleration, mobil_incentive
from .params import RuleBasedParams

VRU = ("pedestrian", "cyclist")


class _Geo:
    # ego outline relative to the CoG (from context.vehicle, overhangs split evenly)
    def __init__(self, vehicle):
        v = getattr(vehicle, "vehicle", None)
        if v is None:
            self.length, self.width, self.l_f, self.l_r = 4.8, 1.85, 1.25, 1.55
        else:
            self.length, self.width = float(v.length), float(v.width)
            self.l_f, self.l_r = float(v.cg_to_front), float(v.wheelbase - v.cg_to_front)
        oh = max(self.length - self.l_f - self.l_r, 0.0) / 2
        self.front = self.l_f + oh           # CoG -> front bumper
        self.rear = self.l_r + oh            # CoG -> rear bumper


class RuleBasedBehavior(BehaviorPlannerBase):
    NAME, VERSION = "rule_based", "1.0.0"
    LABEL = "Regelbasierte Verhaltensplanung"
    PARAMS = RuleBasedParams
    PERIOD = 0.1
    DOC = ComponentDoc(
        summary="Zustandsautomat für Spurhalten, Spurwechsel, Einfädeln, Überholen, Kreuzung/Kreisverkehr und "
                "Einparken; erzeugt Referenzkurve, Längsmodi und Box-Restriktion für den Trajektorienplaner.",
        purpose="Verhaltensebene nach Werling 3.6: Sollvorgaben so wählen, dass die reaktive Trajektorienplanung "
                "möglichst selten eine Kollision vermeiden muss.",
        theory="Spurwechsel MOBIL-artig: $\\tilde a_c - a_c + p(\\tilde a_n - a_n) \\pm a_{bias} > \\Delta a_{th}$ "
               "mit IDM-Beschleunigungen und Sicherheitsprüfung über die Prädiktion. Einfädeln: Lückenmitte "
               "$s_{ref} = \\tfrac12 (s_a + s_b)$ (3.15), Lückenwahl nach erforderlicher Beschleunigung. "
               "Vorfahrt: Zeitlückenannahme mit prädizierten Konfliktzonenbelegungen.",
        assumptions=["Kartenwissen (Spuren, Markierungen, Haltelinien) ist exakt bekannt",
                     "Objekte tragen lane_id/s/d der Szenario-Engine bzw. Perception"],
        limitations=["keine Neuplanung der Route bei verpasster Ausfahrt",
                     "Linksabbiegen bei Grün: einfache Zeitlückenprüfung gegen den Gegenverkehr"],
        design_decisions=["Referenzkurve = Spurkette ab BehaviorCommand.lane_id (konsistent mit PredictedObject.s)",
                          "Gegenfahrbahn-Überholen über d_ref statt Referenzkurvenwechsel (Werling 3.5.1)"],
        references=["werling2011", "kesting2007", "treiber2000", "stvo"],
        equations=["werling2011:(3.15)", "kesting2007:(3)"],
        concepts=["behavior_state_machine", "mobil", "box_restriction", "hazard_indicator", "merging_mode"],
        validation=["tests/behavior/test_behavior_rule_based.py"],
        extension_points=["weitere Verhaltensplaner als Komponente der Ebene behavior_planner"],
    )

    def reset(self, context):
        super().reset(context)
        self.geo = _Geo(getattr(context, "vehicle", None))
        scen = getattr(context, "scenario", None)
        self.mission = dict(getattr(scen, "mission", None) or {})
        self.route = list(self.mission.get("route", []))
        perm = {"lane_change": True, "overtake": True, "use_opposite_lane": True, "reverse": False}
        perm.update(self.mission.get("permissions", {}))
        self.perm = perm
        self.state = "lane_keeping"
        self.lane = None
        self.chain = None
        self.ref = None
        self._s_hint = None
        self.lc = None
        self.merge = None
        self.overtake = None
        self.last_lc_t = -1e9
        self.hazard_until = -1e9
        self.adopt = None
        self.stopped_at = {}
        self.committed = set()
        self.park = None
        self.last_cmd = None

    # ================================================================== helpers
    def _road(self, world):
        return world.road if world is not None and world.road is not None else getattr(self.context, "road", None)

    def _set_lane(self, road, lane_id, force=False):
        self.lane = lane_id
        if force or self.chain is None or lane_id not in self.chain:
            self.chain = road.chain(lane_id, route=self.route, ahead=self.params.route_ahead)
            self.ref = road.route_line(self.chain)
            self._s_hint = None

    def _project(self, line, x, y, s_guess=None):
        hint = None
        if s_guess is not None and not line.closed:
            ds = (line.s[-1] - line.s[0]) / max(len(line.s) - 1, 1)
            hint = int(np.clip((s_guess - line.s[0]) / ds, 0, len(line.s) - 1))
        s, d = line.project(x, y, hint=hint, window=80, max_jump=8.0)
        return float(s), float(d)

    def _lane_at_s(self, s):
        offs = self.ref.lane_offsets
        best = self.chain[0]
        for lid in self.chain:
            if offs[lid] <= s + 1e-6:
                best = lid
        return best

    def _target_speed(self, t, road, s_e):
        p = self.params
        lane = road.lanes[self.lane]
        v_m = self.mission.get("target_speed")
        prof = self.mission.get("speed_profile")
        if prof:
            for t_i, v_i in prof:
                if t >= t_i:
                    v_m = v_i
        v_m = float(lane.speed_limit if v_m is None else v_m)
        ss = s_e + np.arange(0.0, p.speed_lookahead, 5.0)
        if not self.ref.closed:
            ss = ss[ss <= self.ref.s[-1]]
        if len(ss) == 0:
            return v_m, {"mission": v_m}
        k = np.abs(self.ref.evaluate(ss)[3])
        lim = np.array([road.lanes[self._lane_at_s(si)].speed_limit for si in ss]) if not self.ref.closed else \
            np.full_like(ss, lane.speed_limit)
        v_lim = np.minimum(lim, np.sqrt(p.a_lat_max / np.maximum(k, 1e-6)))
        v_lim = np.minimum(v_lim, v_m)
        v_ant = np.sqrt(v_lim ** 2 + 2.0 * p.b_comf * np.maximum(ss - s_e - self.geo.front, 0.0))
        i = int(np.argmin(v_ant))
        return float(min(v_m, v_ant[i])), {"mission": v_m, "limit_at": float(ss[i]), "limit": float(v_lim[i])}

    def _idm(self, v, v0, gap, dv):
        p = self.params
        return idm_acceleration(v, v0, gap, dv, p.idm_a, p.idm_b, p.idm_T, p.idm_s0)

    # ------------------------------------------------------------------ objects relative to a line
    def _objects_on(self, line, objs, s_e, ego):
        # vectorized Frenet coordinates of the objects on `line` (dict of arrays)
        if not objs:
            return None
        ox = np.array([o.x for o in objs])
        oy = np.array([o.y for o in objs])
        s, d = line.project_many(ox, oy)
        ds = s - s_e
        if line.closed:
            ds = (ds + 0.5 * line.length) % line.length - 0.5 * line.length
        th = line.evaluate(s)[2]
        psi = np.array([o.psi for o in objs])
        v = np.array([o.v for o in objs])
        aligned = (np.abs(wrap_angle(psi - th)) < np.pi / 2) | (v < 0.5)
        return {"obj": objs, "s": s, "ds": ds, "d": d, "v": v * np.cos(wrap_angle(psi - th)), "aligned": aligned,
                "L": np.array([o.length for o in objs]), "W": np.array([o.width for o in objs]),
                "id": [o.id for o in objs], "type": [o.type for o in objs]}

    def _pred_frenet(self, pred, obj_id, line, rel_t, t0):
        # predicted s (on `line`) of an object at times t0 + rel_t; None if not predicted
        po = pred.by_id(obj_id) if pred is not None else None
        if po is None or len(po.t) == 0:
            return None
        tt = t0 + np.asarray(rel_t)
        if po.s is not None and getattr(line, "lane_ids", (None,))[0] == po.lane_id and len(po.s) == len(po.t):
            return np.interp(tt, po.t, po.s)
        x, y = np.interp(tt, po.t, po.x), np.interp(tt, po.t, po.y)
        return line.project_many(x, y)[0]

    # ------------------------------------------------------------------ lead selection
    def _lead(self, geo_o, s_e, d_c, v_e, lane_w, pred, t, corridor):
        p = self.params
        if geo_o is None:
            return None, 0.0, {}
        half = 0.5 * self.geo.width + p.lateral_margin
        look = max(p.lead_lookahead_min, p.lead_lookahead_time * v_e)
        best, best_ds, shift_lo, shift_hi, notes = None, np.inf, 0.0, 0.0, {}
        rel = np.arange(0.5, p.intrusion_time + 1e-9, 0.5)
        for i, o in enumerate(geo_o["obj"]):
            ds = geo_o["ds"][i]
            reach = 0.5 * (geo_o["L"][i]) + self.geo.front
            if ds < -reach * 0.5 or ds > look + reach or not geo_o["aligned"][i]:
                if not geo_o["aligned"][i] and o.type == "pedestrian" and 0 < ds < look:
                    pass
                else:
                    continue
            lo, hi = geo_o["d"][i] - 0.5 * geo_o["W"][i], geo_o["d"][i] + 0.5 * geo_o["W"][i]
            intrude = hi > d_c - half and lo < d_c + half
            if not intrude and pred is not None and len(rel):
                po = pred.by_id(o.id)
                if po is not None and len(po.t):
                    xs, ys = np.interp(t + rel, po.t, po.x), np.interp(t + rel, po.t, po.y)
                    sp, dp = self.ref.project_many(xs, ys)
                    w2 = 0.5 * o.width
                    hit = (dp + w2 > d_c - half) & (dp - w2 < d_c + half) & (sp - s_e > 0)
                    intrude = bool(np.any(hit))
            if not intrude:
                continue
            slow = geo_o["v"][i] < max(2.0, 0.3 * v_e)
            crossing = o.type == "pedestrian" and o.v > 0.3 and not (hi > d_c - half and lo < d_c + half) or                 (o.type == "pedestrian" and o.v > 0.3 and abs(np.sin(o.psi - self.ref.evaluate(geo_o["s"][i])[2])) > 0.5)
            if slow and not crossing and (o.type in VRU or o.type in ("static", "car", "truck")) and ds > 0:
                # pass with lateral clearance inside the corridor (d_ref offset, Werling 3.5.1)
                clear = p.clearance_vru if o.type in VRU else p.clearance_static
                need_left = hi + clear + 0.5 * self.geo.width - d_c
                need_right = lo - clear - 0.5 * self.geo.width - d_c
                side_left = geo_o["d"][i] <= d_c
                shift = max(need_left, 0.0) if side_left else min(need_right, 0.0)
                ok = abs(shift) <= p.max_pass_offset and corridor[0] <= d_c + shift - 0.5 * self.geo.width and \
                    d_c + shift + 0.5 * self.geo.width <= corridor[1]
                if ok and (o.type in VRU or o.type == "static" or geo_o["v"][i] < 0.5):
                    shift_hi = max(shift_hi, shift) if shift > 0 else shift_hi
                    shift_lo = min(shift_lo, shift) if shift < 0 else shift_lo
                    notes[o.id] = f"Vorbeifahren mit Versatz {shift:+.2f} m"
                    continue
            if ds < best_ds and ds > -reach * 0.5:
                best, best_ds = i, ds
        shift = shift_hi if abs(shift_hi) >= abs(shift_lo) else shift_lo
        if shift_hi > 0 and shift_lo < 0:
            shift = 0.0          # objects on both sides: no offset, they become leads if intruding
        return best, shift, notes

    # ------------------------------------------------------------------ lane change evaluation
    @trace("kesting2007", section="3", concept="mobil",
           note="MOBIL-artige Spurwechselentscheidung mit IDM-Beschleunigungen und Prädiktions-Sicherheitsprüfung")
    def _lane_change_eval(self, road, side, objs, ego, s_lane, a_c, v_e, v0, pred, t, mandatory=False):
        p = self.params
        lane = road.lanes[self.lane]
        nb_id = lane.neighbor(side, s_lane)
        res = {"side": side, "target": nb_id, "ok": False, "safe": False, "incentive": -np.inf, "reason": ""}
        if nb_id is None:
            res["reason"] = "keine Nachbarspur"
            return res
        nb = road.lanes[nb_id]
        if lane.opposite(side, s_lane):
            res["reason"] = "Gegenfahrbahn"
            return res
        if lane.marking(side, s_lane) not in ("dashed", "none"):
            res["reason"] = "durchgezogene Linie"
            return res
        if nb.type not in ("driving",) and not (mandatory and nb_id in self.route):
            res["reason"] = f"Spurtyp {nb.type}"
            return res
        line_t = road.route_line(road.chain(nb_id, route=self.route, ahead=p.route_ahead))
        s_t, d_t = line_t.project(ego.x, ego.y)
        geo = self._objects_on(line_t, objs, s_t, ego)
        front = rear = None
        if geo is not None:
            band = 0.5 * nb.width
            on = geo["aligned"] & (np.abs(geo["d"]) - 0.5 * geo["W"] < band - 0.3)
            for i in np.flatnonzero(on):
                ds = geo["ds"][i]
                if abs(ds) < 0.5 * (geo["L"][i] + self.geo.length) + 1.0:
                    res["reason"] = f"Objekt {geo['id'][i]} neben dem Ego"
                    return res
                if ds > 0 and (front is None or ds < geo["ds"][front]):
                    front = i
                if ds < 0 and (rear is None or ds > geo["ds"][rear]):
                    rear = i
        # accelerations (IDM) before / after
        if front is not None:
            gap_f = geo["ds"][front] - 0.5 * (geo["L"][front] + self.geo.length)
            a_new = self._idm(v_e, v0, gap_f, v_e - geo["v"][front])
        else:
            a_new = self._idm(v_e, v0, np.inf, 0.0)
        a_n = a_n_new = 0.0
        if rear is not None:
            v_r = max(geo["v"][rear], 0.0)
            v0_r = max(v_r, nb.speed_limit)
            gap_r = -geo["ds"][rear] - 0.5 * (geo["L"][rear] + self.geo.length)
            if front is not None:
                gap_rf = geo["ds"][front] - geo["ds"][rear] - 0.5 * (geo["L"][front] + geo["L"][rear])
                a_n = self._idm(v_r, v0_r, gap_rf, v_r - geo["v"][front])
            else:
                a_n = self._idm(v_r, v0_r, np.inf, 0.0)
            a_n_new = self._idm(v_r, v0_r, gap_r, v_r - v_e)
        bias = p.lc_bias_right if side == "right" else -p.lc_bias_right
        ok, inc, safe_idm = mobil_incentive(a_c, a_new, a_n, a_n_new, 0.0, 0.0, p.lc_politeness, p.lc_threshold, bias,
                                            p.lc_b_safe)
        res.update({"incentive": inc, "a_new": float(a_new), "a_c": float(a_c), "a_n_new": float(a_n_new),
                    "front": geo["id"][front] if front is not None else None,
                    "rear": geo["id"][rear] if rear is not None else None, "line": line_t})
        # safety over the prediction horizon (ego at constant speed)
        rel = np.arange(0.0, p.lc_safety_horizon + 1e-9, 0.25)
        s_ego = s_t + v_e * rel
        safe = bool(safe_idm)
        why = "" if safe else "Hintermann müsste zu stark bremsen"
        for idx, kind in ((front, "front"), (rear, "rear")):
            if idx is None or not safe:
                continue
            o = geo["obj"][idx]
            so = self._pred_frenet(pred, o.id, line_t, rel, t)
            if so is None:
                so = geo["s"][idx] + geo["v"][idx] * rel
            half = 0.5 * (o.length + self.geo.length)
            if kind == "front":
                gap = so - s_ego - half
                need = p.lc_gap_min + p.lc_front_time * v_e
            else:
                gap = s_ego - so - half
                v_o = np.gradient(so, rel) if len(rel) > 1 else np.full_like(rel, geo["v"][idx])
                need = p.lc_gap_min + p.lc_rear_time * np.maximum(v_o, 0.0)
            if np.any(gap < need):
                safe, why = False, f"Lücke zu {'Vorder' if kind == 'front' else 'Hinter'}fahrzeug {o.id} zu klein"
        res["safe"] = safe
        res["ok"] = safe and (mandatory or ok)
        res["reason"] = why or ("Anreiz zu gering" if not ok and not mandatory else "")
        return res

    # ------------------------------------------------------------------ route logic
    def _route_requirement(self, road, s_lane):
        # mandatory lateral move: (side, remaining distance, number of changes) or None
        if not self.route:
            return None
        lane = road.lanes[self.lane]
        if self.lane in self.route:
            i = self.route.index(self.lane)
            if i + 1 < len(self.route):
                nxt = self.route[i + 1]
                for side in ("left", "right"):
                    seg = [x for x in lane.neighbor_segments if x[0] == side and x[1] == nxt]
                    if seg or (getattr(lane, side) == nxt):
                        end = seg[0][3] if seg else lane.length
                        start = seg[0][2] if seg else 0.0
                        return {"side": side, "remaining": end - s_lane, "steps": 1, "target": nxt,
                                "available": start <= s_lane <= end}
            if lane.type == "merge" and lane.left is not None:
                return {"side": "left", "remaining": lane.length - s_lane, "steps": 1, "target": lane.left,
                        "available": True}
            return None
        # lane not on the route: find a route lane via same-direction neighbors
        for side in ("right", "left"):
            cur, s_cur, steps = lane, s_lane, 0
            while steps < 4:
                nb = cur.neighbor(side, s_cur)
                if nb is None or cur.opposite(side, s_cur):
                    break
                steps += 1
                if nb in self.route:
                    rem = np.inf
                    j = self.route.index(nb)
                    if j + 1 < len(self.route):
                        nl = road.lanes[nb]
                        seg = [x for x in nl.neighbor_segments if x[1] == self.route[j + 1]]
                        if seg:
                            rem = seg[0][3] - s_cur
                    return {"side": side, "remaining": rem, "steps": steps, "target": nb, "available": True}
                s_cur = road.neighbor_s(cur.id, s_cur, side) or s_cur
                cur = road.lanes[nb]
        return None

    # ------------------------------------------------------------------ stops
    def _zone_blocked(self, road, zone_id, pred, t, s_e, v_e, dist_line):
        p = self.params
        zone = road.conflict_zones.get(zone_id)
        if zone is None or pred is None:
            return False, None
        yielding = {sl.lane_id for sl in road.stop_lines if sl.zone_id == zone_id and sl.kind in ("yield", "stop")}
        t_need = (max(dist_line, 0.0) + 2.0 * zone.radius) / max(v_e, 3.0) + p.yield_gap_time
        for po in pred.objects:
            if po.lane_id in yielding or len(po.t) == 0 or po.lane_id in self.chain:
                continue
            m = (po.t >= t - 1e-6) & (po.t <= t + t_need)
            if not np.any(m):
                continue
            dist = np.hypot(po.x[m] - zone.x, po.y[m] - zone.y)
            if np.any(dist <= zone.radius + 0.5 * po.length):
                if np.max(np.abs(po.v[m])) < 0.3 and dist[0] > zone.radius:
                    continue
                return True, po.id
        return False, None

    def _stops(self, road, world, pred, t, s_e, v_e, route_turn_left):
        p = self.params
        out = []
        front = s_e + self.geo.front
        look = max(60.0, v_e ** 2 / (2 * p.b_comf) + 40.0)
        offs = self.ref.lane_offsets
        start = self.chain.index(self._lane_at_s(s_e)) if not self.ref.closed else 0
        phases = road.light_phases(t)
        for lid in self.chain[start:]:
            for sl in road.stop_lines_on(lid):
                s_line = offs[lid] + sl.s
                dist = s_line - front
                if dist < -0.5 or dist > look or sl.id in self.committed:
                    continue
                stop, why = False, ""
                if sl.kind == "traffic_light":
                    ph = phases.get(sl.light_id, (world.traffic_lights or {}).get(sl.light_id, "green"))
                    if ph in ("red", "red_yellow"):
                        stop, why = dist > -0.2, f"rote Ampel {sl.light_id}"
                        if v_e ** 2 / (2 * 7.0) > dist + 1.0:
                            stop, why = False, "Rot nicht mehr anhaltbar"
                    elif ph == "yellow":
                        stop = dist > v_e ** 2 / (2 * p.yellow_decel)
                        why = f"gelbe Ampel {sl.light_id}"
                    elif route_turn_left and sl.zone_id:
                        stop, oid = self._zone_blocked(road, sl.zone_id, pred, t, s_e, v_e, dist)
                        why = f"Linksabbiegen: Gegenverkehr {oid}" if stop else ""
                elif sl.kind in ("stop", "yield"):
                    if sl.kind == "stop" and t - self.stopped_at.get(sl.id, np.inf) < p.stop_hold:
                        stop, why = True, "Stoppschild"
                    elif sl.kind == "stop" and sl.id not in self.stopped_at:
                        stop, why = True, "Stoppschild"
                        if v_e < p.standstill_v and dist < 2.0:
                            self.stopped_at[sl.id] = t
                    else:
                        stop, oid = self._zone_blocked(road, sl.zone_id, pred, t, s_e, v_e, dist)
                        why = f"Vorfahrt gewähren ({oid})" if stop else ""
                if stop:
                    out.append({"s_stop": s_line - p.stop_margin, "reason": why, "source": sl.id})
                elif dist < 1.0 + 0.5 * v_e and v_e > 1.0:
                    self.committed.add(sl.id)
        goal = self.mission.get("goal") or {}
        if goal.get("stop") and goal.get("lane") in offs:
            s_goal = offs[goal["lane"]] + goal.get("s", 0.0)
            if s_goal > s_e - 2.0:
                out.append({"s_stop": s_goal, "reason": "Missionsziel", "source": "goal"})
        if not self.ref.closed:
            last = road.lanes[self.chain[-1]]
            end = self.ref.s[-1]
            if not last.successors and end - front < look:
                out.append({"s_stop": end - p.end_of_lane_margin, "reason": f"Spurende {last.id}",
                            "source": last.id})
        return out

    # ------------------------------------------------------------------ corridor
    def _corridor(self, road, s_e, v_e, d_e, d_ref):
        p = self.params
        allow_opp = p.use_opposite_lane and self.perm.get("use_opposite_lane", True)
        lo, hi = -np.inf, np.inf
        for s in s_e + np.array([0.0, 0.5, 1.0]) * max(v_e * p.box_lookahead_time, 1.0):
            if not self.ref.closed and s > self.ref.s[-1]:
                continue
            lid = self._lane_at_s(s) if not self.ref.closed else self.chain[0]
            s_l = (s - self.ref.lane_offsets[lid]) % self.ref.length if self.ref.closed else \
                s - self.ref.lane_offsets[lid]
            a, b = road.corridor(lid, s_l, include_opposite=allow_opp, include_parking=p.use_parking_lane)
            lo, hi = max(lo, a), min(hi, b)
        if not np.isfinite(lo):
            w = 0.5 * road.lanes[self.lane].width
            lo, hi = -w, w
        half = 0.5 * self.geo.width + 0.1
        lo, hi = min(lo, d_e - half, d_ref - half), max(hi, d_e + half, d_ref + half)
        return float(lo), float(hi)

    def _hazard(self, t, traj):
        p = self.params
        if traj is None or getattr(traj, "empty", True):
            return False
        if (p.hazard_on_invalid and not traj.valid) or traj.cost > p.hazard_cost_threshold:
            self.hazard_until = t + p.hazard_hold
        return t < self.hazard_until

    # ================================================================== main step
    def step(self, t, inputs):
        ego, objects, pred, world = (inputs.get(k) for k in ("ego", "objects", "prediction", "world"))
        road = self._road(world)
        if ego is None or road is None:
            return {"behavior": self.last_cmd or BehaviorCommand(t=t)}
        hazard = self._hazard(t, inputs.get("trajectory"))
        objs = list(objects.objects) if objects is not None else []
        objs = [o for o in objs if np.hypot(o.x - ego.x, o.y - ego.y) < 300.0]
        if self.mission.get("parking"):
            cmd = self._parking(t, road, ego, objs, pred)
        else:
            cmd = self._drive(t, road, ego, objs, pred, world, hazard)
        cmd.info["hazard"] = hazard
        self.last_cmd = cmd
        self.signals.update({"target_speed": cmd.target_speed, "d_ref": cmd.d_ref, "n_modes": float(len(cmd.modes))})
        return {"behavior": cmd}

    def _init_lane(self, road, ego):
        loc = road.lane_at(ego.x, ego.y, ego.psi, margin=1.0, prefer=self.route)
        if loc is None:
            loc = road.lane_at(ego.x, ego.y, None, margin=5.0, prefer=self.route)
        if loc is None:
            raise ValueError("ego is not on a lane")
        self._set_lane(road, loc.lane_id, force=True)

    def _drive(self, t, road, ego, objs, pred, world, hazard):
        p = self.params
        info = {}
        if self.lane is None:
            self._init_lane(road, ego)
        s_e, d_e = self._project(self.ref, ego.x, ego.y, self._s_hint)
        lane_here = self._lane_at_s(s_e) if not self.ref.closed else self.chain[0]
        if lane_here != self.lane and self.state != "merging" and self.lc is None:
            self.lane = lane_here
        if not self.ref.closed and s_e > self.ref.s[-1] - 300.0 and road.lanes[self.chain[-1]].successors:
            self._set_lane(road, self.lane, force=True)
            s_e, d_e = self._project(self.ref, ego.x, ego.y)
        self._s_hint = s_e
        v_e = max(ego.vx, 0.0)
        lane = road.lanes[self.lane]
        s_lane = s_e - self.ref.lane_offsets.get(self.lane, 0.0)
        if self.ref.closed:
            s_lane %= self.ref.length

        # ---------------------------------------------------- lane adoption after an evasion
        if self.state == "lane_keeping" and lane.junction is None:
            loc = road.lane_at(ego.x, ego.y, ego.psi, margin=0.0)
            if loc is not None and loc.lane_id != self.lane and abs(loc.d) < 0.8 and \
                    road.lanes[loc.lane_id].type == "driving" and loc.lane_id in (lane.neighbor("left", s_lane),
                                                                                  lane.neighbor("right", s_lane)) \
                    and not lane.opposite("left" if loc.lane_id == lane.neighbor("left", s_lane) else "right", s_lane):
                self.adopt = self.adopt if (self.adopt and self.adopt[0] == loc.lane_id) else (loc.lane_id, t)
                if t - self.adopt[1] >= p.adopt_time:
                    self._set_lane(road, loc.lane_id)
                    s_e, d_e = self._project(self.ref, ego.x, ego.y)
                    lane, s_lane = road.lanes[self.lane], s_e - self.ref.lane_offsets[self.lane]
                    info["adopted"] = self.lane
                    self.adopt = None
            else:
                self.adopt = None

        v_target, v_info = self._target_speed(t, road, s_e)
        geo_o = self._objects_on(self.ref, objs, s_e, ego)
        d_c = self.overtake["d_ref"] if self.overtake else 0.0
        corridor = self._corridor(road, s_e, v_e, d_e, d_c)
        lead_i, shift, pass_notes = self._lead(geo_o, s_e, d_c, v_e, lane.width, pred, t, corridor)
        a_c = self._idm(v_e, v_target, np.inf, 0.0)
        if lead_i is not None:
            gap = geo_o["ds"][lead_i] - 0.5 * geo_o["L"][lead_i] - self.geo.front
            a_c = self._idm(v_e, v_target, gap, v_e - geo_o["v"][lead_i])

        # ---------------------------------------------------- maneuver state machine
        reason = ""
        req = self._route_requirement(road, s_lane)
        info["route"] = {k: v for k, v in (req or {}).items()}
        if self.state in ("lane_change_left", "lane_change_right"):
            reason = self._update_lane_change(road, ego, objs, pred, t, s_e, d_e, v_e, v_target, a_c)
        elif lane.type == "merge" or self.state == "merging":
            reason = self._update_merge(road, ego, objs, pred, t, s_e, d_e, v_e, v_target, info)
        elif self.state == "overtaking":
            reason = self._update_overtake(road, geo_o, s_e, v_e, v_target, t, info)
        else:
            reason = self._decide(road, ego, objs, pred, t, s_e, s_lane, v_e, v_target, a_c, lead_i, geo_o, req,
                                  hazard, info)
        # re-evaluate the reference after a possible state change
        s_e, d_e = self._project(self.ref, ego.x, ego.y)
        self._s_hint = s_e
        d_c = self.overtake["d_ref"] if self.overtake else 0.0
        geo_o = self._objects_on(self.ref, objs, s_e, ego)
        corridor = self._corridor(road, s_e, v_e, d_e, d_c)
        lead_i, shift, pass_notes = self._lead(geo_o, s_e, d_c, v_e, road.lanes[self.lane].width, pred, t, corridor)
        v_target, v_info = self._target_speed(t, road, s_e)

        # ---------------------------------------------------- longitudinal modes
        modes = [LongitudinalMode("velocity", {"v_ref": v_target})]
        merging_mode = None
        if self.merge and self.merge.get("front") is not None and self.merge.get("rear") is not None:
            merging_mode = LongitudinalMode("merging", {"front_id": self.merge["front"], "rear_id": self.merge["rear"]})
            modes.append(merging_mode)
        lead_info = None
        if lead_i is not None:
            o = geo_o["obj"][lead_i]
            lead_info = {"id": o.id, "type": o.type, "gap": float(geo_o["ds"][lead_i] - 0.5 * o.length - self.geo.front),
                         "v": float(geo_o["v"][lead_i])}
            modes.append(LongitudinalMode("following", {"lead_id": o.id, "k0": p.k0, "kv": p.kv,
                                                        "lead_length": o.length, "ego_length": self.geo.length}))
        elif self.merge and self.merge.get("front") is not None and merging_mode is None and geo_o is not None and                 self.merge["front"] in geo_o["id"] and geo_o["ds"][geo_o["id"].index(self.merge["front"])] > 0:
            modes.append(LongitudinalMode("following", {"lead_id": self.merge["front"], "k0": p.k0, "kv": p.kv}))
        turn_left = self._route_turns_left(road)
        stops = self._stops(road, world, pred, t, s_e, v_e, turn_left)
        if self.merge and self.merge.get("switched") and self.merge.get("end_xy") is not None and \
                d_e < -0.5 * road.lanes[self.lane].width:
            s_end, _ = self.ref.project(*self.merge["end_xy"])
            stops.append({"s_stop": s_end - p.end_of_lane_margin, "reason": "Ende Beschleunigungsstreifen",
                          "source": "merge"})
        if stops:
            st = min(stops, key=lambda x: x["s_stop"])
            modes.append(LongitudinalMode("stopping", {"s_stop": float(st["s_stop"]), "reason": st["reason"],
                                                       "source": st["source"]}))
        d_ref = d_c + shift
        maneuver = self.state
        info.update({"state": self.state, "reason": reason, "lane": self.lane, "chain": list(self.chain),
                     "s": s_e, "d": d_e, "lead": lead_info, "stops": stops, "speed": v_info,
                     "passing": pass_notes, "corridor": corridor})
        if self.merge:
            info["merge"] = {k: v for k, v in self.merge.items() if k != "end_xy"}
        return BehaviorCommand(t=t, reference_line=self.ref, lane_id=self.chain[0], target_speed=v_target, modes=modes,
                               d_ref=float(d_ref), d_min=corridor[0], d_max=corridor[1], direction=1, reinit=False,
                               maneuver=maneuver, info=info)

    def _route_turns_left(self, road):
        # the chain contains a junction connector turning left (unprotected left turn at green)
        for lid in self.chain:
            lane = road.lanes[lid]
            if lane.junction is not None and not lane.closed:
                dth = float(wrap_angle(lane.center.theta[-1] - lane.center.theta[0]))
                if dth > 0.8:
                    return True
        return False

    # ------------------------------------------------------------------ decisions in lane keeping
    def _decide(self, road, ego, objs, pred, t, s_e, s_lane, v_e, v_target, a_c, lead_i, geo_o, req, hazard, info):
        p = self.params
        lane = road.lanes[self.lane]
        evals = {}
        if lane.junction is not None or v_e < p.lc_min_speed:
            return "Spurhalten"
        if hazard:
            return "Gefahrenindikator: Spurwechsel verschoben"
        cooldown = t - self.last_lc_t < p.lc_cooldown
        mandatory_side = None
        if req is not None and req.get("available", True):
            near = req["remaining"] < p.exit_prepare_distance * req["steps"] or lane.type in ("merge",)
            if near or self.lane not in self.route:
                mandatory_side = req["side"] if near else None
        v0 = v_target
        best = None
        for side in ("left", "right"):
            mand = side == mandatory_side
            if not mand and (not self.perm.get("lane_change", True) or cooldown):
                continue
            if mandatory_side is not None and not mand:
                continue                  # no discretionary change away from the route near the exit
            if req is not None and not mand and req["remaining"] < p.exit_prepare_distance * (req["steps"] + 1) and \
                    side != req["side"]:
                continue
            ev = self._lane_change_eval(road, side, objs, ego, s_lane, a_c, v_e, v0, pred, t, mandatory=mand)
            evals[side] = {k: v for k, v in ev.items() if k != "line"}
            if ev["ok"] and (best is None or mand or ev["incentive"] > best["incentive"]):
                best = ev
                if mand:
                    break
        info["lane_change"] = evals
        if best is not None:
            self._start_lane_change(road, best["side"], best["target"], t)
            why = "Route" if best["side"] == mandatory_side else "Anreiz %.2f" % best["incentive"]
            return f"Spurwechsel {'links' if best['side'] == 'left' else 'rechts'} ({why})"
        # overtaking on the oncoming lane (two-way road)
        if lead_i is not None and self.perm.get("overtake", True) and self.perm.get("use_opposite_lane", True):
            r = self._try_overtake(road, geo_o, lead_i, s_e, s_lane, v_e, v_target, t, info)
            if r:
                return r
        return "Spurhalten"

    def _start_lane_change(self, road, side, target, t):
        self.lc = {"side": side, "source": self.lane, "target": target, "t0": t}
        self.state = f"lane_change_{side}"
        self._set_lane(road, target, force=True)

    def _update_lane_change(self, road, ego, objs, pred, t, s_e, d_e, v_e, v_target, a_c):
        p = self.params
        lc = self.lc
        lane = road.lanes[self.lane]
        if abs(d_e) < p.lc_done_d:
            self.state, self.lc, self.last_lc_t = "lane_keeping", None, t
            return "Spurwechsel abgeschlossen"
        if p.lc_abort_unsafe and abs(d_e) > 0.5 * lane.width:
            # still in the source lane: check the safety again, abort if unsafe
            src = road.lanes[lc["source"]]
            s_src = src.center.project(ego.x, ego.y)[0]
            saved = self.lane
            self.lane = lc["source"]
            ev = self._lane_change_eval(road, lc["side"], objs, ego, s_src, a_c, v_e, v_target, pred, t,
                                        mandatory=True)
            self.lane = saved
            if not ev["safe"] and ev["target"] == lc["target"]:
                self.state, self.lc = "lane_keeping", None
                self.last_lc_t = t
                self._set_lane(road, src.id, force=True)
                return f"Spurwechsel abgebrochen: {ev['reason']}"
        return "Spurwechsel aktiv"

    # ------------------------------------------------------------------ overtaking via the oncoming lane
    def _oncoming_free(self, geo_o, s_e, d_lo, d_hi, distance, duration):
        p = self.params
        if geo_o is None:
            return True, None
        for i, o in enumerate(geo_o["obj"]):
            if geo_o["aligned"][i] and geo_o["v"][i] > 0.5:
                continue
            if geo_o["d"][i] + 0.5 * o.width < d_lo or geo_o["d"][i] - 0.5 * o.width > d_hi:
                continue
            ds = geo_o["ds"][i]
            if ds < -0.5 * (o.length + self.geo.length):
                continue
            closing = abs(geo_o["v"][i]) * (duration + p.overtake_margin_time)
            if ds - closing < distance + 10.0:
                return False, o.id
        return True, None

    def _try_overtake(self, road, geo_o, lead_i, s_e, s_lane, v_e, v_target, t, info):
        p = self.params
        lane = road.lanes[self.lane]
        lead = geo_o["obj"][lead_i]
        v_lead = geo_o["v"][lead_i]
        if v_target - v_lead < p.overtake_min_dv or not lane.opposite("left", s_lane):
            return ""
        nb = lane.neighbor("left", s_lane)
        if nb is None:
            return ""
        rel = geo_o["ds"][lead_i] + 0.5 * (lead.length + self.geo.length) + p.overtake_return_gap + p.k0
        dv = max(v_target - v_lead, 1.0)
        duration = rel / dv + 2.0
        distance = v_target * duration
        if distance > p.overtake_max_distance:
            info["overtake"] = "Überholweg zu lang"
            return ""
        marks = [lane.marking("left", s_lane + x) for x in np.linspace(0.0, distance, 12)]
        if any(m not in ("dashed", "none") for m in marks):
            info["overtake"] = "Überholverbot (durchgezogene Linie)"
            return ""
        # no further slow object in front of the lead within the overtaking distance (own lane)
        off = 0.5 * (lane.width + road.lanes[nb].width)
        free, oid = self._oncoming_free(geo_o, s_e, off - 0.5 * road.lanes[nb].width, off + 0.5 * road.lanes[nb].width,
                                        distance, duration)
        if not free:
            info["overtake"] = f"Gegenverkehr {oid}"
            return ""
        self.overtake = {"lead": lead.id, "d_ref": off, "t0": t, "distance": distance, "duration": duration}
        self.state = "overtaking"
        return f"Überholen von {lead.id} über die Gegenfahrbahn"

    def _update_overtake(self, road, geo_o, s_e, v_e, v_target, t, info):
        p = self.params
        ot = self.overtake
        lane = road.lanes[self.lane]
        idx = geo_o["id"].index(ot["lead"]) if geo_o is not None and ot["lead"] in geo_o["id"] else None
        if idx is None:
            self.overtake, self.state = None, "lane_keeping"
            return "Überholen beendet (Objekt verloren)"
        o = geo_o["obj"][idx]
        passed = geo_o["ds"][idx] + 0.5 * o.length + self.geo.rear + p.overtake_return_gap < 0
        if passed:
            self.overtake, self.state, self.last_lc_t = None, "lane_keeping", t
            return "Überholen abgeschlossen, Rückkehr nach rechts"
        nb = road.lanes[lane.left] if lane.left else None
        if nb is not None:
            off = ot["d_ref"]
            remaining = geo_o["ds"][idx] + 0.5 * (o.length + self.geo.length) + p.overtake_return_gap
            dur = max(remaining, 0.0) / max(v_e - geo_o["v"][idx], 1.0) + 1.0
            free, oid = self._oncoming_free(geo_o, s_e, off - 0.5 * nb.width, off + 0.5 * nb.width, v_e * dur, dur)
            behind = geo_o["ds"][idx] - 0.5 * (o.length + self.geo.length) > -2.0
            if not free and behind:
                self.overtake, self.state = None, "lane_keeping"
                return f"Überholen abgebrochen (Gegenverkehr {oid})"
        return "Überholen aktiv"

    # ------------------------------------------------------------------ merging (Werling 5.3.2)
    @trace("werling2011", section="5.3.2", equation="(3.15)", concept="merging_mode",
           note="Lückenwahl, Längsreferenz in der Lückenmitte, gleichzeitiges Verlegen der Referenzkurve")
    def _update_merge(self, road, ego, objs, pred, t, s_e, d_e, v_e, v_target, info):
        p = self.params
        if self.merge is None:
            src = road.lanes[self.lane]
            tgt = src.left
            xe, ye, _ = src.pose(src.length)
            self.merge = {"source": src.id, "target": tgt, "front": None, "rear": None, "switched": False,
                          "end_xy": (float(xe), float(ye)), "cost": None}
            self.state = "merging"
        m = self.merge
        tgt = road.lanes[m["target"]]
        line_t = road.route_line(road.chain(m["target"], route=self.route, ahead=p.route_ahead))
        s_t, d_t = line_t.project(ego.x, ego.y)
        if m["switched"] and abs(d_e) < p.lc_done_d:
            self.state, self.merge, self.last_lc_t = "lane_keeping", None, t
            return "Einfädeln abgeschlossen"
        s_end = line_t.project(*m["end_xy"])[0]
        geo = self._objects_on(line_t, objs, s_t, ego)
        veh = []
        if geo is not None:
            on = geo["aligned"] & (np.abs(geo["d"]) - 0.5 * geo["W"] < 0.5 * tgt.width - 0.3)
            veh = sorted(np.flatnonzero(on), key=lambda i: geo["s"][i])
        T = float(np.clip((s_end - s_t) / max(v_e, 5.0), 3.0, p.merge_horizon))
        rel = np.array([0.0, T])
        pos = {}
        for i in veh:
            so = self._pred_frenet(pred, geo["id"][i], line_t, rel, t)
            pos[i] = so if so is not None else geo["s"][i] + geo["v"][i] * rel
        gaps = [(None, veh[0] if veh else None)] + [(veh[k], veh[k + 1]) for k in range(len(veh) - 1)] + \
               ([(veh[-1], None)] if veh else [])
        L_e = self.geo.length
        best, cands = None, []
        for rear, front in gaps:
            v_ref = v_target
            if front is not None and rear is not None:
                a_end, b_end = pos[front][1] - 0.5 * geo["L"][front], pos[rear][1] + 0.5 * geo["L"][rear]
                v_gap = 0.5 * (geo["v"][front] + geo["v"][rear])
                free = a_end - b_end
                if free < L_e + 2 * p.merge_margin + 2 * p.merge_time_gap * v_gap:
                    continue
                c = 0.5 * (a_end + b_end)
            elif front is not None:
                v_gap = geo["v"][front]
                c = pos[front][1] - 0.5 * geo["L"][front] - 0.5 * L_e - p.merge_margin - p.merge_time_gap * v_gap
            elif rear is not None:
                v_gap = geo["v"][rear]
                c = pos[rear][1] + 0.5 * geo["L"][rear] + 0.5 * L_e + p.merge_margin + p.merge_time_gap * v_gap
                c = max(c, s_t + v_e * T)
            else:
                c, v_gap = s_t + v_e * T, v_ref
            a_req = 2.0 * (c - s_t - v_e * T) / T ** 2
            if not (p.merge_a_min <= a_req <= p.merge_a_max) or c > s_end - 0.5 * L_e or v_e + a_req * T < 0:
                continue
            # prefer gaps reachable without braking (merging is a speed synchronization from below)
            cost = abs(a_req) + 2.0 * max(-a_req, 0.0) + 0.05 * abs(v_gap - v_target)
            ids = (geo["id"][rear] if rear is not None else None, geo["id"][front] if front is not None else None)
            cands.append((cost, ids, a_req, c))
        if cands:
            best = min(cands, key=lambda x: x[0])
            prev = [x for x in cands if x[1] == (m["rear"], m["front"])]
            if prev and prev[0][0] <= best[0] + p.merge_hysteresis:
                best = prev[0]
            m["rear"], m["front"] = best[1]
            m["cost"], m["a_req"] = float(best[0]), float(best[2])
        else:
            m["rear"] = m["front"] = None
            m["a_req"] = None
        info["merge_candidates"] = [{"rear": c[1][0], "front": c[1][1], "cost": round(c[0], 3), "a_req": round(c[2], 2)}
                                    for c in cands]
        if not m["switched"] and best is not None:
            # Switch the reference curve when the current gap is safe (Werling 5.3.2).
            # Only the instantaneous gap is checked; the trajectory planner handles the
            # acceleration toward the gap once the reference is on the target lane.
            ok = True
            for oid, kind in ((m["front"], "front"), (m["rear"], "rear")):
                if oid is None:
                    continue
                i = geo["id"].index(oid)
                half = 0.5 * (geo["L"][i] + L_e)
                gap = geo["s"][i] - s_t - half if kind == "front" else s_t - geo["s"][i] - half
                if gap < p.merge_margin:
                    ok = False
            if ok:
                m["switched"] = True
                self._set_lane(road, m["target"], force=True)
                return "Einfädeln: Referenzkurve auf Zielspur verlegt"
            return "Einfädeln: Lücke gewählt, Synchronisation"
        if not m["switched"]:
            return "Einfädeln: keine passende Lücke"
        return "Einfädeln: Spurwechsel in die Lücke"

    # ------------------------------------------------------------------ parking
    def _parking(self, t, road, ego, objs, pred):
        p = self.params
        cfg = self.mission["parking"]
        spot = road.parking_spots[cfg["spot"]]
        drive, plane = cfg.get("drive_lane"), cfg.get("parking_lane", spot.lane_id)
        L_rev = float(cfg.get("reverse_length", 9.0))
        g = self.geo
        info = {}
        if self.park is None:
            self.park = {"phase": "park_approach", "t_hold": None}
            self._set_lane(road, drive, force=True)
        ph = self.park["phase"]
        reinit = False
        v_now = abs(ego.vx)
        if ph in ("park_approach", "park_hold"):
            ref = self.ref
            s_e, d_e = self._project(ref, ego.x, ego.y, self._s_hint)
            self._s_hint = s_e
            s_c = ref.project(spot.x, spot.y)[0]
            s_cog_stop = s_c + L_rev
            s_stop = s_cog_stop + g.front
            modes = [LongitudinalMode("velocity", {"v_ref": cfg.get("v_approach", 2.5)}),
                     LongitudinalMode("stopping", {"s_stop": s_stop, "reason": "Parkposition Phase 1",
                                                   "source": cfg["spot"]})]
            near = s_e >= s_cog_stop - 2 * p.park_tol
            if v_now < p.standstill_v and near:
                if self.park["t_hold"] is None:
                    self.park["t_hold"] = t
                ph = self.park["phase"] = "park_hold"
                if t - self.park["t_hold"] >= p.park_hold:
                    ph = self.park["phase"] = "park_reverse"
                    reinit = True
                    self.ref = road.reversed_line(plane)
                    self.chain = (plane,)
                    self._s_hint = None
            else:
                self.park["t_hold"] = None
                if ph == "park_hold":
                    ph = self.park["phase"] = "park_approach"
            if ph != "park_reverse":
                a, b = road.corridor(drive, s_e - ref.lane_offsets.get(drive, 0.0))
                info.update({"phase": ph, "s": s_e, "s_stop": s_stop})
                return BehaviorCommand(t=t, reference_line=ref, lane_id=self.chain[0],
                                       target_speed=cfg.get("v_approach", 2.5), modes=modes, d_ref=0.0, d_min=a,
                                       d_max=max(b, d_e + 0.5 * g.width + 0.1), direction=1, maneuver=ph,
                                       info={"state": ph, "reason": "Anfahrt neben die Lücke", **info})
        # reverse phase on the reversed parking-lane center line
        ref = self.ref
        Lp = ref.length
        s_c = Lp - road.lanes[plane].center.project(spot.x, spot.y)[0]
        s_e, d_e = self._project(ref, ego.x, ego.y, self._s_hint)
        self._s_hint = s_e
        s_stop = s_c + g.rear                    # rear bumper leads when reversing
        a, b = road.corridor(plane, Lp - s_e)
        d_min, d_max = -b, -a
        d_min, d_max = min(d_min, d_e - 0.5 * g.width - 0.1), max(d_max, d_e + 0.5 * g.width + 0.1)
        if ph == "park_reverse" and v_now < p.standstill_v and abs(s_e - s_c) < p.park_tol and \
                abs(d_e) < p.park_tol and not reinit:
            ph = self.park["phase"] = "parked"
        modes = [LongitudinalMode("velocity", {"v_ref": 0.0 if ph == "parked" else cfg.get("v_reverse", 1.0)}),
                 LongitudinalMode("stopping", {"s_stop": s_stop, "reason": "Lückenmitte", "source": cfg["spot"]})]
        return BehaviorCommand(t=t, reference_line=ref, lane_id=plane, target_speed=0.0 if ph == "parked" else
                               cfg.get("v_reverse", 1.0), modes=modes, d_ref=0.0, d_min=d_min, d_max=d_max,
                               direction=-1, reinit=reinit, maneuver=ph,
                               info={"state": ph, "reason": "Rückwärts in die Lücke" if ph != "parked" else "geparkt",
                                     "s": s_e, "d": d_e, "s_stop": s_stop, "phase": ph})
