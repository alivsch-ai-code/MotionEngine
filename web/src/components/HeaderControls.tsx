import { useTranslation } from "react-i18next";

import { LANGUAGES } from "../i18n";
import { useQuery, useClient } from "../lib/hooks";
import { useSettings } from "../lib/settings";
import { Icon } from "./Icon";

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  const current = i18n.resolvedLanguage ?? "en";
  return (
    <div className="segmented" role="group" aria-label={t("header.language")}>
      {LANGUAGES.map((l) => (
        <button key={l.code} type="button" lang={l.code} aria-pressed={current === l.code} title={l.label}
          onClick={() => void i18n.changeLanguage(l.code)}>{l.code.toUpperCase()}</button>
      ))}
    </div>
  );
}

export function ThemeToggle() {
  const { t } = useTranslation();
  const { theme, update } = useSettings();
  const next = theme === "dark" ? "light" : "dark";
  return (
    <button type="button" className="btn btn--ghost btn--icon" onClick={() => update({ theme: next })}
      aria-label={t(next === "light" ? "header.lightMode" : "header.darkMode")} title={t(next === "light" ? "header.lightMode" : "header.darkMode")}>
      <Icon name={theme === "dark" ? "sun" : "moon"} />
    </button>
  );
}

export function ApiStatus() {
  const { t } = useTranslation();
  const client = useClient();
  const { data, error, loading } = useQuery((s) => client.health(s), [client]);
  const state = loading ? "checking" : error ? "offline" : "online";
  const cls = state === "online" ? "badge--success" : state === "offline" ? "badge--danger" : "";
  return (
    <span className={`badge ${cls}`} title={data ? `MotionEngine API ${data.version}` : undefined} role="status">
      <span className="dot" />{t(`header.api.${state}`)}
    </span>
  );
}
