// Architecture: the signal-flow graph of the AD stack the workbench runs (layers, ports, connections).
// Connections can be removed and added; the server validates the wiring (types, required inputs) and the
// workbench runs the rewired stack. (Desktop equivalent: node editor.)
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { Icon } from "../components/Icon";
import { PageHeader } from "../components/PageHeader";
import { RichText } from "../components/RichText";
import { StackEditor } from "../components/StackEditor";
import { componentLabel, libraryText } from "../lib/domain";
import { useClient, useQuery } from "../lib/hooks";
import type { Connection } from "../lib/api";
import { stackSpecs, useConnections, useStack } from "../lib/stack";

const W = 200, H = 86;

export default function Architecture() {
  const { t, i18n } = useTranslation(["app", "common", "domain"]);
  const client = useClient();
  const catalog = useQuery((s) => client.workbenchCatalog(s), [client]);
  const [stack, setStack] = useStack();
  const { specs, invalid } = useMemo(() => stackSpecs(stack), [stack]);
  const [connections, setConnections] = useConnections();
  const graph = useQuery((s) => client.stackGraph(specs, s, connections), [client, JSON.stringify(specs), JSON.stringify(connections)]);
  const [draft, setDraft] = useState<Connection>({ from: "", to: "" });
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
  const wiring = graph.data?.connections ?? [];
  const ports = graph.data?.ports ?? {};
  const outputs = Object.entries(ports).flatMap(([n, p]) => p.outputs.map((o) => ({ id: `${n}.${o}`, type: p.output_types[o]?.type ?? "" })));
  const inputs = Object.entries(ports).flatMap(([n, p]) => p.inputs.map((o) => ({ id: `${n}.${o}`, type: p.input_types[o]?.type ?? "", optional: p.input_types[o]?.optional ?? false,
    used: wiring.some((c) => c.to === `${n}.${o}`) })));
  const outType = outputs.find((o) => o.id === draft.from)?.type;
  const remove = (c: Connection) => setConnections(wiring.filter((x) => !(x.from === c.from && x.to === c.to)));
  const add = () => {
    if (!draft.from || !draft.to || wiring.some((x) => x.from === draft.from && x.to === draft.to)) return;
    setConnections([...wiring, draft]);
    setDraft({ from: "", to: "" });
  };

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
        {graph.data?.issues.length ? <div className="alert alert--danger" role="alert"><div>{graph.data.issues.map((x, i) => <div key={i} className="mono">{libraryText(x, i18n.language)}</div>)}</div></div>
          : graph.data ? <p className="subtle">{t("architecture.valid", { nodes: graph.data.nodes.length, conns: graph.data.connections.length })}</p> : null}
      </div></div>
      <div className="card">
        <div className="card__header"><div><h2>{t("architecture.wiring.title")}</h2><p>{t("architecture.wiring.text")}</p></div>
          {connections ? <button type="button" className="btn btn--secondary btn--sm" onClick={() => setConnections(null)}>{t("architecture.wiring.reset")}</button>
            : <span className="badge badge--success">{t("architecture.wiring.default")}</span>}</div>
        <div className="card__body stack">
          <div className="table-wrap" style={{ maxHeight: 320, overflowY: "auto" }}><table className="table">
            <thead><tr><th>{t("architecture.wiring.from")}</th><th>{t("architecture.wiring.to")}</th><th>{t("architecture.wiring.type")}</th><th /></tr></thead>
            <tbody>{wiring.map((c) => {
              const [a, pa] = c.from.split("."), [b] = c.to.split(".");
              const hot = a === selected || b === selected;
              return <tr key={`${c.from}>${c.to}`} style={hot ? { background: "var(--me-surface-2)" } : undefined}>
                <td className="mono">{c.from}</td><td className="mono">{c.to}</td><td className="subtle">{ports[a]?.output_types[pa]?.type ?? "–"}</td>
                <td className="num"><button type="button" className="btn btn--ghost btn--sm btn--icon" aria-label={t("architecture.wiring.remove", { from: c.from, to: c.to })}
                  onClick={() => remove(c)}><Icon name="trash" size={14} /></button></td></tr>;
            })}</tbody></table></div>
          <div className="row">
            <select className="select" style={{ flex: 1 }} value={draft.from} aria-label={t("architecture.wiring.from")} onChange={(e) => setDraft({ from: e.target.value, to: "" })}>
              <option value="">{t("architecture.wiring.pickOutput")}</option>
              {outputs.map((o) => <option key={o.id} value={o.id}>{o.id} ({o.type})</option>)}</select>
            <Icon name="arrowRight" size={16} />
            <select className="select" style={{ flex: 1 }} value={draft.to} aria-label={t("architecture.wiring.to")} disabled={!draft.from} onChange={(e) => setDraft({ ...draft, to: e.target.value })}>
              <option value="">{t("architecture.wiring.pickInput")}</option>
              {inputs.filter((i) => i.type === outType).map((i) => <option key={i.id} value={i.id}>{i.id}{i.used ? ` · ${t("architecture.wiring.used")}` : ""}{i.optional ? ` · ${t("architecture.wiring.optional")}` : ""}</option>)}</select>
            <button type="button" className="btn btn--primary btn--sm" disabled={!draft.from || !draft.to} onClick={add}><Icon name="plus" size={14} />{t("architecture.wiring.add")}</button>
          </div>
        </div>
      </div>
      <div className="split">
        <div className="card"><div className="card__body">{catalog.data ? <StackEditor catalog={catalog.data} stack={stack} onChange={setStack} /> : <Skeleton height={80} />}
          <p className="subtle">{t("architecture.stackHint")}</p></div></div>
        <div className="card"><div className="card__body stack">
          {node ? <><h2>{t(`workbench.layers.${node.id}`, { defaultValue: node.id })} · <span className="mono">{node.component}</span></h2>
            <p className="subtle">{componentLabel(t, node.component)}</p>
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
