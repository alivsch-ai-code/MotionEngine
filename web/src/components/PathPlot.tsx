// Top view in world coordinates (SVG, equal axis scale): road corridor, candidate set, selected trajectory, objects.
import { memo, useMemo } from "react";

export interface Polyline { x: (number | null)[]; y: (number | null)[]; kind: "road" | "bound" | "target" | "candidate" | "rejected" | "collision" | "selected" | "prediction" | "physics" | "neural" }
export interface Box { x: number; y: number; psi: number; length: number; width: number; kind: "ego" | "object" }

const STYLE: Record<Polyline["kind"], { stroke: string; width: number; dash?: string; opacity?: number }> = {
  road: { stroke: "var(--me-text-subtle)", width: 1, dash: "6 6" },
  bound: { stroke: "var(--me-border-strong)", width: 1.5 },
  target: { stroke: "var(--me-accent)", width: 1, dash: "2 4", opacity: 0.8 },
  candidate: { stroke: "var(--me-chart-6)", width: 1, opacity: 0.35 },
  rejected: { stroke: "var(--me-text-subtle)", width: 1, opacity: 0.3 },
  collision: { stroke: "var(--me-danger)", width: 1, opacity: 0.45 },
  selected: { stroke: "var(--me-primary)", width: 3 },
  prediction: { stroke: "var(--me-warning)", width: 2, dash: "4 3" },
  physics: { stroke: "var(--me-chart-1)", width: 2.5 },
  neural: { stroke: "var(--me-chart-3)", width: 2, dash: "6 4" },
};

function toPoints(l: Polyline) {
  const pts: string[] = [];
  for (let i = 0; i < l.x.length; i++) {
    const x = l.x[i], y = l.y[i];
    if (x !== null && y !== null && Number.isFinite(x) && Number.isFinite(y)) pts.push(`${x.toFixed(3)},${(-y).toFixed(3)}`);
  }
  return pts.join(" ");
}

// stretch: independent x/y scaling (Frenet view s-d, where d spans metres and s hundreds of metres)
function PathPlotImpl({ lines, boxes = [], height = 320, ariaLabel, focus, stretch = false }:
  { lines: Polyline[]; boxes?: Box[]; height?: number; ariaLabel: string; focus?: { xmin: number; xmax: number }; stretch?: boolean }) {
  const view = useMemo(() => {
    let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
    const take = (x: number, y: number) => { if (focus && (x < focus.xmin || x > focus.xmax)) return; xmin = Math.min(xmin, x); xmax = Math.max(xmax, x); ymin = Math.min(ymin, y); ymax = Math.max(ymax, y); };
    for (const l of lines) if (l.kind !== "road") l.x.forEach((x, i) => { const y = l.y[i]; if (x !== null && y !== null) take(x, y); });
    boxes.forEach((b) => take(b.x, b.y));
    if (!Number.isFinite(xmin)) return { x: 0, y: -10, w: 100, h: 20 };
    const pad = stretch ? 0.5 : 4;
    const w = Math.max(xmax - xmin + 2 * pad, 10), h = Math.max(ymax - ymin + 2 * pad, stretch ? 2 : 12);
    return { x: xmin - pad, y: -(ymax + pad), w, h };
  }, [lines, boxes, focus, stretch]);
  return (
    <svg className="chart" viewBox={`${view.x} ${view.y} ${view.w} ${view.h}`} style={{ height, background: "var(--me-surface-2)", borderRadius: "var(--me-radius-md)" }}
      preserveAspectRatio={stretch ? "none" : "xMidYMid meet"} role="img" aria-label={ariaLabel}>
      {lines.map((l, i) => {
        const s = STYLE[l.kind];
        return <polyline key={i} points={toPoints(l)} fill="none" stroke={s.stroke} strokeWidth={s.width} strokeDasharray={s.dash}
          strokeOpacity={s.opacity ?? 1} vectorEffect="non-scaling-stroke" strokeLinecap="round" strokeLinejoin="round" />;
      })}
      {boxes.map((b, i) => (
        <rect key={i} x={b.x - b.length / 2} y={-b.y - b.width / 2} width={b.length} height={b.width} rx={0.4}
          transform={`rotate(${(-b.psi * 180) / Math.PI} ${b.x} ${-b.y})`}
          fill={b.kind === "ego" ? "var(--me-primary-strong)" : "var(--me-warning)"} fillOpacity={0.85} />
      ))}
    </svg>
  );
}

export const PathPlot = memo(PathPlotImpl);
