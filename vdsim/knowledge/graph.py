"""Knowledge graph: components, algorithms, models, data structures and documents with their relations.

Node ids are "<type>:<key>", e.g.
    package:geometry, module:vdsim.geometry.reference_line,
    function:vdsim.geometry.reference_line.ReferenceLine.to_frenet, concept:frenet_transformation,
    reference:werling2011, component:lateral_controller/stanley, model:tire_model/pacejka

Edges are directed (source -type-> target), e.g.
    function:...to_frenet -implements-> concept:frenet_transformation -cites-> reference:werling2011

Queries: neighbors(), path(a, b), concept_subgraph(), explain("X") ("Wie funktioniert X"),
search(). Export: to_json() and to_html() (standalone page with embedded JavaScript, no CDN).
"""

from __future__ import annotations

import html
import json
from collections import Counter, deque
from dataclasses import dataclass, field

import numpy as np

from ..framework.knowledge import trace
from .collector import as_list, first_sentence

NODE_TYPES = ("package", "module", "component", "class", "function", "concept", "reference", "datatype", "model",
              "document", "test", "example", "config")
EDGE_TYPES = ("contains", "imports", "implements", "cites", "consumes", "produces", "documented_by", "tested_by",
              "example_of", "configured_by", "related_to", "subclass_of")
NODE_LABELS = {"package": "Paket", "module": "Modul", "component": "Komponente", "class": "Klasse",
               "function": "Funktion", "concept": "Verfahren/Konzept", "reference": "Quelle", "datatype": "Datentyp",
               "model": "Modell", "document": "Dokument", "test": "Test", "example": "Beispiel", "config": "Konfiguration"}
EDGE_LABELS = {"contains": "enthält", "imports": "importiert", "implements": "implementiert", "cites": "zitiert",
               "consumes": "konsumiert", "produces": "erzeugt", "documented_by": "dokumentiert durch",
               "tested_by": "getestet durch", "example_of": "Beispiel für", "configured_by": "konfiguriert durch",
               "related_to": "verwandt mit", "subclass_of": "Unterklasse von"}
NODE_COLORS = {"package": "#3987e5", "module": "#6e9bd1", "component": "#3fb950", "class": "#a371f7",
               "function": "#c297ff", "concept": "#f0883e", "reference": "#d29922", "datatype": "#56d4dd",
               "model": "#2ea043", "document": "#8b949e", "test": "#f85149", "example": "#db61a2", "config": "#e3b341"}


@dataclass
class Node:
    id: str
    type: str
    label: str
    data: dict = field(default_factory=dict)

    @property
    def key(self):
        return self.id.split(":", 1)[1]

    def to_dict(self):
        return {"id": self.id, "type": self.type, "label": self.label, **{k: self.data[k] for k in sorted(self.data)}}


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    type: str
    note: str = ""

    def to_dict(self):
        out = {"source": self.source, "target": self.target, "type": self.type}
        if self.note:
            out["note"] = self.note
        return out


