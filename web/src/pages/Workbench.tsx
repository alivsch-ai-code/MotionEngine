// Workbench: run the full automated-driving stack on a scenario and look into every planning cycle.
// (Desktop equivalent: ADWorkbench with planner view, run overview and telemetry.)
import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { EmptyState, Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { NumberField, SelectField } from "../components/Field";
import { Icon } from "../components/Icon";
import { KpiTile } from "../components/KpiTile";
import { LivePanel } from "../components/LivePanel";
import { PageHeader } from "../components/PageHeader";
import { indexAt, SceneView } from "../components/SceneView";
import { StackEditor } from "../components/StackEditor";
import type { JobView, LiveSession, PlannerSnapshot, RunRequest, RunResult, SavedRun, WorkbenchCatalog } from "../lib/api";
import { adScenarioLabel, libraryText } from "../lib/domain";
import { fmt, toDeg } from "../lib/format";
import { useClient, usePersistentState, useQuery } from "../lib/hooks";
import { applyConditions, CONDITIONS, downloadBlob, fileToBase64, stackSpecs, useConnections, useStack, type Conditions } from "../lib/stack";

const Chart = lazy(() => import("../components/Chart").then((m) => ({ default: m.Chart })));
const ACTIVE = ["queued", "running"];
const TABS = ["planner", "signals", "kpis", "events", "profile"] as const;
type Tab = (typeof TABS)[number];
const HEAD_KPIS = ["min_ttc", "min_distance", "max_ay", "max_e_n", "max_jerk"];

interface Form { scenario: string; seed: number; duration: number; conditions?: Conditions }
interface SavedFile extends Partial<SavedRun> { [key: string]: unknown }

export default function Workbench() {
  const { t, i18n } = useTranslation(["app", "common", "domain"]);
  const client = useClient();
  const catalog = useQuery((s) => client.workbenchCatalog(s), [client]);
  const [form, setForm] = usePersistentState<Form>("me.workbench.form", { scenario: "autobahn_ueberholen", seed: NaN, duration: NaN });
  const [stack, setStack] = useStack();
  const [job, setJob] = useState<JobView | null>(null);
  const [result, setResult] = useState<RunResult | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [history, setHistory] = useState<JobView[]>([]);
  const [connections] = useConnections();
  const [live, setLive] = useState<LiveSession | null>(null);
  const [starting, setStarting] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const lang = i18n.language;

  const loadResult = useCallback(async (id: string) => {
    try { setResult(await client.runResult(id)); setError(null); } catch (err) { setError(err); }
  }, [client]);

  // resume: running job, or the most recent finished one (survives page changes; the server keeps the runs)
  useEffect(() => {
    const ctrl = new AbortController();
    client.runs(ctrl.signal).then((jobs) => {
      setHistory(jobs);
      const active = jobs.find((j) => ACTIVE.includes(j.state));
      const last = active ?? jobs.find((j) => j.state === "done");
      if (last) { setJob(last); if (last.state === "done") void loadResult(last.id); }
    }, () => undefined);
    return () => ctrl.abort();
  }, [client, loadResult]);

  const id = job?.id, active = job ? ACTIVE.includes(job.state) : false;
  useEffect(() => {
    if (!id || !active) return;
    const timer = window.setInterval(() => {
      client.run(id).then((j) => {
        setJob(j);
        if (j.state === "done") { void loadResult(j.id); client.runs().then(setHistory, () => undefined); }
      }, () => undefined);
    }, 500);
    return () => window.clearInterval(timer);
  }, [id, active, client, loadResult]);

  const scenario = catalog.data?.scenarios.find((s) => s.name === form.scenario);
  const request = (): RunRequest | null => {
    const { specs, invalid } = stackSpecs(stack);
    if (invalid) { setError(new Error(t("workbench.invalidParams", { layer: invalid }))); return null; }
    const cond = applyConditions(specs, form.conditions ?? "ideal");
    return { scenario: form.scenario, seed: Number.isFinite(form.seed) ? form.seed : null, duration: Number.isFinite(form.duration) ? form.duration : null,
      stack: cond.stack, ...(cond.friction !== null ? { friction: cond.friction } : {}), ...(connections ? { connections } : {}) };
  };
  const start = async () => {
    const body = request();
    if (!body) return;
    try {
      setError(null);
      setLive(null);
      setJob(await client.startRun(body));
    } catch (err) { setError(err); }
  };
  const startLive = async () => {
    const body = request();
    if (!body) return;
    setStarting(true);
    try {
      setError(null);
      setLive(await client.liveStart(body));
    } catch (err) { setError(err); } finally { setStarting(false); }
  };
  const adopt = (j: JobView) => {
    setLive(null);
    setJob(j);
    void loadResult(j.id);
    client.runs().then(setHistory, () => undefined);
  };
  const download = async () => {
    if (!result) return;
    const data = await client.runDownload(result.id);
    downloadBlob(new Blob([JSON.stringify(data)], { type: "application/json" }), `${result.name}-${result.id}.json`);
  };
  // a saved result: the single file of the download, or the .json + .npz pair the library writes
  const loadFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    try {
      setError(null);
      const list = Array.from(files);
      const json = list.find((f) => f.name.toLowerCase().endsWith(".json"));
      const npz = list.find((f) => f.name.toLowerCase().endsWith(".npz"));
      if (!json) throw new Error(t("workbench.load.needJson"));
      const parsed = JSON.parse(await json.text()) as SavedFile;
      const name = json.name.replace(/\.json$/i, "");
      if (typeof parsed.npz === "string" && parsed.meta) adopt(await client.importRun({ meta: parsed.meta, npz: parsed.npz, name: parsed.name ?? name }));
      else if (npz) adopt(await client.importRun({ meta: parsed, npz: await fileToBase64(npz), name }));
      else throw new Error(t("workbench.load.needNpz"));
    } catch (err) {
      setError(err instanceof SyntaxError ? new Error(t("workbench.load.needJson")) : err);
    } finally {
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("workbench.title")} description={t("workbench.subtitle")} />
      <div className="split">
        <form className="card" onSubmit={(e) => { e.preventDefault(); void start(); }}>
          <div className="card__header"><h2>{t("workbench.setup")}</h2></div>
          <div className="card__body stack">
            <SelectField label={t("workbench.scenario")} value={form.scenario} onChange={(v) => setForm({ ...form, scenario: v })}
              options={(catalog.data?.scenarios ?? [{ name: form.scenario, label: form.scenario }]).map((s) => ({ value: s.name, label: adScenarioLabel(t, s) }))}
              hint={scenario ? t(`domain:adScenario.${scenario.name}`, { defaultValue: scenario.description }) : undefined} />
            <div className="grid grid--2-tight">
              <NumberField label={t("workbench.seed")} value={form.seed} step={1} min={0} onChange={(v) => setForm({ ...form, seed: v })}
                hint={scenario ? t("workbench.defaultValue", { v: scenario.seed }) : undefined} />
              <NumberField label={t("workbench.duration")} unit="s" value={form.duration} min={1} max={catalog.data?.limits.max_duration ?? 120}
                onChange={(v) => setForm({ ...form, duration: v })} hint={scenario ? t("workbench.defaultValue", { v: scenario.duration }) : undefined} />
            </div>
            <SelectField label={t("workbench.conditions.label")} value={form.conditions ?? "ideal"} onChange={(v) => setForm({ ...form, conditions: v })}
              options={CONDITIONS.map((c) => ({ value: c, label: t(`workbench.conditions.${c}`) }))} hint={t(`workbench.conditions.hint.${form.conditions ?? "ideal"}`)} />
            {catalog.data ? <StackEditor catalog={catalog.data} stack={stack} onChange={setStack} /> : <Skeleton height={120} />}
            {active ? (
              <button type="button" className="btn btn--secondary btn--lg" onClick={() => job && void client.cancelRun(job.id).then(setJob)}>
                <Icon name="stop" />{t("common:cancel")}</button>
            ) : (
              <div className="row">
                <button type="submit" className="btn btn--primary btn--lg" style={{ flex: 1 }} disabled={!catalog.data || starting}><Icon name="play" />{t("workbench.run")}</button>
                <button type="button" className="btn btn--secondary btn--lg" disabled={!catalog.data || starting} onClick={() => void startLive()}>
                  {starting ? <span className="spinner" /> : <Icon name="radar" />}{t("live.start")}</button>
              </div>
            )}
            {connections ? <p className="subtle"><Icon name="plug" size={14} /> {t("workbench.rewired", { n: connections.length })}</p> : null}
            <input ref={fileInput} type="file" accept=".json,.npz" multiple hidden onChange={(e) => void loadFiles(e.target.files)} />
            <button type="button" className="btn btn--ghost btn--sm" onClick={() => fileInput.current?.click()} title={t("workbench.load.hint")}>
              <Icon name="upload" size={14} />{t("workbench.load.button")}</button>
            {history.length ? (
              <details className="expert"><summary><Icon name="layers" />{t("workbench.history", { n: history.length })}</summary>
                <div className="stack stack--sm">
                  {history.map((h) => (
                    <button key={h.id} type="button" className={`btn btn--sm ${h.id === result?.id ? "btn--secondary" : "btn--ghost"}`} disabled={h.state !== "done"}
                      onClick={() => { setLive(null); setJob(h); void loadResult(h.id); }}>
                      {h.name} · {new Date(h.created * 1000).toLocaleTimeString(lang)} · {h.kind === "run" ? t(`models.jobStates.${h.state}`) : t(`workbench.kinds.${h.kind}`, { defaultValue: h.kind })}</button>
                  ))}
                </div>
              </details>
            ) : null}
          </div>
        </form>
        <div className="stack" aria-live="polite">
          <ErrorAlert error={catalog.error ?? error} />
          {job && active ? (
            <div className="card"><div className="card__body stack">
              <h2>{t("workbench.running", { name: job.name })}</h2>
              <div className="progress" role="progressbar" aria-valuenow={Math.round(job.progress * 100)} aria-valuemin={0} aria-valuemax={100}>
                <span style={{ width: `${job.progress * 100}%` }} /></div>
            </div></div>
          ) : null}
          {job?.state === "failed" ? <div className="alert alert--danger" role="alert"><Icon name="alert" /><div><strong>{t("workbench.failed")}</strong>
            <div className="mono subtle">{job.error}</div></div></div> : null}
          {live ? <LivePanel key={live.id} session={live} lang={lang} onFinished={adopt} onClosed={() => setLive(null)} /> : null}
          {!result && !active && !live ? <div className="card"><EmptyState art="scenario" title={t("workbench.empty.title")} text={t("workbench.empty.text")}
            action={<button type="button" className="btn btn--primary" onClick={() => void start()}><Icon name="play" />{t("workbench.run")}</button>} /></div> : null}
          {result && !live ? <RunView result={result} catalog={catalog.data} lang={lang} onDownload={download} /> : null}
        </div>
      </div>
    </div>
  );
}

