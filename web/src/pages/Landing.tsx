import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { LanguageSwitcher, ThemeToggle } from "../components/HeaderControls";
import { Icon, type IconName } from "../components/Icon";
import { LogoMark, Wordmark } from "../components/Logo";

const FEATURES: { key: string; icon: IconName }[] = [
  { key: "planning", icon: "route" }, { key: "explain", icon: "sigma" }, { key: "dynamics", icon: "car" },
  { key: "learning", icon: "brain" }, { key: "prediction", icon: "radar" }, { key: "api", icon: "code" },
];
const PIPELINE = ["perception", "prediction", "behavior", "planner", "controller", "vehicle"] as const;

const QUINTIC = "d(t) = c₀ + c₁t + … + c₅t⁵";
const CURL = `curl -X POST https://your-host/plan/explain \\
  -H "Content-Type: application/json" -H "X-API-Key: $KEY" \\
  -d '{"target_offset": 3.5, "target_speed": 20, "ego": {"vx": 20}}'`;
const PYTHON = `from vdsim.simulation.scenario import Scenario
from vdsim.simulation.simulator import Simulator

result = Simulator.from_scenario(Scenario(
    model="double_track", maneuver="iso_double_lane_change")).run()`;

export default function Landing() {
  const { t } = useTranslation(["landing", "common"]);
  return (
    <div className="landing">
      <header className="landing__nav">
        <Link to="/" className="shell__brand" aria-label="MotionEngine"><LogoMark size={32} /><Wordmark /></Link>
        <nav className="row hide-mobile" aria-label={t("nav.label")}>
          <a className="btn btn--ghost" href="#features">{t("nav.features")}</a>
          <a className="btn btn--ghost" href="#architecture">{t("nav.architecture")}</a>
          <a className="btn btn--ghost" href="#api">{t("nav.api")}</a>
          <a className="btn btn--ghost" href="#docs">{t("nav.docs")}</a>
        </nav>
        <div className="row"><LanguageSwitcher /><ThemeToggle /><Link className="btn btn--primary" to="/app">{t("cta.open")}</Link></div>
      </header>

      <main>
        <section className="hero grid grid--2" style={{ alignItems: "center" }}>
          <div>
            <span className="badge badge--info">{t("hero.badge")}</span>
            <h1 style={{ marginTop: "var(--me-space-4)" }}>{t("hero.title")}</h1>
            <p>{t("hero.text")}</p>
            <div className="row">
              <Link className="btn btn--primary btn--lg" to="/app/simulate"><Icon name="play" />{t("cta.simulate")}</Link>
              <Link className="btn btn--secondary btn--lg" to="/app/inspector"><Icon name="sigma" />{t("cta.inspect")}</Link>
            </div>
          </div>
          <HeroArt />
        </section>

        <section id="features" className="stack stack--lg" aria-labelledby="features-title">
          <h2 id="features-title" className="section-title">{t("features.title")}</h2>
          <div className="grid grid--3">
            {FEATURES.map((f) => (
              <div key={f.key} className="card feature"><div className="card__body stack stack--sm">
                <Icon name={f.icon} size={28} /><h3>{t(`features.${f.key}.title`)}</h3><p className="muted">{t(`features.${f.key}.text`)}</p>
              </div></div>
            ))}
          </div>
        </section>

        <section className="stack stack--lg" aria-labelledby="screens-title">
          <h2 id="screens-title" className="section-title">{t("screens.title")}</h2>
          <div className="grid grid--2">
            {(["inspector", "simulate"] as const).map((s) => (
              <figure key={s} className="stack stack--sm" style={{ margin: 0 }}>
                <img className="screenshot" src={`/screenshots/${s}-dark.png`} alt={t(`screens.${s}`)} loading="lazy" width={1440} height={900} />
                <figcaption className="subtle">{t(`screens.${s}`)}</figcaption>
              </figure>
            ))}
          </div>
        </section>

        <section id="architecture" className="stack stack--lg" aria-labelledby="arch-title">
          <h2 id="arch-title" className="section-title">{t("architecture.title")}</h2>
          <p className="muted" style={{ maxWidth: "70ch" }}>{t("architecture.text")}</p>
          <div className="row" style={{ gap: "var(--me-space-2)" }} role="list">
            {PIPELINE.map((p, i) => (
              <div key={p} className="row" role="listitem" style={{ gap: "var(--me-space-2)" }}>
                <div className="card" style={{ padding: "var(--me-space-3) var(--me-space-4)" }}><strong>{t(`architecture.blocks.${p}`)}</strong></div>
                {i < PIPELINE.length - 1 ? <span className="muted"><Icon name="arrowRight" /></span> : null}
              </div>
            ))}
          </div>
          <div className="grid grid--3">
            {(["library", "service", "web"] as const).map((k) => (
              <div key={k} className="card"><div className="card__body stack stack--sm"><h3>{t(`architecture.layers.${k}.title`)}</h3><p className="muted">{t(`architecture.layers.${k}.text`)}</p></div></div>
            ))}
          </div>
        </section>

        <section id="api" className="stack stack--lg" aria-labelledby="api-title">
          <h2 id="api-title" className="section-title">{t("api.title")}</h2>
          <p className="muted" style={{ maxWidth: "70ch" }}>{t("api.text")}</p>
          <div className="grid grid--2">
            <div className="stack stack--sm"><h3>{t("api.rest")}</h3><div className="code-block">{CURL}</div></div>
            <div className="stack stack--sm"><h3>{t("api.python")}</h3><div className="code-block">{PYTHON}</div></div>
          </div>
        </section>

        <section id="docs" className="stack stack--lg" aria-labelledby="docs-title">
          <h2 id="docs-title" className="section-title">{t("docs.title")}</h2>
          <div className="grid grid--3">
            <a className="card card--interactive" href="/docs"><div className="card__body stack stack--sm"><Icon name="book" /><h3>{t("docs.openapi.title")}</h3><p className="muted">{t("docs.openapi.text")}</p></div></a>
            <a className="card card--interactive" href="https://github.com/alivsch-ai-code/MotionEngine/tree/main/docs"><div className="card__body stack stack--sm"><Icon name="layers" /><h3>{t("docs.theory.title")}</h3><p className="muted">{t("docs.theory.text")}</p></div></a>
            <a className="card card--interactive" href="https://github.com/alivsch-ai-code/MotionEngine"><div className="card__body stack stack--sm"><Icon name="github" /><h3>{t("docs.source.title")}</h3><p className="muted">{t("docs.source.text")}</p></div></a>
          </div>
        </section>
      </main>
      <footer className="footer"><section className="row row--between" style={{ paddingTop: "var(--me-space-5)", paddingBottom: "var(--me-space-5)" }}>
        <span>{t("footer.license")}</span><Link to="/app">{t("cta.open")}</Link>
      </section></footer>
    </div>
  );
}

