import { lazy, Suspense, useMemo, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link, useSearchParams } from "react-router-dom";

import { EmptyState, Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { CheckboxField, NumberField, SelectField } from "../components/Field";
import { Icon } from "../components/Icon";
import { KpiTile } from "../components/KpiTile";
import { PageHeader } from "../components/PageHeader";
import { PathPlot, type Polyline } from "../components/PathPlot";
import { RunCompare } from "../components/RunCompare";
import { TrackPlayer, type Track } from "../components/TrackPlayer";
import type { SimulateRequest, SimulateResponse } from "../lib/api";
import { controllerLabel, kpiLabel, kpiValue, maneuverDescription, maneuverLabel, maneuverParamLabel, modelLabel } from "../lib/domain";
import { fmt, toDeg } from "../lib/format";
import { useClient, useMutation, usePersistentState, useQuery } from "../lib/hooks";
import { addRun, APPLIED_KEY, useRuns, type AppliedTrajectory } from "../lib/simRuns";
import { addRecentRun } from "./recentRuns";

const Chart = lazy(() => import("../components/Chart"));
const SIGNALS = ["t", "x", "y", "psi", "vx", "r", "ay", "ax", "beta", "delta_f", "lateral_error"];
const SUMMARY = ["max_ay", "max_yaw_rate", "max_beta", "max_lateral_error", "max_steer", "min_ax", "max_friction_utilization", "duration"];
const MODELS_BASIC = ["bicycle_kinematic", "bicycle_linear", "bicycle_nonlinear", "double_track", "multibody"];

interface Form {
  vehicle: string; maneuver: string; model: string; params: Record<string, number>; lateral: string; longitudinal: string;
  solver: "rk4" | "heun" | "euler"; dt: number; duration: number; mu: number; esp: boolean;
}
const DEFAULT: Form = { vehicle: "mid_size_sedan", maneuver: "iso_double_lane_change", model: "double_track", params: {},
  lateral: "stanley", longitudinal: "speed_pi", solver: "rk4", dt: 0.01, duration: 0, mu: 1.0, esp: false };

const LAST_KEY = "me.simulate.last";
let lastRun: { request: SimulateRequest; data: SimulateResponse } | null = null;
function readLastRun() {
  if (lastRun) return lastRun;
  try {
    const raw = sessionStorage.getItem(LAST_KEY);
    lastRun = raw ? JSON.parse(raw) : null;
  } catch {
    lastRun = null;
  }
  return lastRun;
}
function storeLastRun(run: { request: SimulateRequest; data: SimulateResponse }) {
  lastRun = run;
  try { sessionStorage.setItem(LAST_KEY, JSON.stringify(run)); } catch { /* quota: memory copy is enough */ }
}

export default function Simulate() {
  const { t, i18n } = useTranslation(["app", "common", "domain"]);
  const client = useClient();
  const [search] = useSearchParams();
  const [form, setForm] = usePersistentState<Form>("me.simulate.form", { ...DEFAULT, ...(search.get("model") ? { model: search.get("model")! } : {}) });
  const set = (patch: Partial<Form>) => setForm({ ...form, ...patch });
  const catalog = useQuery((s) => client.catalog(s), [client]);
  const maneuvers = useQuery((s) => client.maneuvers(s), [client]);
  const neural = useQuery((s) => client.models(s), [client]);
  const sim = useMutation((body: SimulateRequest) => client.simulate(body));
  // the last result stays when the page is left and opened again (memory + session storage)
  const [last, setLast] = useState<{ request: SimulateRequest; data: SimulateResponse } | null>(readLastRun);
  const [applied, setApplied] = usePersistentState<AppliedTrajectory | null>(APPLIED_KEY, null);
  const runs = useRuns();

  const maneuverOptions = useMemo(() => Object.keys(maneuvers.data ?? {}).filter((m) => m !== "custom")
    .map((m) => ({ value: m, label: maneuverLabel(t, m) })), [maneuvers.data, t]);
  const info = maneuvers.data?.[form.maneuver];
  const paramKeys = Object.keys(info?.params ?? {}).filter((p) => p !== "steering_ratio" && p !== "vehicle_width");
  const modelOptions = [...MODELS_BASIC, ...(neural.data ?? []).map((m) => m.vehicle_model)]
    .map((m) => ({ value: m, label: modelLabel(t, m) }));

  const run = async () => {
    const body: SimulateRequest = {
      vehicle: form.vehicle, model: form.model, maneuver: form.maneuver,
      maneuver_params: Object.fromEntries(Object.entries(form.params).filter(([k, v]) => paramKeys.includes(k) && Number.isFinite(v))),
      lateral_controller: form.lateral, longitudinal_controller: form.longitudinal, solver: form.solver, dt_control: form.dt,
      duration: form.duration || undefined, vehicle_overrides: { "tires.mu": form.mu, "systems.esp_enabled": form.esp },
      signals: SIGNALS, max_points: 1500,
      ...(applied?.waypoints ? { waypoints: { waypoints: applied.waypoints, ay_max: applied.ay_max || null } } : {}),
      ...(applied?.patches.length ? { environment: { friction: { base: form.mu, patches: applied.patches } } } : {}),
    };
    const res = await sim.run(body);
    if (res) {
      setLast({ request: body, data: res });
      storeLastRun({ request: body, data: res });
      addRun({ label: `${runs.length + 1}: ${applied?.waypoints ? t("simulate.editorPath") : maneuverLabel(t, form.maneuver)} · ${modelLabel(t, form.model)}`, at: Date.now(), request: body, data: res });
      const ay = res.kpis.find((k) => k.key === "max_ay")?.value;
      addRecentRun({ at: Date.now(), maneuver: form.maneuver, model: form.model, maxAy: typeof ay === "number" ? ay : null, wall: res.wall_time });
    }
  };

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("simulate.title")} description={t("simulate.subtitle")} />
      <div className="split">
        <form className="card" onSubmit={(e) => { e.preventDefault(); void run(); }} aria-labelledby="setup">
          <div className="card__header"><h2 id="setup">{t("simulate.setup")}</h2></div>
          <div className="card__body stack">
            <SelectField label={t("simulate.vehicle")} value={form.vehicle} onChange={(v) => set({ vehicle: v })}
              options={(catalog.data?.presets ?? [form.vehicle]).map((p) => ({ value: p, label: t(`vehiclePresets.${p}`, { defaultValue: p }) }))} />
            <SelectField label={t("simulate.maneuver")} value={form.maneuver} onChange={(v) => set({ maneuver: v, params: {} })}
              options={maneuverOptions.length ? maneuverOptions : [{ value: form.maneuver, label: maneuverLabel(t, form.maneuver) }]}
              hint={maneuverDescription(t, form.maneuver)} />
            {paramKeys.filter((p) => p.includes("speed")).slice(0, 1).map((p) => (
              <NumberField key={p} label={maneuverParamLabel(t, p)} unit={info?.params[p][1]} value={form.params[p] ?? NaN}
                onChange={(v) => set({ params: { ...form.params, [p]: v } })} hint={t("simulate.defaultHint")} />
            ))}
            {applied ? (
              <div className="alert alert--info"><Icon name="route" /><div>
                <strong>{applied.waypoints ? t("simulate.editorActive", { n: applied.waypoints.length }) : t("simulate.editorFriction")}</strong>
                {applied.patches.length ? <div className="subtle">{t("simulate.editorPatches", { n: applied.patches.length })}</div> : null}
                <div className="row"><Link className="btn btn--ghost btn--sm" to="/app/trajectory">{t("simulate.editorEdit")}</Link>
                  <button type="button" className="btn btn--ghost btn--sm" onClick={() => setApplied(null)}>{t("simulate.editorRemove")}</button></div>
              </div></div>
            ) : <Link className="subtle" to="/app/trajectory">{t("simulate.editorLink")}</Link>}
            <SelectField label={t("simulate.model")} value={form.model} onChange={(v) => set({ model: v })} options={modelOptions}
              tip={t("simulate.modelTip")} />
            <details className="expert">
              <summary><Icon name="settings" />{t("common:expertSettings")}</summary>
              <div className="stack">
                {paramKeys.filter((p) => !p.includes("speed")).map((p) => (
                  <NumberField key={p} label={maneuverParamLabel(t, p)} unit={info?.params[p][1]} value={form.params[p] ?? NaN}
                    onChange={(v) => set({ params: { ...form.params, [p]: v } })} />
                ))}
                <SelectField label={t("simulate.lateral")} value={form.lateral} onChange={(v) => set({ lateral: v })} tip={t("simulate.lateralTip")}
                  options={(catalog.data?.lateral_controllers ?? [form.lateral]).filter((c) => c !== "open_loop").map((c) => ({ value: c, label: controllerLabel(t, c) }))} />
                <SelectField label={t("simulate.longitudinal")} value={form.longitudinal} onChange={(v) => set({ longitudinal: v })}
                  options={(catalog.data?.longitudinal_controllers ?? [form.longitudinal]).map((c) => ({ value: c, label: controllerLabel(t, c) }))} />
                <NumberField label={t("simulate.mu")} value={form.mu} onChange={(v) => set({ mu: v })} min={0.05} max={1.5} step={0.05} tip={t("simulate.muTip")} />
                <CheckboxField label={t("simulate.esp")} checked={form.esp} onChange={(v) => set({ esp: v })} />
                <SelectField label={t("simulate.solver")} value={form.solver} onChange={(v) => set({ solver: v })}
                  options={(["rk4", "heun", "euler"] as const).map((s) => ({ value: s, label: t(`solvers.${s}`) }))} tip={t("simulate.solverTip")} />
                <NumberField label={t("simulate.dt")} unit="s" value={form.dt} onChange={(v) => set({ dt: v })} min={0.001} max={0.1} step={0.001} />
                <NumberField label={t("simulate.duration")} unit="s" value={form.duration} onChange={(v) => set({ duration: v })} min={0} max={120}
                  hint={t("simulate.durationHint")} />
                <button type="button" className="btn btn--ghost btn--sm" onClick={() => setForm(DEFAULT)}>{t("common:reset")}</button>
              </div>
            </details>
            <button type="submit" className="btn btn--primary btn--lg" disabled={sim.loading}>
              {sim.loading ? <span className="spinner" /> : <Icon name="play" />}{sim.loading ? t("simulate.running") : t("simulate.run")}
            </button>
          </div>
        </form>

        <div className="stack" aria-live="polite">
          <ErrorAlert error={sim.error} />
          {sim.loading && !last ? <ResultsSkeleton /> : null}
          {!sim.loading && !last && !sim.error ? (
            <div className="card"><EmptyState art="simulation" title={t("empty.simulation.title")} text={t("empty.simulation.text")}
              action={<button type="button" className="btn btn--primary" onClick={() => void run()}><Icon name="play" />{t("empty.simulation.action")}</button>} /></div>
          ) : null}
          {last ? <Results data={last.data} request={last.request} lang={i18n.language} /> : null}
          {runs.length ? <RunCompare lang={i18n.language} /> : null}
        </div>
      </div>
    </div>
  );
}