function RunView({ result, catalog, lang, onDownload }: { result: RunResult; catalog?: WorkbenchCatalog; lang: string; onDownload: () => void }) {
  const { t } = useTranslation(["app", "common", "domain"]);
  const client = useClient();
  const tt = (result.signals.t ?? []) as number[];
  const t0 = tt[0] ?? 0, t1 = tt[tt.length - 1] ?? 0;
  const [time, setTime] = useState(t0);
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [showCandidates, setShowCandidates] = useState(true);
  const [tab, setTab] = useState<Tab>("planner");
  const [snapshot, setSnapshot] = useState<PlannerSnapshot | null>(null);
  const cache = useRef(new Map<number, PlannerSnapshot>());
  const last = useRef<number | null>(null);

  useEffect(() => { setTime(t0); setPlaying(true); cache.current = new Map(); setSnapshot(null); }, [result.id, t0]);
  useEffect(() => {
    if (!playing) return;
    let raf = 0;
    const tick = (now: number) => {
      const dt = last.current === null ? 0 : (now - last.current) / 1000;
      last.current = now;
      setTime((cur) => { const n = cur + dt * speed; if (n >= t1) { setPlaying(false); return t1; } return n; });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(raf); last.current = null; };
  }, [playing, speed, t1]);

  // planning cycle active at `time`: the last snapshot that started before it
  const k = useMemo(() => {
    const snaps = result.snapshots;
    let lo = 0, hi = snaps.length - 1;
    if (hi < 0) return -1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (snaps[mid].t <= time) lo = mid; else hi = mid; }
    return snaps[hi].t <= time ? hi : lo;
  }, [result.snapshots, time]);
  useEffect(() => {
    if (k < 0) return;
    const hit = cache.current.get(k);
    if (hit) { setSnapshot(hit); return; }
    const ctrl = new AbortController();
    client.runSnapshot(result.id, k, ctrl.signal).then((s) => { cache.current.set(k, s); setSnapshot(s); }, () => undefined);
    return () => ctrl.abort();
  }, [k, result.id, client]);

  const i = indexAt(tt, time);
  const sig = result.signals;
  const meta = k >= 0 ? result.snapshots[k] : null;
  const kpiLabel = (key: string) => t(`domain:adKpi.${key}`, { defaultValue: catalog?.kpi_info[key]?.[0] ?? key });
  const head = HEAD_KPIS.filter((key) => result.kpis[key] !== undefined);
  const deg = useMemo(() => (sig.delta ?? []).map((v) => (v === null ? null : toDeg(v))), [sig.delta]);

  return (
    <>
      <div className="row row--between">
        <div className="row">
          {result.mission ? <span className={`badge ${result.mission.passed ? "badge--success" : "badge--warning"}`}>
            {result.mission.passed ? t("workbench.missionPassed") : t("workbench.missionFailed")}</span> : null}
          {(result.kpis.collision ?? 0) > 0 ? <span className="badge badge--danger">{t("workbench.collision")}</span> : null}
          <span className="subtle">{t("workbench.timing", { sim: fmt(result.duration, lang, 3), wall: fmt(result.wall_time ?? 0, lang, 2) })}</span>
        </div>
        <button type="button" className="btn btn--secondary btn--sm" onClick={onDownload}><Icon name="upload" />{t("workbench.download")}</button>
      </div>
      <div className="grid grid--4">
        {head.map((key) => <KpiTile key={key} label={kpiLabel(key)} value={result.kpis[key]} unit={catalog?.kpi_info[key]?.[1]} lang={lang} />)}
      </div>
      <div className="card"><div className="card__body player">
        <SceneView result={result} time={time} snapshot={snapshot} showCandidates={showCandidates} ariaLabel={t("workbench.scene")} />
        <div className="player__controls">
          <button type="button" className="btn btn--secondary btn--sm btn--icon" aria-label={playing ? t("common:player.pause") : t("common:player.play")}
            onClick={() => { if (!playing && time >= t1) setTime(t0); setPlaying((p) => !p); }}><Icon name={playing ? "pause" : "play"} size={16} /></button>
          <input type="range" className="player__scrub" min={t0} max={t1} step={0.05} value={time} aria-label={t("common:player.time")}
            onChange={(e) => { setPlaying(false); setTime(Number(e.target.value)); }} />
          <span className="player__readout mono">{fmt(time, lang, 3)} s · {fmt(((sig.ego_v?.[i] ?? 0) as number) * 3.6, lang, 2)} km/h</span>
          <select className="select select--sm" value={speed} aria-label={t("common:player.speed")} onChange={(e) => setSpeed(Number(e.target.value))}>
            {[0.25, 0.5, 1, 2, 4].map((s) => <option key={s} value={s}>{s}×</option>)}</select>
          <button type="button" className={`btn btn--sm ${showCandidates ? "btn--secondary" : "btn--ghost"}`} aria-pressed={showCandidates}
            onClick={() => setShowCandidates((v) => !v)}>{t("workbench.candidates")}</button>
        </div>
        <p className="subtle">{t("workbench.legend")}</p>
      </div></div>
      <div className="tabs" role="tablist" aria-label={t("workbench.details")}>
        {TABS.map((x) => <button key={x} role="tab" type="button" aria-selected={tab === x} onClick={() => setTab(x)}>{t(`workbench.tabs.${x}`)}</button>)}
      </div>
      {tab === "planner" ? (
        <div className="grid grid--2">
          <div className="card"><div className="card__header"><h2>{t("workbench.cycle")}</h2></div><div className="card__body table-wrap">
            {meta && snapshot ? <table className="table"><tbody>
              <tr><td>{t("workbench.cycleTime")}</td><td className="num">{fmt(meta.t, lang, 3)} s</td></tr>
              <tr><td>{t("workbench.maneuver")}</td><td className="num">{String(meta.maneuver ?? "–")}</td></tr>
              <tr><td>{t("workbench.mode")}</td><td className="num">{snapshot.mode}</td></tr>
              <tr><td>{t("workbench.nCandidates")}</td><td className="num">{fmt(snapshot.n_candidates, lang)} / {fmt(snapshot.n_checked, lang)}</td></tr>
              <tr><td>{t("workbench.computeTime")}</td><td className="num">{fmt(snapshot.compute_time * 1000, lang, 3)} ms</td></tr>
              <tr><td>{t("workbench.controller")}</td><td className="num">{String(snapshot.controller?.active ?? "–")}</td></tr>
              <tr><td>{t("workbench.flags")}</td><td className="num">{[snapshot.fallback ? t("workbench.fallback") : "", snapshot.reinitialized ? t("workbench.reinit") : ""].filter(Boolean).join(", ") || "–"}</td></tr>
              {Object.entries(snapshot.constraint_violations).map(([name, n]) => <tr key={name}><td className="subtle">{name}</td><td className="num">{n}</td></tr>)}
            </tbody></table> : <Skeleton height={160} />}
          </div></div>
          <div className="card"><div className="card__header"><h2>{t("workbench.costTerms")}</h2></div><div className="card__body table-wrap">
            {snapshot ? <table className="table"><tbody>
              {Object.entries(snapshot.cost_terms).map(([name, v]) => <tr key={name}><td className="mono">{name}</td><td className="num">{fmt(v, lang, 4)}</td></tr>)}
            </tbody></table> : <Skeleton height={160} />}
          </div></div>
        </div>
      ) : null}
      {tab === "signals" ? (
        <Suspense fallback={<Skeleton height={240} />}>
          <div className="grid grid--2">
            <ChartCard title={t("workbench.charts.speed")}><Chart x={tt} xLabel="t [s]" yLabel="m/s" height={200} ariaLabel={t("workbench.charts.speed")}
              series={[{ label: t("workbench.series.actual"), values: sig.ego_v ?? [] }, { label: t("workbench.series.planned"), values: sig.des_v ?? [], color: 2, dash: true },
                { label: t("workbench.series.target"), values: sig.target_speed ?? [], color: 3 }]} /></ChartCard>
            <ChartCard title={t("workbench.charts.accel")}><Chart x={tt} xLabel="t [s]" yLabel="m/s²" height={200} ariaLabel={t("workbench.charts.accel")}
              series={[{ label: "a_x", values: sig.ego_ax ?? [] }, { label: "a_y", values: sig.ego_ay ?? [], color: 1 }]} /></ChartCard>
            <ChartCard title={t("workbench.charts.errors")}><Chart x={tt} xLabel="t [s]" yLabel="m" height={200} ariaLabel={t("workbench.charts.errors")}
              series={[{ label: "e_n", values: sig.e_n ?? [], color: 4 }, { label: "e_t", values: sig.e_t ?? [], color: 3 }]} /></ChartCard>
            <ChartCard title={t("workbench.charts.steering")}><Chart x={tt} xLabel="t [s]" yLabel="°" height={200} ariaLabel={t("workbench.charts.steering")}
              series={[{ label: "δ", values: deg, color: 3 }]} /></ChartCard>
            <ChartCard title={t("workbench.charts.cost")}><Chart x={tt} xLabel="t [s]" yLabel="J" height={200} ariaLabel={t("workbench.charts.cost")}
              series={[{ label: "J", values: sig.plan_cost ?? [], color: 5 }]} /></ChartCard>
            <ChartCard title={t("workbench.charts.planTime")}><Chart x={tt} xLabel="t [s]" yLabel="ms" height={200} ariaLabel={t("workbench.charts.planTime")}
              series={[{ label: "ms", values: (sig.plan_time ?? []).map((v) => (v === null ? null : v * 1000)), color: 2 }]} /></ChartCard>
          </div>
        </Suspense>
      ) : null}
      {tab === "kpis" ? (
        <div className="grid grid--2">
          <div className="card"><div className="card__header"><h2>{t("workbench.tabs.kpis")}</h2></div><div className="card__body table-wrap"><table className="table">
            <thead><tr><th>{t("simulate.kpiTable.group")}</th><th>{t("simulate.kpiTable.kpi")}</th><th className="num">{t("simulate.kpiTable.value")}</th><th>{t("simulate.kpiTable.unit")}</th></tr></thead>
            <tbody>{Object.entries(result.kpis).map(([key, v]) => (
              <tr key={key}><td className="subtle">{t(`domain:adKpiGroup.${catalog?.kpi_info[key]?.[2] ?? ""}`, { defaultValue: catalog?.kpi_info[key]?.[2] ?? "" })}</td>
                <td>{kpiLabel(key)}</td><td className="num">{fmt(v, lang, 4)}</td><td className="subtle">{(catalog?.kpi_info[key]?.[1] ?? "").replace("-", "")}</td></tr>
            ))}</tbody></table></div></div>
          <div className="card"><div className="card__header"><h2>{t("workbench.mission")}</h2></div><div className="card__body table-wrap">
            {result.mission ? <table className="table"><tbody>{Object.entries(result.mission.criteria).map(([name, c]) => (
              <tr key={name}><td><span className={`badge ${c.ok ? "badge--success" : "badge--danger"}`}>{c.ok ? "✓" : "✕"}</span></td>
                <td>{t(`domain:adCriterion.${name}`, { defaultValue: name })}</td><td className="subtle">{libraryText(c.detail, lang)}</td></tr>))}</tbody></table> : <p className="subtle">{t("workbench.noMission")}</p>}
          </div></div>
        </div>
      ) : null}
      {tab === "events" ? (
        <div className="card"><div className="card__body table-wrap"><table className="table">
          <thead><tr><th className="num">t [s]</th><th>{t("workbench.eventType")}</th><th>{t("workbench.eventDetail")}</th></tr></thead>
          <tbody>{result.events.map((e, n) => {
            const { t: et, type, ...rest } = e;
            return <tr key={n} onClick={() => { setPlaying(false); setTime(et); }} style={{ cursor: "pointer" }}>
              <td className="num">{fmt(et, lang, 3)}</td><td><span className="badge badge--info">{type}</span></td>
              <td className="subtle">{Object.entries(rest).map(([a, b]) => `${a}: ${typeof b === "object" ? JSON.stringify(b) : String(b)}`).join(" · ")}</td></tr>;
          })}</tbody></table></div></div>
      ) : null}
      {tab === "profile" ? (
        <div className="card"><div className="card__body table-wrap"><table className="table">
          <thead><tr><th>{t("workbench.node")}</th><th className="num">{t("workbench.calls")}</th><th className="num">{t("workbench.mean")}</th>
            <th className="num">{t("workbench.p95")}</th><th className="num">{t("workbench.maxTime")}</th><th className="num">{t("workbench.total")}</th></tr></thead>
          <tbody>{Object.entries(result.profile).sort((a, b) => b[1].total - a[1].total).map(([name, p]) => (
            <tr key={name}><td className="mono">{name}</td><td className="num">{p.calls}</td><td className="num">{fmt(p.mean * 1000, lang, 3)} ms</td>
              <td className="num">{fmt(p.p95 * 1000, lang, 3)} ms</td><td className="num">{fmt(p.max * 1000, lang, 3)} ms</td><td className="num">{fmt(p.total, lang, 3)} s</td></tr>
          ))}</tbody></table></div></div>
      ) : null}
    </>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return <div className="card"><div className="card__header"><h2>{title}</h2></div><div className="card__body">{children}</div></div>;
}