// Hero illustration: a road with the sampled candidate set and the selected quintic lane change.
function HeroArt() {
  const { t } = useTranslation("landing");
  const candidates = [-3.5, -1.75, 1.75, 5.25, 7].map((d) => `M20 200 C150 200 170 ${200 - d * 18} 300 ${200 - d * 18} H460`);
  return (
    <svg viewBox="0 0 480 300" role="img" aria-label={t("hero.art")} style={{ width: "100%", height: "auto" }}>
      <rect x="0" y="40" width="480" height="220" rx="16" fill="var(--me-surface)" stroke="var(--me-border)" />
      {[105, 170, 235].map((y, i) => <path key={y} d={`M0 ${y} H480`} stroke="var(--me-border-strong)" strokeDasharray={i === 1 ? "14 12" : undefined} />)}
      {candidates.map((d, i) => <path key={i} d={d} fill="none" stroke="var(--me-chart-6)" strokeOpacity="0.35" strokeWidth="2" />)}
      <path d="M20 200 C150 200 170 137 300 137 H460" fill="none" stroke="var(--me-primary)" strokeWidth="5" strokeLinecap="round" />
      <rect x="8" y="188" width="44" height="24" rx="6" fill="var(--me-primary-strong)" />
      <rect x="330" y="188" width="54" height="26" rx="6" fill="var(--me-warning)" />
      <text x="24" y="282" fill="var(--me-text-muted)" fontSize="13" fontFamily="var(--me-font-mono)">{QUINTIC}</text>
    </svg>
  );
}
