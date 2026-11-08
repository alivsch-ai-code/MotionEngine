import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { ApiError } from "../lib/api";
import { Icon } from "./Icon";

export function ErrorAlert({ error }: { error: unknown }) {
  const { t } = useTranslation();
  if (!error) return null;
  const key = error instanceof ApiError ? error.key : "errors.unknown";
  const detail = error instanceof ApiError ? error.detail : String(error);
  const settingsHint = error instanceof ApiError && ["errors.network", "errors.unauthorized"].includes(error.key);
  return (
    <div className="alert alert--danger" role="alert">
      <span style={{ color: "var(--me-danger)" }}><Icon name="alert" /></span>
      <div className="stack stack--sm">
        <strong>{t(key)}</strong>
        {detail ? <span className="subtle mono">{detail}</span> : null}
        {settingsHint ? <Link to="/app/settings">{t("errors.checkSettings")}</Link> : null}
      </div>
    </div>
  );
}
