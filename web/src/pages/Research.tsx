// Research: batch experiments on the AD stack - compare components, sweep a parameter, Monte Carlo.
import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { EmptyState, Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { NumberField, SelectField, TextField } from "../components/Field";
import { Icon } from "../components/Icon";
import { PageHeader } from "../components/PageHeader";
import type { ExperimentRequest, ExperimentView } from "../lib/api";
import { adScenarioLabel } from "../lib/domain";
import { fmt } from "../lib/format";
import { useClient, usePersistentState, useQuery } from "../lib/hooks";
import { stackSpecs, useStack } from "../lib/stack";

const Chart = lazy(() => import("../components/Chart").then((m) => ({ default: m.Chart })));
const KINDS = ["compare", "sweep", "monte_carlo"] as const;
const COLUMNS = ["collision", "min_ttc", "min_distance", "max_ay", "max_jerk", "rms_e_n", "max_e_n"];

interface Form { kind: (typeof KINDS)[number]; scenario: string; duration: number; layer: string; variants: string[]; path: string; values: string; low: number; high: number; n: number }
const DEFAULT: Form = { kind: "compare", scenario: "autobahn_ueberholen", duration: 10, layer: "controller", variants: [], path: "stack.planner.params.cost.k_lat",
  values: "0.5, 1, 2", low: 0.5, high: 2, n: 8 };

export default function Research() {
  const { t, i18n } = useTranslation(["app", "common", "domain"]);
  const client = useClient();
  const lang = i18n.language;
  const catalog = useQuery((s) => client.workbenchCatalog(s), [client]);
  const [form, setForm] = usePersistentState<Form>("me.research.form", DEFAULT);
  const set = (patch: Partial<Form>) => setForm({ ...form, ...patch });
  const [stack] = useStack();
  const [exp, setExp] = useState<ExperimentView | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [metric, setMetric] = useState("max_ay");
  const layer = catalog.data?.layers.find((l) => l.layer === form.layer);
  const active = exp ? ["queued", "running"].includes(exp.state) : false;

  useEffect(() => {
    if (!exp || !active) return;
    const timer = window.setInterval(() => { client.experiment(exp.id).then(setExp, () => undefined); }, 700);
    return () => window.clearInterval(timer);
  }, [exp?.id, active, client]); // eslint-disable-line

  const start = async () => {
    const { specs, invalid } = stackSpecs(stack);
    if (invalid) { setError(new Error(t("workbench.invalidParams", { layer: invalid }))); return; }
    const body: ExperimentRequest = { kind: form.kind, base: { scenario: form.scenario, duration: Number.isFinite(form.duration) ? form.duration : null, stack: specs } };
    if (form.kind === "compare") {
      body.layer = form.layer;
      body.variants = Object.fromEntries((form.variants.length ? form.variants : (layer?.components ?? []).map((c) => c.spec)).map((spec) => [spec.split("/")[1], { component: spec }]));
    } else if (form.kind === "sweep") {
      body.grid = { [form.path]: form.values.split(/[,;\s]+/).filter(Boolean).map((v) => (Number.isFinite(Number(v)) ? Number(v) : v)) };
    } else {
      body.distributions = { [form.path]: [form.low, form.high] };
      body.n = form.n;
    }
    try { setError(null); setExp(await client.startExperiment(body)); } catch (err) { setError(err); }
  };

  const records = exp?.records ?? [];
  const keys = useMemo(() => Array.from(new Set(records.flatMap((r) => Object.keys(r.kpis)))), [records]);
  const columns = COLUMNS.filter((c) => keys.includes(c));
  const label = (key: string) => t(`domain:adKpi.${key}`, { defaultValue: catalog.data?.kpi_info[key]?.[0] ?? key });
  const chart = useMemo(() => ({ x: records.map((_, i) => i + 1), y: records.map((r) => r.kpis[metric] ?? null) }), [records, metric]);

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("research.title")} description={t("research.subtitle")} />
      <div className="split">
        <form className="card" onSubmit={(e) => { e.preventDefault(); void start(); }}>
          <div className="card__header"><h2>{t("research.setup")}</h2></div>
          <div className="card__body stack">
            <SelectField label={t("research.kindLabel")} value={form.kind} onChange={(v) => set({ kind: v })} options={KINDS.map((k) => ({ value: k, label: t(`research.kind.${k}`) }))}
              hint={t(`research.kindHint.${form.kind}`)} />
            <SelectField label={t("workbench.scenario")} value={form.scenario} onChange={(v) => set({ scenario: v })}
              options={(catalog.data?.scenarios ?? [{ name: form.scenario, label: form.scenario }]).map((s) => ({ value: s.name, label: adScenarioLabel(t, s) }))} />
            <NumberField label={t("workbench.duration")} unit="s" value={form.duration} min={1} max={120} onChange={(v) => set({ duration: v })} />
            {form.kind === "compare" ? (
              <>
                <SelectField label={t("research.layer")} value={form.layer} onChange={(v) => set({ layer: v, variants: [] })}
                  options={(catalog.data?.layers ?? []).filter((l) => l.components.length > 1).map((l) => ({ value: l.layer, label: t(`workbench.layers.${l.layer}`) }))} />
                <fieldset className="field"><legend className="field__label">{t("research.variants")}</legend>
                  {(layer?.components ?? []).map((c) => {
                    const on = form.variants.length === 0 || form.variants.includes(c.spec);
                    return <label key={c.spec} className="check"><input type="checkbox" checked={on} onChange={() => {
                      const all = (layer?.components ?? []).map((x) => x.spec);
                      const cur = form.variants.length ? form.variants : all;
                      set({ variants: on ? cur.filter((x) => x !== c.spec) : [...cur, c.spec] });
                    }} /><span className="mono">{c.spec.split("/")[1]}</span></label>;
                  })}
                </fieldset>
              </>
            ) : (
              <TextField label={t("research.path")} value={form.path} onChange={(v) => set({ path: v })} hint={t("research.pathHint")} />
            )}
            {form.kind === "sweep" ? <TextField label={t("research.values")} value={form.values} onChange={(v) => set({ values: v })} hint={t("research.valuesHint")} /> : null}
            {form.kind === "monte_carlo" ? (
              <div className="grid grid--2-tight">
                <NumberField label={t("research.low")} value={form.low} onChange={(v) => set({ low: v })} />
                <NumberField label={t("research.high")} value={form.high} onChange={(v) => set({ high: v })} />
                <NumberField label={t("research.samples")} value={form.n} min={1} max={40} step={1} onChange={(v) => set({ n: v })} />
              </div>
            ) : null}
            <p className="subtle">{t("research.stackNote", { n: Object.keys(stack).length })}</p>
            {active ? <button type="button" className="btn btn--secondary btn--lg" onClick={() => exp && void client.cancelExperiment(exp.id)}><Icon name="stop" />{t("common:cancel")}</button>
              : <button type="submit" className="btn btn--primary btn--lg" disabled={!catalog.data}><Icon name="play" />{t("research.run")}</button>}
          </div>
        </form>
        <div className="stack" aria-live="polite">
          <ErrorAlert error={catalog.error ?? error} />
          {!exp ? <div className="card"><EmptyState art="results" title={t("research.empty.title")} text={t("research.empty.text")} /></div> : null}
          {exp ? (
            <>
              <div className="card"><div className="card__body stack">
                <div className="row row--between"><h2>{exp.name}</h2><span className="badge badge--info">{t(`models.jobStates.${exp.state}`)}</span></div>
                <div className="progress" role="progressbar" aria-valuenow={Math.round(exp.progress * 100)} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${exp.progress * 100}%` }} /></div>
                {exp.error ? <div className="alert alert--danger">{exp.error}</div> : null}
              </div></div>
              {records.length ? (
                <div className="card"><div className="card__body table-wrap"><table className="table">
                  <thead><tr><th>{t("research.variant")}</th>{columns.map((c) => <th key={c} className="num">{label(c)}</th>)}</tr></thead>
                  <tbody>{records.map((r, i) => (
                    <tr key={i}><td className="mono">{r.label}{r.ok ? "" : <span className="badge badge--danger" title={r.error ?? ""}>✕</span>}</td>
                      {columns.map((c) => <td key={c} className="num">{fmt(r.kpis[c], lang, 3)}</td>)}</tr>
                  ))}</tbody></table>
                  {records.some((r) => !r.ok) ? <p className="subtle mono">{records.find((r) => !r.ok)?.error}</p> : null}
                </div></div>
              ) : null}
              {records.length > 1 && keys.length ? (
                <div className="card"><div className="card__header"><h2>{t("research.chart")}</h2>
                  <select className="select select--sm" value={metric} aria-label={t("research.metric")} onChange={(e) => setMetric(e.target.value)}>
                    {keys.map((k) => <option key={k} value={k}>{label(k)}</option>)}</select></div>
                  <div className="card__body"><Suspense fallback={<Skeleton height={220} />}>
                    <Chart x={chart.x} xLabel={t("research.runIndex")} yLabel={catalog.data?.kpi_info[metric]?.[1] ?? ""} height={220} ariaLabel={label(metric)}
                      series={[{ label: label(metric), values: chart.y }]} /></Suspense>
                    <p className="subtle">{records.map((r, i) => `${i + 1}: ${r.label}`).join(" · ")}</p></div></div>
              ) : null}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
