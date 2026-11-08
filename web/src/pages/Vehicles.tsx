import { lazy, Suspense, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { SelectField, TextField } from "../components/Field";
import { KpiTile } from "../components/KpiTile";
import { PageHeader } from "../components/PageHeader";
import { InfoTip } from "../components/Tooltip";
import { paramLabel } from "../lib/domain";
import { fmt, toDeg } from "../lib/format";
import { useClient, useQuery } from "../lib/hooks";

const Chart = lazy(() => import("../components/Chart"));

export default function Vehicles() {
  const { t, i18n } = useTranslation(["app", "domain", "common"]);
  const client = useClient();
  const [preset, setPreset] = useState("mid_size_sedan");
  const [filter, setFilter] = useState("");
  const catalog = useQuery((s) => client.catalog(s), [client]);
  const detail = useQuery((s) => client.vehicle(preset, s), [client, preset]);
  const lang = i18n.language;
  const groups = useMemo(() => {
    const out: Record<string, NonNullable<typeof detail.data>["schema"]> = {};
    const f = filter.trim().toLowerCase();
    for (const p of detail.data?.schema ?? []) {
      if (f && !paramLabel(t, p.key).toLowerCase().includes(f) && !p.key.includes(f)) continue;
      (out[p.key.split(".")[0]] ??= []).push(p);
    }
    return out;
  }, [detail.data, filter, t]);
  const a = detail.data?.analysis;

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("vehicles.title")} description={t("vehicles.subtitle")} />
      <div className="grid grid--3">
        <SelectField label={t("vehicles.preset")} value={preset} onChange={setPreset}
          options={(catalog.data?.presets ?? [preset]).map((p) => ({ value: p, label: t(`vehiclePresets.${p}`, { defaultValue: p }) }))} />
      </div>
      <ErrorAlert error={detail.error} />
      {detail.loading && !a ? <Skeleton height={300} /> : null}
      {a ? (
        <>
          <div className="grid grid--4">
            <KpiTile label={t("vehicles.eg")} value={a.understeer_gradient_deg_per_g} unit="°/g" lang={lang} />
            <KpiTile label={t("vehicles.vchar")} value={a.characteristic_speed !== null ? a.characteristic_speed * 3.6 : null} unit="km/h" lang={lang} />
            <KpiTile label={t("vehicles.cf")} value={a.cornering_stiffness_front / 1000} unit="kN/rad" lang={lang} />
            <KpiTile label={t("vehicles.cr")} value={a.cornering_stiffness_rear / 1000} unit="kN/rad" lang={lang} />
          </div>
          <div className="grid grid--2">
            <div className="card"><div className="card__header"><div><h2>{t("vehicles.linear")}<InfoTip text={t("vehicles.linearTip")} /></h2></div></div>
              <div className="card__body table-wrap"><table className="table">
                <thead><tr><th className="num">v [km/h]</th><th className="num">ψ̇/δ [1/s]</th><th className="num">a_y/δ [m/s²/°]</th><th className="num">f₀ [Hz]</th><th className="num">D [–]</th></tr></thead>
                <tbody>{a.per_speed.map((r) => (
                  <tr key={r.speed}><td className="num">{fmt(r.speed * 3.6, lang)}</td><td className="num">{fmt(r.yaw_gain, lang)}</td><td className="num">{fmt(r.ay_gain / toDeg(1), lang)}</td>
                    <td className="num">{fmt(r.natural_frequency, lang)}</td><td className="num">{fmt(r.damping, lang)}</td></tr>
                ))}</tbody></table></div></div>
            <div className="card"><div className="card__body"><div className="chart-title">{t("vehicles.yawGainChart")}</div>
              <Suspense fallback={<Skeleton height={220} />}>
                <Chart x={a.per_speed.map((r) => r.speed * 3.6)} xLabel="v [km/h]" yLabel="1/s" height={220} ariaLabel={t("vehicles.yawGainChart")}
                  series={[{ label: "ψ̇/δ", values: a.per_speed.map((r) => r.yaw_gain) }]} />
              </Suspense></div></div>
          </div>
          <div className="card"><div className="card__header"><h2>{t("vehicles.parameters")}</h2>
            <div style={{ width: 260 }}><TextField label={<span className="visually-hidden">{t("common:search")}</span>} value={filter} onChange={setFilter} placeholder={t("common:search")} /></div></div>
            <div className="card__body stack">
              {Object.entries(groups).map(([g, params]) => (
                <details key={g} open={g === "vehicle" || Boolean(filter)}>
                  <summary style={{ cursor: "pointer", fontWeight: 600, padding: "var(--me-space-2) 0" }}>{t(`domain:paramGroup.${g}`)} <span className="subtle">({params.length})</span></summary>
                  <div className="table-wrap"><table className="table"><tbody>{params.map((p) => (
                    <tr key={p.key}><td>{paramLabel(t, p.key)}</td><td className="num mono">{Array.isArray(p.value) ? p.value.map((v) => fmt(v, lang)).join(", ") : typeof p.value === "number" ? fmt(p.value, lang, 4) : String(p.value)}</td>
                      <td className="subtle">{p.unit}</td><td className="subtle mono">{p.key}</td></tr>
                  ))}</tbody></table></div>
                </details>
              ))}
            </div></div>
        </>
      ) : null}
    </div>
  );
}
