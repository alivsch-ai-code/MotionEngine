// Architecture: the signal-flow graph of the AD stack the workbench runs (layers, ports, connections).
// Connections can be removed and added; the server validates the wiring (types, required inputs) and the
// workbench runs the rewired stack. (Desktop equivalent: node editor.)
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { Icon } from "../components/Icon";
import { PageHeader } from "../components/PageHeader";
import { RichText } from "../components/RichText";
import { StackDiagram } from "../components/StackDiagram";
import { StackEditor } from "../components/StackEditor";
import { componentLabel, componentList, componentNote, libraryText } from "../lib/domain";
import { useClient, useQuery } from "../lib/hooks";
import type { Connection } from "../lib/api";
import { stackSpecs, useConnections, useStack } from "../lib/stack";

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
          <StackDiagram nodes={graph.data.nodes} connections={graph.data.connections} selected={selected} onSelect={setSelected} ariaLabel={t("architecture.title")} />
        ) : <Skeleton height={420} />}
        {graph.data?.issues.length ? <div className="alert alert--danger" role="alert"><div>{graph.data.issues.map((x, i) => <div key={i} className="mono">{libraryText(x, i18n.language)}</div>)}</div></div>
          : graph.data ? <div className="row row--between"><p className="subtle">{t("architecture.valid", { nodes: graph.data.nodes.length, conns: graph.data.connections.length })}</p>
            <Link className="btn btn--secondary btn--sm" to="/app/workbench"><Icon name="radar" size={16} />{t("architecture.runLive")}</Link></div> : null}
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
            {typeof d.summary === "string" && node ? <p>{t(`domain:componentDoc.${node.component.replace("/", ".")}.summary`, { defaultValue: d.summary })}</p> : null}
            {typeof d.purpose === "string" && d.purpose && node ? <div><h3>{t("architecture.doc.purpose")}</h3>
              <p>{t(`domain:componentDoc.${node.component.replace("/", ".")}.purpose`, { defaultValue: d.purpose })}</p></div> : null}
            {typeof d.theory === "string" && d.theory && node ? <div><h3>{t("architecture.doc.theory")}</h3><RichText text={componentNote(t, node.component, "theory", d.theory)} /></div> : null}
            {node ? (["assumptions", "limitations"] as const).map((field) => { const items = componentList(t, node.component, field, d[field]); return items.length ? (
              <div key={field}><h3>{t(`architecture.doc.${field}`)}</h3><ul>{items.map((x) => <li key={x}>{x}</li>)}</ul></div>) : null; }) : null}
            {Array.isArray(d.references) && d.references.length ? <p className="subtle">{t("architecture.doc.references")}: {(d.references as string[]).join(", ")}</p> : null}
          </> : !doc.loading ? <p className="subtle">{t("architecture.noDoc")}</p> : null}
        </div></div>
      </div>
    </div>
  );
}
