import { lazy, Suspense, useMemo, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { EmptyState, Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { NumberField, SelectField } from "../components/Field";
import { Formula } from "../components/Formula";
import { Icon } from "../components/Icon";
import { PageHeader } from "../components/PageHeader";
import { PathPlot, type Box, type Polyline } from "../components/PathPlot";
import { InfoTip } from "../components/Tooltip";
import type { ExplainResponse, ExplainStep, ObjectSpec, PlanRequest } from "../lib/api";
import { fmt, toDeg } from "../lib/format";
import { useClient, useMutation, usePersistentState } from "../lib/hooks";

const Chart = lazy(() => import("../components/Chart"));

type Preset = "laneChange" | "obstacle" | "stopLine" | "slow" | "curve";
interface Setup { preset: Preset; speed: number; targetSpeed: number; offset: number; stopAt: number; obstacleX: number; obstacleV: number; curvature: number; config: string }
const PRESETS: Record<Preset, Partial<Setup>> = {
  laneChange: { speed: 20, targetSpeed: 20, offset: 3.5, stopAt: 0, obstacleX: 0, curvature: 0 },
  obstacle: { speed: 15, targetSpeed: 15, offset: 0, stopAt: 0, obstacleX: 35, obstacleV: 3, curvature: 0 },
  stopLine: { speed: 10, targetSpeed: 10, offset: 0, stopAt: 45, obstacleX: 0, curvature: 0 },
  slow: { speed: 1, targetSpeed: 2, offset: 1.0, stopAt: 0, obstacleX: 0, curvature: 0 },
  curve: { speed: 18, targetSpeed: 18, offset: 0, stopAt: 0, obstacleX: 0, curvature: 1 / 120 },
};
const DEFAULT: Setup = { preset: "laneChange", speed: 20, targetSpeed: 20, offset: 3.5, stopAt: 0, obstacleX: 0, obstacleV: 3, curvature: 0, config: "default" };
const STEP_IDS = ["start_state", "lateral", "longitudinal", "selection", "transformation", "constraints", "vehicle_physics"] as const;

function toRequest(s: Setup): PlanRequest {
  const obstacles: ObjectSpec[] = s.obstacleX > 0 ? [{ id: 1, x: s.obstacleX, y: 0, v: s.obstacleV, length: 4.5, width: 1.8 }] : [];
  return {
    config: s.config, ego: { vx: s.speed }, target_speed: s.targetSpeed, target_offset: s.offset, stop_at: s.stopAt > 0 ? s.stopAt : null,
    obstacles, d_min: -5.25, d_max: 5.25,
    road: s.curvature ? [{ kind: "straight", length: 40 }, { kind: "arc", length: 300, curvature: s.curvature }] : [{ kind: "straight", length: 400 }],
  };
}

export default function Inspector() {
  const { t, i18n } = useTranslation(["inspector", "app", "common"]);
  const client = useClient();
  const [setup, setSetup] = usePersistentState<Setup>("me.inspector.setup", DEFAULT);
  const [step, setStep] = useState<(typeof STEP_IDS)[number]>("start_state");
  const explain = useMutation((body: PlanRequest) => client.explain(body));
  const compute = (s: Setup) => { setSetup(s); void explain.run(toRequest(s)); };
  const data = explain.data;
  const current = data?.steps.find((x) => x.id === step);

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("title")} description={t("subtitle")} />
      <div className="card">
        <div className="card__body stack">
          <div className="row" role="group" aria-label={t("presets.label")}>
            {(Object.keys(PRESETS) as Preset[]).map((p) => (
              <button key={p} type="button" className={`btn btn--sm ${setup.preset === p ? "btn--primary" : "btn--secondary"}`}
                aria-pressed={setup.preset === p} onClick={() => compute({ ...setup, ...PRESETS[p], preset: p })}>{t(`presets.${p}`)}</button>
            ))}
          </div>
          <details className="expert">
            <summary><Icon name="settings" />{t("common:expertSettings")}</summary>
            <form className="grid grid--4" onSubmit={(e) => { e.preventDefault(); compute(setup); }}>
              <NumberField label={t("setup.speed")} unit="m/s" value={setup.speed} min={0} max={60} onChange={(v) => setSetup({ ...setup, speed: v })} />
              <NumberField label={t("setup.targetSpeed")} unit="m/s" value={setup.targetSpeed} min={0} max={60} onChange={(v) => setSetup({ ...setup, targetSpeed: v })} />
              <NumberField label={t("setup.offset")} unit="m" value={setup.offset} min={-7} max={7} onChange={(v) => setSetup({ ...setup, offset: v })} tip={t("setup.offsetTip")} />
              <NumberField label={t("setup.stopAt")} unit="m" value={setup.stopAt} min={0} onChange={(v) => setSetup({ ...setup, stopAt: v })} hint={t("setup.zeroOff")} />
              <NumberField label={t("setup.obstacleX")} unit="m" value={setup.obstacleX} min={0} onChange={(v) => setSetup({ ...setup, obstacleX: v })} hint={t("setup.zeroOff")} />
              <NumberField label={t("setup.obstacleV")} unit="m/s" value={setup.obstacleV} min={0} onChange={(v) => setSetup({ ...setup, obstacleV: v })} />
              <NumberField label={t("setup.curvature")} unit="1/m" value={setup.curvature} step={0.001} onChange={(v) => setSetup({ ...setup, curvature: v })} />
              <SelectField label={t("setup.config")} value={setup.config} onChange={(v) => setSetup({ ...setup, config: v })}
                options={["default", "comfort", "sporty"].map((c) => ({ value: c, label: t(`configs.${c}`) }))} />
              <div className="field" style={{ justifyContent: "end" }}><button type="submit" className="btn btn--primary">{t("compute")}</button></div>
            </form>
          </details>
        </div>
      </div>

      <ErrorAlert error={explain.error} />
      {explain.loading && !data ? <Skeleton height={420} /> : null}
      {!data && !explain.loading && !explain.error ? (
        <div className="card"><EmptyState art="scenario" title={t("empty.title")} text={t("empty.text")}
          action={<button type="button" className="btn btn--primary" onClick={() => compute(setup)}><Icon name="sigma" />{t("empty.action")}</button>} /></div>
      ) : null}

      {data ? (
        <>
          <TopView data={data} />
          <div className="split split--nav">
            <nav className="card" aria-label={t("steps.label")}>
              <div className="card__body steps">
                {STEP_IDS.map((id, i) => (
                  <button key={id} type="button" className="step-link" aria-current={step === id ? "step" : undefined} onClick={() => setStep(id)}>
                    <span className="step-link__num">{i + 1}</span><span>{t(`steps.${id}.title`)}</span>
                  </button>
                ))}
              </div>
            </nav>
            {current ? <StepView step={current} data={data} lang={i18n.language} /> : null}
          </div>
        </>
      ) : null}
    </div>
  );
}

