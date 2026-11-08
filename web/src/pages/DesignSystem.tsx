import { lazy, Suspense, useState } from "react";
import { useTranslation } from "react-i18next";

import { EmptyState, Skeleton } from "../components/EmptyState";
import { NumberField, SelectField } from "../components/Field";
import { Icon } from "../components/Icon";
import { KpiTile } from "../components/KpiTile";
import { LogoMark, Wordmark } from "../components/Logo";
import { PageHeader } from "../components/PageHeader";
import { InfoTip } from "../components/Tooltip";

const Chart = lazy(() => import("../components/Chart"));
const COLORS = ["--me-brand-primary", "--me-brand-secondary", "--me-brand-accent", "--me-bg", "--me-surface", "--me-surface-2", "--me-border",
  "--me-text", "--me-text-muted", "--me-primary", "--me-success", "--me-warning", "--me-danger", "--me-chart-1", "--me-chart-2", "--me-chart-3",
  "--me-chart-4", "--me-chart-5", "--me-chart-6"];
const TYPE = [["--me-text-4xl", "4xl"], ["--me-text-3xl", "3xl"], ["--me-text-2xl", "2xl"], ["--me-text-xl", "xl"], ["--me-text-lg", "lg"], ["--me-text-md", "md"],
  ["--me-text-sm", "sm"], ["--me-text-xs", "xs"]];
const SPACE = [1, 2, 3, 4, 5, 6, 7, 8];
const X = Array.from({ length: 50 }, (_, i) => i / 10);

export default function DesignSystem() {
  const { t, i18n } = useTranslation(["app", "common"]);
  const [n, setN] = useState(42);
  const [sel, setSel] = useState("a");
  return (
    <div className="stack stack--lg">
      <PageHeader title={t("design.title")} description={t("design.subtitle")} />
      <section className="card"><div className="card__header"><h2>{t("design.brand")}</h2></div>
        <div className="card__body row" style={{ gap: "var(--me-space-6)" }}>
          <div className="row" style={{ fontSize: "var(--me-text-xl)" }}><LogoMark size={40} /><Wordmark /></div>
          <img src="/brand/motionengine-logo-light.svg" alt={t("design.logoLight")} height={40} style={{ background: "#fff", padding: 8, borderRadius: 8 }} />
          <img src="/brand/motionengine-logo-dark.svg" alt={t("design.logoDark")} height={40} style={{ background: "#0B1120", padding: 8, borderRadius: 8 }} />
          <img src="/icon-192.png" alt={t("design.appIcon")} width={56} height={56} />
        </div></section>
      <section className="card"><div className="card__header"><h2>{t("design.colors")}</h2></div>
        <div className="card__body grid grid--4">{COLORS.map((c) => (
          <div key={c} className="row"><span style={{ width: 36, height: 36, borderRadius: 8, background: `var(${c})`, border: "1px solid var(--me-border-strong)" }} />
            <code className="subtle">{c}</code></div>
        ))}</div></section>
      <div className="grid grid--2">
        <section className="card"><div className="card__header"><h2>{t("design.typography")}</h2></div>
          <div className="card__body stack stack--sm">{TYPE.map(([v, n]) => (
            <div key={v} className="row"><code className="subtle" style={{ width: 40 }}>{n}</code><span style={{ fontSize: `var(${v})`, lineHeight: 1.2 }}>{t("design.sample")}</span></div>
          ))}<p className="mono">{t("design.mono")}</p></div></section>
        <section className="card"><div className="card__header"><h2>{t("design.spacing")}</h2></div>
          <div className="card__body stack stack--sm">{SPACE.map((s) => (
            <div key={s} className="row"><code className="subtle" style={{ width: 80 }}>--me-space-{s}</code><span style={{ height: 12, width: `var(--me-space-${s})`, background: "var(--me-primary)", borderRadius: 2 }} /></div>
          ))}</div></section>
      </div>
      <section className="card"><div className="card__header"><h2>{t("design.buttons")}</h2></div>
        <div className="card__body row">
          <button type="button" className="btn btn--primary"><Icon name="play" />{t("design.primary")}</button>
          <button type="button" className="btn btn--secondary">{t("design.secondary")}</button>
          <button type="button" className="btn btn--ghost">{t("design.ghost")}</button>
          <button type="button" className="btn btn--danger"><Icon name="trash" />{t("design.danger")}</button>
          <button type="button" className="btn btn--primary" disabled>{t("design.disabled")}</button>
          <button type="button" className="btn btn--secondary btn--sm">{t("design.small")}</button>
          <span className="badge badge--success"><span className="dot" />{t("design.badges.success")}</span>
          <span className="badge badge--warning">{t("design.badges.warning")}</span>
          <span className="badge badge--danger">{t("design.badges.danger")}</span>
          <span className="badge badge--info">{t("design.badges.info")}</span>
          <InfoTip text={t("design.tooltip")} />
        </div></section>
      <div className="grid grid--2">
        <section className="card"><div className="card__header"><h2>{t("design.forms")}</h2></div>
          <div className="card__body stack">
            <NumberField label={t("design.numberField")} unit="m/s" value={n} onChange={setN} tip={t("design.tooltip")} hint={t("design.hint")} />
            <SelectField label={t("design.selectField")} value={sel} onChange={setSel} options={[{ value: "a", label: "A" }, { value: "b", label: "B" }]} />
            <details className="expert"><summary><Icon name="settings" />{t("common:expertSettings")}</summary><p className="subtle">{t("design.expertText")}</p></details>
          </div></section>
        <section className="card"><div className="card__header"><h2>{t("design.kpis")}</h2></div>
          <div className="card__body grid grid--2">
            <KpiTile label={t("design.kpiA")} value={5.42} unit="m/s²" lang={i18n.language} />
            <KpiTile label={t("design.kpiB")} value={0.031} unit="m" lang={i18n.language} badge="warn" />
            <Skeleton height={84} /><div className="progress" style={{ alignSelf: "center" }}><span style={{ width: "62%" }} /></div>
          </div></section>
      </div>
      <section className="card"><div className="card__header"><h2>{t("design.table")}</h2></div>
        <div className="card__body table-wrap"><table className="table">
          <thead><tr><th>{t("design.col.name")}</th><th className="num">{t("design.col.value")}</th><th>{t("design.col.unit")}</th></tr></thead>
          <tbody><tr><td>m</td><td className="num">1 600</td><td className="subtle">kg</td></tr><tr><td>l</td><td className="num">2.80</td><td className="subtle">m</td></tr></tbody>
        </table></div></section>
      <section className="card"><div className="card__header"><h2>{t("design.charts")}</h2></div>
        <div className="card__body"><Suspense fallback={<Skeleton height={220} />}>
          <Chart x={X} xLabel="t [s]" yLabel="–" height={220} ariaLabel={t("design.charts")}
            series={[0, 1, 2, 3, 4, 5].map((k) => ({ label: `${k + 1}`, values: X.map((x) => Math.sin(x + k * 0.6)), color: k }))} />
        </Suspense></div></section>
      <section className="card"><div className="card__header"><h2>{t("design.emptyStates")}</h2></div>
        <div className="card__body grid grid--3">
          <EmptyState art="simulation" title={t("empty.simulation.title")} text={t("empty.simulation.text")} />
          <EmptyState art="api" title={t("empty.api.title")} text={t("empty.api.text")} />
          <EmptyState art="model" title={t("empty.models.title")} text={t("empty.models.text")} />
        </div></section>
    </div>
  );
}
