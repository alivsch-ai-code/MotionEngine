import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { EmptyState, Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { NumberField, SelectField, TextField } from "../components/Field";
import { Icon } from "../components/Icon";
import { KpiTile } from "../components/KpiTile";
import { PageHeader } from "../components/PageHeader";
import { PathPlot } from "../components/PathPlot";
import { PlannerModel } from "../components/PlannerModel";
import type { ModelMeta, TrainRequest } from "../lib/api";
import { isActive, useTraining } from "../lib/training";
import { maneuverLabel } from "../lib/domain";
import { fmt } from "../lib/format";
import { useClient, useMutation, useQuery } from "../lib/hooks";

const Chart = lazy(() => import("../components/Chart"));
type Tab = "models" | "train" | "connect";

export default function Models() {
  const { t } = useTranslation(["app", "common"]);
  const { job: activeJob } = useTraining();
  const [tab, setTab] = useState<Tab>(() => (isActive(activeJob) ? "train" : "models"));
  useEffect(() => { if (isActive(activeJob)) setTab((cur) => (cur === "models" ? "train" : cur)); }, [activeJob?.id]); // eslint-disable-line
  const client = useClient();
  const list = useQuery((s) => client.models(s), [client]);
  const [selected, setSelected] = useState<string | null>(null);
  const onCreated = (id: string) => { list.reload(); setSelected(id); setTab("models"); };

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("models.title")} description={t("models.subtitle")} />
      <div className="tabs" role="tablist" aria-label={t("models.title")}>
        {(["models", "train", "connect"] as const).map((k) => (
          <button key={k} role="tab" type="button" aria-selected={tab === k} onClick={() => setTab(k)}>{t(`models.tabs.${k}`)}</button>
        ))}
      </div>
      {tab === "models" ? (
        <ModelList models={list.data} loading={list.loading} error={list.error} selected={selected} onSelect={setSelected}
          onDeleted={() => { setSelected(null); list.reload(); }} onTrain={() => setTab("train")} />
      ) : null}
      {tab === "train" ? <TrainPanel onDone={onCreated} /> : null}
      {tab === "connect" ? <ConnectPanel onDone={onCreated} /> : null}
    </div>
  );
}

function ModelList({ models, loading, error, selected, onSelect, onDeleted, onTrain }:
  { models?: ModelMeta[]; loading: boolean; error: unknown; selected: string | null; onSelect: (id: string) => void; onDeleted: () => void; onTrain: () => void }) {
  const { t, i18n } = useTranslation(["app", "common"]);
  if (error) return <ErrorAlert error={error} />;
  if (loading && !models) return <Skeleton height={200} />;
  if (!models?.length) {
    return <div className="card"><EmptyState art="model" title={t("empty.models.title")} text={t("empty.models.text")}
      action={<button type="button" className="btn btn--primary" onClick={onTrain}><Icon name="brain" />{t("empty.models.action")}</button>} /></div>;
  }
  const current = models.find((m) => m.id === selected) ?? models[0];
  return (
    <div className="stack">
      <div className="card"><div className="card__body table-wrap"><table className="table">
        <thead><tr><th>{t("models.table.name")}</th><th>{t("models.table.kind")}</th><th>{t("models.table.backend")}</th><th>{t("models.table.teacher")}</th><th className="num">{t("models.table.quality")}</th><th className="num">{t("models.table.params")}</th><th>{t("models.table.created")}</th></tr></thead>
        <tbody>{models.map((m) => (
          <tr key={m.id} onClick={() => onSelect(m.id)} style={{ cursor: "pointer", background: m.id === current.id ? "var(--me-surface-2)" : undefined }}
            aria-selected={m.id === current.id}>
            <td><button type="button" className="btn btn--ghost btn--sm" onClick={() => onSelect(m.id)}>{m.name}</button></td>
            <td><span className={`badge ${m.kind === "trajectory_planner" ? "badge--info" : ""}`}>{t(`models.kinds.${m.kind}`, { defaultValue: m.kind })}</span></td>
            <td><span className="badge">{t(`models.backends.${m.backend}`)}</span></td>
            <td className="subtle">{m.teacher ? t(`vehicleModels.${m.teacher}`, { defaultValue: m.teacher }) : "–"}</td>
            <td className="num">{m.kind === "trajectory_planner"
              ? (m.planner_metrics ? t("models.table.acceptance", { v: fmt(m.planner_metrics.acceptance * 100, i18n.language, 3) }) : "–")
              : t("models.table.r2", { v: fmt(m.test_metrics?.r_dot?.r2 ?? null, i18n.language, 4) })}</td>
            <td className="num">{m.n_parameters ? fmt(m.n_parameters, i18n.language) : "–"}</td>
            <td className="subtle">{new Date(m.created * 1000).toLocaleString(i18n.language)}</td>
          </tr>
        ))}</tbody></table></div></div>
      <ModelDetail key={current.id} id={current.id} onDeleted={onDeleted} />
    </div>
  );
}

