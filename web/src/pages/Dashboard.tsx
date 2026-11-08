import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { EmptyState, Skeleton } from "../components/EmptyState";
import { Icon, type IconName } from "../components/Icon";
import { PageHeader } from "../components/PageHeader";
import { useClient, useQuery } from "../lib/hooks";
import { fmt } from "../lib/format";
import { maneuverLabel, modelLabel } from "../lib/domain";
import { readRecentRuns } from "./recentRuns";

const ACTIONS: { to: string; icon: IconName; key: string }[] = [
  { to: "/app/simulate", icon: "play", key: "simulate" },
  { to: "/app/inspector", icon: "sigma", key: "inspector" },
  { to: "/app/models", icon: "brain", key: "models" },
  { to: "/app/vehicles", icon: "car", key: "vehicles" },
];

export default function Dashboard() {
  const { t, i18n } = useTranslation(["app", "common"]);
  const client = useClient();
  const health = useQuery((s) => client.health(s), [client]);
  const catalog = useQuery((s) => client.catalog(s), [client]);
  const models = useQuery((s) => client.models(s), [client]);
  const runs = readRecentRuns();
  const offline = Boolean(health.error);

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("dashboard.title")} description={t("dashboard.subtitle")}
        actions={<Link className="btn btn--primary" to="/app/simulate"><Icon name="play" />{t("dashboard.startSimulation")}</Link>} />

      {offline ? (
        <div className="card"><EmptyState art="api" title={t("empty.api.title")} text={t("empty.api.text")}
          action={<Link className="btn btn--primary" to="/app/settings">{t("empty.api.action")}</Link>} /></div>
      ) : null}

      <div className="grid grid--4">
        <div className="kpi"><div className="kpi__label">{t("dashboard.stats.api")}</div>
          <div className="kpi__value">{health.loading ? <Skeleton height={28} width={90} /> : health.data ? `v${health.data.version}` : "–"}</div></div>
        <div className="kpi"><div className="kpi__label">{t("dashboard.stats.vehicles")}</div>
          <div className="kpi__value">{catalog.data?.presets.length ?? "–"}</div></div>
        <div className="kpi"><div className="kpi__label">{t("dashboard.stats.models")}</div>
          <div className="kpi__value">{catalog.data ? catalog.data.vehicle_models.length : "–"}</div></div>
        <div className="kpi"><div className="kpi__label">{t("dashboard.stats.neural")}</div>
          <div className="kpi__value">{models.data?.length ?? "–"}</div></div>
      </div>

      <section className="stack" aria-labelledby="quick">
        <h2 id="quick">{t("dashboard.quickActions")}</h2>
        <div className="grid grid--4">
          {ACTIONS.map((a) => (
            <Link key={a.to} to={a.to} className="card card--interactive">
              <div className="card__body stack stack--sm">
                <span style={{ color: "var(--me-accent)" }}><Icon name={a.icon} size={22} /></span>
                <h3>{t(`dashboard.actions.${a.key}.title`)}</h3>
                <p className="subtle">{t(`dashboard.actions.${a.key}.text`)}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <div className="grid grid--2">
        <section className="card" aria-labelledby="recent">
          <div className="card__header"><h2 id="recent">{t("dashboard.recent")}</h2></div>
          <div className="card__body">
            {runs.length === 0 ? (
              <EmptyState art="results" title={t("empty.results.title")} text={t("empty.results.text")}
                action={<Link className="btn btn--secondary" to="/app/simulate">{t("empty.results.action")}</Link>} />
            ) : (
              <div className="table-wrap"><table className="table">
                <thead><tr><th>{t("dashboard.table.maneuver")}</th><th>{t("dashboard.table.model")}</th><th className="num">{t("dashboard.table.maxAy")}</th><th className="num">{t("dashboard.table.wall")}</th></tr></thead>
                <tbody>{runs.map((r) => (
                  <tr key={r.at}><td>{maneuverLabel(t, r.maneuver)}</td><td>{modelLabel(t, r.model)}</td>
                    <td className="num">{fmt(r.maxAy, i18n.language)} m/s²</td><td className="num">{fmt(r.wall, i18n.language)} s</td></tr>
                ))}</tbody>
              </table></div>
            )}
          </div>
        </section>
        <section className="card" aria-labelledby="start">
          <div className="card__header"><h2 id="start">{t("dashboard.gettingStarted.title")}</h2></div>
          <div className="card__body">
            <ol className="stack" style={{ margin: 0, paddingLeft: "1.2rem" }}>
              {(["connect", "simulate", "inspect", "learn"] as const).map((k) => (
                <li key={k}><strong>{t(`dashboard.gettingStarted.${k}.title`)}</strong><p className="subtle">{t(`dashboard.gettingStarted.${k}.text`)}</p></li>
              ))}
            </ol>
          </div>
        </section>
      </div>
    </div>
  );
}
