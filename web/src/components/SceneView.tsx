// Top view of an AD run at one instant: lanes, actors, the ego vehicle with its driven path, and the planning
// cycle (candidate set colored by status, selected trajectory, predictions). The time is controlled outside.
import { memo, useMemo } from "react";

import type { PlannerSnapshot, RunResult } from "../lib/api";

// lane polylines come as [xs, ys]
const poly = (p: number[][], reverse = false) => {
  const pts = (p[0] ?? []).map((x, i) => `${x.toFixed(2)},${(-(p[1]?.[i] ?? 0)).toFixed(2)}`);
  return (reverse ? pts.reverse() : pts).join(" ");
};
const line = (x: (number | null)[], y: (number | null)[], n = x.length) => {
  const out: string[] = [];
  for (let i = 0; i < n; i++) { const a = x[i], b = y[i]; if (a !== null && b !== null) out.push(`${a.toFixed(2)},${(-b).toFixed(2)}`); }
  return out.join(" ");
};

export function indexAt(tt: (number | null)[], time: number) {
  let lo = 0, hi = tt.length - 1;
  if (hi < 0) return 0;
  while (hi - lo > 1) { const mid = (lo + hi) >> 1; if ((tt[mid] ?? 0) <= time) lo = mid; else hi = mid; }
  return Math.abs((tt[hi] ?? 0) - time) < Math.abs((tt[lo] ?? 0) - time) ? hi : lo;
}

const STATUS = ["var(--me-chart-6)", "var(--me-text-subtle)", "var(--me-danger)", "var(--me-border-strong)"];

function SceneViewImpl({ result, time, snapshot, showCandidates, width = 90, height = 380, ariaLabel }:
  { result: RunResult; time: number; snapshot: PlannerSnapshot | null; showCandidates: boolean; width?: number; height?: number; ariaLabel: string }) {
  const s = result.signals;
  const i = indexAt(s.t ?? [], time);
  const ex = (s.ego_x?.[i] ?? 0) as number, ey = (s.ego_y?.[i] ?? 0) as number, epsi = (s.ego_psi?.[i] ?? 0) as number;
  const road = useMemo(() => (
    <g>
      {result.road.lanes.map((l) => (
        <g key={l.id}>
          <polygon points={`${poly(l.left)} ${poly(l.right, true)}`} fill={l.type === "parking" ? "var(--me-surface-3)" : "var(--me-bg)"} fillOpacity={0.9} />
          <polyline points={poly(l.left)} fill="none" stroke="var(--me-text-subtle)" strokeWidth={1.2} vectorEffect="non-scaling-stroke"
            strokeDasharray={l.marking_left === "dashed" ? "8 8" : undefined} />
          <polyline points={poly(l.right)} fill="none" stroke="var(--me-text-subtle)" strokeWidth={1.2} vectorEffect="non-scaling-stroke"
            strokeDasharray={l.marking_right === "dashed" ? "8 8" : undefined} />
        </g>
      ))}
    </g>
  ), [result.road]);
  const actors = Object.entries(result.objects).map(([id, o]) => {
    if (!o.t.length || time < o.t[0] - 0.2 || time > o.t[o.t.length - 1] + 0.2) return null;
    const k = indexAt(o.t, time);
    const x = o.x[k], y = o.y[k], psi = o.psi?.[k] ?? 0;
    return <rect key={id} x={x - o.length / 2} y={-y - o.width / 2} width={o.length} height={o.width} rx={0.3}
      transform={`rotate(${(-psi * 180) / Math.PI} ${x} ${-y})`} fill={o.type === "pedestrian" || o.type === "cyclist" ? "var(--me-chart-5)" : "var(--me-warning)"} fillOpacity={0.9} />;
  });
  const h = (width * height) / 900;
  return (
    <svg className="chart player__view" viewBox={`${ex - width * 0.35} ${-ey - h / 2} ${width} ${h}`} style={{ height }} preserveAspectRatio="xMidYMid meet"
      role="img" aria-label={ariaLabel}>
      {road}
      {snapshot && showCandidates ? snapshot.candidates_x.map((cx, k) => (k === snapshot.best_index ? null
        : <polyline key={k} points={line(cx, snapshot.candidates_y[k])} fill="none" stroke={STATUS[snapshot.candidates_status[k]] ?? STATUS[3]}
          strokeOpacity={0.35} strokeWidth={1} vectorEffect="non-scaling-stroke" />)) : null}
      {snapshot?.prediction?.map((p) => <polyline key={p.id} points={line(p.x, p.y)} fill="none" stroke="var(--me-warning)" strokeDasharray="4 3"
        strokeWidth={1.5} vectorEffect="non-scaling-stroke" />)}
      <polyline points={line(s.ego_x ?? [], s.ego_y ?? [], i + 1)} fill="none" stroke="var(--me-text-subtle)" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
      {snapshot?.trajectory ? <polyline points={line(snapshot.trajectory.x, snapshot.trajectory.y)} fill="none" stroke="var(--me-primary)" strokeWidth={3}
        vectorEffect="non-scaling-stroke" strokeLinecap="round" /> : null}
      {actors}
      <g transform={`rotate(${(-epsi * 180) / Math.PI} ${ex} ${-ey})`}>
        <rect x={ex - result.ego.length / 2} y={-ey - result.ego.width / 2} width={result.ego.length} height={result.ego.width} rx={0.35} fill="var(--me-primary)" />
        <rect x={ex + result.ego.length * 0.12} y={-ey - result.ego.width * 0.38} width={result.ego.length * 0.14} height={result.ego.width * 0.76} rx={0.15}
          fill="var(--me-surface)" fillOpacity={0.75} />
      </g>
    </svg>
  );
}

export const SceneView = memo(SceneViewImpl);