function TopView({ data }: { data: ExplainResponse }) {
  const { t } = useTranslation("inspector");
  const lines: Polyline[] = useMemo(() => {
    const kind = (status: number): Polyline["kind"] => (status === 0 ? "candidate" : status === 2 ? "collision" : "rejected");
    return [
      { x: data.road.left_x, y: data.road.left_y, kind: "bound" }, { x: data.road.right_x, y: data.road.right_y, kind: "bound" },
      { x: data.road.x, y: data.road.y, kind: "road" }, { x: data.road.target_x, y: data.road.target_y, kind: "target" },
      ...data.candidates.filter((c) => !c.selected).map((c) => ({ x: c.x, y: c.y, kind: kind(c.status) })),
      { x: data.series.x, y: data.series.y, kind: "selected" },
    ];
  }, [data]);
  const boxes: Box[] = [
    { x: data.series.x[0] ?? 0, y: data.series.y[0] ?? 0, psi: data.series.theta[0] ?? 0, length: 4.8, width: 1.85, kind: "ego" },
    ...data.obstacles.map((o) => ({ x: o.x, y: o.y, psi: o.psi ?? 0, length: o.length ?? 4.5, width: o.width ?? 1.8, kind: "object" as const })),
  ];
  const xs = data.series.x.filter((v): v is number => v !== null);
  return (
    <div className="card">
      <div className="card__header">
        <div><h2>{t("topView.title")}</h2><p>{t("topView.legend")}</p></div>
        <span className="subtle">{t("topView.computeTime", { ms: (data.compute_time * 1000).toFixed(1) })}</span>
      </div>
      <div className="card__body">
        <PathPlot lines={lines} boxes={boxes} height={260} ariaLabel={t("topView.title")}
          focus={xs.length ? { xmin: Math.min(...xs) - 10, xmax: Math.max(...xs) + 10 } : undefined} />
      </div>
    </div>
  );
}

function Quantity({ name, value, unit, lang }: { name: ReactNode; value: unknown; unit?: string; lang: string }) {
  const shown = typeof value === "number" ? fmt(value, lang, 4) : typeof value === "boolean" ? String(value) : String(value ?? "–");
  return <tr><td>{name}</td><td className="num mono">{shown}</td><td className="subtle">{unit ?? ""}</td></tr>;
}

