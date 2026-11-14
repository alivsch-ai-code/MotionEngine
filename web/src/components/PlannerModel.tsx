// Detail view of a trajectory planner model: how often the network path solves a cycle, how close it is to
// its teacher (the Werling planner), and a closed-loop drive of both planners through one situation.
import { lazy, Suspense, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import type { DriveResult, ModelMeta, PlanRequest } from "../lib/api";
import { fmt } from "../lib/format";
import { useClient, useMutation } from "../lib/hooks";
import { useStack } from "../lib/stack";
import { Skeleton } from "./EmptyState";
import { ErrorAlert } from "./ErrorAlert";
import { Icon } from "./Icon";
import { KpiTile } from "./KpiTile";
import { PathPlot, type Box, type Polyline } from "./PathPlot";

const Chart = lazy(() => import("./Chart"));
const TARGETS = ["lat_delta", "lat_tau", "lon_nu", "lon_tau"] as const;
const straight = [{ kind: "straight" as const, length: 500 }];
const PRESETS: Record<string, PlanRequest> = {
  overtake: { road: straight, ego: { x: 0, y: 0, psi: 0, vx: 22 }, target_speed: 22, d_min: -1.75, d_max: 5.25, obstacles: [{ id: 1, x: 70, y: 0, v: 8 }] },
  laneChange: { road: straight, ego: { x: 0, y: -3.5, psi: 0, vx: 25 }, target_speed: 25, d_min: -5.25, d_max: 1.75, obstacles: [{ id: 1, x: 40, y: -3.5, v: 20 }] },
  curve: { road: [{ kind: "straight", length: 40 }, { kind: "arc", length: 260, curvature: 1 / 150 }, { kind: "straight", length: 200 }],
    ego: { x: 0, y: 0.4, psi: 0, vx: 18 }, target_speed: 20, d_min: -1.75, d_max: 5.25, obstacles: [] },
  slowTraffic: { road: straight, ego: { x: 0, y: 0, psi: 0, vx: 28 }, target_speed: 28, d_min: -1.75, d_max: 1.75, obstacles: [{ id: 1, x: 120, y: 0, v: 14 }] },
};

export function PlannerModel({ model }: { model: ModelMeta }) {
  const { t, i18n } = useTranslation(["app", "common"]);
  const lang = i18n.language;
  const client = useClient();
  const navigate = useNavigate();
  const [stack, setStack] = useStack();
  const [seed, setSeed] = useState(1);
  const [label, setLabel] = useState("");
  const drive = useMutation((body: { situation?: PlanRequest; seed?: number }) => client.drive(model.id, { ...body, cycles: 80 }));
  const m = model.planner_metrics;
  const pct = (v: number | null | undefined) => (v === null || v === undefined ? null : v * 100);
  const useInWorkbench = () => {
    setStack({ ...stack, planner: { component: "trajectory_planner/learned", paramsText: JSON.stringify({ model: model.id }, null, 1) } });
    navigate("/app/workbench");
  };

  return (
    <div className="stack">
      <div className="row">
        <span className="badge badge--info">{t(`models.approaches.${model.approach ?? "regression"}`, { defaultValue: model.approach ?? "" })}</span>
        {model.situations ? <span className="subtle">{t("plannerModel.situations", { vmin: fmt(model.situations.speed_min, lang, 3), vmax: fmt(model.situations.speed_max, lang, 3),
          objects: model.situations.max_objects, curves: fmt(model.situations.curve_share * 100, lang, 3) })}</span> : null}
      </div>
      {m ? (
        <>
          <div className="grid grid--4">
            <KpiTile label={t("plannerModel.acceptance")} value={pct(m.acceptance)} unit="%" lang={lang} />
            <KpiTile label={t("plannerModel.sameChoice")} value={pct(m.same_choice_share)} unit="%" lang={lang} />
            <KpiTile label={t("plannerModel.costRatio")} value={m.closed_loop_cost_ratio} unit="×" lang={lang} />
            <KpiTile label={t("plannerModel.time")} value={m.time_learned_ms} unit={t("plannerModel.timeUnit", { teacher: fmt(m.time_teacher_ms, lang, 3) })} lang={lang} />
          </div>
          <p className="subtle">{t("plannerModel.metricsText", { n: m.n_situations, cycles: m.cycles, fallback: fmt(m.fallback_share * 100, lang, 2), infeasible: fmt(m.infeasible_share * 100, lang, 2),
            within: fmt((m.within_5_percent_share ?? 0) * 100, lang, 3) })}</p>
          <div className={`alert ${m.invalid_cycles === m.invalid_cycles_teacher && m.collisions === m.collisions_teacher ? "alert--info" : "alert--danger"}`}>
            <Icon name="check" /><div>{t("plannerModel.safety", { invalid: m.invalid_cycles, invalidTeacher: m.invalid_cycles_teacher, collisions: m.collisions, collisionsTeacher: m.collisions_teacher })}</div></div>
        </>
      ) : null}
      {model.test_metrics ? (
        <div className="grid grid--4">
          {TARGETS.map((k) => <KpiTile key={k} label={t(`plannerModel.targets.${k}`)} value={model.test_metrics?.[k]?.r2 ?? null}
            unit={`R² · RMSE ${fmt(model.test_metrics?.[k]?.rmse ?? null, lang)}`} lang={lang} />)}
        </div>
      ) : null}
      <h3>{t("plannerModel.drive.title")}</h3>
      <p className="subtle">{t("plannerModel.drive.text")}</p>
      <div className="row">
        {Object.keys(PRESETS).map((k) => (
          <button key={k} type="button" className="btn btn--secondary btn--sm" disabled={drive.loading}
            onClick={() => { setLabel(t(`plannerModel.presets.${k}`)); void drive.run({ situation: PRESETS[k] }); }}>{t(`plannerModel.presets.${k}`)}</button>
        ))}
        <button type="button" className="btn btn--primary btn--sm" disabled={drive.loading}
          onClick={() => { setLabel(t("plannerModel.drive.randomLabel", { seed })); void drive.run({ seed }); setSeed(seed + 1); }}>
          {drive.loading ? <span className="spinner" /> : <Icon name="play" size={14} />}{t("plannerModel.drive.random")}</button>
      </div>
      <ErrorAlert error={drive.error} />
      {drive.data ? <DriveView data={drive.data} label={label} lang={lang} /> : null}
      <div className="row row--between">
        <p className="subtle" style={{ flex: 1 }}>{t("plannerModel.stackHint")}</p>
        <button type="button" className="btn btn--secondary btn--sm" onClick={useInWorkbench}><Icon name="route" size={14} />{t("plannerModel.useInWorkbench")}</button>
      </div>
    </div>
  );
}

function DriveView({ data, label, lang }: { data: DriveResult; label: string; lang: string }) {
  const { t } = useTranslation(["app", "common"]);
  const s = data.summary;
  const lines: Polyline[] = [
    { x: data.road.left_x, y: data.road.left_y, kind: "bound" }, { x: data.road.right_x, y: data.road.right_y, kind: "bound" },
    { x: data.road.x, y: data.road.y, kind: "road" },
    { x: data.teacher.x, y: data.teacher.y, kind: "physics" }, { x: data.learned.x, y: data.learned.y, kind: "neural" },
  ];
  const boxes: Box[] = data.objects.map((o) => ({ x: o.x[1], y: o.y[1], psi: o.psi, length: o.length, width: o.width, kind: "object" as const }));
  const last = data.learned.x.length - 1;
  const focus = { xmin: Math.min(...data.learned.x, ...data.teacher.x) - 10, xmax: Math.max(...data.learned.x, ...data.teacher.x) + 25 };
  const kmh = (v: number[]) => v.map((x) => x * 3.6);
  return (
    <div className="stack">
      <div className="row">
        <span className="badge badge--info">{label}</span>
        <span className={`badge ${s.collision_learned ? "badge--danger" : "badge--success"}`}>{s.collision_learned ? t("plannerModel.drive.collision") : t("plannerModel.drive.noCollision")}</span>
      </div>
      <div className="grid grid--4">
        <KpiTile label={t("plannerModel.drive.network")} value={s.network_share * 100} unit="%" lang={lang} />
        <KpiTile label={t("plannerModel.drive.pathDiff")} value={s.max_path_difference} unit="m" lang={lang} />
        <KpiTile label={t("plannerModel.drive.cost")} value={s.cost_teacher > 0 ? s.cost_learned / s.cost_teacher : null} unit="×" lang={lang} />
        <KpiTile label={t("plannerModel.time")} value={s.time_learned_ms} unit={t("plannerModel.timeUnit", { teacher: fmt(s.time_teacher_ms, lang, 3) })} lang={lang} />
      </div>
      <PathPlot height={260} ariaLabel={t("plannerModel.drive.paths")} lines={lines} focus={focus}
        boxes={[...boxes, { x: data.learned.x[last], y: data.learned.y[last], psi: Math.atan2(data.learned.y[last] - data.learned.y[Math.max(last - 1, 0)], data.learned.x[last] - data.learned.x[Math.max(last - 1, 0)]),
          length: 4.8, width: 1.85, kind: "ego" }]} />
      <div className="row subtle"><span style={{ color: "var(--me-chart-1)" }}>━</span>{t("plannerModel.drive.teacher")}<span style={{ color: "var(--me-chart-3)" }}>╍</span>{t("plannerModel.drive.learned")}
        <span>{t("plannerModel.drive.objectsNote")}</span></div>
      <Suspense fallback={<Skeleton height={200} />}>
        <div className="grid grid--2">
          <div><div className="chart-title">{t("plannerModel.drive.speed")}</div>
            <Chart x={data.learned.t} xLabel="t [s]" yLabel="km/h" height={200} ariaLabel={t("plannerModel.drive.speed")}
              series={[{ label: t("plannerModel.drive.teacher"), values: kmh(data.teacher.v) }, { label: t("plannerModel.drive.learned"), values: kmh(data.learned.v), color: 2, dash: true }]} /></div>
          <div><div className="chart-title">{t("plannerModel.drive.source")}</div>
            <Chart x={data.learned.t} xLabel="t [s]" yLabel="" height={200} ariaLabel={t("plannerModel.drive.source")}
              series={[{ label: t("plannerModel.drive.networkCycle"), values: (data.learned.source ?? []).map((x) => (x === "network" ? 1 : 0)), color: 5 }]} /></div>
        </div>
      </Suspense>
    </div>
  );
}
