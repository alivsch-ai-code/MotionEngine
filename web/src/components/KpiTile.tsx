import { memo } from "react";

import { fmt } from "../lib/format";

export const KpiTile = memo(function KpiTile({ label, value, unit, lang, badge }:
  { label: string; value: number | string | null; unit?: string; lang: string; badge?: "ok" | "warn" | "fail" | "" }) {
  const shown = typeof value === "number" ? fmt(value, lang) : value ?? "–";
  return (
    <div className="kpi">
      <div className="row row--between">
        <div className="kpi__label" title={label}>{label}</div>
        {badge === "warn" ? <span className="badge badge--warning">!</span> : badge === "fail" ? <span className="badge badge--danger">✕</span> : null}
      </div>
      <div className="kpi__value">{shown}{unit && unit !== "-" ? <span className="kpi__unit">{unit}</span> : null}</div>
    </div>
  );
});