function ModelDetail({ id, onDeleted }: { id: string; onDeleted: () => void }) {
  const { t, i18n } = useTranslation(["app", "common"]);
  const client = useClient();
  const meta = useQuery((s) => client.model(id, s), [client, id]);
  const [maneuver, setManeuver] = useState("iso_double_lane_change");
  const evaluation = useMutation(() => client.evaluate(id, { maneuver }));
  const remove = useMutation(async () => { await client.deleteModel(id); onDeleted(); });
  const lang = i18n.language;
  const m = meta.data;
  if (meta.error) return <ErrorAlert error={meta.error} />;
  if (!m) return <Skeleton height={240} />;
  const hist = m.history ?? [];
  const ev = evaluation.data;
  const planner = m.kind === "trajectory_planner";
  return (
    <div className="card">
      <div className="card__header">
        <div><h2>{m.name}</h2><p className="mono">{planner ? m.id : m.vehicle_model}</p></div>
        <div className="row">
          {planner ? null : <Link className="btn btn--secondary btn--sm" to={`/app/simulate?model=${encodeURIComponent(m.vehicle_model)}`}><Icon name="play" />{t("models.useInSimulation")}</Link>}
          <button type="button" className="btn btn--danger btn--sm" onClick={() => { if (window.confirm(t("models.confirmDelete", { name: m.name }))) void remove.run(); }}>
            <Icon name="trash" />{t("common:delete")}</button>
        </div>
      </div>
      <div className="card__body stack">
        {planner ? <PlannerModel model={m} /> : null}
        {planner ? null : m.test_metrics ? (
          <div className="grid grid--3">
            {(["vx_dot", "vy_dot", "r_dot"] as const).map((k) => (
              <KpiTile key={k} label={t(`models.targets.${k}`)} value={m.test_metrics?.[k]?.r2 ?? null} unit={`R² · RMSE ${fmt(m.test_metrics?.[k]?.rmse ?? null, lang)}`} lang={lang} />
            ))}
          </div>
        ) : <div className="alert alert--info">{t("models.externalInfo")}</div>}
        {hist.length ? (
          <Suspense fallback={<Skeleton height={220} />}><div className="chart-title">{t("models.lossCurve")}</div>
            <Chart x={hist.map((h) => h.epoch)} xLabel={t("models.epoch")} yLabel="MSE" height={220} ariaLabel={t("models.lossCurve")}
              series={[{ label: t("models.train"), values: hist.map((h) => h.train) }, { label: t("models.validation"), values: hist.map((h) => h.val), color: 2 }]} /></Suspense>
        ) : null}
        {planner ? <ErrorAlert error={remove.error} /> : <>
        <h3>{t("models.evaluate.title")}</h3>
        <p className="subtle">{t("models.evaluate.text")}</p>
        <div className="row" style={{ alignItems: "end" }}>
          <div style={{ minWidth: 260 }}><SelectField label={t("simulate.maneuver")} value={maneuver} onChange={setManeuver}
            options={["iso_double_lane_change", "step_steer", "slalom", "sine_with_dwell", "lane_change"].map((x) => ({ value: x, label: maneuverLabel(t, x) }))} /></div>
          <button type="button" className="btn btn--primary" disabled={evaluation.loading} onClick={() => void evaluation.run()}>
            {evaluation.loading ? <span className="spinner" /> : <Icon name="check" />}{t("models.evaluate.run")}</button>
        </div>
        <ErrorAlert error={evaluation.error ?? remove.error} />
        {ev ? (
          <div className="stack">
            <div className="grid grid--3">
              <KpiTile label={t("models.evaluate.position")} value={ev.max_position_error} unit="m" lang={lang} />
              <KpiTile label={t("models.evaluate.yawRate")} value={(ev.max_yaw_rate_error * 180) / Math.PI} unit="°/s" lang={lang} />
              <KpiTile label={t("models.evaluate.speedup")} value={ev.wall_time.physics / Math.max(ev.wall_time.neural, 1e-6)} unit="×" lang={lang} />
            </div>
            <PathPlot height={220} ariaLabel={t("models.evaluate.paths")} lines={[{ x: ev.series.physics_x, y: ev.series.physics_y, kind: "physics" }, { x: ev.series.neural_x, y: ev.series.neural_y, kind: "neural" }]} />
            <div className="row subtle"><span style={{ color: "var(--me-chart-1)" }}>━</span>{t("models.evaluate.physics")}<span style={{ color: "var(--me-chart-3)" }}>╍</span>{t("models.evaluate.neural")}</div>
            <Suspense fallback={<Skeleton height={200} />}>
              <Chart x={ev.series.t} xLabel="t [s]" yLabel="rad/s" height={200} ariaLabel={t("models.evaluate.yawRate")}
                series={[{ label: t("models.evaluate.physics"), values: ev.series.physics_r }, { label: t("models.evaluate.neural"), values: ev.series.neural_r, color: 2, dash: true }]} /></Suspense>
          </div>
        ) : null}
        </>}
      </div>
    </div>
  );
}

