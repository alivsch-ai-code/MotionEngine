// Trajectory editor: a path through waypoints with corner radii and a speed profile, plus a friction map.
// The result drives the vehicle-dynamics simulation instead of a maneuver.
// (Desktop equivalent: trajectory editor panel of the main window.)
import { lazy, Suspense, useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { NumberField, SelectField } from "../components/Field";
import { Icon } from "../components/Icon";
import { PageHeader } from "../components/PageHeader";
import type { FrictionPatch, TrajectoryData, Waypoint } from "../lib/api";
import { maneuverLabel } from "../lib/domain";
import { fmt } from "../lib/format";
import { useClient, usePersistentState, useQuery } from "../lib/hooks";
import { APPLIED_KEY, type AppliedTrajectory } from "../lib/simRuns";
import { downloadBlob } from "../lib/stack";

const Chart = lazy(() => import("../components/Chart"));

interface State { waypoints: Waypoint[]; ayMax: number; radius: number; patches: FrictionPatch[] }
const DEFAULT: State = {
  waypoints: [{ x: 0, y: 0, v_kmh: 50, radius: 0 }, { x: 80, y: 0, v_kmh: 50, radius: 20 }, { x: 120, y: 40, v_kmh: 40, radius: 15 },
    { x: 80, y: 90, v_kmh: 40, radius: 15 }, { x: 0, y: 90, v_kmh: 50, radius: 0 }],
  ayMax: 4, radius: 15, patches: [],
};
const WP_COLS = ["x", "y", "v_kmh", "radius"] as const;
const PATCH_COLS = ["x_min", "x_max", "y_min", "y_max", "mu"] as const;
const round = (v: number) => Math.round(v * 100) / 100;

export default function TrajectoryEditor() {
  const { t, i18n } = useTranslation(["app", "common", "domain"]);
  const lang = i18n.language;
  const client = useClient();
  const navigate = useNavigate();
  const [state, setStored] = usePersistentState<State>("me.editor.state", DEFAULT);
  const [, setApplied] = usePersistentState<AppliedTrajectory | null>(APPLIED_KEY, null);
  const undo = useRef<State[]>([]);
  const [canUndo, setCanUndo] = useState(false);
  const [preview, setPreview] = useState<TrajectoryData | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [maneuver, setManeuver] = useState("iso_double_lane_change");
  const maneuvers = useQuery((s) => client.maneuvers(s), [client]);
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<{ index: number; moved: boolean } | null>(null);
  const [frozen, setFrozen] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  // every edit can be undone; a drag is one edit
  const commit = (next: State, snapshot = true) => {
    if (snapshot) { undo.current = [...undo.current.slice(-49), state]; setCanUndo(true); }
    setStored(next);
  };
  const setWaypoints = (waypoints: Waypoint[], snapshot = true) => commit({ ...state, waypoints }, snapshot);
  const back = () => {
    const prev = undo.current.pop();
    if (prev) setStored(prev);
    setCanUndo(undo.current.length > 0);
  };

  // preview from the server (same code as the simulation uses), shortly after the last edit
  const key = JSON.stringify([state.waypoints, state.ayMax]);
  useEffect(() => {
    if (state.waypoints.length < 2) { setPreview(null); return; }
    const ctrl = new AbortController();
    const timer = window.setTimeout(() => {
      client.waypointTrajectory({ waypoints: state.waypoints, ay_max: state.ayMax || null }, ctrl.signal)
        .then((p) => { setPreview(p); setError(null); }, (err) => { if ((err as Error).name !== "AbortError") { setPreview(null); setError(err); } });
    }, 200);
    return () => { window.clearTimeout(timer); ctrl.abort(); };
  }, [key, client]);

  const view = useMemo(() => {
    const xs = [...state.waypoints.map((w) => w.x), ...state.patches.flatMap((p) => [p.x_min, p.x_max])];
    const ys = [...state.waypoints.map((w) => w.y), ...state.patches.flatMap((p) => [p.y_min, p.y_max])];
    if (!xs.length) return { x: -20, y: -60, w: 160, h: 120 };
    const xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = Math.min(...ys), ymax = Math.max(...ys);
    const pad = Math.max(xmax - xmin, ymax - ymin, 40) * 0.12;
    return { x: xmin - pad, y: -(ymax + pad), w: xmax - xmin + 2 * pad, h: ymax - ymin + 2 * pad };
  }, [state.waypoints, state.patches]);
  const box = frozen ?? view;
  const handle = Math.max(box.w, box.h * 1.6) / 70;

  const toWorld = (e: { clientX: number; clientY: number }) => {
    const el = svg.current, m = el?.getScreenCTM();
    if (!el || !m) return { x: 0, y: 0 };
    const p = new DOMPoint(e.clientX, e.clientY).matrixTransform(m.inverse());
    return { x: round(p.x), y: round(-p.y) };
  };
  const down = (index: number) => (e: ReactPointerEvent<SVGCircleElement>) => {
    if (e.button !== 0) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    drag.current = { index, moved: false };
    setFrozen(view);
  };
  const move = (e: ReactPointerEvent<SVGCircleElement>) => {
    const d = drag.current;
    if (!d) return;
    const p = toWorld(e);
    setWaypoints(state.waypoints.map((w, i) => (i === d.index ? { ...w, ...p } : w)), !d.moved);
    d.moved = true;
  };
  const up = () => { drag.current = null; setFrozen(null); };
  // double click: a new waypoint in the nearest segment
  const insert = (e: React.MouseEvent) => {
    const p = toWorld(e), w = state.waypoints;
    let best = w.length - 1, bestD = Infinity;
    for (let i = 0; i < w.length - 1; i++) {
      const ax = w[i].x, ay = w[i].y, bx = w[i + 1].x, by = w[i + 1].y;
      const len = (bx - ax) ** 2 + (by - ay) ** 2 || 1;
      const u = Math.max(0, Math.min(1, ((p.x - ax) * (bx - ax) + (p.y - ay) * (by - ay)) / len));
      const d = Math.hypot(p.x - (ax + u * (bx - ax)), p.y - (ay + u * (by - ay)));
      if (d < bestD) { bestD = d; best = i; }
    }
    const ref = w[Math.min(best, w.length - 1)] ?? { v_kmh: 50 };
    const point = { ...p, v_kmh: ref.v_kmh, radius: state.radius };
    setWaypoints(w.length < 2 ? [...w, point] : [...w.slice(0, best + 1), point, ...w.slice(best + 1)]);
  };
  const remove = (index: number) => { if (state.waypoints.length > 2) setWaypoints(state.waypoints.filter((_, i) => i !== index)); };

  const save = () => downloadBlob(new Blob([JSON.stringify({ waypoints: state.waypoints, friction_patches: state.patches }, null, 1)], { type: "application/json" }), "waypoints.json");
  const load = async (files: FileList | null) => {
    const file = files?.[0];
    if (!file) return;
    try {
      const j = JSON.parse(await file.text()) as { waypoints?: Partial<Waypoint>[]; friction_patches?: FrictionPatch[] };
      const pts = (j.waypoints ?? []).filter((w) => Number.isFinite(w.x) && Number.isFinite(w.y))
        .map((w) => ({ x: w.x as number, y: w.y as number, v_kmh: Number.isFinite(w.v_kmh) ? (w.v_kmh as number) : 50, radius: Number.isFinite(w.radius) ? (w.radius as number) : 0 }));
      if (pts.length < 2) throw new Error("waypoints");
      commit({ ...state, waypoints: pts, patches: Array.isArray(j.friction_patches) ? j.friction_patches : state.patches });
      setError(null);
    } catch {
      setError(new Error(t("editor.badFile")));
    } finally {
      if (fileInput.current) fileInput.current.value = "";
    }
  };
  const fromManeuver = async () => {
    try {
      const r = await client.waypointsFromManeuver({ maneuver, vehicle: "mid_size_sedan", n_points: 25 });
      setWaypoints(r.waypoints.map((w) => ({ x: round(w.x), y: round(w.y), v_kmh: round(w.v_kmh), radius: 0 })));
      setError(null);
    } catch (err) { setError(err); }
  };
  const apply = (withPath: boolean) => {
    setApplied({ waypoints: withPath ? state.waypoints : null, ay_max: state.ayMax, patches: state.patches });
    navigate("/app/simulate");
  };

  const vmax = preview ? Math.max(...preview.v, 0.1) : 1;
  const maneuverOptions = Object.keys(maneuvers.data ?? {}).filter((m) => m !== "custom").map((m) => ({ value: m, label: maneuverLabel(t, m) }));
  const kmh = useMemo(() => (preview?.v ?? []).map((v) => v * 3.6), [preview]);
  const ay = useMemo(() => (preview ? preview.v.map((v, i) => v * v * Math.abs(preview.kappa[i] ?? 0)) : []), [preview]);

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("editor.title")} description={t("editor.subtitle")} />
      <ErrorAlert error={error} />
      <div className="split split--editor">
        <div className="stack">
          <div className="card"><div className="card__body stack">
            <svg ref={svg} className="chart editor" viewBox={`${box.x} ${box.y} ${box.w} ${box.h}`} style={{ height: 420 }} preserveAspectRatio="xMidYMid meet"
              role="application" aria-label={t("editor.canvas")} onDoubleClick={insert}>
              {state.patches.map((p, i) => (
                <g key={i}><rect x={Math.min(p.x_min, p.x_max)} y={-Math.max(p.y_min, p.y_max)} width={Math.abs(p.x_max - p.x_min)} height={Math.abs(p.y_max - p.y_min)}
                  fill="var(--me-chart-2)" fillOpacity={0.18} stroke="var(--me-chart-2)" strokeWidth={1} vectorEffect="non-scaling-stroke" />
                  <text x={Math.min(p.x_min, p.x_max) + handle * 0.5} y={-Math.max(p.y_min, p.y_max) + handle * 1.8} fontSize={handle * 1.5} fill="var(--me-text-muted)">μ {fmt(p.mu, lang, 2)}</text></g>
              ))}
              <polyline points={state.waypoints.map((w) => `${w.x},${-w.y}`).join(" ")} fill="none" stroke="var(--me-text-subtle)" strokeWidth={1} strokeDasharray="5 5"
                vectorEffect="non-scaling-stroke" />
              {preview ? preview.x.slice(0, -1).map((x, i) => (i % 2 ? null : (
                <line key={i} x1={x} y1={-preview.y[i]} x2={preview.x[Math.min(i + 2, preview.x.length - 1)]} y2={-preview.y[Math.min(i + 2, preview.y.length - 1)]}
                  stroke={`color-mix(in srgb, var(--me-chart-3) ${Math.round((1 - preview.v[i] / vmax) * 100)}%, var(--me-primary))`} strokeWidth={3} strokeLinecap="round"
                  vectorEffect="non-scaling-stroke" />))) : null}
              {state.waypoints.map((w, i) => (
                <g key={i}>
                  <circle cx={w.x} cy={-w.y} r={handle} className="editor__handle" tabIndex={0} role="button" aria-label={t("editor.waypoint", { n: i + 1 })}
                    onPointerDown={down(i)} onPointerMove={move} onPointerUp={up} onPointerCancel={up} onDoubleClick={(e) => e.stopPropagation()}
                    onContextMenu={(e) => { e.preventDefault(); remove(i); }}
                    onKeyDown={(e) => {
                      const step = e.shiftKey ? 5 : 1;
                      const d = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, step], ArrowDown: [0, -step] }[e.key];
                      if (d) { e.preventDefault(); setWaypoints(state.waypoints.map((p, k) => (k === i ? { ...p, x: round(p.x + d[0]), y: round(p.y + d[1]) } : p))); }
                      if (e.key === "Delete" || e.key === "Backspace") { e.preventDefault(); remove(i); }
                    }} />
                  <text x={w.x + handle * 1.3} y={-w.y - handle * 1.1} fontSize={handle * 1.6} fill="var(--me-text-muted)" pointerEvents="none">{i + 1}</text>
                </g>
              ))}
            </svg>
            <p className="subtle">{t("editor.hint")}</p>
            <div className="row">
              {preview ? <><span className="badge badge--info">{t("editor.length", { v: fmt(preview.length, lang, 4) })}</span>
                <span className="badge badge--info">{t("editor.speedRange", { min: fmt(Math.min(...kmh), lang, 3), max: fmt(Math.max(...kmh), lang, 3) })}</span>
                <span className="badge badge--info">{t("editor.maxAy", { v: fmt(Math.max(...ay, 0), lang, 3) })}</span></> : null}
            </div>
          </div></div>
          {preview ? (
            <Suspense fallback={<Skeleton height={200} />}>
              <div className="grid grid--2">
                <div className="card"><div className="card__body"><div className="chart-title">{t("editor.charts.speed")}</div>
                  <Chart x={preview.s} xLabel="s [m]" yLabel="km/h" height={190} ariaLabel={t("editor.charts.speed")} series={[{ label: "v", values: kmh }]} /></div></div>
                <div className="card"><div className="card__body"><div className="chart-title">{t("editor.charts.curvature")}</div>
                  <Chart x={preview.s} xLabel="s [m]" yLabel="1/m" height={190} ariaLabel={t("editor.charts.curvature")} series={[{ label: "κ", values: preview.kappa, color: 3 }]} /></div></div>
              </div>
            </Suspense>
          ) : null}
        </div>
        <div className="stack">
          <div className="card"><div className="card__header"><h2>{t("editor.waypoints", { n: state.waypoints.length })}</h2></div><div className="card__body stack">
            <div className="table-wrap" style={{ maxHeight: 300, overflowY: "auto" }}><table className="table table--edit">
              <thead><tr><th>#</th>{WP_COLS.map((c) => <th key={c}>{t(`editor.cols.${c}`)}</th>)}<th /></tr></thead>
              <tbody>{state.waypoints.map((w, i) => (
                <tr key={i}><td className="subtle">{i + 1}</td>
                  {WP_COLS.map((c) => <td key={c}><input className="input input--cell" type="number" step="any" value={Number.isFinite(w[c]) ? w[c] : ""} aria-label={`${t(`editor.cols.${c}`)} ${i + 1}`}
                    disabled={c === "radius" && (i === 0 || i === state.waypoints.length - 1)}
                    onChange={(e) => setWaypoints(state.waypoints.map((p, k) => (k === i ? { ...p, [c]: Number.isFinite(e.target.valueAsNumber) ? e.target.valueAsNumber : 0 } : p)))} /></td>)}
                  <td><button type="button" className="btn btn--ghost btn--sm btn--icon" disabled={state.waypoints.length <= 2} aria-label={t("editor.removeWaypoint", { n: i + 1 })}
                    onClick={() => remove(i)}><Icon name="trash" size={14} /></button></td></tr>
              ))}</tbody></table></div>
            <button type="button" className="btn btn--ghost btn--sm" onClick={() => { const l = state.waypoints[state.waypoints.length - 1]; setWaypoints([...state.waypoints, { x: round(l.x + 20), y: l.y, v_kmh: l.v_kmh, radius: 0 }]); }}>
              <Icon name="plus" size={14} />{t("editor.addWaypoint")}</button>
            <div className="grid grid--2-tight">
              <NumberField label={t("editor.radius")} unit="m" value={state.radius} min={0} max={500} onChange={(v) => commit({ ...state, radius: v }, false)} />
              <NumberField label={t("editor.ayMax")} unit="m/s²" value={state.ayMax} min={0} max={15} step={0.5} onChange={(v) => commit({ ...state, ayMax: Number.isFinite(v) ? v : 0 }, false)}
                hint={t("editor.ayMaxHint")} />
            </div>
            <div className="row">
              <button type="button" className="btn btn--secondary btn--sm" onClick={() => setWaypoints(state.waypoints.map((w, i) => (i === 0 || i === state.waypoints.length - 1 ? w : { ...w, radius: state.radius || 0 })))}>
                {t("editor.radiusAll")}</button>
              <button type="button" className="btn btn--secondary btn--sm" disabled={!canUndo} onClick={back}>{t("editor.undo")}</button>
              <button type="button" className="btn btn--ghost btn--sm" onClick={save}>{t("editor.save")}</button>
              <input ref={fileInput} type="file" accept=".json" hidden onChange={(e) => void load(e.target.files)} />
              <button type="button" className="btn btn--ghost btn--sm" onClick={() => fileInput.current?.click()}><Icon name="upload" size={14} />{t("editor.load")}</button>
            </div>
            <div className="row" style={{ alignItems: "flex-end" }}>
              <div style={{ flex: 1 }}><SelectField label={t("editor.fromManeuver")} value={maneuver} onChange={setManeuver}
                options={maneuverOptions.length ? maneuverOptions : [{ value: maneuver, label: maneuverLabel(t, maneuver) }]} /></div>
              <button type="button" className="btn btn--secondary" onClick={() => void fromManeuver()}>{t("editor.take")}</button>
            </div>
          </div></div>
          <div className="card"><div className="card__header"><div><h2>{t("editor.friction.title")}</h2><p>{t("editor.friction.text")}</p></div></div><div className="card__body stack">
            {state.patches.length ? <div className="table-wrap"><table className="table table--edit">
              <thead><tr>{PATCH_COLS.map((c) => <th key={c}>{t(`editor.friction.cols.${c}`)}</th>)}<th /></tr></thead>
              <tbody>{state.patches.map((p, i) => (
                <tr key={i}>{PATCH_COLS.map((c) => <td key={c}><input className="input input--cell" type="number" step="any" value={Number.isFinite(p[c]) ? p[c] : ""}
                  aria-label={`${t(`editor.friction.cols.${c}`)} ${i + 1}`}
                  onChange={(e) => commit({ ...state, patches: state.patches.map((q, k) => (k === i ? { ...q, [c]: Number.isFinite(e.target.valueAsNumber) ? e.target.valueAsNumber : 0 } : q)) })} /></td>)}
                  <td><button type="button" className="btn btn--ghost btn--sm btn--icon" aria-label={t("editor.friction.remove", { n: i + 1 })}
                    onClick={() => commit({ ...state, patches: state.patches.filter((_, k) => k !== i) })}><Icon name="trash" size={14} /></button></td></tr>
              ))}</tbody></table></div> : null}
            <button type="button" className="btn btn--ghost btn--sm" onClick={() => commit({ ...state, patches: [...state.patches, { x_min: 40, x_max: 80, y_min: -5, y_max: 5, mu: 0.4 }] })}>
              <Icon name="plus" size={14} />{t("editor.friction.add")}</button>
          </div></div>
          <button type="button" className="btn btn--primary btn--lg" disabled={!preview} onClick={() => apply(true)}><Icon name="play" />{t("editor.apply")}</button>
          {state.patches.length ? <button type="button" className="btn btn--secondary" onClick={() => apply(false)}>{t("editor.applyFriction")}</button> : null}
        </div>
      </div>
    </div>
  );
}
