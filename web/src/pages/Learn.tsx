// Guided lessons: each one states a question, runs a prepared experiment with the real controllers and
// planner, shows the numbers that answer it, and links to the tool where the learner can go on.
import { lazy, Suspense, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { Icon } from "../components/Icon";
import { PageHeader } from "../components/PageHeader";
import type { ControlRunRequest, ExperimentRequest, LayerSpec, RunRequest } from "../lib/api";
import { fmt } from "../lib/format";
import { useClient, usePersistentState } from "../lib/hooks";
import { applyConditions, type Conditions } from "../lib/stack";
import { CONTROL_DEFAULT, CONTROL_FORM_KEY, type ControlForm } from "./ControlLab";

const Chart = lazy(() => import("../components/Chart"));

type Action =
  | { kind: "control"; requests: { label: string; body: ControlRunRequest }[]; open: Partial<ControlForm> }
  | { kind: "experiment"; body: ExperimentRequest; kpis: string[]; open: string }
  | { kind: "runs"; runs: { label: string; scenario: string; conditions: Conditions }[]; kpis: string[]; open: string };
interface Lesson { id: string; topic: "control" | "planning" | "system"; action: Action }
interface Row { label: string; values: (number | null)[]; flag?: "ok" | "fail" }
interface Outcome { columns: string[]; units: string[]; rows: Row[]; chart?: { x: number[]; series: { label: string; values: (number | null)[] }[] } }

const c = (name: string, params?: Record<string, unknown>, label?: string) => ({ name, params, label: label ?? name });
const NAMES = ["pure_pursuit", "stanley", "lqr", "werling_bilevel"];
const LESSONS: Lesson[] = [
  { id: "lookahead", topic: "control", action: { kind: "control", open: { controllers: ["pure_pursuit"], path: "s_curve", speed: 15 },
    requests: [{ label: "", body: { path: "s_curve", speed: 15, controllers: [0.4, 0.8, 1.5].map((g) => c("pure_pursuit", { lookahead_gain: g }, `k = ${g} s`)) } }] } },
  { id: "feedforward", topic: "control", action: { kind: "control", open: { controllers: ["stanley"], path: "curve_entry", speed: 15 },
    requests: [{ label: "", body: { path: "curve_entry", speed: 15, controllers: [c("stanley", { feedforward: true }, "on"), c("stanley", { feedforward: false }, "off")] } }] } },
  { id: "disturbance", topic: "control", action: { kind: "control", open: { controllers: NAMES, path: "straight", speed: 25, gust: 4000, gustTime: 2 },
    requests: [{ label: "", body: { path: "straight", speed: 25, disturbance: { t: 2, duration: 0.5, fy: 4000 }, controllers: NAMES.map((n) => c(n)) } }] } },
  { id: "model", topic: "control", action: { kind: "control", open: { controllers: ["lqr", "werling_bilevel"], path: "double_lane_change", speed: 25, plant: "double_track" },
    requests: ["werling_desm", "double_track"].map((plant) => ({ label: plant, body: { path: "double_lane_change", speed: 25, plant, controllers: [c("lqr"), c("werling_bilevel")] } })) } },
  { id: "actuator", topic: "control", action: { kind: "control", open: { controllers: ["stanley", "lqr"], path: "double_lane_change", speed: 25, actuator: "realistic" },
    requests: (["ideal", "realistic"] as const).map((actuator) => ({ label: actuator, body: { path: "double_lane_change", speed: 25, actuator, controllers: [c("stanley"), c("lqr")] } })) } },
  { id: "friction", topic: "control", action: { kind: "control", open: { controllers: ["werling_bilevel"], path: "curve_entry", speed: 18, plant: "double_track", mu: 0.5 },
    requests: [1.0, 0.5, 0.3].map((mu) => ({ label: `μ = ${mu}`, body: { path: "curve_entry", speed: 18, plant: "double_track", mu, controllers: [c("werling_bilevel")] } })) } },
  { id: "jerk", topic: "planning", action: { kind: "experiment", open: "/app/research", kpis: ["max_ay", "rms_jerk_lat", "max_jerk", "mean_speed"],
    body: { kind: "sweep", base: { scenario: "autobahn_ueberholen", duration: 14 }, grid: { "stack.planner.params.cost.jerk.k_lat": [0.05, 1, 20] } } } },
  { id: "stack", topic: "system", action: { kind: "experiment", open: "/app/research", kpis: ["max_e_n", "max_ay", "max_jerk", "mission_passed"],
    body: { kind: "compare", base: { scenario: "kreisverkehr" }, layer: "controller",
      variants: Object.fromEntries(["werling_bilevel", "mpc", "pure_pursuit", "stanley", "lqr"].map((n) => [n, { component: `tracking_controller/${n}` } as LayerSpec])) } } },
  { id: "conditions", topic: "system", action: { kind: "runs", open: "/app/workbench", kpis: ["max_e_n", "max_ay", "max_jerk", "min_distance", "mission_passed"],
    runs: (["ideal", "realistic", "wet"] as const).map((conditions) => ({ label: conditions, scenario: "notausweichen_hindernis", conditions })) } },
];
const UNITS: Record<string, string> = { max_e_n: "m", rms_e_n: "m", max_ay: "m/s²", max_jerk: "m/s³", rms_jerk_lat: "m/s³", mean_speed: "m/s", min_distance: "m", mission_passed: "", steer_rate: "°/s" };
const sleep = (ms: number) => new Promise((r) => window.setTimeout(r, ms));

export default function Learn() {
  const { t, i18n } = useTranslation(["app", "common", "domain"]);
  const lang = i18n.language;
  const [done, setDone] = usePersistentState<string[]>("me.learn.done", []);
  const topics = ["control", "planning", "system"] as const;
  return (
    <div className="stack stack--lg">
      <PageHeader title={t("learn.title")} description={t("learn.subtitle")} />
      <div className="row"><span className="badge badge--info">{t("learn.progress", { done: done.filter((d) => LESSONS.some((l) => l.id === d)).length, n: LESSONS.length })}</span>
        <span className="subtle">{t("learn.note")}</span></div>
      {topics.map((topic) => (
        <section key={topic} className="stack" aria-labelledby={`topic-${topic}`}>
          <h2 id={`topic-${topic}`}>{t(`learn.topics.${topic}`)}</h2>
          {LESSONS.filter((l) => l.topic === topic).map((l) => (
            <LessonCard key={l.id} lesson={l} lang={lang} done={done.includes(l.id)}
              onDone={(v) => setDone(v ? [...done.filter((d) => d !== l.id), l.id] : done.filter((d) => d !== l.id))} />
          ))}
        </section>
      ))}
    </div>
  );
}

function LessonCard({ lesson, lang, done, onDone }: { lesson: Lesson; lang: string; done: boolean; onDone: (v: boolean) => void }) {
  const { t } = useTranslation(["app", "common", "domain"]);
  const client = useClient();
  const navigate = useNavigate();
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [answer, setAnswer] = useState(false);
  const key = `learn.lessons.${lesson.id}`;
  const label = (raw: string) => t(`learn.labels.${raw}`, { defaultValue: t(`control.names.${raw}`, { defaultValue: raw }) });
  const kpiName = (k: string) => t(`learn.kpis.${k}`, { defaultValue: t(`domain:adKpi.${k}`, { defaultValue: k }) });

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      const a = lesson.action;
      if (a.kind === "control") {
        const rows: Row[] = [], series: { label: string; values: (number | null)[] }[] = [];
        let x: number[] = [];
        for (const req of a.requests) {
          const res = await client.controlRun(req.body);
          x = (res.runs[0].signals.t ?? []) as number[];
          for (const r of res.runs) {
            const name = [req.label ? label(req.label) : "", a.requests.length > 1 || res.runs.some((o) => o.name !== r.name) ? label(r.name) : "", r.label !== r.name ? label(r.label) : ""].filter(Boolean).join(" · ");
            rows.push({ label: name, values: [r.kpis?.max_e_n ?? null, r.kpis?.rms_e_n ?? null, r.kpis?.max_steer_rate_deg_s ?? null, r.kpis?.max_ay ?? null], flag: r.stable && r.on_path ? undefined : "fail" });
            series.push({ label: name, values: r.signals.e_n ?? [] });
          }
        }
        setOutcome({ columns: ["max_e_n", "rms_e_n", "steer_rate", "max_ay"], units: ["m", "m", "°/s", "m/s²"], rows, chart: { x, series } });
      } else if (a.kind === "experiment") {
        let job = await client.startExperiment(a.body);
        while (job.state === "queued" || job.state === "running") { await sleep(700); job = await client.experiment(job.id); }
        if (job.state !== "done") throw new Error(job.error ?? job.state);
        setOutcome({ columns: a.kpis, units: a.kpis.map((k) => UNITS[k] ?? ""),
          rows: job.records.map((r) => ({ label: label(r.label), values: a.kpis.map((k) => r.kpis[k] ?? null), flag: r.kpis.mission_passed === 0 && a.kpis.includes("mission_passed") ? "fail" : undefined })) });
      } else {
        const rows: Row[] = [];
        for (const r of a.runs) {
          const cond = applyConditions({}, r.conditions);
          const body: RunRequest = { scenario: r.scenario, stack: cond.stack, ...(cond.friction !== null ? { friction: cond.friction } : {}), name: `${r.scenario} (${r.conditions})` };
          let job = await client.startRun(body);
          while (job.state === "queued" || job.state === "running") { await sleep(600); job = await client.run(job.id); }
          if (job.state !== "done") throw new Error(job.error ?? job.state);
          const res = await client.runResult(job.id, undefined, 50);
          rows.push({ label: t(`workbench.conditions.${r.conditions}`), values: a.kpis.map((k) => res.kpis[k] ?? null), flag: res.kpis.mission_passed === 0 ? "fail" : undefined });
          setOutcome({ columns: a.kpis, units: a.kpis.map((k) => UNITS[k] ?? ""), rows: [...rows] });
        }
      }
    } catch (err) { setError(err); } finally { setBusy(false); }
  };
  const open = () => {
    const a = lesson.action;
    if (a.kind === "control") {
      try { sessionStorage.setItem(CONTROL_FORM_KEY, JSON.stringify({ ...CONTROL_DEFAULT, ...a.open, autorun: true })); } catch { /* storage unavailable: the page opens with its own settings */ }
      navigate("/app/control");
    } else navigate(a.open);
  };

  return (
    <article className="card lesson">
      <div className="card__header">
        <div><h3>{t(`${key}.title`)}</h3><p>{t(`${key}.goal`)}</p></div>
        <label className="checkbox"><input type="checkbox" checked={done} onChange={(e) => onDone(e.target.checked)} />{t("learn.done")}</label>
      </div>
      <div className="card__body stack">
        <div className="grid grid--2">
          <div><div className="chart-title">{t("learn.experiment")}</div><p>{t(`${key}.experiment`)}</p></div>
          <div><div className="chart-title">{t("learn.watch")}</div><p>{t(`${key}.watch`)}</p></div>
        </div>
        <div className="row">
          <button type="button" className="btn btn--primary" disabled={busy} onClick={() => void run()}>{busy ? <span className="spinner" /> : <Icon name="play" />}{t("learn.run")}</button>
          <button type="button" className="btn btn--secondary" onClick={open}><Icon name="arrowRight" size={16} />{t(`learn.open.${lesson.action.kind}`)}</button>
          {busy && lesson.action.kind !== "control" ? <span className="subtle">{t("learn.takes")}</span> : null}
        </div>
        <ErrorAlert error={error} />
        {busy && !outcome ? <Skeleton height={120} /> : null}
        {outcome ? (
          <>
            <div className="table-wrap"><table className="table">
              <thead><tr><th>{t("learn.variant")}</th>{outcome.columns.map((k, i) => <th key={k} className="num">{kpiName(k)}{outcome.units[i] ? ` [${outcome.units[i]}]` : ""}</th>)}</tr></thead>
              <tbody>{outcome.rows.map((r) => (
                <tr key={r.label}><td>{r.label}{r.flag === "fail" ? <span className="badge badge--danger">{lesson.action.kind === "control" ? t("learn.lost") : t("learn.failed")}</span> : null}</td>
                  {r.values.map((v, i) => <td key={i} className="num mono">{outcome.columns[i] === "mission_passed" ? (v === null ? "–" : v ? t("learn.yes") : t("learn.no")) : fmt(v, lang, 3)}</td>)}</tr>
              ))}</tbody></table></div>
            {outcome.chart ? <Suspense fallback={<Skeleton height={200} />}><div className="chart-title">{t("control.series.e_n")}</div>
              <Chart x={outcome.chart.x} xLabel="t [s]" yLabel="m" height={200} ariaLabel={t("control.series.e_n")}
                series={outcome.chart.series.map((s, i) => ({ ...s, color: i }))} /></Suspense> : null}
            <div className="alert alert--info"><Icon name="info" /><div><strong>{t(`${key}.question`)}</strong>
              {answer ? <p>{t(`${key}.answer`)}</p> : <div><button type="button" className="btn btn--ghost btn--sm" onClick={() => setAnswer(true)}>{t("learn.showAnswer")}</button></div>}</div></div>
          </>
        ) : null}
      </div>
    </article>
  );
}
