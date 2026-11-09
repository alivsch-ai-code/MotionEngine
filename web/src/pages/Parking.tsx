// Parking: plan and drive a parking maneuver for any spot type, steering configuration and drive layout.
import { lazy, Suspense, useState } from "react";
import { useTranslation } from "react-i18next";

import { EmptyState, Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { NumberField, SelectField } from "../components/Field";
import { Icon } from "../components/Icon";
import { KpiTile } from "../components/KpiTile";
import { PageHeader } from "../components/PageHeader";
import { ParkingView } from "../components/ParkingView";
import type { ParkRequest, ParkResponse } from "../lib/api";
import { fmt } from "../lib/format";
import { useClient, useMutation, usePersistentState, useQuery } from "../lib/hooks";

const Chart = lazy(() => import("../components/Chart").then((m) => ({ default: m.Chart })));

const KINDS = ["parallel", "perpendicular", "angled"] as const;
const ENTRIES = ["reverse", "forward"] as const;
const SIDES = ["right", "left"] as const;
const STEERING = ["front", "rear", "counter", "in_phase"] as const;
const LAYOUTS = ["fwd", "rwd", "awd"] as const;

const DEFAULT: ParkRequest = { vehicle: "mid_size_sedan", kind: "parallel", entry: "reverse", side: "right", steering: "front",
  layout: "fwd", mu: 0.9, slope: 0 };

export default function Parking() {
  const { t, i18n } = useTranslation(["app", "common"]);
  const client = useClient();
  const catalog = useQuery((s) => client.catalog(s), [client]);
  const [form, setForm] = usePersistentState<ParkRequest>("me.parking.form", DEFAULT);
  const set = (patch: Partial<ParkRequest>) => setForm({ ...form, ...patch });
  const [result, setResult] = useState<ParkResponse | null>(null);
  const run = useMutation((body: ParkRequest) => client.park(body));
  const submit = async () => {
    const r = await run.run(form);
    if (r) setResult(r);
  };
  const lang = i18n.language;
  const opt = (group: string, values: readonly string[]) => values.map((v) => ({ value: v, label: t(`parking.${group}.${v}`) }));

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("parking.title")} description={t("parking.subtitle")} />
      <div className="split">
        <form className="card" onSubmit={(e) => { e.preventDefault(); void submit(); }} aria-labelledby="park-setup">
          <div className="card__header"><h2 id="park-setup">{t("parking.setup")}</h2></div>
          <div className="card__body stack">
            <SelectField label={t("simulate.vehicle")} value={form.vehicle ?? "mid_size_sedan"} onChange={(v) => set({ vehicle: v })}
              options={(catalog.data?.presets ?? [form.vehicle ?? "mid_size_sedan"]).map((p) => ({ value: p, label: t(`vehiclePresets.${p}`, { defaultValue: p }) }))} />
            <SelectField label={t("parking.kindLabel")} value={form.kind} onChange={(v) => set({ kind: v as ParkRequest["kind"] })} options={opt("kind", KINDS)} />
            <div className="grid grid--2-tight">
              <SelectField label={t("parking.entryLabel")} value={form.entry} onChange={(v) => set({ entry: v as ParkRequest["entry"] })} options={opt("entry", ENTRIES)} />
              <SelectField label={t("parking.sideLabel")} value={form.side} onChange={(v) => set({ side: v as ParkRequest["side"] })} options={opt("side", SIDES)} />
            </div>
            <SelectField label={t("parking.steeringLabel")} value={form.steering} onChange={(v) => set({ steering: v as ParkRequest["steering"] })}
              options={opt("steering", STEERING)} tip={t("parking.steeringTip")} hint={t(`parking.steeringHint.${form.steering}`)} />
            <SelectField label={t("parking.layoutLabel")} value={form.layout} onChange={(v) => set({ layout: v as ParkRequest["layout"] })}
              options={opt("layout", LAYOUTS)} tip={t("parking.layoutTip")} />
            <details className="expert"><summary><Icon name="settings" />{t("common:expertSettings")}</summary>
              <div className="stack">
                {form.kind === "parallel" ? (
                  <NumberField label={t("parking.gapLength")} unit="m" value={form.gap_length ?? NaN} min={3} max={15} step={0.1}
                    onChange={(v) => set({ gap_length: Number.isFinite(v) ? v : undefined })} hint={t("parking.gapHint")} />
                ) : (
                  <>
                    <NumberField label={t("parking.aisleWidth")} unit="m" value={form.aisle_width ?? NaN} min={3} max={12} step={0.1}
                      onChange={(v) => set({ aisle_width: Number.isFinite(v) ? v : undefined })} hint={t("parking.defaultHint")} />
                    <NumberField label={t("parking.spotWidth")} unit="m" value={form.spot_width ?? NaN} min={2} max={4} step={0.05}
                      onChange={(v) => set({ spot_width: Number.isFinite(v) ? v : undefined })} hint={t("parking.defaultHint")} />
                  </>
                )}
                {form.kind === "angled" ? (
                  <NumberField label={t("parking.angle")} unit="°" value={form.angle_deg ?? NaN} min={30} max={75} step={5}
                    onChange={(v) => set({ angle_deg: Number.isFinite(v) ? v : undefined })} hint={t("parking.defaultHint")} />
                ) : null}
                {form.steering === "counter" || form.steering === "in_phase" ? (
                  <NumberField label={t("parking.ratio")} value={form.ratio ?? NaN} min={-1} max={0.99} step={0.05}
                    onChange={(v) => set({ ratio: Number.isFinite(v) ? v : undefined })} tip={t("parking.ratioTip")} hint={t("parking.defaultHint")} />
                ) : null}
                <NumberField label={t("parking.mu")} value={form.mu ?? 0.9} min={0.05} max={1.5} step={0.05} onChange={(v) => set({ mu: v })} tip={t("parking.muTip")} />
                <NumberField label={t("parking.slope")} unit="%" value={(form.slope ?? 0) * 100} min={-30} max={30} step={1}
                  onChange={(v) => set({ slope: v / 100 })} tip={t("parking.slopeTip")} />
                <button type="button" className="btn btn--ghost btn--sm" onClick={() => setForm(DEFAULT)}>{t("common:reset")}</button>
              </div>
            </details>
            <button type="submit" className="btn btn--primary btn--lg" disabled={run.loading}>
              {run.loading ? <span className="spinner" /> : <Icon name="parking" />}{run.loading ? t("parking.running") : t("parking.run")}
            </button>
          </div>
        </form>
        <div className="stack" aria-live="polite">
          <ErrorAlert error={run.error} />
          {run.loading && !result ? <Skeleton height={420} /> : null}
          {!run.loading && !result && !run.error ? (
            <div className="card"><EmptyState art="scenario" title={t("parking.empty.title")} text={t("parking.empty.text")}
              action={<button type="button" className="btn btn--primary" onClick={() => void submit()}><Icon name="parking" />{t("parking.run")}</button>} /></div>
          ) : null}
          {result ? <Results r={result} lang={lang} /> : null}
        </div>
      </div>
    </div>
  );
}

