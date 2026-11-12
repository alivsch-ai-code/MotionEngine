// Architecture: the signal-flow graph of the AD stack the workbench runs (layers, ports, connections).
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { PageHeader } from "../components/PageHeader";
import { RichText } from "../components/RichText";
import { StackEditor } from "../components/StackEditor";
import { useClient, useQuery } from "../lib/hooks";
import { stackSpecs, useStack } from "../lib/stack";

const W = 200, H = 86;

export default function Architecture() {
  const { t } = useTranslation(["app", "common"]);
  const client = useClient();
  const catalog = useQuery((s) => client.workbenchCatalog(s), [client]);
  const [stack, setStack] = useStack();
  const { specs, invalid } = useMemo(() => stackSpecs(stack), [stack]);
  const graph = useQuery((s) => client.stackGraph(specs, s), [client, JSON.stringify(specs)]);
  const [selected, setSelected] = useState("planner");
  const node = graph.data?.nodes.find((n) => n.id === selected);
  const doc = useQuery((s) => (node ? client.componentDoc(node.component, s) : Promise.resolve(null)), [client, node?.component]);
  const pos = useMemo(() => Object.fromEntries((graph.data?.nodes ?? []).map((n) => [n.id, n.position])), [graph.data]);
  const box = useMemo(() => {
    const xs = Object.values(pos).map((p) => p[0]), ys = Object.values(pos).map((p) => p[1]);
    if (!xs.length) return "0 0 800 400";
    return `${Math.min(...xs) - 30} ${Math.min(...ys) - 30} ${Math.max(...xs) - Math.min(...xs) + W + 60} ${Math.max(...ys) - Math.min(...ys) + H + 60}`;
  }, [pos]);
  // one label per pair of nodes: all ports of that direction
  const labels = useMemo(() => {
    const out: Record<string, { first: number; ports: string[] }> = {};
    (graph.data?.connections ?? []).forEach((c, i) => {
      const [a, pa] = c.from.split("."), [b] = c.to.split(".");
      const key = `${a}>${b}`;
      if (!out[key]) out[key] = { first: i, ports: [] };
      if (!out[key].ports.includes(pa)) out[key].ports.push(pa);
    });
    return out;
  }, [graph.data]);
  const d = doc.data?.doc as Record<string, unknown> | null | undefined;

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("architecture.title")} description={t("architecture.subtitle")} />
      <ErrorAlert error={catalog.error ?? graph.error} />
      {invalid ? <div className="alert alert--danger" role="alert">{t("workbench.invalidParams", { layer: invalid })}</div> : null}
      <div className="card"><div className="card__body">
        {graph.data ? (
          <svg className="chart" viewBox={box} style={{ height: 420, width: "100%" }} role="img" aria-label={t("architecture.title")}>
            <defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M0 0 L10 5 L0 10 z" fill="var(--me-text-subtle)" /></marker></defs>
            {graph.data.connections.map((c, i) => {
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
            {graph.data.nodes.map((n) => (
              <g key={n.id} transform={`translate(${n.position[0]} ${n.position[1]})`} onClick={() => setSelected(n.id)} style={{ cursor: "pointer" }}
                role="button" tabIndex={0} aria-pressed={selected === n.id} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setSelected(n.id); }}>
                <rect width={W} height={H} rx={10} fill="var(--me-surface-2)" stroke={selected === n.id ? "var(--me-primary)" : "var(--me-border-strong)"} strokeWidth={selected === n.id ? 2.5 : 1} />
                <text x={12} y={26} fontSize="14" fontWeight="600" fill="var(--me-text-strong)">{t(`workbench.layers.${n.id}`, { defaultValue: n.id })}</text>
                <text x={12} y={48} fontSize="11.5" fill="var(--me-text-muted)" fontFamily="var(--me-font-mono)">{n.component.split("/")[1]}</text>
                <text x={12} y={68} fontSize="11" fill="var(--me-text-subtle)">{n.period ? `${Math.round(1 / n.period)} Hz` : ""}</text>
              </g>
            ))}
          </svg>
        ) : <Skeleton height={420} />}
        {graph.data?.issues.length ? <div className="alert alert--danger" role="alert"><div>{graph.data.issues.map((x, i) => <div key={i} className="mono">{x}</div>)}</div></div>
          : graph.data ? <p className="subtle">{t("architecture.valid", { nodes: graph.data.nodes.length, conns: graph.data.connections.length })}</p> : null}
      </div></div>
      <div className="split">
        <div className="card"><div className="card__body">{catalog.data ? <StackEditor catalog={catalog.data} stack={stack} onChange={setStack} /> : <Skeleton height={80} />}
          <p className="subtle">{t("architecture.stackHint")}</p></div></div>
        <div className="card"><div className="card__body stack">
          {node ? <><h2>{t(`workbench.layers.${node.id}`, { defaultValue: node.id })} · <span className="mono">{node.component}</span></h2>
            <div className="row"><span className="badge badge--info">{t("architecture.inputs")}: {(graph.data?.ports[node.id]?.inputs ?? []).join(", ") || "–"}</span>
              <span className="badge badge--success">{t("architecture.outputs")}: {(graph.data?.ports[node.id]?.outputs ?? []).join(", ") || "–"}</span></div></> : null}
          {doc.loading ? <Skeleton height={120} /> : null}
          {d ? <>
            {typeof d.summary === "string" ? <p>{d.summary}</p> : null}
            {(["purpose", "theory"] as const).map((key) => (typeof d[key] === "string" && d[key] ? <div key={key}><h3>{t(`architecture.doc.${key}`)}</h3><RichText text={d[key] as string} /></div> : null))}
            {Array.isArray(d.references) && d.references.length ? <p className="subtle">{t("architecture.doc.references")}: {(d.references as string[]).join(", ")}</p> : null}
          </> : !doc.loading ? <p className="subtle">{t("architecture.noDoc")}</p> : null}
        </div></div>
      </div>
    </div>
  );
}