class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self._edge_set = set()
        self._out, self._in = {}, {}

    # ------------------------------------------------------------------ construction
    def add_node(self, node_type, key, label=None, **data):
        nid = f"{node_type}:{key}"
        node = self.nodes.get(nid)
        if node is None:
            node = Node(nid, node_type, label or str(key), {k: v for k, v in data.items() if v not in (None, "", [], {})})
            self.nodes[nid] = node
        else:
            for k, v in data.items():
                if v not in (None, "", [], {}) and k not in node.data:
                    node.data[k] = v
            if label and node.label == node.key:
                node.label = label
        return nid

    def add_edge(self, source, target, edge_type, note=""):
        if source not in self.nodes or target not in self.nodes or source == target:
            return None
        key = (source, target, edge_type)
        if key in self._edge_set:
            return None
        self._edge_set.add(key)
        edge = Edge(source, target, edge_type, note)
        self.edges.append(edge)
        self._out.setdefault(source, []).append(edge)
        self._in.setdefault(target, []).append(edge)
        return edge

    def finalize(self):
        self.edges.sort(key=lambda e: (e.source, e.type, e.target))
        self._out, self._in = {}, {}
        for e in self.edges:
            self._out.setdefault(e.source, []).append(e)
            self._in.setdefault(e.target, []).append(e)
        self.nodes = dict(sorted(self.nodes.items()))
        return self

    # ------------------------------------------------------------------ access
    def __contains__(self, node_id):
        return node_id in self.nodes

    def node(self, node_id):
        return self.nodes.get(self.resolve(node_id) or "")

    def resolve(self, query):
        # node id from an id, a key ("frenet_transformation"), a dotted suffix ("geometry.ReferenceLine.to_frenet")
        # or a label; None if nothing matches
        if query in self.nodes:
            return query
        q = str(query).strip()
        if ":" in q and q.split(":", 1)[0] in NODE_TYPES:
            t, k = q.split(":", 1)
            hits = [n for n in self.nodes.values() if n.type == t and (n.key.endswith("." + k) or n.key.endswith("/" + k))]
            return hits[0].id if len(hits) == 1 else (sorted(hits, key=lambda n: len(n.id))[0].id if hits else None)
        priority = {t: i for i, t in enumerate(("concept", "component", "model", "package", "function", "class",
                                                "module", "reference", "datatype", "document", "test", "example",
                                                "config"))}
        exact = [n for n in self.nodes.values() if n.key == q]
        if exact:
            return sorted(exact, key=lambda n: priority.get(n.type, 99))[0].id
        parts = q.split(".")
        suffix = []
        for n in self.nodes.values():
            kparts = n.key.replace("/", ".").split(".")
            if len(kparts) >= len(parts) and kparts[-len(parts):] == parts:
                suffix.append(n)
            elif len(parts) > 1 and parts[0] in kparts:
                # "geometry.ReferenceLine.to_frenet": package name plus qualname suffix
                if kparts[-(len(parts) - 1):] == parts[1:] and parts[0] in kparts[:-(len(parts) - 1)]:
                    suffix.append(n)
        if suffix:
            return sorted(suffix, key=lambda n: (priority.get(n.type, 99), len(n.id)))[0].id
        low = q.lower()
        labels = [n for n in self.nodes.values() if n.label.lower() == low]
        if labels:
            return sorted(labels, key=lambda n: priority.get(n.type, 99))[0].id
        return None

    def out_edges(self, node_id, edge_type=None):
        return [e for e in self._out.get(node_id, []) if edge_type is None or e.type == edge_type]

    def in_edges(self, node_id, edge_type=None):
        return [e for e in self._in.get(node_id, []) if edge_type is None or e.type == edge_type]

    def neighbors(self, node_id, edge_types=None, direction="both", node_types=None):
        # [(edge, neighbor_id, "out"|"in")], sorted
        node_id = self.resolve(node_id) or node_id
        types = set(as_list(edge_types)) if edge_types else None
        out = []
        if direction in ("both", "out"):
            out += [(e, e.target, "out") for e in self._out.get(node_id, []) if types is None or e.type in types]
        if direction in ("both", "in"):
            out += [(e, e.source, "in") for e in self._in.get(node_id, []) if types is None or e.type in types]
        if node_types:
            out = [x for x in out if self.nodes[x[1]].type in set(as_list(node_types))]
        return sorted(out, key=lambda x: (x[2], x[0].type, x[1]))

    @trace("gotel1994", concept="knowledge_graph_model", note="Breitensuche: kürzester Pfad")
    def path(self, a, b, max_depth=10, directed=False, edge_types=None):
        # shortest path a -> b as list of node ids (empty if none)
        a, b = self.resolve(a), self.resolve(b)
        if a is None or b is None:
            return []
        prev = {a: None}
        queue = deque([(a, 0)])
        while queue:
            nid, depth = queue.popleft()
            if nid == b:
                break
            if depth >= max_depth:
                continue
            for _, other, _ in self.neighbors(nid, edge_types, "out" if directed else "both"):
                if other not in prev:
                    prev[other] = nid
                    queue.append((other, depth + 1))
        if b not in prev:
            return []
        out = [b]
        while prev[out[-1]] is not None:
            out.append(prev[out[-1]])
        return out[::-1]

    def edges_between(self, a, b):
        return [e for e in self._out.get(a, []) if e.target == b] + [e for e in self._out.get(b, []) if e.target == a]

    def subgraph(self, node_ids):
        ids = set(node_ids)
        g = KnowledgeGraph()
        for nid in sorted(ids):
            if nid in self.nodes:
                n = self.nodes[nid]
                g.nodes[nid] = Node(n.id, n.type, n.label, dict(n.data))
        for e in self.edges:
            if e.source in ids and e.target in ids:
                g.add_edge(e.source, e.target, e.type, e.note)
        return g.finalize()

    def neighborhood(self, node_id, depth=1, node_types=None, limit=400):
        start = self.resolve(node_id)
        if start is None:
            return KnowledgeGraph()
        seen = {start}
        frontier = [start]
        for _ in range(depth):
            nxt = []
            for nid in frontier:
                for _, other, _ in self.neighbors(nid, node_types=node_types):
                    if other not in seen and len(seen) < limit:
                        seen.add(other)
                        nxt.append(other)
            frontier = nxt
        return self.subgraph(seen)

    def concept_subgraph(self, concept, depth=2):
        # everything around one concept: implementations, components, sources, documents, tests
        cid = self.resolve(concept if str(concept).startswith("concept:") else f"concept:{concept}") or self.resolve(concept)
        return self.neighborhood(cid, depth) if cid else KnowledgeGraph()

    def search(self, query, node_types=None, limit=50):
        tokens = [t for t in str(query).lower().split() if t]
        if not tokens:
            return []
        hits = []
        for n in self.nodes.values():
            if node_types and n.type not in node_types:
                continue
            hay_main = (n.key + " " + n.label).lower()
            hay_doc = " ".join(str(n.data.get(k, "")) for k in ("summary", "title", "doc")).lower()
            score = 0
            for tok in tokens:
                s = (6 if tok == n.key.lower() or tok == n.label.lower() else 3 if tok in hay_main else
                     1 if tok in hay_doc else 0)
                if s == 0:
                    score = 0
                    break
                score += s
            if score:
                hits.append((-score, len(n.id), n.id))
        return [self.nodes[h[2]] for h in sorted(hits)[:limit]]

    # ------------------------------------------------------------------ "how does X work"
    def explain(self, query):
        # collection of all linked knowledge for X (concept, component, function, package ...)
        nid = self.resolve(query)
        if nid is None:
            return {"query": query, "found": False}
        node = self.nodes[nid]
        groups = {t: [] for t in NODE_TYPES}
        seen = {nid}
        # first ring: direct neighbors; second ring through concepts and implementing code
        ring = [o for _, o, _ in self.neighbors(nid)]
        for other in ring:
            seen.add(other)
        second = []
        for other in list(ring) + [nid]:
            if self.nodes[other].type in ("concept", "component", "model", "function", "class"):
                for e, o2, _ in self.neighbors(other, ("implements", "cites", "tested_by", "documented_by",
                                                       "consumes", "produces", "configured_by", "example_of")):
                    if o2 not in seen:
                        seen.add(o2)
                        second.append(o2)
        for other in ring + second:
            groups[self.nodes[other].type].append(other)
        result = {"query": query, "found": True, "id": nid, "type": node.type, "label": node.label,
                  "data": dict(node.data), "path_to_sources": {}}
        for t, ids in groups.items():
            result[t] = sorted(set(ids))
        for ref in result["reference"]:
            result["path_to_sources"][ref] = self.path(nid, ref, max_depth=4)
        return result

    def explain_markdown(self, query, references=None):
        info = self.explain(query)
        if not info["found"]:
            return f"# Wie funktioniert „{query}“?\n\nKein passender Knoten im Wissensgraph gefunden.\n"
        lines = [f"# Wie funktioniert „{info['label']}“?", "",
                 f"*{NODE_LABELS.get(info['type'], info['type'])}* `{info['id']}`", ""]
        if info["data"].get("summary"):
            lines += [info["data"]["summary"], ""]
        order = ("concept", "package", "module", "component", "model", "class", "function", "datatype", "reference",
                 "document", "test", "example", "config")
        for t in order:
            ids = info.get(t) or []
            if not ids:
                continue
            lines += [f"## {NODE_LABELS[t]}", ""]
            for i in ids:
                n = self.nodes[i]
                text = n.label
                if t == "reference" and references is not None and n.key in references:
                    text = references.cite(n.key, style="full")
                extra = f" – {n.data['summary']}" if n.data.get("summary") and t != "reference" else ""
                lines.append(f"- {text}{extra} (`{i}`)")
            lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------ statistics and export
    def stats(self):
        return {"nodes": len(self.nodes), "edges": len(self.edges),
                "node_types": dict(sorted(Counter(n.type for n in self.nodes.values()).items())),
                "edge_types": dict(sorted(Counter(e.type for e in self.edges).items()))}

    def to_dict(self):
        return {"format_version": 1, "node_types": list(NODE_TYPES), "edge_types": list(EDGE_TYPES),
                "nodes": [n.to_dict() for n in self.nodes.values()], "edges": [e.to_dict() for e in self.edges],
                "stats": self.stats()}

    def to_json(self, indent=1):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, sort_keys=False, default=str)

    @classmethod
    def from_dict(cls, data):
        g = cls()
        for n in data.get("nodes", []):
            n = dict(n)
            nid, ntype, label = n.pop("id"), n.pop("type"), n.pop("label")
            g.nodes[nid] = Node(nid, ntype, label, n)
        for e in data.get("edges", []):
            g.add_edge(e["source"], e["target"], e["type"], e.get("note", ""))
        return g.finalize()

    def to_html(self, title="vdsim Wissensgraph"):
        payload = {"nodes": [{"id": n.id, "type": n.type, "label": n.label,
                              "summary": str(n.data.get("summary", ""))[:300], "path": n.data.get("path", "")}
                             for n in self.nodes.values()],
                   "edges": [[e.source, e.target, e.type] for e in self.edges],
                   "colors": NODE_COLORS, "nodeLabels": NODE_LABELS, "edgeLabels": EDGE_LABELS}
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        return HTML_TEMPLATE.replace("__TITLE__", html.escape(title)).replace("__DATA__", data)


