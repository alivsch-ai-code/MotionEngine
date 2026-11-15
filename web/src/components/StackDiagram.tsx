// Block diagram of the stack: one box per layer, arrows for the connections. Used by the Architecture page
// (edit the wiring) and by the live mode (click a block to see its signals while the run is paused).
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import type { Connection } from "../lib/api";

const W = 200, H = 86;
export interface DiagramNode { id: string; component: string; position: [number, number]; period?: number | null }

export function StackDiagram({ nodes, connections, selected, onSelect, active, captions, height = 420, ariaLabel }:
  { nodes: DiagramNode[]; connections: Connection[]; selected: string; onSelect: (id: string) => void; active?: string | null;
    captions?: Record<string, string>; height?: number; ariaLabel: string }) {
  const { t } = useTranslation(["app"]);
  const pos = useMemo(() => Object.fromEntries(nodes.map((n) => [n.id, n.position])), [nodes]);
  const box = useMemo(() => {
    const xs = Object.values(pos).map((p) => p[0]), ys = Object.values(pos).map((p) => p[1]);
    if (!xs.length) return "0 0 800 400";
    return `${Math.min(...xs) - 30} ${Math.min(...ys) - 30} ${Math.max(...xs) - Math.min(...xs) + W + 60} ${Math.max(...ys) - Math.min(...ys) + H + 60}`;
  }, [pos]);
  // one label per pair of nodes: all ports of that direction
  const labels = useMemo(() => {
    const out: Record<string, { first: number; ports: string[] }> = {};
    connections.forEach((c, i) => {
      const [a, pa] = c.from.split("."), [b] = c.to.split(".");
      const key = `${a}>${b}`;
      if (!out[key]) out[key] = { first: i, ports: [] };
      if (!out[key].ports.includes(pa)) out[key].ports.push(pa);
    });
    return out;
  }, [connections]);
  return (
    <svg className="chart" viewBox={box} style={{ height, width: "100%" }} role="img" aria-label={ariaLabel}>
      <defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0 0 L10 5 L0 10 z" fill="var(--me-text-subtle)" /></marker></defs>
      {connections.map((c, i) => {
        const a = c.from.split(".")[0], b = c.to.split(".")[0];
        const p = pos[a], q = pos[b];
        if (!p || !q) return null;
        const hot = a === selected || b === selected;
        const x1 = p[0] + W / 2, y1 = p[1] + H / 2, x2 = q[0] + W / 2, y2 = q[1] + H / 2;
        // end on the border of the target box
        const dx = x2 - x1, dy = y2 - y1, k = Math.min(Math.abs(dx) > 1e-6 ? (W / 2) / Math.abs(dx) : 1e9, Math.abs(dy) > 1e-6 ? (H / 2) / Math.abs(dy) : 1e9);
        return <g key={i}>
          <line x1={x1 + dx * k} y1={y1 + dy * k} x2={x2 - dx * k} y2={y2 - dy * k} stroke={hot ? "var(--me-primary)" : "var(--me-text-subtle)"}
            strokeWidth={hot ? 2 : 1} strokeOpacity={hot ? 1 : 0.5} markerEnd="url(#arrow)" />
          {hot && labels[`${a}>${b}`]?.first === i ? <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 - 6 + (a < b ? 0 : 16)} textAnchor="middle" fontSize="11"
            fill="var(--me-text-muted)">{labels[`${a}>${b}`].ports.join(", ")}</text> : null}
        </g>;
      })}
      {nodes.map((n) => (
        <g key={n.id} transform={`translate(${n.position[0]} ${n.position[1]})`} onClick={() => onSelect(n.id)} style={{ cursor: "pointer" }}
          role="button" tabIndex={0} aria-pressed={selected === n.id} aria-label={t(`workbench.layers.${n.id}`, { defaultValue: n.id })}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(n.id); } }}>
          <rect width={W} height={H} rx={10} fill={active === n.id ? "var(--me-primary-soft, var(--me-surface-2))" : "var(--me-surface-2)"}
            stroke={selected === n.id ? "var(--me-primary)" : active === n.id ? "var(--me-success, var(--me-primary))" : "var(--me-border-strong)"} strokeWidth={selected === n.id || active === n.id ? 2.5 : 1} />
          <text x={12} y={26} fontSize="14" fontWeight="600" fill="var(--me-text-strong)">{t(`workbench.layers.${n.id}`, { defaultValue: n.id })}</text>
          <text x={12} y={48} fontSize="11.5" fill="var(--me-text-muted)" fontFamily="var(--me-font-mono)">{n.component.split("/")[1]}</text>
          <text x={12} y={68} fontSize="11" fill="var(--me-text-subtle)">{captions?.[n.id] ?? (n.period ? `${Math.round(1 / n.period)} Hz` : "")}</text>
        </g>
      ))}
    </svg>
  );
}
