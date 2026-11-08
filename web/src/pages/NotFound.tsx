import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";

export default function NotFound() {
  const { t } = useTranslation("app");
  return (
    <div className="card" style={{ margin: "var(--me-space-7) auto", maxWidth: 640 }}>
      <h1 className="visually-hidden">{t("notFound.title")}</h1>
      <EmptyState art="scenario" title={t("notFound.title")} text={t("notFound.text")}
        action={<Link className="btn btn--primary" to="/app">{t("notFound.action")}</Link>} />
    </div>
  );
}
