import { Suspense, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";

import { ApiStatus, LanguageSwitcher, ThemeToggle } from "../components/HeaderControls";
import { Icon, type IconName } from "../components/Icon";
import { TrainingProvider, useTraining } from "../lib/training";
import { LogoMark, Wordmark } from "../components/Logo";
import { PageSkeleton } from "../components/PageSkeleton";

const NAV: { section: string; items: { to: string; key: string; icon: IconName; end?: boolean }[] }[] = [
  { section: "nav.sections.overview", items: [{ to: "/app", key: "nav.dashboard", icon: "dashboard", end: true }] },
  { section: "nav.sections.work", items: [
    { to: "/app/assistant", key: "nav.assistant", icon: "chat" },
    { to: "/app/simulate", key: "nav.simulate", icon: "play" },
    { to: "/app/inspector", key: "nav.inspector", icon: "sigma" },
    { to: "/app/parking", key: "nav.parking", icon: "parking" },
    { to: "/app/predict", key: "nav.predict", icon: "radar" },
  ] },
  { section: "nav.sections.models", items: [
    { to: "/app/vehicles", key: "nav.vehicles", icon: "car" },
    { to: "/app/models", key: "nav.models", icon: "brain" },
  ] },
  { section: "nav.sections.system", items: [
    { to: "/app/settings", key: "nav.settings", icon: "settings" },
    { to: "/app/design", key: "nav.design", icon: "palette" },
  ] },
];

function TrainingBadge() {
  const { t } = useTranslation();
  const { job } = useTraining();
  if (!job || !["queued", "running", "done"].includes(job.state)) return null;
  const done = job.state === "done";
  return (
    <Link to="/app/models" className={`badge ${done ? "badge--success" : "badge--info"} training-badge`} aria-live="polite"
      title={job.name ?? ""}>
      {done ? <Icon name="check" size={14} /> : <span className="spinner spinner--sm" aria-hidden="true" />}
      {done ? t("header.trainingDone") : t("header.training", { pct: Math.round(job.progress * 100) })}
    </Link>
  );
}

export function AppShell() {
  return <TrainingProvider><Shell /></TrainingProvider>;
}

function Shell() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const location = useLocation();
  useEffect(() => setOpen(false), [location.pathname]);
  return (
    <div className="shell">
      <a href="#main" className="skip-link">{t("a11y.skipToContent")}</a>
      <header className="shell__header">
        <button type="button" className="btn btn--ghost btn--icon menu-button" aria-expanded={open} aria-controls="app-nav"
          aria-label={t("header.menu")} onClick={() => setOpen((o) => !o)}><Icon name="menu" /></button>
        <Link to="/" className="shell__brand" aria-label={t("header.home")}><LogoMark /><Wordmark /></Link>
        <div className="grow" />
        <TrainingBadge />
        <ApiStatus />
        <LanguageSwitcher />
        <ThemeToggle />
        <a className="btn btn--ghost btn--icon hide-mobile" href="/docs" target="_blank" rel="noreferrer" aria-label={t("header.apiDocs")} title={t("header.apiDocs")}>
          <Icon name="book" />
        </a>
      </header>
      <nav id="app-nav" className="shell__nav" data-open={open} aria-label={t("nav.label")}>
        {NAV.map((group) => (
          <div key={group.section}>
            <div className="nav-section">{t(group.section)}</div>
            {group.items.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className="nav-link">
                <Icon name={item.icon} />{t(item.key)}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <main id="main" className="shell__main" tabIndex={-1}>
        <div className="shell__content">
          <Suspense fallback={<PageSkeleton />}><Outlet /></Suspense>
        </div>
      </main>
    </div>
  );
}