# ---------------------------------------------------------------------------- building
@trace("gotel1994", concept="knowledge_graph_model", note="Knoten und Kanten aus Code, Doku und Quellen")
def build_graph(kb):
    g = KnowledgeGraph()
    refs = kb.references

    # references
    for ref in refs or []:
        g.add_node("reference", ref.id, ref.short(), title=ref.title, summary=ref.full(), ref_type=ref.type,
                   year=ref.year_text, file=f"docs/references/{ref.source_file}", user=ref.user or None)

    # packages, modules, classes, functions
    for pkg in kb.packages.values():
        g.add_node("package", pkg.name, pkg.name, title=pkg.title, summary=pkg.summary, path=pkg.path,
                   documented=pkg.has_meta)
        g.add_node("document", f"docs/generated/{pkg.name}/index.md", f"Doku {pkg.name}", path=f"docs/generated/{pkg.name}/index.md",
                   summary=f"Generierte Paketdokumentation {pkg.name}", generated=True)
        g.add_edge(f"package:{pkg.name}", f"document:docs/generated/{pkg.name}/index.md", "documented_by")
        for sub_dir in pkg.sub_meta:
            g.add_node("document", f"{sub_dir}/module.yaml", f"module.yaml ({sub_dir})", path=f"{sub_dir}/module.yaml",
                       summary=str(pkg.sub_meta[sub_dir].get("summary", "")))
            g.add_edge(f"package:{pkg.name}", f"document:{sub_dir}/module.yaml", "documented_by")
        if pkg.has_meta:
            path = f"{pkg.docs_dir}/module.yaml"
            g.add_node("document", path, f"module.yaml ({pkg.name})", path=path, summary="Modul-Metadaten")
            g.add_edge(f"package:{pkg.name}", f"document:{path}", "documented_by")
        for doc in ([pkg.theory] if pkg.theory else []) + pkg.documents:
            g.add_node("document", doc.path, f"{doc.path.rsplit('/', 1)[-1]} ({pkg.name})", path=doc.path,
                       summary=doc.title)
            g.add_edge(f"package:{pkg.name}", f"document:{doc.path}", "documented_by")
        for ref_id in pkg.meta_list("references"):
            g.add_edge(f"package:{pkg.name}", f"reference:{ref_id}", "cites")
    for pkg in kb.packages.values():
        for other in as_list(pkg.meta.get("related_modules")):
            g.add_edge(f"package:{pkg.name}", f"package:{other}", "related_to")

    traced = {t["implementation"] for t in kb.traces}
    class_index = {}
    for mod in kb.modules.values():
        mid = g.add_node("module", mod.name, mod.name.rsplit(".", 1)[-1] if "." in mod.name else mod.name,
                         summary=mod.summary, path=mod.path, package=mod.package, lines=mod.lines)
        g.add_edge(f"package:{mod.package}", mid, "contains")
        for cls in mod.classes:
            cid = g.add_node("class", cls.id, cls.qualname, summary=first_sentence(cls.doc), path=mod.path,
                             line=cls.lineno, package=mod.package)
            class_index.setdefault(cls.name, []).append((mod.name, cid))
            g.add_edge(mid, cid, "contains")
            for m in cls.methods:
                if m.name.startswith("_") and m.id not in traced:
                    continue
                fid = g.add_node("function", m.id, m.qualname, summary=first_sentence(m.doc), path=mod.path,
                                 line=m.lineno, package=mod.package)
                g.add_edge(cid, fid, "contains")
        for fn in mod.functions:
            if fn.name.startswith("_") and fn.id not in traced:
                continue
            fid = g.add_node("function", fn.id, fn.qualname, summary=first_sentence(fn.doc), path=mod.path,
                             line=fn.lineno, package=mod.package)
            g.add_edge(mid, fid, "contains")
    for mod in kb.modules.values():
        for dep in mod.imports:
            g.add_edge(f"module:{mod.name}", f"module:{dep}", "imports")
        for cls in mod.classes:
            for base in cls.bases:
                bname = base.rsplit(".", 1)[-1]
                candidates = class_index.get(bname, [])
                pick = [c for m, c in candidates if m == mod.name or m in mod.imports or base.startswith(m)]
                pick = pick or (candidates if len(candidates) == 1 else [])
                if pick:
                    g.add_edge(f"class:{cls.id}", pick[0], "subclass_of")

    # data types
    for dt in kb.datatypes.values():
        did = g.add_node("datatype", dt.name, dt.name, summary=dt.description, module=dt.module, legacy=dt.legacy or None)
        if dt.module and f"module:{dt.module}" in g.nodes:
            g.add_edge(f"module:{dt.module}", did, "contains")
            g.add_edge(f"class:{dt.module}.{dt.qualname}", did, "implements")

    # components / models
    for comp in kb.components.values():
        ntype = "model" if comp.is_model else "component"
        nid = g.add_node(ntype, comp.id, comp.label or comp.id, summary=comp.doc.get("summary", ""), kind=comp.kind,
                         version=comp.version, legacy=comp.legacy or None, package=comp.package,
                         path=f"docs/generated/{comp.package}/components/{component_file(comp.id)}")
        if f"module:{comp.module}" in g.nodes:
            g.add_edge(f"module:{comp.module}", nid, "contains")
        impl = f"class:{comp.class_id}" if f"class:{comp.class_id}" in g.nodes else f"function:{comp.class_id}"
        if impl not in g.nodes and comp.class_id:
            impl = g.add_node("function", comp.class_id, comp.qualname, package=comp.package)
        g.add_edge(impl, nid, "implements")
        page = f"docs/generated/{comp.package}/components/{component_file(comp.id)}"
        g.add_node("document", page, f"Seite {comp.id}", path=page, generated=True)
        g.add_edge(nid, f"document:{page}", "documented_by")
        for port in comp.inputs.values():
            g.add_edge(nid, f"datatype:{port.get('type', 'Any')}", "consumes")
        for port in comp.outputs.values():
            g.add_edge(nid, f"datatype:{port.get('type', 'Any')}", "produces")
        for ref_id in as_list(comp.doc.get("references")):
            g.add_edge(nid, f"reference:{ref_id}", "cites")
        if comp.interface:
            mod, _, qual = comp.interface.rpartition(".")
            g.add_edge(impl, f"class:{comp.interface}", "subclass_of")

    # concepts
    for c in kb.concepts.values():
        cid = g.add_node("concept", c.id, c.title, summary=_concept_summary(c), package=c.package,
                         documented=c.documented, path=c.section.file if c.section else "")
        if c.section is not None:
            g.add_edge(cid, f"document:{c.section.file}", "documented_by")
            for ref_id, _ in c.section.citations:
                g.add_edge(cid, f"reference:{ref_id}", "cites")
        for pkg in c.packages:
            g.add_edge(f"package:{pkg}", cid, "contains" if pkg == c.package else "related_to")
        for comp_id in c.components:
            comp = kb.components[comp_id]
            g.add_edge(f"{'model' if comp.is_model else 'component'}:{comp_id}", cid, "implements")
    # concept <-> concept links inside theory sections ("[...](#other-id)")
    import re
    for c in kb.concepts.values():
        if c.section is not None:
            for other in sorted(set(re.findall(r"\]\(#([A-Za-z0-9_.:\-]+)\)", c.section.text))):
                g.add_edge(f"concept:{c.id}", f"concept:{other}", "related_to")

    # traces: implementation -> concept -> reference
    for t in kb.traces:
        impl = t["implementation"]
        nid = f"function:{impl}" if f"function:{impl}" in g.nodes else f"class:{impl}"
        if nid not in g.nodes:
            nid = g.add_node("function", impl, t["qualname"], package=t["package"])
            if f"module:{t['module']}" in g.nodes:
                g.add_edge(f"module:{t['module']}", nid, "contains")
        note = " ".join(p for p in (f"Abschn. {t['section']}" if t.get("section") else "", t.get("equation", "")) if p)
        if t.get("concept"):
            g.add_edge(nid, f"concept:{t['concept']}", "implements", note)
            if t.get("source"):
                g.add_edge(f"concept:{t['concept']}", f"reference:{t['source']}", "cites")
        if t.get("source"):
            g.add_edge(nid, f"reference:{t['source']}", "cites", note)
        for test in as_list(t.get("tests")):
            test = str(test).split("::")[0]
            if test in kb.tests:
                g.add_node("test", test, test.rsplit("/", 1)[-1], path=test)
                g.add_edge(nid, f"test:{test}", "tested_by")

    # tests, examples, configs
    for usage in kb.tests.values():
        tid = g.add_node("test", usage.path, usage.path.rsplit("/", 1)[-1], path=usage.path,
                         summary=first_sentence(usage.doc) or ", ".join(n for n, _ in usage.functions[:6]))
        for m in usage.modules:
            g.add_edge(f"module:{m}", tid, "tested_by")
        for c in usage.components:
            g.add_edge(_comp_node(g, c), tid, "tested_by")
        for pkg in usage.shows:
            g.add_edge(f"package:{pkg}", tid, "tested_by", usage.shows[pkg])
    for usage in kb.examples.values():
        eid = g.add_node("example", usage.path, usage.path.rsplit("/", 1)[-1], path=usage.path,
                         summary=first_sentence(usage.doc))
        for m in usage.modules:
            g.add_edge(eid, f"module:{m}", "example_of")
        for c in usage.components:
            g.add_edge(eid, _comp_node(g, c), "example_of")
    for pkg in kb.packages.values():
        for ex in pkg.meta_list("examples"):
            g.add_edge(f"example:{ex}", f"package:{pkg.name}", "example_of")
    for usage in kb.configs.values():
        if not usage.components and not usage.related:
            continue
        cid = g.add_node("config", usage.path, usage.title or usage.path, path=usage.path, summary=usage.doc)
        for c in usage.components:
            g.add_edge(_comp_node(g, c), cid, "configured_by")
        for other in usage.related:
            g.add_node("config", other, other.rsplit("/", 1)[-1], path=other)
            g.add_edge(cid, f"config:{other}", "related_to")

    # user links (links.yaml): target -cites-> reference
    for link in refs.links if refs else []:
        target = g.resolve(link["target"])
        if target:
            g.add_edge(target, f"reference:{link['reference']}", "cites", link.get("note", ""))
        else:
            kb.warn(f"links.yaml: Ziel '{link['target']}' nicht im Wissensgraph")
    return g.finalize()