function Results({ r, lang }: { r: ParkResponse; lang: string }) {
  const { t } = useTranslation(["app", "common"]);
  const k = r.driven?.kpis;
  const deg = (v: (number | null)[]) => v.map((a) => (a === null ? null : (a * 180) / Math.PI));
  return (
    <>
      <div className="row row--between">
        <div className="row">
          <span className={`badge ${r.success ? "badge--success" : "badge--danger"}`}>{r.success ? t("parking.planned") : t("parking.notPlanned")}</span>
          {r.driven ? <span className={`badge ${r.driven.success ? "badge--success" : "badge--warning"}`}>
            {r.driven.success ? t("parking.parked") : t("parking.notParked")}</span> : null}
          {k && (k.min_clearance ?? 1) <= 0.01 ? <span className="badge badge--warning">{t("parking.contact")}</span> : null}
        </div>
        <span className="subtle">{t("parking.timing", { s: fmt(r.compute_time, lang, 2), n: r.nodes_expanded })}</span>
      </div>
      {!r.success ? <div className="alert alert--danger" role="alert"><Icon name="alert" /><div>{t("parking.failed")} <span className="mono subtle">{r.message}</span></div></div> : null}
      {r.driven && !r.driven.success ? <div className="alert alert--info"><Icon name="info" /><div>{r.driven.message}</div></div> : null}
      {r.path ? (
        <div className="grid grid--4">
          <KpiTile label={t("parking.kpi.moves")} value={r.path.segments.length} lang={lang} />
          <KpiTile label={t("parking.kpi.length")} value={r.path.length} unit="m" lang={lang} />
          <KpiTile label={t("parking.kpi.radius")} value={r.geometry.min_radius} unit="m" lang={lang} />
          {k ? <KpiTile label={t("parking.kpi.time")} value={k.maneuver_time} unit="s" lang={lang} /> : null}
          {k ? <KpiTile label={t("parking.kpi.finalError")} value={(k.final_position_error ?? 0) * 100} unit="cm" lang={lang} /> : null}
          {k ? <KpiTile label={t("parking.kpi.heading")} value={k.final_heading_error_deg} unit="°" lang={lang} /> : null}
          {k ? <KpiTile label={t("parking.kpi.tracking")} value={(k.max_lateral_error ?? 0) * 100} unit="cm" lang={lang} /> : null}
          {k ? <KpiTile label={t("parking.kpi.clearance")} value={(k.min_clearance ?? 0) * 100} unit="cm" lang={lang} /> : null}
        </div>
      ) : null}
      <div className="card"><div className="card__header"><div><h2>{t("parking.view")}</h2><p>{t("parking.viewHint")}</p></div></div>
        <div className="card__body">
          <ParkingView r={r} ariaLabel={t("parking.view")} />
        </div>
      </div>
      {r.driven ? (
        <Suspense fallback={<Skeleton height={220} />}>
          <div className="grid grid--2">
            <div className="card"><div className="card__header"><h2>{t("parking.steeringChart")}</h2></div><div className="card__body">
              <Chart x={r.driven.t} xLabel="t [s]" yLabel="°" height={200} ariaLabel={t("parking.steeringChart")}
                series={[{ label: t("parking.front"), values: deg(r.driven.delta_f) }, { label: t("parking.rear"), values: deg(r.driven.delta_r), color: 2 }]} />
            </div></div>
            <div className="card"><div className="card__header"><h2>{t("parking.speedChart")}</h2></div><div className="card__body">
              <Chart x={r.driven.t} xLabel="t [s]" yLabel="m/s" height={200} ariaLabel={t("parking.speedChart")}
                series={[{ label: t("parking.speed"), values: r.driven.v, color: 1 }]} />
            </div></div>
          </div>
        </Suspense>
      ) : null}
      <div className="card"><div className="card__body stack stack--sm">
        <h2>{t(`parking.steering.${r.geometry.mode}`)}</h2>
        <p>{t(`parking.steeringHint.${r.geometry.mode}`)}</p>
        <p className="subtle">{t("parking.geometryInfo", { r: fmt(r.geometry.min_radius, lang, 3), p: fmt(r.geometry.reference_from_rear_axle, lang, 2),
          f: fmt(r.geometry.max_front_deg, lang, 2), rr: fmt(r.geometry.max_rear_deg, lang, 2) })}</p>
      </div></div>
    </>
  );
}