const TRAIN_DEFAULTS = {
  vehicle_dynamics: { n_samples: 20000, hiddenText: "64, 64", epochs: 150 },
  trajectory_planner: { n_samples: 3000, hiddenText: "96, 96", epochs: 200 },
};

function TrainPanel({ onDone }: { onDone: (id: string) => void }) {
  const { t, i18n } = useTranslation(["app", "common"]);
  const client = useClient();
  const [form, setForm] = useState<TrainRequest & { hiddenText: string }>({ kind: "vehicle_dynamics", vehicle: "mid_size_sedan", teacher: "bicycle_nonlinear", n_samples: 20000,
    hidden: [64, 64], hiddenText: "64, 64", epochs: 150, learning_rate: 0.002, seed: 0, name: "" });
  // the job is followed app-wide (lib/training.tsx): leaving this page does not lose it
  const { job, starting, error: startError, start, cancel, dismiss } = useTraining();
  const catalog = useQuery((s) => client.catalog(s), [client]);
  const handled = useRef<string | null>(null);

  useEffect(() => {
    if (job && job.state === "done" && job.model_id && handled.current !== job.id) {
      handled.current = job.id;
      onDone(job.model_id);
      dismiss();
    }
  }, [job, onDone, dismiss]);

  const submit = async () => {
    const hidden = form.hiddenText.split(/[,\s]+/).map(Number).filter((n) => Number.isFinite(n) && n > 0);
    const { hiddenText: _unused, ...body } = form;
    void _unused;
    await start({ ...body, hidden: hidden.length ? hidden : [64, 64] });
  };
  const running = isActive(job);
  const planner = form.kind === "trajectory_planner";
  const hist = job?.history ?? [];
  const last = hist[hist.length - 1];
  const chart = useMemo(() => ({ x: hist.map((h) => h.epoch), train: hist.map((h) => h.train), val: hist.map((h) => h.val) }), [hist]);

  return (
    <div className="split split--wide">
      <form className="card" onSubmit={(e) => { e.preventDefault(); void submit(); }}>
        <div className="card__header"><div><h2>{t("models.trainForm.title")}</h2><p>{t("models.trainForm.text")}</p></div></div>
        <div className="card__body stack">
          <SelectField label={t("models.trainForm.kind")} value={form.kind ?? "vehicle_dynamics"} hint={t(`models.trainForm.kindHint.${form.kind ?? "vehicle_dynamics"}`)}
            onChange={(v) => setForm({ ...form, kind: v, ...TRAIN_DEFAULTS[v] })}
            options={(["vehicle_dynamics", "trajectory_planner"] as const).map((v) => ({ value: v, label: t(`models.kinds.${v}`) }))} />
          <SelectField label={t("simulate.vehicle")} value={form.vehicle} onChange={(v) => setForm({ ...form, vehicle: v })}
            options={(catalog.data?.presets ?? [form.vehicle]).map((p) => ({ value: p, label: t(`vehiclePresets.${p}`, { defaultValue: p }) }))} />
          {planner ? null : <SelectField label={t("models.trainForm.teacher")} value={form.teacher} tip={t("models.trainForm.teacherTip")}
            onChange={(v) => setForm({ ...form, teacher: v })} options={(["bicycle_nonlinear", "bicycle_linear"] as const).map((v) => ({ value: v, label: t(`vehicleModels.${v}`) }))} />}
          <NumberField label={planner ? t("models.trainForm.demonstrations") : t("models.trainForm.samples")} value={form.n_samples} min={500} max={planner ? 20000 : 200000} step={500}
            onChange={(v) => setForm({ ...form, n_samples: v })} tip={planner ? t("models.trainForm.demonstrationsTip") : t("models.trainForm.samplesTip")} />
          <details className="expert"><summary><Icon name="settings" />{t("common:expertSettings")}</summary>
            <div className="stack">
              <TextField label={t("models.trainForm.hidden")} value={form.hiddenText} onChange={(v) => setForm({ ...form, hiddenText: v })} hint={t("models.trainForm.hiddenHint")} />
              <NumberField label={t("models.trainForm.epochs")} value={form.epochs} min={1} max={1000} onChange={(v) => setForm({ ...form, epochs: v })} />
              <NumberField label={t("models.trainForm.lr")} value={form.learning_rate} min={0.0001} max={0.1} step={0.0001} onChange={(v) => setForm({ ...form, learning_rate: v })} />
              <NumberField label={t("models.trainForm.seed")} value={form.seed} step={1} onChange={(v) => setForm({ ...form, seed: v })} />
              <TextField label={t("models.trainForm.name")} value={form.name} onChange={(v) => setForm({ ...form, name: v })} />
            </div>
          </details>
          <button type="submit" className="btn btn--primary btn--lg" disabled={running || starting}><Icon name="brain" />{t("models.trainForm.start")}</button>
        </div>
      </form>
      <div className="stack">
        <ErrorAlert error={startError} />
        {job ? (
          <div className="card"><div className="card__body stack">
            <div className="row row--between">
              <h2>{t(`models.jobStates.${job.state}`)}{job.phase ? ` · ${t(`models.phases.${job.phase}`, { defaultValue: job.phase })}` : ""}</h2>
              {running ? <button type="button" className="btn btn--secondary btn--sm" onClick={() => void cancel()}>{t("common:cancel")}</button> : null}
            </div>
            <div className="progress" role="progressbar" aria-valuenow={Math.round(job.progress * 100)} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${job.progress * 100}%` }} /></div>
            {last ? <p className="subtle">{t("models.lastEpoch", { epoch: last.epoch, train: fmt(last.train, i18n.language, 3), val: fmt(last.val, i18n.language, 3) })}</p> : null}
            {job.error ? <div className="alert alert--danger">{job.error}</div> : null}
            {hist.length > 1 ? <Suspense fallback={<Skeleton height={240} />}>
              <Chart x={chart.x} xLabel={t("models.epoch")} yLabel="MSE" ariaLabel={t("models.lossCurve")}
                series={[{ label: t("models.train"), values: chart.train }, { label: t("models.validation"), values: chart.val, color: 2 }]} /></Suspense> : null}
          </div></div>
        ) : (
          <div className="card"><div className="card__body stack">
            <h2>{t("models.how.title")}</h2>
            <p>{planner ? t("models.howPlanner.text") : t("models.how.text")}</p>
            <div className="code-block">{planner ? "x = [d, ḋ, d̈, ṡ, s̈, v_ref, d_min, d_max, κ(s), objects, previous plan]   →   MLP (tanh)   →   y = [δ, τ_lat, ν, τ_lon]"
              : "x = [vₓ, v_y, ψ̇, δ, Fₓ]   →   MLP (tanh)   →   y = [v̇ₓ, v̇_y, ψ̈]"}</div>
            <p className="subtle">{planner ? t("models.howPlanner.validation") : t("models.how.validation")}</p>
          </div></div>
        )}
      </div>
    </div>
  );
}

function ConnectPanel({ onDone }: { onDone: (id: string) => void }) {
  const { t } = useTranslation(["app", "common"]);
  const client = useClient();
  const [backend, setBackend] = useState<"onnx" | "http">("onnx");
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const connect = useMutation(async () => {
    let onnx_base64: string | undefined;
    if (backend === "onnx" && file) {
      const bytes = new Uint8Array(await file.arrayBuffer());
      let bin = "";
      for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
      onnx_base64 = btoa(bin);
    }
    const meta = await client.connect({ name: name || file?.name || url, backend, onnx_base64, url: backend === "http" ? url : undefined, vehicle: "mid_size_sedan" });
    onDone(meta.id);
    return meta;
  });
  return (
    <div className="grid grid--2" style={{ alignItems: "start" }}>
      <form className="card" onSubmit={(e) => { e.preventDefault(); void connect.run(); }}>
        <div className="card__header"><div><h2>{t("models.connect.title")}</h2><p>{t("models.connect.text")}</p></div></div>
        <div className="card__body stack">
          <div className="segmented" role="group" aria-label={t("models.connect.backend")}>
            {(["onnx", "http"] as const).map((b) => <button key={b} type="button" aria-pressed={backend === b} onClick={() => setBackend(b)}>{t(`models.backends.${b}`)}</button>)}
          </div>
          <TextField label={t("models.trainForm.name")} value={name} onChange={setName} />
          {backend === "onnx" ? (
            <div className="field"><label className="field__label" htmlFor="onnx-file">{t("models.connect.file")}</label>
              <input id="onnx-file" className="input" style={{ paddingTop: 6 }} type="file" accept=".onnx" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
              <span className="field__hint">{t("models.connect.fileHint")}</span></div>
          ) : (
            <TextField label={t("models.connect.url")} value={url} onChange={setUrl} placeholder="https://models.example.com/predict" hint={t("models.connect.urlHint")} />
          )}
          <ErrorAlert error={connect.error} />
          <button type="submit" className="btn btn--primary" disabled={connect.loading || (backend === "onnx" ? !file : !url)}><Icon name="plug" />{t("models.connect.submit")}</button>
        </div>
      </form>
      <div className="card"><div className="card__body stack">
        <h2>{t("models.connect.contract")}</h2>
        <p className="subtle">{t("models.connect.contractText")}</p>
        <div className="code-block">{`inputs  (n, 5): [vx m/s, vy m/s, r rad/s, delta rad, Fx N]
outputs (n, 3): [dvx/dt m/s², dvy/dt m/s², dr/dt rad/s²]

# PyTorch -> ONNX
torch.onnx.export(model, torch.zeros(1, 5), "vehicle.onnx",
                  input_names=["x"], output_names=["y"],
                  dynamic_axes={"x": {0: "n"}, "y": {0: "n"}})

# HTTP: POST {"inputs": [[...5 floats...], ...]}
#    -> 200 {"outputs": [[...3 floats...], ...]}`}</div>
      </div></div>
    </div>
  );
}
