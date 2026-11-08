import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { EmptyState, Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { NumberField, SelectField } from "../components/Field";
import { Icon } from "../components/Icon";
import { PageHeader } from "../components/PageHeader";
import { PathPlot, type Box, type Polyline } from "../components/PathPlot";
import type { ObjectSpec } from "../lib/api";
import { useClient, useMutation, usePersistentState } from "../lib/hooks";

type Predictor = "constant_velocity" | "constant_acceleration" | "ctrv";
interface Row { id: number; x: number; y: number; psiDeg: number; v: number; a: number; yawRateDeg: number }
const DEFAULT_ROWS: Row[] = [
  { id: 1, x: 0, y: 0, psiDeg: 0, v: 15, a: 0, yawRateDeg: 0 },
  { id: 2, x: 10, y: 3.5, psiDeg: 0, v: 20, a: -2, yawRateDeg: 0 },
  { id: 3, x: 5, y: -3.5, psiDeg: 5, v: 12, a: 0.5, yawRateDeg: 6 },
];
const rad = (d: number) => (d * Math.PI) / 180;

export default function Predict() {
  const { t } = useTranslation(["app", "common"]);
  const client = useClient();
  const [rows, setRows] = usePersistentState<Row[]>("me.predict.rows", DEFAULT_ROWS);
  const [predictor, setPredictor] = usePersistentState<Predictor>("me.predict.predictor", "ctrv");
  const [horizon, setHorizon] = usePersistentState<number>("me.predict.horizon", 5);
  const pred = useMutation((objects: ObjectSpec[]) => client.predict({ predictor, horizon, dt: 0.1, objects }));
  const update = (i: number, patch: Partial<Row>) => setRows(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  const run = () => void pred.run(rows.map((r) => ({ id: r.id, x: r.x, y: r.y, psi: rad(r.psiDeg), v: Math.max(r.v, 0), a: r.a, yaw_rate: rad(r.yawRateDeg) })));

  const plot = useMemo(() => {
    if (!pred.data) return null;
    const lines: Polyline[] = pred.data.objects.map((o) => ({ x: o.x, y: o.y, kind: "prediction" }));
    const boxes: Box[] = pred.data.objects.map((o) => ({ x: o.x[0], y: o.y[0], psi: o.psi[0], length: o.length, width: o.width, kind: "object" }));
    return { lines, boxes };
  }, [pred.data]);

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("predict.title")} description={t("predict.subtitle")} />
      <div className="card"><div className="card__body stack">
        <div className="grid grid--3">
          <SelectField label={t("predict.model")} value={predictor} onChange={setPredictor} tip={t("predict.modelTip")}
            options={(["constant_velocity", "constant_acceleration", "ctrv"] as const).map((p) => ({ value: p, label: t(`predict.models.${p}`) }))} />
          <NumberField label={t("predict.horizon")} unit="s" value={horizon} min={0.5} max={20} onChange={setHorizon} />
        </div>
        <div className="table-wrap"><table className="table">
          <thead><tr><th>ID</th><th>x [m]</th><th>y [m]</th><th>ψ [°]</th><th>v [m/s]</th><th>a [m/s²]</th><th>ψ̇ [°/s]</th><th><span className="visually-hidden">{t("common:actions")}</span></th></tr></thead>
          <tbody>{rows.map((r, i) => (
            <tr key={r.id}><td>{r.id}</td>
              {(["x", "y", "psiDeg", "v", "a", "yawRateDeg"] as const).map((k) => (
                <td key={k}><input className="input" style={{ height: 30, maxWidth: 96 }} type="number" step="any" aria-label={`${k} ${r.id}`}
                  value={r[k]} onChange={(e) => update(i, { [k]: e.target.valueAsNumber || 0 })} /></td>
              ))}
              <td><button type="button" className="btn btn--ghost btn--icon btn--sm" aria-label={t("predict.remove", { id: r.id })}
                onClick={() => setRows(rows.filter((_, j) => j !== i))}><Icon name="trash" /></button></td></tr>
          ))}</tbody>
        </table></div>
        <div className="row">
          <button type="button" className="btn btn--secondary btn--sm" onClick={() => setRows([...rows, { id: Math.max(0, ...rows.map((r) => r.id)) + 1, x: 0, y: 0, psiDeg: 0, v: 10, a: 0, yawRateDeg: 0 }])}>
            {t("predict.add")}</button>
          <div className="grow" />
          <button type="button" className="btn btn--primary" disabled={pred.loading || rows.length === 0} onClick={run}>
            {pred.loading ? <span className="spinner" /> : <Icon name="radar" />}{t("predict.run")}</button>
        </div>
      </div></div>
      <ErrorAlert error={pred.error} />
      {pred.loading && !plot ? <Skeleton height={320} /> : null}
      {plot ? (
        <div className="card"><div className="card__header"><h2>{t("predict.result")}</h2></div>
          <div className="card__body"><PathPlot lines={plot.lines} boxes={plot.boxes} height={360} ariaLabel={t("predict.result")} /></div></div>
      ) : !pred.loading && !pred.error ? (
        <div className="card"><EmptyState art="scenario" title={t("empty.prediction.title")} text={t("empty.prediction.text")}
          action={<button type="button" className="btn btn--primary" onClick={run}>{t("empty.prediction.action")}</button>} /></div>
      ) : null}
    </div>
  );
}
