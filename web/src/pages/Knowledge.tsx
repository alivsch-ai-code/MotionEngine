// Knowledge: search the knowledge graph (components, concepts, classes, equations) and the literature.
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { EmptyState, Skeleton } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { PageHeader } from "../components/PageHeader";
import { RichText } from "../components/RichText";
import { useClient, useQuery } from "../lib/hooks";

type Tab = "graph" | "references";

export default function Knowledge() {
  const { t } = useTranslation(["app", "common"]);
  const client = useClient();
  const [tab, setTab] = useState<Tab>("graph");
  const [q, setQ] = useState("werling");
  const [query, setQuery] = useState("werling");
  const [selected, setSelected] = useState<string | null>(null);
  useEffect(() => { const id = window.setTimeout(() => setQuery(q), 250); return () => window.clearTimeout(id); }, [q]);
  const nodes = useQuery((s) => client.knowledgeNodes(query, s), [client, query]);
  const explain = useQuery((s) => (selected ? client.knowledgeExplain(selected, s) : Promise.resolve(null)), [client, selected]);
  const refs = useQuery((s) => client.references(s), [client]);
  const refList = useMemo(() => Object.entries(refs.data ?? {}).filter(([id, r]) => !q || tab !== "references"
    || `${id} ${r.title ?? ""} ${(r.authors ?? []).join(" ")}`.toLowerCase().includes(q.toLowerCase())), [refs.data, q, tab]);

  return (
    <div className="stack stack--lg">
      <PageHeader title={t("knowledge.title")} description={t("knowledge.subtitle")} />
      <div className="row">
        <div className="tabs" role="tablist" aria-label={t("knowledge.title")}>
          {(["graph", "references"] as const).map((x) => <button key={x} role="tab" type="button" aria-selected={tab === x} onClick={() => setTab(x)}>{t(`knowledge.tabs.${x}`)}</button>)}
        </div>
        <label htmlFor="kn-q" className="visually-hidden">{t("knowledge.search")}</label>
        <input id="kn-q" className="input" style={{ maxWidth: 320 }} type="search" value={q} placeholder={t("knowledge.search")} onChange={(e) => setQ(e.target.value)} />
      </div>
      <ErrorAlert error={nodes.error ?? refs.error ?? explain.error} />
      {tab === "graph" ? (
        <div className="split split--nav">
          <div className="card"><div className="card__body stack stack--sm knowledge-list">
            {nodes.loading && !nodes.data ? <Skeleton height={200} /> : null}
            {(nodes.data ?? []).map((n) => (
              <button key={n.id} type="button" className={`btn btn--sm ${selected === n.id ? "btn--secondary" : "btn--ghost"} knowledge-item`} onClick={() => setSelected(n.id)}>
                <span className="badge badge--info">{n.type}</span><span>{n.label || n.id}</span></button>
            ))}
            {nodes.data && !nodes.data.length ? <p className="subtle">{t("knowledge.noHits")}</p> : null}
          </div></div>
          <div className="card"><div className="card__body stack">
            {!selected ? <EmptyState art="model" title={t("knowledge.empty.title")} text={t("knowledge.empty.text")} /> : null}
            {explain.loading ? <Skeleton height={240} /> : null}
            {explain.data ? <>
              <RichText text={explain.data.markdown} headings />
              <h3>{t("knowledge.linked")}</h3>
              <div className="row" style={{ flexWrap: "wrap" }}>
                {explain.data.nodes.filter((n) => n.id !== selected).map((n) => (
                  <button key={n.id} type="button" className="btn btn--ghost btn--sm" onClick={() => setSelected(n.id)}>{n.label || n.id}</button>))}
              </div>
            </> : null}
          </div></div>
        </div>
      ) : (
        <div className="card"><div className="card__body table-wrap"><table className="table">
          <thead><tr><th>{t("knowledge.ref.id")}</th><th>{t("knowledge.ref.authors")}</th><th>{t("knowledge.ref.title")}</th><th className="num">{t("knowledge.ref.year")}</th></tr></thead>
          <tbody>{refList.map(([id, r]) => (
            <tr key={id}><td className="mono">{id}</td><td>{(r.authors ?? []).slice(0, 3).join(", ")}{(r.authors ?? []).length > 3 ? " …" : ""}</td>
              <td>{r.url || r.doi ? <a href={r.url ?? `https://doi.org/${r.doi}`} target="_blank" rel="noreferrer">{r.title}</a> : r.title}</td><td className="num">{r.year ?? ""}</td></tr>
          ))}</tbody></table></div></div>
      )}
    </div>
  );
}