function ResultsSkeleton() {
  return <div className="stack"><div className="grid grid--4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} height={84} />)}</div><Skeleton height={320} /></div>;
}

function Results({ data, request, lang }: { data: SimulateResponse; request: SimulateRequest | null; lang: string }) {
  const { t } = useTranslation(["app", "common", "domain"]);
  const client = useClient();
  const reference = useQuery((sig) => (request?.waypoints ? client.waypointTrajectory(request.waypoints, sig) : request?.maneuver ? client.trajectory({ maneuver: request.maneuver, vehicle: request.vehicle ?? "mid_size_sedan",
    params: request.maneuver_params, max_points: 800 }, sig) : Promise.resolve(null)), [client, request]);
  const vehicle = useQuery((sig) => client.vehicle(request?.vehicle ?? "mid_size_sedan", sig), [client, request?.vehicle]);
  const track = useMemo<Track>(() => {
    const p = Object.fromEntries((vehicle.data?.schema ?? []).map((q) => [q.key, q.value as number]));
    const length = p["vehicle.length"] ?? 4.8, width = p["vehicle.width"] ?? 1.85;
    // geometric center relative to the CoG: overhangs split evenly
    const offset = (p["vehicle.cg_to_front"] ?? 1.25) - 0.5 * (p["vehicle.wheelbase"] ?? 2.8);
    return { t: data.signals.t ?? [], x: data.signals.x ?? [], y: data.signals.y ?? [], psi: data.signals.psi ?? [],
      v: data.signals.vx ?? [], length, width, centerOffset: offset };
  }, [data, vehicle.data]);
  const refLines = useMemo<Polyline[]>(() => (reference.data ? [{ x: reference.data.x, y: reference.data.y, kind: "road" }] : []), [reference.data]);
  const s = data.signals;
  const tt = s.t ?? [];
  const deg = useMemo(() => ({
    r: (s.r ?? []).map((v) => (v === null ? null : toDeg(v))),
    delta: (s.delta_f ?? []).map((v) => (v === null ? null : toDeg(v))),
    beta: (s.beta ?? []).map((v) => (v === null ? null : toDeg(v))),
    kmh: (s.vx ?? []).map((v) => (v === null ? null : v * 3.6)),
  }), [s]);
  const summary = SUMMARY.map((k) => data.kpis.find((x) => x.key === k)).filter((k): k is NonNullable<typeof k> => Boolean(k));
  return (
    <>
      <div className="row row--between">
        <div className="row">
          <span className="badge badge--info">{modelLabel(t, data.model)}</span>
          <span className={`badge ${data.stop_code === "duration_reached" || data.stop_code === "end_of_trajectory" ? "badge--success" : "badge--warning"}`}>
            {t(`stopCodes.${data.stop_code}`, { defaultValue: data.stop_reason })}</span>
        </div>
        <span className="subtle">{t("simulate.timing", { sim: fmt(data.simulated_time, lang), wall: fmt(data.wall_time, lang), rtf: fmt(data.simulated_time / Math.max(data.wall_time, 1e-6), lang) })}</span>
      </div>
      <div className="grid grid--4">
        {summary.map((k) => <KpiTile key={k.key} label={kpiLabel(t, k)} value={kpiValue(t, k)} unit={k.unit} lang={lang} badge={k.rating as "ok" | "warn" | "fail" | ""} />)}
      </div>
      <div className="card"><div className="card__header"><div><h2>{t("simulate.drive")}</h2><p>{t("simulate.driveHint")}</p></div></div><div className="card__body">
        {track.psi.length ? <TrackPlayer track={track} lines={refLines} height={280} ariaLabel={t("simulate.drive")} />
          : <PathPlot ariaLabel={t("simulate.path")} lines={[{ x: s.x ?? [], y: s.y ?? [], kind: "selected" }]} height={260} />}
      </div></div>
      <Suspense fallback={<Skeleton height={240} />}>
        <div className="grid grid--2">
          <ChartCard title={t("simulate.charts.yaw")}><Chart x={tt} xLabel="t [s]" yLabel="°/s" ariaLabel={t("simulate.charts.yaw")}
            series={[{ label: t("simulate.series.yawRate"), values: deg.r }]} /></ChartCard>
          <ChartCard title={t("simulate.charts.lateral")}><Chart x={tt} xLabel="t [s]" yLabel="m/s²" ariaLabel={t("simulate.charts.lateral")}
            series={[{ label: t("simulate.series.ay"), values: s.ay ?? [], color: 1 }, { label: t("simulate.series.ax"), values: s.ax ?? [], color: 2 }]} /></ChartCard>
          <ChartCard title={t("simulate.charts.steering")}><Chart x={tt} xLabel="t [s]" yLabel="°" ariaLabel={t("simulate.charts.steering")}
            series={[{ label: t("simulate.series.delta"), values: deg.delta, color: 3 }, { label: t("simulate.series.beta"), values: deg.beta, color: 4 }]} /></ChartCard>
          <ChartCard title={t("simulate.charts.tracking")}><Chart x={tt} xLabel="t [s]" yLabel="m" ariaLabel={t("simulate.charts.tracking")}
            series={[{ label: t("simulate.series.lateralError"), values: s.lateral_error ?? [], color: 4 }]} /></ChartCard>
        </div>
      </Suspense>
      <details className="card" style={{ padding: "var(--me-space-4)" }}>
        <summary style={{ cursor: "pointer", fontWeight: 600 }}>{t("simulate.allKpis", { n: data.kpis.length })}</summary>
        <div className="table-wrap" style={{ marginTop: "var(--me-space-3)" }}><table className="table">
          <thead><tr><th>{t("simulate.kpiTable.group")}</th><th>{t("simulate.kpiTable.kpi")}</th><th className="num">{t("simulate.kpiTable.value")}</th><th>{t("simulate.kpiTable.unit")}</th></tr></thead>
          <tbody>{data.kpis.map((k) => {
            const v = kpiValue(t, k);
            return <tr key={k.key}><td className="subtle">{t(`kpiGroups.${k.group_code}`, { defaultValue: k.group })}</td><td>{kpiLabel(t, k)}</td>
              <td className="num">{typeof v === "number" ? fmt(v, lang) : v ?? "–"}</td><td className="subtle">{k.unit}</td></tr>;
          })}</tbody>
        </table></div>
      </details>
    </>
  );
}

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return <div className="card"><div className="card__body"><div className="chart-title">{title}</div>{children}</div></div>;
}
