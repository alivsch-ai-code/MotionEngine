// Run comparison of the vehicle-dynamics simulation: the finished runs, a KPI table side by side, overlaid
// paths and signals, the PDF report and saving/loading a run. (Desktop equivalent: compare panel and exports.)
import { lazy, Suspense, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import type { SimulateResponse } from "../lib/api";
import { kpiLabel, kpiValue } from "../lib/domain";
import { fmt, toDeg } from "../lib/format";
import { useClient } from "../lib/hooks";
import { addRun, removeRuns, resample, useRuns, type SimRun } from "../lib/simRuns";
import { downloadBlob } from "../lib/stack";
import { Skeleton } from "./EmptyState";
import { ErrorAlert } from "./ErrorAlert";
import { Icon } from "./Icon";
import { PathPlot } from "./PathPlot";

const Chart = lazy(() => import("./Chart"));
const OVERLAYS: { key: string; unit: string; conv?: (v: number) => number }[] = [
  { key: "r", unit: "°/s", conv: toDeg }, { key: "ay", unit: "m/s²" }, { key: "delta_f", unit: "°", conv: toDeg },
  { key: "lateral_error", unit: "m" }, { key: "vx", unit: "km/h", conv: (v) => v * 3.6 }, { key: "beta", unit: "°", conv: toDeg },
];

export function RunCompare({ lang }: { lang: string }) {
  const { t } = useTranslation(["app", "common", "domain"]);
  const client = useClient();
  const runs = useRuns();
  const [off, setOff] = useState<string[]>([]);
  const [busy, setBusy] = useState<"" | "pdf" | "summary">("");
  const [error, setError] = useState<unknown>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const selected = runs.filter((r) => !off.includes(r.key));
  const stored = selected.filter((r) => r.data.run_id && !r.loaded);

  const grid = useMemo(() => {
    const end = Math.max(0, ...selected.map((r) => { const tt = r.data.signals.t ?? []; return (tt[tt.length - 1] ?? 0) as number; }));
    const n = 600;
    return Array.from({ length: n + 1 }, (_, i) => (end * i) / n);
  }, [selected]);
  const kpiKeys = useMemo(() => {
    const keys: string[] = [];
    selected.forEach((r) => r.data.kpis.forEach((k) => { if (!keys.includes(k.key)) keys.push(k.key); }));
    return keys;
  }, [selected]);

  const report = async (format: "pdf" | "summary") => {
    setBusy(format);
    try {
      setError(null);
      const blob = await client.report(stored.map((r) => r.data.run_id as string), format, t("compare.reportTitle"));
      downloadBlob(blob, format === "pdf" ? "report.pdf" : "summary.md");
    } catch (err) { setError(err); } finally { setBusy(""); }
  };
  const save = (r: SimRun) => downloadBlob(new Blob([JSON.stringify({ format: "motionengine-sim-run", label: r.label, request: r.request, data: r.data })],
    { type: "application/json" }), `${r.label.replace(/[^\w.-]+/g, "_")}.json`);
  const load = async (files: FileList | null) => {
    try {
      setError(null);
      for (const file of Array.from(files ?? [])) {
        const j = JSON.parse(await file.text()) as { format?: string; label?: string; request?: SimRun["request"]; data?: SimulateResponse };
        if (j.format !== "motionengine-sim-run" || !j.data?.signals || !Array.isArray(j.data.kpis)) throw new Error(t("compare.badFile", { name: file.name }));
        addRun({ label: j.label ?? file.name.replace(/\.json$/i, ""), at: Date.now(), request: j.request ?? null, data: { ...j.data, run_id: undefined }, loaded: true });
      }
    } catch (err) {
      setError(err instanceof SyntaxError ? new Error(t("compare.badFile", { name: "" })) : err);
    } finally {
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  return (
    <details className="card" style={{ padding: "var(--me-space-4)" }} open={runs.length > 1}>
      <summary style={{ cursor: "pointer", fontWeight: 600 }}>{t("compare.title", { n: runs.length })}</summary>
      <div className="stack" style={{ marginTop: "var(--me-space-3)" }}>
        <p className="subtle">{t("compare.text")}</p>
        <ErrorAlert error={error} />
        <div className="stack stack--sm">
          {runs.map((r, i) => (
            <div key={r.key} className="row row--between">
              <label className="checkbox"><input type="checkbox" checked={!off.includes(r.key)}
                onChange={(e) => setOff(e.target.checked ? off.filter((k) => k !== r.key) : [...off, r.key])} />
                <span className="swatch" style={{ background: `var(--me-chart-${(i % 6) + 1})` }} />{r.label}
                {r.loaded ? <span className="badge badge--info">{t("compare.loaded")}</span> : null}</label>
              <div className="row">
                <button type="button" className="btn btn--ghost btn--sm" onClick={() => save(r)}>{t("compare.save")}</button>
                <button type="button" className="btn btn--ghost btn--sm btn--icon" aria-label={t("compare.remove", { name: r.label })} onClick={() => removeRuns([r.key])}>
                  <Icon name="trash" size={14} /></button>
              </div>
            </div>
          ))}
        </div>
        <div className="row">
          <button type="button" className="btn btn--primary btn--sm" disabled={!stored.length || busy !== ""} onClick={() => void report("pdf")}
            title={stored.length ? undefined : t("compare.needStored")}>{busy === "pdf" ? <span className="spinner" /> : <Icon name="book" size={14} />}{t("compare.pdf")}</button>
          <button type="button" className="btn btn--secondary btn--sm" disabled={!stored.length || busy !== ""} onClick={() => void report("summary")}>
            {busy === "summary" ? <span className="spinner" /> : null}{t("compare.summary")}</button>
          <input ref={fileInput} type="file" accept=".json" multiple hidden onChange={(e) => void load(e.target.files)} />
          <button type="button" className="btn btn--ghost btn--sm" onClick={() => fileInput.current?.click()}><Icon name="upload" size={14} />{t("compare.load")}</button>
        </div>
        {selected.length > 1 ? (
          <>
            <PathPlot ariaLabel={t("compare.paths")} height={240}
              lines={selected.map((r) => ({ x: r.data.signals.x ?? [], y: r.data.signals.y ?? [], kind: "physics" as const, color: runs.indexOf(r) }))} />
            <Suspense fallback={<Skeleton height={220} />}>
              <div className="grid grid--2">
                {OVERLAYS.filter((o) => selected.some((r) => r.data.signals[o.key]?.length)).map((o) => (
                  <div key={o.key}><div className="chart-title">{t(`compare.signals.${o.key}`)}</div>
                    <Chart x={grid} xLabel="t [s]" yLabel={o.unit} height={200} ariaLabel={t(`compare.signals.${o.key}`)}
                      series={selected.map((r) => ({ label: r.label, color: runs.indexOf(r),
                        values: resample(r.data.signals.t ?? [], r.data.signals[o.key] ?? [], grid).map((v) => (v === null || !o.conv ? v : o.conv(v))) }))} /></div>
                ))}
              </div>
            </Suspense>
            <div className="table-wrap"><table className="table">
              <thead><tr><th>{t("simulate.kpiTable.kpi")}</th><th>{t("simulate.kpiTable.unit")}</th>{selected.map((r) => <th key={r.key} className="num">{r.label}</th>)}</tr></thead>
              <tbody>{kpiKeys.map((key) => {
                const first = selected.map((r) => r.data.kpis.find((k) => k.key === key)).find(Boolean)!;
                return <tr key={key}><td>{kpiLabel(t, first)}</td><td className="subtle">{first.unit}</td>
                  {selected.map((r) => { const k = r.data.kpis.find((x) => x.key === key); const v = k ? kpiValue(t, k) : null;
                    return <td key={r.key} className="num">{typeof v === "number" ? fmt(v, lang) : v ?? "–"}</td>; })}</tr>;
              })}</tbody></table></div>
          </>
        ) : <p className="subtle">{t("compare.needTwo")}</p>}
      </div>
    </details>
  );
}
