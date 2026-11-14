// Controller lab: several tracking controllers on the same reference path and plant, side by side, and the
// control law of one of them with the value of every term at the selected time.
import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { EmptyState, Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { CheckboxField, NumberField, SelectField } from "../components/Field";
import { Formula } from "../components/Formula";
import { Icon } from "../components/Icon";
import { PageHeader } from "../components/PageHeader";
import { ParamDialog } from "../components/ParamDialog";
import { PathPlot, type Polyline } from "../components/PathPlot";
import { RichText } from "../components/RichText";
import type { ControlResult, ControlRun, ControlRunRequest } from "../lib/api";
import { fmt } from "../lib/format";
import { useClient, useMutation, usePersistentState, useQuery } from "../lib/hooks";

const Chart = lazy(() => import("../components/Chart"));
export const CONTROL_FORM_KEY = "me.control.form";
export interface ControlForm {
  controllers: string[]; params: Record<string, Record<string, unknown>>; path: string; speed: number; plant: string; mu: number;
  lateralOffset: number; gust: number; gustTime: number; actuator?: "ideal" | "realistic"; autorun?: boolean;
}
export const CONTROL_DEFAULT: ControlForm = { controllers: ["pure_pursuit", "stanley", "lqr"], params: {}, path: "lane_change", speed: 15, plant: "werling_desm", mu: 1,
  lateralOffset: 0, gust: 0, gustTime: 3 };

// control laws (language neutral) and the terms each controller reports per step
const LAWS: Record<string, { tex: string; terms: [string, string, "deg" | "m" | "none"][] }> = {
  pure_pursuit: { tex: "\\delta = \\arctan\\!\\left(\\frac{2\\,l\\,\\sin\\alpha}{L_d}\\right),\\qquad L_d = \\max(L_{\\min},\\,k\\,v)",
    terms: [["lookahead", "L_d", "m"], ["alpha", "\\alpha", "deg"]] },
  stanley: { tex: "\\delta = \\underbrace{\\theta_e}_{\\text{heading}} + \\underbrace{\\arctan\\!\\left(\\frac{-k\\,e_{fa}}{k_{soft}+v}\\right)}_{\\text{feedback}} + \\underbrace{\\delta_{ff}}_{\\text{feedforward}} \\underbrace{-\\,k_r\\,(r - v\\kappa)}_{\\text{damping}}",
    terms: [["e_front", "e_{fa}", "m"], ["heading", "\\theta_e", "deg"], ["feedback", "\\arctan(\\cdot)", "deg"], ["feedforward", "\\delta_{ff}", "deg"], ["damping", "-k_r(r-v\\kappa)", "deg"]] },
  lqr: { tex: "\\delta = -K\\,x + \\delta_{ff},\\qquad x = [\\,e_1,\\ \\dot e_1,\\ e_2,\\ \\dot e_2\\,]^T,\\qquad K = \\text{DARE}(A(v), B, Q, R)",
    terms: [["x1", "e_1", "m"], ["x2", "\\dot e_1", "none"], ["x3", "e_2", "deg"], ["x4", "\\dot e_2", "none"], ["K1", "K_1", "none"], ["K2", "K_2", "none"], ["K3", "K_3", "none"], ["K4", "K_4", "none"],
      ["feedback", "-Kx", "deg"], ["feedforward", "\\delta_{ff}", "deg"]] },
  mpc: { tex: "\\min_{u_0..u_{N-1}} \\sum_{k=1}^{N} q_y e_{y,k}^2 + q_\\psi e_{\\psi,k}^2 + r\\,u_k^2 \\quad \\text{s.t.}\\quad \\dot e_y = v\\,e_\\psi,\\ \\ |\\delta|\\le\\delta_{\\max},\\ |u|\\le\\dot\\delta_{\\max},\\qquad u=\\dot\\delta",
    terms: [["steer_rate_plan", "u_0 = \\dot\\delta", "deg"]] },
  werling_bilevel: { tex: "\\ddot e_n + k_1\\,\\dot e_n + k_0\\,e_n = 0 \\quad\\text{(exact input-output linearization of the single-track model)}", terms: [] },
};
const SERIES: [string, string, string][] = [["e_n", "m", "e_n"], ["delta_deg", "°", "delta"], ["e_theta_deg", "°", "e_theta"], ["ay", "m/s²", "ay"]];
const conv = (v: number | null | undefined, unit: string) => (v === null || v === undefined ? null : unit === "deg" ? (v * 180) / Math.PI : v);

export default function ControlLab() {
  const { t, i18n } = useTranslation(["app", "common"]);
  const lang = i18n.language;
  const client = useClient();
  const catalog = useQuery((s) => client.controlCatalog(s), [client]);
  const [form, setForm] = usePersistentState<ControlForm>(CONTROL_FORM_KEY, CONTROL_DEFAULT);
  const set = (patch: Partial<ControlForm>) => setForm({ ...form, ...patch });
  const run = useMutation((body: ControlRunRequest) => client.controlRun(body));
  const [dialog, setDialog] = useState<string | null>(null);
  const [focus, setFocus] = useState<string>("");
  const [time, setTime] = useState(0);

  const start = (f: ControlForm = form) => run.run({
    controllers: f.controllers.map((name) => ({ name, params: f.params[name] ?? {}, label: t(`control.names.${name}`) })),
    path: f.path, speed: f.speed, plant: f.plant, mu: f.mu, actuator: f.actuator ?? "ideal", lateral_offset: f.lateralOffset,
    disturbance: f.gust ? { t: f.gustTime, duration: 0.5, fy: f.gust } : null,
  });
  // a lesson can open this page with a prepared experiment that starts at once
  useEffect(() => {
    if (form.autorun) { const f = { ...form, autorun: false }; setForm(f); void start(f); }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const data = run.data;
  const names = catalog.data?.controllers.map((c) => c.name) ?? form.controllers;
  const toggle = (name: string, on: boolean) => set({ controllers: on ? [...form.controllers, name].filter((v, i, a) => a.indexOf(v) === i) : form.controllers.filter((n) => n !== name) });

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("control.title")} description={t("control.subtitle")} />
      <div className="split">
        <form className="card" onSubmit={(e) => { e.preventDefault(); void start(); }}>
          <div className="card__header"><h2>{t("control.setup")}</h2></div>
          <div className="card__body stack">
            <div className="field"><span className="field__label">{t("control.controllers")}</span>
              {names.map((name) => {
                const info = catalog.data?.controllers.find((c) => c.name === name);
                const changed = Object.keys(form.params[name] ?? {}).length;
                return (
                  <div key={name} className="row row--between">
                    <CheckboxField label={t(`control.names.${name}`)} checked={form.controllers.includes(name)} onChange={(v) => toggle(name, v)} />
                    {info?.params.length ? <button type="button" className="btn btn--ghost btn--sm" onClick={() => setDialog(name)}>
                      <Icon name="settings" size={14} />{changed ? t("control.paramsChanged", { n: changed }) : t("control.params")}</button> : null}
                    {dialog === name && info ? <ParamDialog title={t(`control.names.${name}`)} schema={info.params} overrides={form.params[name] ?? {}} onClose={() => setDialog(null)}
                      onApply={(c) => { set({ params: { ...form.params, [name]: c } }); setDialog(null); }} /> : null}
                  </div>
                );
              })}
            </div>
            <SelectField label={t("control.path")} value={form.path} onChange={(v) => set({ path: v })} hint={t(`control.pathHints.${form.path}`)}
              options={Object.keys(catalog.data?.paths ?? { [form.path]: {} }).map((p) => ({ value: p, label: t(`control.paths.${p}`) }))} />
            <NumberField label={t("control.speed")} unit="m/s" value={form.speed} min={2} max={50} step={1} onChange={(v) => set({ speed: v })}
              hint={t("control.speedHint", { kmh: fmt(form.speed * 3.6, lang, 3) })} />
            <details className="expert" open={form.plant !== "werling_desm" || (form.actuator ?? "ideal") !== "ideal" || form.mu !== 1 || form.lateralOffset !== 0 || form.gust !== 0}>
              <summary><Icon name="settings" />{t("control.conditions")}</summary>
              <div className="stack">
                <SelectField label={t("control.plant")} value={form.plant} onChange={(v) => set({ plant: v })} tip={t("control.plantTip")}
                  options={(catalog.data?.plants ?? [form.plant]).map((p) => ({ value: p, label: t(`control.plants.${p}`) }))} />
                <SelectField label={t("control.actuator")} value={form.actuator ?? "ideal"} onChange={(v) => set({ actuator: v })} hint={t("control.actuatorHint")}
                  options={(["ideal", "realistic"] as const).map((a) => ({ value: a, label: t(`control.actuators.${a}`) }))} />
                <NumberField label={t("control.mu")} value={form.mu} min={0.05} max={1.5} step={0.05} onChange={(v) => set({ mu: v })} hint={t("control.muHint")} />
                <NumberField label={t("control.offset")} unit="m" value={form.lateralOffset} min={-3} max={3} step={0.1} onChange={(v) => set({ lateralOffset: v })} hint={t("control.offsetHint")} />
                <div className="grid grid--2-tight">
                  <NumberField label={t("control.gust")} unit="N" value={form.gust} min={-20000} max={20000} step={500} onChange={(v) => set({ gust: Number.isFinite(v) ? v : 0 })} />
                  <NumberField label={t("control.gustTime")} unit="s" value={form.gustTime} min={0} max={30} step={0.5} onChange={(v) => set({ gustTime: v })} />
                </div>
                <span className="field__hint">{t("control.gustHint")}</span>
                <button type="button" className="btn btn--ghost btn--sm" onClick={() => setForm(CONTROL_DEFAULT)}>{t("common:reset")}</button>
              </div>
            </details>
            <button type="submit" className="btn btn--primary btn--lg" disabled={run.loading || !form.controllers.length}>
              {run.loading ? <span className="spinner" /> : <Icon name="play" />}{t("control.run")}</button>
          </div>
        </form>
        <div className="stack" aria-live="polite">
          <ErrorAlert error={catalog.error ?? run.error} />
          {run.loading && !data ? <Skeleton height={320} /> : null}
          {!data && !run.loading ? <div className="card"><EmptyState art="simulation" title={t("control.empty.title")} text={t("control.empty.text")}
            action={<button type="button" className="btn btn--primary" onClick={() => void start()}><Icon name="play" />{t("control.run")}</button>} /></div> : null}
          {data ? <Results data={data} lang={lang} focus={data.runs.some((r) => r.name === focus) ? focus : data.runs[0].name} onFocus={setFocus} time={Math.min(time, data.duration)} onTime={setTime}
            docs={Object.fromEntries((catalog.data?.controllers ?? []).map((c) => [c.name, c.doc]))} /> : null}
        </div>
      </div>
    </div>
  );
}

function Results({ data, lang, focus, onFocus, time, onTime, docs }:
  { data: ControlResult; lang: string; focus: string; onFocus: (n: string) => void; time: number; onTime: (t: number) => void; docs: Record<string, Record<string, unknown>> }) {
  const { t } = useTranslation(["app", "common"]);
  const tt = (data.runs[0].signals.t ?? []) as number[];
  const lines = useMemo<Polyline[]>(() => [{ x: data.path.x, y: data.path.y, kind: "road" },
    ...data.runs.map((r, i) => ({ x: r.signals.x, y: r.signals.y, kind: "physics" as const, color: i }))], [data]);
  const best = Math.min(...data.runs.filter((r) => r.on_path).map((r) => r.kpis?.max_e_n ?? Infinity));
  const current = data.runs.find((r) => r.name === focus) ?? data.runs[0];
  const k = Math.max(0, Math.min(tt.length - 1, tt.findIndex((x) => x >= time) < 0 ? tt.length - 1 : tt.findIndex((x) => x >= time)));
  return (
    <>
      <div className="card"><div className="card__header"><div><h2>{t("control.result.title")}</h2>
        <p>{t("control.result.text", { plant: t(`control.plants.${data.plant}`), mu: fmt(data.mu, lang, 2), speed: fmt(data.speed * 3.6, lang, 3) })}</p></div></div>
        <div className="card__body table-wrap"><table className="table">
          <thead><tr><th>{t("control.controllers")}</th><th className="num">{t("control.kpi.max_e_n")}</th><th className="num">{t("control.kpi.rms_e_n")}</th><th className="num">{t("control.kpi.settled")}</th>
            <th className="num">{t("control.kpi.steer")}</th><th className="num">{t("control.kpi.steerRate")}</th><th className="num">{t("control.kpi.ay")}</th><th className="num">{t("control.kpi.time")}</th></tr></thead>
          <tbody>{data.runs.map((r, i) => (
            <tr key={r.name} onClick={() => onFocus(r.name)} style={{ cursor: "pointer", background: r.name === current.name ? "var(--me-surface-2)" : undefined }}>
              <td><span className="swatch" style={{ background: `var(--me-chart-${(i % 6) + 1})` }} /> {r.label}
                {!r.stable ? <span className="badge badge--danger">{t("control.unstable")}</span> : !r.on_path ? <span className="badge badge--danger">{t("learn.lost")}</span> : r.kpis?.max_e_n === best && data.runs.length > 1 ? <span className="badge badge--success">{t("control.best")}</span> : null}</td>
              <td className="num">{fmt(r.kpis?.max_e_n ?? null, lang, 3)} m</td><td className="num">{fmt(r.kpis?.rms_e_n ?? null, lang, 3)} m</td>
              <td className="num">{r.kpis?.settled_after === null || r.kpis === null ? t("control.notSettled") : `${fmt(r.kpis.settled_after, lang, 3)} s`}</td>
              <td className="num">{fmt(r.kpis?.max_steer_deg ?? null, lang, 3)}°</td><td className="num">{fmt(r.kpis?.max_steer_rate_deg_s ?? null, lang, 3)} °/s</td>
              <td className="num">{fmt(r.kpis?.max_ay ?? null, lang, 3)} m/s²</td><td className="num">{fmt(r.kpis?.compute_time_ms ?? null, lang, 2)} ms</td></tr>
          ))}</tbody></table>
          <p className="subtle">{t("control.kpi.note")}</p></div></div>
      <div className="card"><div className="card__body"><PathPlot height={220} ariaLabel={t("control.pathsPlot")} lines={lines} /></div></div>
      <Suspense fallback={<Skeleton height={220} />}>
        <div className="grid grid--2">
          {SERIES.map(([key, unit, label]) => (
            <div key={key} className="card"><div className="card__body"><div className="chart-title">{t(`control.series.${label}`)}</div>
              <Chart x={tt} xLabel="t [s]" yLabel={unit} height={190} ariaLabel={t(`control.series.${label}`)}
                series={data.runs.map((r, i) => ({ label: r.label, values: r.signals[key] ?? [], color: i }))} /></div></div>
          ))}
        </div>
      </Suspense>
      <Law run={current} runs={data.runs} onFocus={onFocus} k={k} tt={tt} time={time} onTime={onTime} duration={data.duration} lang={lang} doc={docs[current.name]} />
    </>
  );
}

function Law({ run, runs, onFocus, k, tt, time, onTime, duration, lang, doc }:
  { run: ControlRun; runs: ControlRun[]; onFocus: (n: string) => void; k: number; tt: number[]; time: number; onTime: (t: number) => void; duration: number; lang: string; doc?: Record<string, unknown> }) {
  const { t } = useTranslation(["app", "common", "domain"]);
  const law = LAWS[run.name];
  const sig = (key: string) => run.signals[key]?.[k] ?? null;
  return (
    <div className="card">
      <div className="card__header"><div><h2>{t("control.law.title")}</h2><p>{t("control.law.text")}</p></div>
        <select className="select" style={{ width: "auto" }} value={run.name} aria-label={t("control.controllers")} onChange={(e) => onFocus(e.target.value)}>
          {runs.map((r) => <option key={r.name} value={r.name}>{r.label}</option>)}</select></div>
      <div className="card__body stack">
        {law ? <Formula tex={law.tex} /> : null}
        <p>{t(`control.explain.${run.name}`)}</p>
        <div className="player__controls">
          <input type="range" className="player__scrub" min={0} max={duration} step={0.02} value={time} aria-label={t("common:player.time")} onChange={(e) => onTime(Number(e.target.value))} />
          <span className="player__readout mono">{fmt(tt[k] ?? 0, lang, 3)} s</span>
        </div>
        <div className="grid grid--2">
          <div className="table-wrap"><table className="table">
            <thead><tr><th>{t("control.law.state")}</th><th className="num">{t("simulate.kpiTable.value")}</th></tr></thead>
            <tbody>
              <tr><td>{t("control.series.e_n")}</td><td className="num mono">{fmt(sig("e_n"), lang, 4)} m</td></tr>
              <tr><td>{t("control.series.e_theta")}</td><td className="num mono">{fmt(sig("e_theta_deg"), lang, 4)}°</td></tr>
              <tr><td>{t("control.law.speed")}</td><td className="num mono">{fmt(sig("vx"), lang, 4)} m/s</td></tr>
              <tr><td>{t("control.law.command")}</td><td className="num mono">{fmt(sig("delta_cmd_deg"), lang, 4)}°</td></tr>
              <tr><td>{t("control.law.actual")}</td><td className="num mono">{fmt(sig("delta_deg"), lang, 4)}°</td></tr>
            </tbody></table></div>
          <div className="table-wrap">{law?.terms.length ? <table className="table">
            <thead><tr><th>{t("control.law.term")}</th><th className="num">{t("simulate.kpiTable.value")}</th></tr></thead>
            <tbody>{law.terms.filter(([key]) => run.terms[key]).map(([key, tex, unit]) => (
              <tr key={key}><td><Formula tex={tex} display={false} /></td>
                <td className="num mono">{fmt(conv(run.terms[key]?.[k], unit), lang, 4)}{unit === "deg" ? "°" : unit === "m" ? " m" : ""}</td></tr>
            ))}</tbody></table> : <p className="subtle">{t("control.law.noTerms")}</p>}</div>
        </div>
        {typeof doc?.theory === "string" && doc.theory ? <details className="expert"><summary><Icon name="book" />{t("control.law.library")}</summary>
          <div className="stack"><p>{t(`domain:componentDoc.tracking_controller.${run.name}.summary`, { defaultValue: String(doc.summary ?? "") })}</p>
            <p>{t(`domain:componentDoc.tracking_controller.${run.name}.purpose`, { defaultValue: String(doc.purpose ?? "") })}</p>
            {(["theory", "expert"] as const).map((key) => (typeof doc[key] === "string" && doc[key] ? <RichText key={key} text={doc[key] as string} /> : null))}
            {lang.startsWith("de") ? null : <p className="subtle">{t("architecture.doc.german")}</p>}
            {Array.isArray(doc.limitations) && doc.limitations.length ? <RichText text={(doc.limitations as string[]).map((x) => `- ${x}`).join("\n")} /> : null}</div></details> : null}
      </div>
    </div>
  );
}