def _comp_node(g, cid):
    return f"model:{cid}" if f"model:{cid}" in g.nodes else f"component:{cid}"


def _concept_summary(c):
    if c.section is None:
        return ""
    body = c.section.subsection("Ziel") or c.section.subsection("In einfachen Worten") or c.section.text
    return first_sentence(body.replace("\n", " "))


def component_file(component_id):
    return component_id.replace("/", "__").replace("@", "_") + ".md"


# ---------------------------------------------------------------------------- force layout
@trace("fruchterman1991", concept="force_directed_layout", note="Abstoßung k²/d, Anziehung d²/k, Abkühlung")
def force_layout(n, edges, iterations=200, seed=0, size=1.0, positions=None):
    # Fruchterman-Reingold layout (deterministic for a given seed); returns an (n, 2) array
    if n == 0:
        return np.zeros((0, 2))
    rng = np.random.default_rng(seed)
    pos = rng.uniform(-size, size, (n, 2)) if positions is None else np.array(positions, dtype=float)
    if n == 1:
        return np.zeros((1, 2))
    edges = np.array([(a, b) for a, b in edges if a != b], dtype=int).reshape(-1, 2)
    k = size * np.sqrt(4.0 / n)               # ideal edge length for the area (2 size)^2
    temp = size * 0.2
    cool = temp / (iterations + 1)
    for _ in range(iterations):
        delta = pos[:, None, :] - pos[None, :, :]
        dist2 = np.maximum((delta ** 2).sum(-1), 1e-6 * k * k)
        rep = (k * k / dist2)[:, :, None] * delta               # repulsion k^2 / d (direction delta / d)
        disp = rep.sum(axis=1)
        if len(edges):
            d = pos[edges[:, 0]] - pos[edges[:, 1]]
            dist = np.maximum(np.linalg.norm(d, axis=1), 1e-9)
            att = (dist / k)[:, None] * d                       # attraction d^2 / k
            np.add.at(disp, edges[:, 0], -att)
            np.add.at(disp, edges[:, 1], att)
        disp -= 0.01 * pos / k                                   # weak gravity keeps components together
        length = np.maximum(np.linalg.norm(disp, axis=1), 1e-9)
        pos += disp / length[:, None] * np.minimum(length, temp)[:, None]
        temp = max(temp - cool, 1e-4 * size)
    pos -= pos.mean(axis=0)
    scale = np.abs(pos).max()
    return pos / scale * size if scale > 0 else pos