function StepView({ step, data, lang }: { step: ExplainStep; data: ExplainResponse; lang: string }) {
  const { t } = useTranslation("inspector");
  const q = step.quantities as Record<string, unknown>;
  const s = data.series;
  return (
    <article className="card" aria-labelledby="step-title">
      <div className="card__header"><div><h2 id="step-title">{t(`steps.${step.id}.title`)}</h2><p>{t(`steps.${step.id}.source`)}</p></div></div>
      <div className="card__body stack">
        <p style={{ maxWidth: "80ch" }}>{t(`steps.${step.id}.text`)}</p>
        <section aria-label={t("formulas")} className="stack stack--sm">
          {step.formulas.map((f, i) => <Formula key={i} tex={f} />)}
        </section>
        <StepDetails step={step} q={q} lang={lang} />
        <Suspense fallback={<Skeleton height={220} />}>
          {step.id === "lateral" ? (
            <Chart x={s.t} xLabel="t [s]" yLabel="m" ariaLabel={t("charts.lateral")}
              series={[{ label: "d(t)", values: s.d }, { label: "ḋ(t) [m/s]", values: s.d_d, color: 1, dash: true }, { label: "d̈(t) [m/s²]", values: s.d_dd, color: 2, dash: true }]} />
          ) : null}
          {step.id === "longitudinal" ? (
            <Chart x={s.t} xLabel="t [s]" yLabel="m/s, m/s², m/s³" ariaLabel={t("charts.longitudinal")}
              series={[{ label: "ṡ(t)", values: s.s_d }, { label: "s̈(t)", values: s.s_dd, color: 1 }, { label: "s⃛(t)", values: s.s_ddd, color: 2, dash: true }]} />
          ) : null}
          {step.id === "transformation" ? (
            <Chart x={s.t} xLabel="t [s]" yLabel="1/m" ariaLabel={t("charts.curvature")} series={[{ label: "κ(t)", values: s.kappa, color: 3 }]} />
          ) : null}
          {step.id === "constraints" || step.id === "vehicle_physics" ? (
            <Chart x={s.t} xLabel="t [s]" yLabel="m/s²" ariaLabel={t("charts.accelerations")}
              series={[{ label: "a_y = v²κ", values: s.a_lat }, { label: "a_x", values: s.a, color: 2 }]} />
          ) : null}
          {step.id === "selection" ? <FrenetCandidates data={data} /> : null}
        </Suspense>
      </div>
    </article>
  );
}

