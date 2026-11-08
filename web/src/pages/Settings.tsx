import { useState } from "react";
import { useTranslation } from "react-i18next";

import { ErrorAlert } from "../components/ErrorAlert";
import { SelectField, TextField } from "../components/Field";
import { Icon } from "../components/Icon";
import { PageHeader } from "../components/PageHeader";
import { LANGUAGES } from "../i18n";
import { createClient, type Health } from "../lib/api";
import { useSettings, type Theme } from "../lib/settings";

export default function Settings() {
  const { t, i18n } = useTranslation(["app", "common"]);
  const settings = useSettings();
  const [apiBase, setApiBase] = useState(settings.apiBase);
  const [apiKey, setApiKey] = useState(settings.apiKey);
  const [test, setTest] = useState<{ ok?: Health; error?: unknown; loading?: boolean }>({});
  const check = async () => {
    setTest({ loading: true });
    try {
      setTest({ ok: await createClient({ apiBase, apiKey }).catalog().then(() => createClient({ apiBase, apiKey }).health()) });
    } catch (error) {
      setTest({ error });
    }
  };
  return (
    <div className="stack stack--lg" style={{ maxWidth: 760 }}>
      <PageHeader title={t("settings.title")} description={t("settings.subtitle")} />
      <form className="card" onSubmit={(e) => { e.preventDefault(); settings.update({ apiBase, apiKey }); void check(); }}>
        <div className="card__header"><h2>{t("settings.api.title")}</h2></div>
        <div className="card__body stack">
          <TextField label={t("settings.api.url")} value={apiBase} onChange={setApiBase} placeholder="https://motionengine.example.com" hint={t("settings.api.urlHint")} />
          <TextField label={t("settings.api.key")} value={apiKey} onChange={setApiKey} type="password" hint={t("settings.api.keyHint")} />
          <div className="row">
            <button type="submit" className="btn btn--primary">{test.loading ? <span className="spinner" /> : <Icon name="check" />}{t("settings.api.save")}</button>
            {test.ok ? <span className="badge badge--success"><span className="dot" />{t("settings.api.connected", { version: test.ok.version })}</span> : null}
          </div>
          <ErrorAlert error={test.error} />
        </div>
      </form>
      <div className="card">
        <div className="card__header"><h2>{t("settings.appearance")}</h2></div>
        <div className="card__body grid grid--2">
          <SelectField label={t("settings.language")} value={i18n.resolvedLanguage ?? "en"} onChange={(v) => void i18n.changeLanguage(v)}
            options={LANGUAGES.map((l) => ({ value: l.code, label: l.label }))} hint={t("settings.languageHint")} />
          <SelectField<Theme> label={t("settings.theme")} value={settings.theme} onChange={(v) => settings.update({ theme: v })}
            options={[{ value: "dark", label: t("settings.themes.dark") }, { value: "light", label: t("settings.themes.light") }]} />
        </div>
      </div>
    </div>
  );
}