# ---------------------------------------------------------------------------- standalone HTML
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root { --bg:#1e1f22; --panel:#26282c; --border:#3a3d43; --text:#e6e6e6; --muted:#9a9ca3; --accent:#3987e5; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--text); font:13px/1.45 "Segoe UI", system-ui, sans-serif; display:flex; height:100vh; overflow:hidden; }
#side { width:330px; min-width:260px; background:var(--panel); border-right:1px solid var(--border); display:flex; flex-direction:column; }
#side header { padding:10px 12px; border-bottom:1px solid var(--border); }
h1 { font-size:15px; margin:0 0 6px 0; }
input[type=search] { width:100%; padding:6px 8px; background:#1e1f22; color:var(--text); border:1px solid #44474e; border-radius:4px; }
#filters { padding:8px 12px; border-bottom:1px solid var(--border); display:flex; flex-wrap:wrap; gap:4px 10px; }
#filters label { display:flex; align-items:center; gap:4px; cursor:pointer; color:var(--muted); }
.dot { width:10px; height:10px; border-radius:50%; display:inline-block; }
#results { max-height:28%; overflow:auto; border-bottom:1px solid var(--border); }
#results div, #neighbors div { padding:3px 12px; cursor:pointer; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
#results div:hover, #neighbors div:hover { background:#2f3237; }
#details { padding:10px 12px; overflow:auto; flex:1; }
#details h2 { font-size:14px; margin:0 0 4px 0; }
.muted { color:var(--muted); }
.tag { font-size:11px; padding:1px 6px; border-radius:8px; border:1px solid var(--border); }
#canvas { flex:1; display:block; cursor:grab; }
#bar { position:absolute; right:12px; top:10px; display:flex; gap:6px; }
button { background:#2f3237; color:var(--text); border:1px solid #44474e; border-radius:4px; padding:4px 10px; cursor:pointer; }
button:hover { border-color:var(--accent); }
#stats { position:absolute; right:12px; bottom:8px; color:var(--muted); }
</style>
</head>
<body>
<aside id="side">
  <header><h1>__TITLE__</h1><input id="q" type="search" placeholder="Suche (Name, Konzept, Quelle …)"></header>
  <div id="filters"></div>
  <div id="results"></div>
  <div id="details"><p class="muted">Knoten anklicken für Details und Nachbarn. Mausrad zoomt, Ziehen verschiebt
  die Ansicht, Ziehen eines Knotens verschiebt den Knoten.</p></div>
</aside>
<canvas id="canvas"></canvas>
<div id="bar"><button id="focus">Nur Nachbarschaft</button><button id="all">Alles</button><button id="run">Layout ▶</button></div>
<div id="stats"></div>
<script id="graph-data" type="application/json">__DATA__</script>
<script>
(function () {
  "use strict";
  const DATA = JSON.parse(document.getElementById("graph-data").textContent);
  const nodes = DATA.nodes, idx = new Map();
  nodes.forEach((n, i) => { idx.set(n.id, i); n.nb = []; });
  const edges = [];
  DATA.edges.forEach(e => { const a = idx.get(e[0]), b = idx.get(e[1]); if (a === undefined || b === undefined) return;
    edges.push({a: a, b: b, t: e[2]}); nodes[a].nb.push([b, e[2], "out"]); nodes[b].nb.push([a, e[2], "in"]); });
  // deterministic initial positions (golden-angle spiral, grouped by type)
  const types = Object.keys(DATA.colors);
  nodes.forEach((n, i) => { const r = 30 * Math.sqrt(i + 1), a = i * 2.39996 + types.indexOf(n.type);
    n.x = r * Math.cos(a); n.y = r * Math.sin(a); n.vx = 0; n.vy = 0; });
  const hidden = new Set(["function", "class", "module", "document"]);
  let focusSet = null, selected = -1, running = true, alpha = 1.0;
  const canvas = document.getElementById("canvas"), ctx = canvas.getContext("2d");
  let view = {x: 0, y: 0, s: 0.6}, W = 0, H = 0;
  function resize() { W = canvas.width = canvas.clientWidth * devicePixelRatio; H = canvas.height = canvas.clientHeight * devicePixelRatio; }
  window.addEventListener("resize", resize); resize();
  function visible(i) { const n = nodes[i]; if (focusSet) return focusSet.has(i); return !hidden.has(n.type); }
  // filters
  const filters = document.getElementById("filters");
  types.forEach(t => { const l = document.createElement("label");
    l.innerHTML = '<input type="checkbox"' + (hidden.has(t) ? "" : " checked") + '><span class="dot" style="background:' + DATA.colors[t] + '"></span>' + DATA.nodeLabels[t];
    l.firstChild.addEventListener("change", ev => { if (ev.target.checked) hidden.delete(t); else hidden.add(t); focusSet = null; alpha = 1; running = true; });
    filters.appendChild(l); });
  // physics: repulsion on a spatial grid (O(n)), springs on edges, weak gravity
  function tick() {
    const vis = []; for (let i = 0; i < nodes.length; i++) if (visible(i)) vis.push(i);
    const cell = 120, grid = new Map();
    vis.forEach(i => { const n = nodes[i], k = Math.floor(n.x / cell) + "," + Math.floor(n.y / cell);
      if (!grid.has(k)) grid.set(k, []); grid.get(k).push(i); });
    vis.forEach(i => { const n = nodes[i], cx = Math.floor(n.x / cell), cy = Math.floor(n.y / cell);
      for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) { const g = grid.get((cx + dx) + "," + (cy + dy)); if (!g) continue;
        g.forEach(j => { if (j <= i) return; const m = nodes[j]; let ux = n.x - m.x, uy = n.y - m.y, d2 = ux * ux + uy * uy + 0.01;
          if (d2 > cell * cell) return; const f = 900 / d2 * alpha; n.vx += ux * f; n.vy += uy * f; m.vx -= ux * f; m.vy -= uy * f; }); } });
    edges.forEach(e => { if (!visible(e.a) || !visible(e.b)) return; const n = nodes[e.a], m = nodes[e.b];
      const ux = m.x - n.x, uy = m.y - n.y, d = Math.sqrt(ux * ux + uy * uy) + 0.01, f = (d - 60) / d * 0.04 * alpha;
      n.vx += ux * f; n.vy += uy * f; m.vx -= ux * f; m.vy -= uy * f; });
    vis.forEach(i => { const n = nodes[i]; if (n.fixed) { n.vx = n.vy = 0; return; } n.vx -= n.x * 0.002 * alpha; n.vy -= n.y * 0.002 * alpha;
      n.vx *= 0.6; n.vy *= 0.6; const v = Math.hypot(n.vx, n.vy); if (v > 40) { n.vx *= 40 / v; n.vy *= 40 / v; } n.x += n.vx; n.y += n.vy; });
    alpha = Math.max(alpha * 0.995, 0.02);
  }
  function toScreen(n) { return [(n.x - view.x) * view.s * devicePixelRatio + W / 2, (n.y - view.y) * view.s * devicePixelRatio + H / 2]; }
  function draw() {
    ctx.clearRect(0, 0, W, H); ctx.fillStyle = "#1e1f22"; ctx.fillRect(0, 0, W, H);
    const nbSel = new Set(); if (selected >= 0) nodes[selected].nb.forEach(x => nbSel.add(x[0]));
    ctx.lineWidth = 1 * devicePixelRatio;
    edges.forEach(e => { if (!visible(e.a) || !visible(e.b)) return; const p = toScreen(nodes[e.a]), q = toScreen(nodes[e.b]);
      const hot = selected >= 0 && (e.a === selected || e.b === selected);
      ctx.strokeStyle = hot ? "rgba(57,135,229,0.9)" : "rgba(150,150,160,0.18)"; ctx.beginPath(); ctx.moveTo(p[0], p[1]); ctx.lineTo(q[0], q[1]); ctx.stroke(); });
    const showLabels = view.s > 0.9;
    nodes.forEach((n, i) => { if (!visible(i)) return; const p = toScreen(n), r = (i === selected ? 8 : n.type === "package" ? 7 : 4.5) * devicePixelRatio;
      ctx.fillStyle = DATA.colors[n.type] || "#888"; ctx.globalAlpha = selected < 0 || i === selected || nbSel.has(i) ? 1 : 0.35;
      ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, 6.2832); ctx.fill();
      if (showLabels || i === selected || nbSel.has(i) || n.type === "package") { ctx.fillStyle = "#e6e6e6"; ctx.font = (11 * devicePixelRatio) + "px Segoe UI, sans-serif"; ctx.fillText(n.label, p[0] + r + 3, p[1] + 4); }
      ctx.globalAlpha = 1; });
    let cnt = 0; for (let i = 0; i < nodes.length; i++) if (visible(i)) cnt++;
    document.getElementById("stats").textContent = cnt + " von " + nodes.length + " Knoten, " + edges.length + " Kanten";
  }
  function loop() { if (running) { tick(); if (alpha <= 0.021) running = false; } draw(); requestAnimationFrame(loop); }
  // interaction
  let drag = null, last = null;
  function pick(mx, my) { let best = -1, bd = 12 * 12; nodes.forEach((n, i) => { if (!visible(i)) return; const p = toScreen(n);
      const dx = (p[0] - mx * devicePixelRatio) / devicePixelRatio, dy = (p[1] - my * devicePixelRatio) / devicePixelRatio, d = dx * dx + dy * dy; if (d < bd) { bd = d; best = i; } }); return best; }
  canvas.addEventListener("mousedown", ev => { const i = pick(ev.offsetX, ev.offsetY); last = [ev.offsetX, ev.offsetY];
    if (i >= 0) { drag = {node: i}; nodes[i].fixed = true; select(i); } else drag = {pan: true}; });
  window.addEventListener("mousemove", ev => { if (!drag) return; const dx = ev.offsetX - last[0], dy = ev.offsetY - last[1]; last = [ev.offsetX, ev.offsetY];
    if (drag.pan) { view.x -= dx / view.s; view.y -= dy / view.s; } else { const n = nodes[drag.node]; n.x += dx / view.s; n.y += dy / view.s; } });
  window.addEventListener("mouseup", () => { if (drag && drag.node !== undefined) nodes[drag.node].fixed = false; drag = null; });
  canvas.addEventListener("wheel", ev => { ev.preventDefault(); view.s *= ev.deltaY < 0 ? 1.15 : 1 / 1.15; view.s = Math.min(Math.max(view.s, 0.05), 8); }, {passive: false});
  function esc(s) { return String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c])); }
  function select(i) {
    selected = i; const n = nodes[i];
    let h = '<h2>' + esc(n.label) + '</h2><span class="tag" style="border-color:' + DATA.colors[n.type] + '">' + esc(DATA.nodeLabels[n.type]) + '</span> <span class="muted">' + esc(n.id) + '</span>';
    if (n.summary) h += '<p>' + esc(n.summary) + '</p>'; if (n.path) h += '<p class="muted">' + esc(n.path) + '</p>';
    h += '<h2 style="margin-top:10px">Nachbarn (' + n.nb.length + ')</h2><div id="neighbors">';
    n.nb.slice().sort((x, y) => (x[1] + nodes[x[0]].label).localeCompare(y[1] + nodes[y[0]].label)).forEach(x => {
      const m = nodes[x[0]]; h += '<div data-i="' + x[0] + '"><span class="dot" style="background:' + DATA.colors[m.type] + '"></span> ' +
        '<span class="muted">' + (x[2] === "out" ? "" : "← ") + esc(DATA.edgeLabels[x[1]]) + (x[2] === "out" ? " →" : "") + '</span> ' + esc(m.label) + '</div>'; });
    h += '</div>'; const d = document.getElementById("details"); d.innerHTML = h;
    d.querySelectorAll("#neighbors div").forEach(el => el.addEventListener("click", () => { const j = +el.dataset.i; if (!visible(j)) hidden.delete(nodes[j].type); center(j); select(j); }));
  }
  function center(i) { view.x = nodes[i].x; view.y = nodes[i].y; }
  document.getElementById("q").addEventListener("input", ev => { const q = ev.target.value.toLowerCase().trim(), box = document.getElementById("results"); box.innerHTML = "";
    if (!q) return; nodes.map((n, i) => [n, i]).filter(x => (x[0].label + " " + x[0].id + " " + x[0].summary).toLowerCase().includes(q)).slice(0, 60).forEach(x => {
      const el = document.createElement("div"); el.innerHTML = '<span class="dot" style="background:' + DATA.colors[x[0].type] + '"></span> ' + esc(x[0].label) + ' <span class="muted">' + esc(DATA.nodeLabels[x[0].type]) + '</span>';
      el.addEventListener("click", () => { hidden.delete(x[0].type); center(x[1]); select(x[1]); }); box.appendChild(el); }); });
  document.getElementById("focus").addEventListener("click", () => { if (selected < 0) return; focusSet = new Set([selected]);
    nodes[selected].nb.forEach(x => { focusSet.add(x[0]); nodes[x[0]].nb.forEach(y => { if (focusSet.size < 250) focusSet.add(y[0]); }); }); alpha = 1; running = true; });
  document.getElementById("all").addEventListener("click", () => { focusSet = null; alpha = 1; running = true; });
  document.getElementById("run").addEventListener("click", () => { alpha = 1; running = true; });
  loop();
})();
</script>
</body>
</html>
"""