function StepDetails({ step, q, lang }: { step: ExplainStep; q: Record<string, unknown>; lang: string }) {
  const { t } = useTranslation("inspector");
  const table = (rows: [ReactNode, unknown, string?][]) => (
    <div className="table-wrap"><table className="table"><thead><tr><th>{t("quantity")}</th><th className="num">{t("value")}</th><th>{t("unit")}</th></tr></thead>
      <tbody>{rows.map(([n, v, u], i) => <Quantity key={i} name={n} value={v} unit={u} lang={lang} />)}</tbody></table></div>
  );
  const verified = (err: unknown) => (
    <div className="alert alert--info"><Icon name="check" />
      <span>{t("verified", { err: typeof err === "number" ? err.toExponential(1) : "–" })}</span></div>
  );
  switch (step.id) {
    case "start_state":
      return table([["s₀", q.s, "m"], ["ṡ₀", q.s_d, "m/s"], ["s̈₀", q.s_dd, "m/s²"], ["d₀", q.d, "m"], ["ḋ₀", q.d_d, "m/s"], ["d̈₀", q.d_dd, "m/s²"],
        [t("q.referencePoint"), t(`refPoints.${String(q.reference_point)}`, { defaultValue: String(q.reference_point) })],
        [t("q.lateralMode"), t(`latModes.${String(q.lateral_mode)}`)], [t("q.source"), String(q.source)]]);
    case "lateral":
      return <>{verified(q.verification_max_abs_error)}{table([[t("q.mode"), t(`latModes.${String(q.mode)}`)], ["τ / S", q.tau, q.mode === "arc" ? "m" : "s"],
        ["δ", q.delta, "m"], ["d_ref + δ", q.d_end, "m"], ["J_d", q.jerk_integral], ["C_d", q.cost],
        ...((q.coefficients as number[]) ?? []).map((c, i) => [`c${i}`, c] as [ReactNode, unknown])])}</>;
    case "longitudinal":
      return <>{verified(q.verification_max_abs_error)}{table([[t("q.mode"), t(`lonModes.${String(q.mode)}`, { defaultValue: String(q.mode) })], ["τ", q.tau, "s"],
        [t("q.offset"), q.offset], ["J_s", q.jerk_integral], ["C_s", q.cost], ...((q.coefficients as number[]) ?? []).map((c, i) => [`c${i}`, c] as [ReactNode, unknown])])}</>;
    case "selection": {
      const counts = q.sample_status_counts as Record<string, number>;
      const viol = q.constraint_violations as Record<string, number>;
      const terms = q.cost_terms_planner as Record<string, number>;
      return <>
        {table([[t("q.nCandidates"), q.n_candidates], [t("q.nChecked"), q.n_checked], [t("q.costTotal"), q.cost_total], [t("q.costPlanner"), q.cost_planner],
          [t("q.fallback"), q.fallback ? t("yes") : t("no")]])}
        <h3>{t("costBreakdown")}</h3>
        <CostBars terms={terms} lang={lang} />
        <div className="row">{Object.entries(counts).map(([k, v]) => <span key={k} className="badge">{t(`status.${k}`)}: {v}</span>)}</div>
        {Object.keys(viol).length ? <div className="row">{Object.entries(viol).map(([k, v]) => <span key={k} className="badge badge--warning">{t(`constraints.${k}`, { defaultValue: k })}: {v}</span>)}</div> : null}
      </>;
    }
    case "transformation": {
      const samples = q.samples as Record<string, number>[];
      return <div className="table-wrap"><table className="table"><thead><tr>{["t", "s", "d", "d'", "κ_r", "x", "y", "θ [°]", "κ", "v"].map((h) => <th key={h} className="num">{h}</th>)}</tr></thead>
        <tbody>{samples.map((r, i) => <tr key={i}>{[r.t, r.s, r.d, r.d_p, r.kappa_r, r.x, r.y, toDeg(r.theta), r.kappa, r.v].map((v, j) => <td key={j} className="num mono">{fmt(v, lang, 4)}</td>)}</tr>)}</tbody></table></div>;
    }
    case "constraints": {
      const checks = q.checks as { name: string; max: number; limit: number; unit: string; ok: boolean; utilization: number | null }[];
      return <div className="table-wrap"><table className="table"><thead><tr><th>{t("constraint")}</th><th className="num">{t("max")}</th><th className="num">{t("limit")}</th><th>{t("utilization")}</th></tr></thead>
        <tbody>{checks.map((c) => (
          <tr key={c.name}><td>{t(`checks.${c.name}`)}</td><td className="num mono">{fmt(c.max, lang)} {c.unit}</td><td className="num mono">{fmt(c.limit, lang)}</td>
            <td style={{ minWidth: 140 }}><div className="progress" role="progressbar" aria-valuenow={Math.round((c.utilization ?? 0) * 100)} aria-valuemin={0} aria-valuemax={100}>
              <span style={{ width: `${Math.min((c.utilization ?? 0) * 100, 100)}%`, background: c.ok ? undefined : "var(--me-danger)" }} /></div></td></tr>
        ))}</tbody></table></div>;
    }
    case "vehicle_physics":
      return table([["v", q.v, "m/s"], ["κ", q.kappa, "1/m"], ["a_y", q.a_y, "m/s²"], ["F_y,v", q.F_yf, "N"], ["F_y,h", q.F_yr, "N"],
        ["α_v", toDeg(q.alpha_f as number), "°"], ["α_h", toDeg(q.alpha_r as number), "°"], ["δ", toDeg(q.delta as number), "°"], ["β", toDeg(q.beta as number), "°"],
        [<span key="eg">EG <InfoTip text={t("egTip")} /></span>, q.understeer_gradient, "rad/(m/s²)"], ["C_v", q.C_f, "N/rad"], ["C_h", q.C_r, "N/rad"],
        [t("q.friction"), q.friction_utilization, "–"]]);
    default:
      return null;
  }
}

function CostBars({ terms, lang }: { terms: Record<string, number>; lang: string }) {
  const { t } = useTranslation("inspector");
  const rows = Object.entries(terms).filter(([k]) => k !== "gesamt" && k !== "konsistent");
  const max = Math.max(...rows.map(([, v]) => v), 1e-9);
  return (
    <div className="stack stack--sm">
      {rows.map(([k, v]) => (
        <div key={k} className="grid" style={{ gridTemplateColumns: "minmax(140px, 220px) 1fr 80px", alignItems: "center", gap: "var(--me-space-3)" }}>
          <span className="subtle">{t(`costTerms.${k.replace(".", "_")}`, { defaultValue: k })}</span>
          <div className="progress"><span style={{ width: `${(v / max) * 100}%` }} /></div>
          <span className="num mono" style={{ textAlign: "right" }}>{fmt(v, lang)}</span>
        </div>
      ))}
    </div>
  );
}

function FrenetCandidates({ data }: { data: ExplainResponse }) {
  const { t } = useTranslation("inspector");
  const lines: Polyline[] = data.candidates.map((c) => ({ x: c.s, y: c.d, kind: c.selected ? "selected" : c.status === 0 ? "candidate" : c.status === 2 ? "collision" : "rejected" }));
  const sel = data.candidates.find((c) => c.selected);
  if (sel) lines.push({ x: sel.s, y: sel.d, kind: "selected" });
  return <div><div className="chart-title">{t("charts.frenet")}</div><PathPlot lines={lines} height={220} ariaLabel={t("charts.frenet")} stretch /></div>;
}
