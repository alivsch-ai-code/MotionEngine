"""Documentation generator: docs/generated/<package>/ for every package (deterministic, idempotent).

Per package:
    index.md          overview, architecture, design decisions, implementation
    interfaces.md     components, ports, types, versions, public API
    configuration.md  parameters with unit, limits, default
    theory.md         hand-written theory (vdsim/<package>/docs/theory.md) or "noch nicht dokumentiert"
    examples.md, limitations.md, validation.md, references.md
    traceability.md   implementation -> equation / concept -> source -> test
    components/<kind>__<name>.md   one page per component
Global:
    README.md, traceability_matrix.md, references.md, references.bib, report.md,
    knowledge_graph.json, knowledge_graph.html, _meta.json (the only file with a time stamp)

Pages are written only if their content changed; files of a previous run that are no longer
produced are removed. The page builders are also used by the GUI (Linker in "gui" mode
creates "node:<id>" links instead of file links).
"""

from __future__ import annotations

import json
import posixpath
import re
from datetime import datetime, timezone
from pathlib import Path

from ..framework.knowledge import trace
from .collector import as_list, first_sentence, humanize
from .graph import EDGE_LABELS, NODE_LABELS, build_graph, component_file
from .paths import generated_dir
from .references import CITATION_PATTERN, TYPE_LABELS, parse_citations

PAGES = ("index", "interfaces", "configuration", "theory", "examples", "limitations", "validation", "references",
         "traceability")
PAGE_TITLES = {"index": "Übersicht", "interfaces": "Schnittstellen", "configuration": "Konfiguration",
               "theory": "Theorie und Verfahren", "examples": "Beispiele", "limitations": "Einschränkungen",
               "validation": "Validierung", "references": "Quellen", "traceability": "Rückverfolgbarkeit"}
GENERATED_NOTE = "> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten."
THEORY_SUBSECTIONS = ("Ziel und Zweck", "Theorie", "Herleitung", "Annahmen", "Randbedingungen", "Variablen",
                      "Anwendungsgrenzen", "Vor- und Nachteile", "Numerische Aspekte", "Praktische Auswirkungen",
                      "In einfachen Worten", "Quellen")


# ---------------------------------------------------------------------------- links
class Linker:
    # file mode: relative Markdown links from the page directory; gui mode: "node:<graph id>" links
    def __init__(self, kb, mode="file", base="docs/generated"):
        self.kb, self.mode, self.base = kb, mode, base

    def at(self, base):
        return Linker(self.kb, self.mode, base)

    def _rel(self, target):
        return posixpath.relpath(target, self.base) if self.mode == "file" else target

    def pkg(self, name, page="index", anchor=""):
        if self.mode == "gui":
            return f"page:{name}/{page}" + (f"#{anchor}" if anchor else "")
        return self._rel(f"docs/generated/{name}/{page}.md") + (f"#{anchor}" if anchor else "")

    def comp(self, cid):
        comp = self.kb.components.get(cid)
        if self.mode == "gui":
            return f"node:{'model' if comp and comp.is_model else 'component'}:{cid}"
        pkg = comp.package if comp else "unknown"
        return self._rel(f"docs/generated/{pkg}/components/{component_file(cid)}")

    def concept(self, cid):
        c = self.kb.concepts.get(cid)
        if self.mode == "gui":
            return f"node:concept:{cid}"
        if c is not None and c.package:
            return self._rel(f"docs/generated/{c.package}/theory.md") + f"#{cid}"
        return self._rel("docs/generated/README.md") + "#konzepte-ohne-dokumentation"

    def ref(self, rid):
        return f"node:reference:{rid}" if self.mode == "gui" else self._rel("docs/generated/references.md") + f"#{rid}"

    def source(self, path, line=None):
        if self.mode == "gui":
            return f"src:{path}" + (f"#L{line}" if line else "")
        return self._rel(path) + (f"#L{line}" if line else "")

    def module(self, name):
        if self.mode == "gui":
            return f"node:module:{name}"
        mod = self.kb.modules.get(name)
        return self.source(mod.path) if mod else "#"

    def impl(self, dotted):
        if self.mode == "gui":
            fn = self.kb.function(dotted)
            kind = "class" if fn is not None and fn.__class__.__name__ == "ClassInfo" else "function"
            return f"node:{kind}:{dotted}"
        fn = self.kb.function(dotted)
        module, _ = self.kb.split_implementation(dotted)
        mod = self.kb.modules.get(module)
        return self.source(mod.path, fn.lineno if fn else None) if mod else "#"

    def test(self, path):
        return f"node:test:{path}" if self.mode == "gui" else self._rel(path)

    def any(self, path):
        return f"src:{path}" if self.mode == "gui" else self._rel(path)


# ---------------------------------------------------------------------------- markdown helpers
def md_escape(text):
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def table(header, rows):
    if not rows:
        return ""
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(md_escape(c) if not str(c).startswith("[") else str(c).replace("\n", " ")
                               for c in row) + " |" for row in rows]
    return "\n".join(out) + "\n"


def fmt_value(value):
    if value is None:
        return "–"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (list, tuple)):
        text = ", ".join(fmt_value(v) for v in value[:8]) + (", …" if len(value) > 8 else "")
        return f"[{text}]"
    if isinstance(value, dict):
        return "{…}"
    text = str(value)
    return text if len(text) < 60 else text[:57] + "…"


def bullet(items):
    out = []
    for item in as_list(items):
        if isinstance(item, dict):
            out.append("- " + "; ".join(f"**{k}:** {v}" for k, v in item.items()))
        else:
            out.append(f"- {item}")
    return "\n".join(out) + ("\n" if out else "")


def cite_text(kb, text, linker):
    # "[@werling2011, Abschn. 3.4]" -> "[Werling (2011, Abschn. 3.4)](...)"
    refs = kb.references

    def repl(m):
        parts = []
        for rid, loc in parse_citations(m.group(0)):
            label = refs.cite(rid, loc) if rid in refs else f"{rid}?{', ' + loc if loc else ''}"
            parts.append(f"[{label}]({linker.ref(rid)})")
        return "[" + "; ".join(parts) + "]" if parts else m.group(0)
    text = CITATION_PATTERN.sub(repl, text or "")
    # links to concept anchors of other theory pages: "](#concept-id)"
    return re.sub(r"\]\(#([A-Za-z0-9_.:\-]+)\)",
                  lambda m: f"]({linker.concept(m.group(1))})" if m.group(1) in kb.concepts else m.group(0), text)


def ref_links(kb, ids, linker):
    out = []
    for rid in sorted(set(str(i) for i in as_list(ids) if i)):
        label = kb.references.cite(rid) if rid in kb.references else f"{rid} (fehlt in docs/references)"
        out.append(f"[{label}]({linker.ref(rid)})")
    return ", ".join(out)


def concept_links(kb, ids, linker):
    out = []
    for cid in sorted(set(str(i) for i in as_list(ids) if i)):
        c = kb.concepts.get(cid)
        title = c.title if c else humanize(cid)
        out.append(f"[{title}]({linker.concept(cid)})" + ("" if c and c.documented else " (undokumentiert)"))
    return ", ".join(out)


def nav(pkg_name, linker, current):
    items = []
    for page in PAGES:
        label = PAGE_TITLES[page]
        items.append(f"**{label}**" if page == current else f"[{label}]({linker.pkg(pkg_name, page)})")
    return " · ".join(items) + "\n"


def header(pkg, linker, page):
    title = f"# {pkg.title} – {PAGE_TITLES[page]}" if page != "index" else f"# {pkg.title}"
    lines = [title, "", GENERATED_NOTE, "", nav(pkg.name, linker, page)]
    return "\n".join(lines) + "\n"


def stub_notice(pkg):
    return (f"> **Automatischer Stub:** Für `{pkg.dotted}` gibt es noch keine handgeschriebene Dokumentation "
            f"(`{pkg.docs_dir}/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. "
            f"Vorlage anlegen: `python tools/build_docs.py --init {pkg.name}`\n\n")


# ---------------------------------------------------------------------------- package pages
def page_index(kb, pkg, linker):
    meta = pkg.meta
    out = [header(pkg, linker, "index")]
    if not pkg.has_meta:
        out.append(stub_notice(pkg))
    out.append(f"`{pkg.dotted}` · Quellcode: [{pkg.path}/]({linker.source(pkg.path)})"
               + (f" · Paketdoku: [{pkg.docs_dir}/]({linker.source(pkg.docs_dir)})" if pkg.has_meta else "") + "\n")
    out.append("## Übersicht\n")
    if meta.get("summary"):
        out.append(f"**{str(meta['summary']).strip()}**\n")
    if meta.get("purpose"):
        out.append(cite_text(kb, str(meta["purpose"]).strip(), linker) + "\n")
    if pkg.doc and pkg.doc.strip() != str(meta.get("summary", "")).strip():
        out.append("Paket-Docstring:\n\n```text\n" + pkg.doc.strip() + "\n```\n")
    stats = [("Module", len(pkg.modules)), ("Komponenten", len(pkg.components)), ("Verfahren/Konzepte", len(pkg.concepts)),
             ("@trace-Einträge", len(pkg.traces)), ("Tests", len(pkg.tests)), ("Beispiele", len(pkg.examples))]
    out.append(table(["Kennzahl", "Anzahl"], [(k, v) for k, v in stats]))
    out.append("## Architektur\n")
    if meta.get("architecture"):
        out.append(cite_text(kb, str(meta["architecture"]).strip(), linker) + "\n")
    if meta.get("data_flow"):
        out.append("### Datenfluss\n\n" + str(meta["data_flow"]).strip() + "\n")
    rows = []
    for name in pkg.modules:
        mod = kb.modules[name]
        rows.append((f"[`{name}`]({linker.module(name)})", mod.lines, ", ".join(c.name for c in mod.classes[:6]) or "–",
                     first_sentence(mod.doc) or "–"))
    out.append("### Module\n\n" + table(["Modul", "Zeilen", "Klassen", "Inhalt"], rows))
    deps = sorted({kb.modules[d].package for m in pkg.modules for d in kb.modules[m].imports} - {pkg.name})
    users = sorted({mod.package for mod in kb.modules.values() if mod.package != pkg.name
                    and any(kb.modules.get(d) and kb.modules[d].package == pkg.name for d in mod.imports)})
    out.append("### Abhängigkeiten\n")
    out.append(f"- nutzt: {', '.join(f'[{d}]({linker.pkg(d)})' for d in deps) or '–'}")
    out.append(f"- genutzt von: {', '.join(f'[{u}]({linker.pkg(u)})' for u in users) or '–'}")
    ext = sorted({e for m in pkg.modules for e in kb.modules[m].external_imports})
    out.append(f"- externe Bibliotheken: {', '.join(f'`{e}`' for e in ext) or '–'}\n")
    out.append("## Designentscheidungen\n")
    decisions = as_list(meta.get("design_decisions"))
    if decisions:
        rows = [(d.get("decision", ""), cite_text(kb, str(d.get("reason", "")), linker), d.get("alternatives", "–"))
                if isinstance(d, dict) else (str(d), "", "") for d in decisions]
        out.append(table(["Entscheidung", "Begründung", "Alternativen"], rows))
    else:
        out.append("_Noch nicht dokumentiert._\n")
    out.append("## Implementierung\n")
    out.append(bullet(meta.get("implementation")) or "_Keine Implementierungshinweise in module.yaml._\n")
    if pkg.components:
        out.append("### Komponenten\n")
        rows = [(f"[`{c}`]({linker.comp(c)})", kb.components[c].label or "–", kb.components[c].version,
                 first_sentence(kb.components[c].doc.get("summary", "")) or "–") for c in pkg.components]
        out.append(table(["Komponente", "Bezeichnung", "Version", "Kurzbeschreibung"], rows))
    if pkg.concepts:
        out.append("### Verfahren und Konzepte\n")
        out.append(bullet([concept_links(kb, [c], linker) for c in pkg.concepts]))
    if meta.get("models"):
        out.append("### Modelle\n\n" + bullet(meta.get("models")))
    out.append("## Erweiterungspunkte\n")
    out.append(bullet(meta.get("extension_points")) or "_Keine angegeben._\n")
    if meta.get("expert") or meta.get("stability"):
        out.append("## Expertenmodus: Stabilitätsbetrachtungen und Hinweise\n")
        for key in ("stability", "expert"):
            if meta.get(key):
                out.append(cite_text(kb, str(meta[key]).strip(), linker) + "\n")
    if pkg.sub_meta:
        out.append("## Unterpakete mit eigener Doku\n")
        rows = [(f"[{d}]({linker.source(d)})", str(m.get("title", "")) or "–", first_sentence(str(m.get("summary", ""))) or "–")
                for d, m in sorted(pkg.sub_meta.items())]
        out.append(table(["Ordner", "Titel", "Kurzfassung"], rows))
    related = as_list(meta.get("related_modules"))
    if related:
        out.append("## Verwandte Module\n\n" + ", ".join(f"[{r}]({linker.pkg(r)})" for r in related) + "\n")
    if meta.get("references"):
        out.append("## Hauptquellen\n\n" + ref_links(kb, meta.get("references"), linker) + "\n")
    return "\n".join(out)


def _port_rows(ports):
    rows = []
    for name, p in sorted(ports.items()):
        flags = ", ".join(f for f, on in (("optional", p.get("optional")), ("Rückführung", p.get("feedback"))) if on)
        rows.append((f"`{name}`", f"`{p.get('type', 'Any')}`", p.get("unit") or "–", p.get("description") or "–",
                     flags or "–"))
    return rows


def page_interfaces(kb, pkg, linker):
    out = [header(pkg, linker, "interfaces")]
    if not pkg.has_meta:
        out.append(stub_notice(pkg))
    out.append("## Komponenten\n")
    if not pkg.components:
        out.append("_Dieses Paket registriert keine Komponenten._\n")
    for cid in pkg.components:
        comp = kb.components[cid]
        out.append(f"### [{comp.label or cid}]({linker.comp(cid)})\n")
        meta_rows = [("Spec", f"`{cid}`" + (f"@{comp.version}" if not comp.legacy else "")),
                     ("Versionen", ", ".join(comp.versions) or "–"),
                     ("Registry", "klassisch (`vdsim.core.registry`)" if comp.legacy else "versioniert (`vdsim.framework.plugins`)"),
                     ("Klasse", f"`{comp.module}.{comp.qualname}`"), ("Schnittstelle", f"`{comp.interface}`" if comp.interface else "–")]
        if not comp.legacy:
            meta_rows += [("Periode", f"{comp.period} s" if comp.period else "jeder Schritt"),
                          ("Direkter Durchgriff", "ja" if comp.direct_feedthrough else "nein"), ("Sprache", comp.language)]
        out.append(table(["Eigenschaft", "Wert"], meta_rows))
        if comp.inputs:
            out.append("Eingänge:\n\n" + table(["Port", "Typ", "Einheit", "Beschreibung", "Merkmale"], _port_rows(comp.inputs)))
        if comp.outputs:
            out.append("Ausgänge:\n\n" + table(["Port", "Typ", "Einheit", "Beschreibung", "Merkmale"], _port_rows(comp.outputs)))
    types = [dt for dt in kb.datatypes.values() if dt.module and kb.package_of(dt.module) == pkg.name]
    if types:
        out.append("## Datentypen\n")
        for dt in sorted(types, key=lambda d: d.name):
            out.append(f"### `{dt.name}`\n\n{dt.description or ''}\n\nDefiniert in `{dt.module}.{dt.qualname}`.\n")
            if dt.fields:
                out.append(table(["Feld", "Typ", "Default"], [(f"`{f[0]}`", f[1], f[2] or "–") for f in dt.fields]))
    out.append("## Öffentliche API\n")
    for name in pkg.modules:
        mod = kb.modules[name]
        items = [(c.qualname, c.lineno, first_sentence(c.doc), "Klasse") for c in mod.classes if not c.name.startswith("_")]
        items += [(f.qualname + "(" + ", ".join(a for a in f.args if a not in ("self", "cls")) + ")", f.lineno,
                   first_sentence(f.doc), "Funktion") for f in mod.functions if not f.name.startswith("_")]
        if not items:
            continue
        out.append(f"### `{name}`\n")
        rows = [(f"[`{n}`]({linker.source(mod.path, line)})", kind, doc or "–") for n, line, doc, kind in items]
        out.append(table(["Name", "Art", "Beschreibung"], rows))
    return "\n".join(out)


def page_configuration(kb, pkg, linker):
    out = [header(pkg, linker, "configuration")]
    if not pkg.has_meta:
        out.append(stub_notice(pkg))
    entries = as_list(pkg.meta.get("configuration"))
    out.append("## Konfigurationsmöglichkeiten (Paketdoku)\n")
    if entries:
        rows = [(f"`{e.get('name', '')}`", e.get("description", ""), e.get("unit", "–"), fmt_value(e.get("default")))
                if isinstance(e, dict) else (str(e), "", "", "") for e in entries]
        out.append(table(["Name", "Beschreibung", "Einheit", "Default"], rows))
    else:
        out.append("_Keine Einträge in module.yaml._\n")
    for cid in pkg.components:
        comp = kb.components[cid]
        if not comp.params and not comp.config_fields:
            continue
        out.append(f"## Parameter von [{comp.label or cid}]({linker.comp(cid)})\n")
        out.append(param_table(comp.params))
        if comp.config_fields:
            out.append("Zugehörige Fahrzeugparameter (`VehicleConfig`):\n\n" + param_table(comp.config_fields))
    for ps in pkg.param_sets:
        out.append(f"## Parametersatz `{ps.qualname}` (`{ps.module}`)\n")
        if ps.doc:
            out.append(first_sentence(ps.doc) + "\n")
        out.append(param_table(ps.fields))
    if pkg.configs:
        out.append("## Konfigurationsdateien, die Komponenten dieses Pakets verwenden\n")
        rows = [(f"[{p}]({linker.any(p)})", kb.configs[p].title,
                 ", ".join(f"`{c}`" for c in kb.configs[p].components if c in pkg.components)) for p in pkg.configs]
        out.append(table(["Datei", "Titel", "Komponenten"], rows))
    return "\n".join(out)


def param_table(params):
    rows = []
    for p in params:
        label = p.get("label") if p.get("label") not in (None, "", p.get("name")) else ""
        desc = p.get("description", "")
        text = " – ".join(x for x in (label, desc) if x) or "–"
        rows.append((f"`{p.get('name')}`", text, p.get("unit") or "–", fmt_value(p.get("default")),
                     fmt_value(p.get("min")) if "min" in p else "–", fmt_value(p.get("max")) if "max" in p else "–"))
    return table(["Name", "Bezeichnung", "Einheit", "Default", "Min", "Max"], rows) if rows else "_Keine Parameter._\n"


def page_theory(kb, pkg, linker):
    out = [header(pkg, linker, "theory")]
    documented = set()
    if pkg.theory is not None:
        text = pkg.theory.text
        text = re.sub(r"^# .*\n", "", text, count=1)
        out.append(f"Übernommen aus [{pkg.theory.path}]({linker.source(pkg.theory.path)}).\n")
        out.append(cite_text(kb, text.strip(), linker) + "\n")
        documented = {s.id for s in pkg.theory.sections}
    else:
        out.append("**Noch nicht dokumentiert.** Es gibt keine handgeschriebene `theory.md` "
                   f"(`{pkg.docs_dir}/theory.md`).\n")
    for doc in pkg.documents:
        documented |= {s.id for s in doc.sections}
        out.append(f"Weiteres Kapitel: [{doc.title or doc.path}]({linker.source(doc.path)})\n")
    missing = [c for c in pkg.concepts if c not in documented and not (kb.concepts.get(c) and kb.concepts[c].documented)]
    if missing:
        out.append("## Konzepte ohne Theorieabschnitt {#konzepte-ohne-theorie}\n")
        out.append("Folgende Konzepte werden im Code oder in der Paketdoku genannt, haben aber noch keinen Abschnitt "
                   "`## … {#concept-id}`:\n")
        out.append(bullet([f"`{c}`" for c in missing]))
    concepts = [c for c in pkg.concepts if c in kb.concepts]
    if concepts:
        out.append("## Verknüpfung der Verfahren {#verknuepfung}\n")
        rows = []
        for cid in concepts:
            c = kb.concepts[cid]
            impls = ", ".join(f"[`{i.split('.', 2)[-1]}`]({linker.impl(i)})" for i in c.implementations) or "–"
            comps = ", ".join(f"[`{x}`]({linker.comp(x)})" for x in c.components) or "–"
            rows.append((f"[{c.title}]({linker.concept(cid)})", impls, comps, ref_links(kb, c.references, linker) or "–"))
        out.append(table(["Verfahren", "Implementierung", "Komponenten", "Quellen"], rows))
    return "\n".join(out)


def page_examples(kb, pkg, linker):
    out = [header(pkg, linker, "examples")]
    if not pkg.examples and not pkg.configs:
        out.append("_Keine Beispiele gefunden._ Beispiele gehören nach `examples/" + pkg.name + "/`.\n")
    for path in pkg.examples:
        ex = kb.examples.get(path)
        out.append(f"## [{path}]({linker.any(path)})\n")
        if ex and ex.doc:
            out.append(ex.doc.strip() + "\n")
        if ex:
            used = [m for m in ex.modules if kb.modules[m].package == pkg.name]
            if used:
                out.append("Verwendet: " + ", ".join(f"`{m}`" for m in used) + "\n")
            out.append(f"Ausführen: `python {path}`\n")
    if pkg.configs:
        out.append("## Szenarien und Konfigurationen\n")
        rows = [(f"[{p}]({linker.any(p)})", kb.configs[p].title, kb.configs[p].doc or "–") for p in pkg.configs]
        out.append(table(["Datei", "Titel", "Beschreibung"], rows))
    return "\n".join(out)


def page_limitations(kb, pkg, linker):
    out = [header(pkg, linker, "limitations")]
    if not pkg.has_meta:
        out.append(stub_notice(pkg))
    out.append("## Bekannte Grenzen des Pakets\n")
    out.append(bullet([cite_text(kb, str(x), linker) for x in pkg.meta_list("limitations")])
               or "_Noch nicht dokumentiert._\n")
    for cid in pkg.components:
        doc = kb.components[cid].doc
        if doc.get("limitations") or doc.get("assumptions"):
            out.append(f"## [{kb.components[cid].label or cid}]({linker.comp(cid)})\n")
            if doc.get("assumptions"):
                out.append("Annahmen:\n\n" + bullet(doc["assumptions"]))
            if doc.get("limitations"):
                out.append("Grenzen:\n\n" + bullet(doc["limitations"]))
    theory_limits = []
    for c in pkg.concepts:
        con = kb.concepts.get(c)
        if con and con.section and con.package == pkg.name:
            body = con.section.subsection("Anwendungsgrenzen")
            if body:
                theory_limits.append(f"### [{con.title}]({linker.concept(c)})\n\n{cite_text(kb, body, linker)}\n")
    if theory_limits:
        out.append("## Anwendungsgrenzen der Verfahren\n\n" + "\n".join(theory_limits))
    return "\n".join(out)


def page_validation(kb, pkg, linker):
    out = [header(pkg, linker, "validation")]
    declared = [v for v in pkg.meta_list("validation") if isinstance(v, dict)]
    out.append("## Validierung laut Paketdoku\n")
    if declared:
        out.append(table(["Test", "Zeigt"], [(f"[{v.get('test')}]({linker.test(str(v.get('test')).split('::')[0])})",
                                              v.get("shows", "")) for v in declared]))
    else:
        out.append("_Keine Validierungsangaben in module.yaml._\n")
    out.append("## Tests, die dieses Paket verwenden\n")
    if not pkg.tests:
        out.append(f"_Keine Tests gefunden._ Tests gehören nach `tests/{pkg.name}/test_{pkg.name}_*.py`.\n")
    for path in pkg.tests:
        t = kb.tests[path]
        out.append(f"### [{path}]({linker.test(path)})\n")
        if t.shows.get(pkg.name):
            out.append(f"**Zeigt:** {t.shows[pkg.name]}\n")
        mods = [m for m in t.modules if kb.modules[m].package == pkg.name]
        comps = [c for c in t.components if c in pkg.components]
        if mods:
            out.append("Importiert: " + ", ".join(f"`{m}`" for m in mods) + "\n")
        if comps:
            out.append("Komponenten: " + ", ".join(f"`{c}`" for c in comps) + "\n")
        if t.functions:
            out.append(table(["Testfunktion", "Beschreibung"], [(f"`{n}`", d or "–") for n, d in t.functions]))
    for cid in pkg.components:
        val = kb.components[cid].doc.get("validation")
        if val:
            out.append(f"## Validierung von [{cid}]({linker.comp(cid)})\n\n" + bullet(val))
    return "\n".join(out)


def package_reference_ids(kb, pkg):
    used = {}

    def add(rid, where):
        if rid:
            used.setdefault(str(rid), set()).add(where)
    for rid in pkg.meta_list("references"):
        add(rid, "module.yaml")
    for doc in ([pkg.theory] if pkg.theory else []) + pkg.documents:
        for rid, _ in parse_citations(doc.text):
            add(rid, doc.path.rsplit("/", 1)[-1])
    for t in pkg.traces:
        add(t.get("source"), f"{t['qualname']} ({t.get('origin')})")
    for cid in pkg.components:
        for rid in as_list(kb.components[cid].doc.get("references")):
            add(rid, cid)
    for link in kb.references.links:
        target = link["target"]
        if target in (f"package:{pkg.name}", pkg.name) or any(target.endswith(c) for c in pkg.components) \
                or any(target.endswith(m) for m in pkg.modules):
            add(link["reference"], f"links.yaml → {target}")
    return {k: sorted(v) for k, v in sorted(used.items())}


def page_references(kb, pkg, linker):
    out = [header(pkg, linker, "references")]
    used = package_reference_ids(kb, pkg)
    if not used:
        out.append("_Keine Quellen verknüpft._\n")
    rows = []
    for rid, where in used.items():
        ref = kb.references.get(rid)
        if ref is None:
            rows.append((f"`{rid}`", "**fehlt in docs/references**", "–", ", ".join(where)))
        else:
            rows.append((f"[{ref.short()}]({linker.ref(rid)})", ref.full(), TYPE_LABELS.get(ref.type, ref.type),
                         ", ".join(where)))
    out.append(table(["Zitat", "Quelle", "Typ", "Verwendet in"], rows))
    return "\n".join(out)


def trace_tests(kb, trace):
    tests = [str(t).split("::")[0] for t in as_list(trace.get("tests"))]
    for path, usage in kb.tests.items():
        if trace["module"] in usage.modules and path not in tests:
            tests.append(path)
    return sorted(set(tests))


@trace("gotel1994", concept="traceability_model", note="Kette Implementierung → Gleichung → Konzept → Quelle → Test")
def trace_rows(kb, traces, linker, with_package=False):
    rows = []
    for t in traces:
        impl = f"[`{t['qualname']}`]({linker.impl(t['implementation'])})"
        eq = " ".join(x for x in (f"Abschn. {t['section']}" if t.get("section") else "", t.get("equation", "")) if x) or "–"
        concept = concept_links(kb, [t["concept"]], linker) if t.get("concept") else "–"
        source = ref_links(kb, [t["source"]], linker) if t.get("source") else "–"
        tests = ", ".join(f"[{p.rsplit('/', 1)[-1]}]({linker.test(p)})" for p in trace_tests(kb, t)) or "–"
        row = [impl, eq, concept, source, tests, "Code (@trace)" if t.get("origin") != "module.yaml" else "module.yaml"]
        if with_package:
            row.insert(0, f"[{t['package']}]({linker.pkg(t['package'], 'traceability')})")
        rows.append(tuple(row))
    return rows


def page_traceability(kb, pkg, linker):
    out = [header(pkg, linker, "traceability")]
    out.append("Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. "
               "„Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` "
               "der Paketdoku.\n")
    if not pkg.traces:
        out.append("_Keine Rückverfolgbarkeitseinträge._ Funktionen, die eine Gleichung umsetzen, erhalten "
                   "`@trace(quelle, section=, equation=, concept=)` aus `vdsim.framework.knowledge`.\n")
    else:
        out.append(table(["Implementierung", "Gleichung", "Konzept", "Quelle", "Tests", "Herkunft"],
                         trace_rows(kb, pkg.traces, linker)))
    why = []
    for t in pkg.traces:
        c = kb.concepts.get(t.get("concept", ""))
        if c and c.section:
            goal = first_sentence(c.section.subsection("Ziel") or c.section.text)
            assume = c.section.subsection("Annahmen")
            why.append(f"### `{t['qualname']}`\n\n- **Warum:** {goal or '–'}\n- **Theorie:** "
                       f"[{c.title}]({linker.concept(c.id)})\n- **Annahmen:** "
                       f"{first_sentence(assume.replace(chr(10), ' ')) if assume else '–'}\n"
                       f"- **Quelle:** {ref_links(kb, [t.get('source')], linker) or '–'}"
                       + (f"\n- **Hinweis:** {t['note']}" if t.get("note") else "") + "\n")
    if why:
        out.append("## Warum es diese Implementierungen gibt\n\n" + "\n".join(why))
    return "\n".join(out)


PAGE_BUILDERS = {"index": page_index, "interfaces": page_interfaces, "configuration": page_configuration,
                 "theory": page_theory, "examples": page_examples, "limitations": page_limitations,
                 "validation": page_validation, "references": page_references, "traceability": page_traceability}


def package_page(kb, pkg_name, page="index", linker=None):
    pkg = kb.packages[pkg_name]
    linker = (linker or Linker(kb)).at(f"docs/generated/{pkg_name}")
    return PAGE_BUILDERS[page](kb, pkg, linker).rstrip() + "\n"


# ---------------------------------------------------------------------------- component page
def component_page(kb, cid, linker=None):
    comp = kb.components[cid]
    linker = (linker or Linker(kb)).at(f"docs/generated/{comp.package}/components")
    doc = comp.doc
    out = [f"# {comp.label or cid}", "", GENERATED_NOTE, "",
           f"Paket [{comp.package}]({linker.pkg(comp.package)}) · `{cid}`"
           + (f" · Version {comp.version}" if not comp.legacy else " · klassische Registry") + "\n"]
    if doc.get("summary"):
        out.append(f"**{doc['summary']}**\n")
    if doc.get("purpose"):
        out.append("## Zweck\n\n" + cite_text(kb, str(doc["purpose"]), linker) + "\n")
    rows = [("Art (KIND)", f"`{comp.kind}`"), ("Name", f"`{comp.name}`"), ("Versionen", ", ".join(comp.versions) or "–"),
            ("Implementierung", f"[`{comp.module}.{comp.qualname}`]({linker.impl(comp.class_id)})"),
            ("Schnittstelle", f"`{comp.interface}`" if comp.interface else "–"), ("Sprache", comp.language)]
    if not comp.legacy:
        rows += [("Periode", f"{comp.period} s" if comp.period else "jeder Schritt"),
                 ("Direkter Durchgriff", "ja" if comp.direct_feedthrough else "nein")]
    out.append("## Steckbrief\n\n" + table(["Eigenschaft", "Wert"], rows))
    if comp.inputs or comp.outputs:
        out.append("## Ports\n")
        if comp.inputs:
            out.append("Eingänge:\n\n" + table(["Port", "Typ", "Einheit", "Beschreibung", "Merkmale"], _port_rows(comp.inputs)))
        if comp.outputs:
            out.append("Ausgänge:\n\n" + table(["Port", "Typ", "Einheit", "Beschreibung", "Merkmale"], _port_rows(comp.outputs)))
    out.append("## Parameter\n\n" + param_table(comp.params))
    if comp.config_fields:
        out.append("Zugehörige Fahrzeugparameter:\n\n" + param_table(comp.config_fields))
    if doc.get("theory"):
        out.append("## Theorie\n\n" + cite_text(kb, str(doc["theory"]), linker) + "\n")
    if doc.get("concepts"):
        out.append("## Verfahren\n\n" + concept_links(kb, doc["concepts"], linker) + "\n")
    for key, title in (("assumptions", "Annahmen"), ("limitations", "Einschränkungen"), ("validation", "Validierung")):
        if doc.get(key):
            out.append(f"## {title}\n\n" + bullet([cite_text(kb, str(x), linker) for x in as_list(doc[key])]))
    if doc.get("equations"):
        out.append("## Umgesetzte Gleichungen\n\n" + bullet([f"`{e}`" for e in as_list(doc["equations"])]))
    if doc.get("references"):
        out.append("## Quellen\n\n" + ref_links(kb, doc["references"], linker) + "\n")
    if doc.get("design_decisions"):
        out.append("## Designentscheidungen\n\n" + bullet(doc["design_decisions"]))
    if doc.get("extension_points"):
        out.append("## Erweiterungspunkte\n\n" + bullet(doc["extension_points"]))
    if doc.get("expert"):
        out.append("## Expertenmodus: Herleitungen und Hinweise\n\n" + cite_text(kb, str(doc["expert"]), linker) + "\n")
    tests = sorted(p for p, t in kb.tests.items() if cid in t.components or comp.module in t.modules)
    configs = sorted(p for p, c in kb.configs.items() if cid in c.components)
    examples = sorted(p for p, e in kb.examples.items() if cid in e.components or comp.module in e.modules)
    if tests or configs or examples:
        out.append("## Verwendung\n")
        if tests:
            out.append("Tests: " + ", ".join(f"[{p}]({linker.test(p)})" for p in tests) + "\n")
        if examples:
            out.append("Beispiele: " + ", ".join(f"[{p}]({linker.any(p)})" for p in examples) + "\n")
        if configs:
            out.append("Konfigurationen: " + ", ".join(f"[{p}]({linker.any(p)})" for p in configs) + "\n")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------------------- pages used by the GUI
def concept_page(kb, cid, linker=None):
    linker = linker or Linker(kb, "gui")
    c = kb.concepts.get(cid)
    if c is None:
        return f"# {cid}\n\nUnbekanntes Konzept.\n"
    out = [f"# {c.title}", "", f"Konzept `{cid}`" + (f" · Paket [{c.package}]({linker.pkg(c.package, 'theory')})"
                                                     if c.package else "") + "\n"]
    if c.section is not None:
        body = re.sub(r"^#### ", "##### ", c.section.text, flags=re.M)
        body = re.sub(r"^### ", "## ", body, flags=re.M)
        out.append(cite_text(kb, body, linker) + "\n")
    else:
        out.append("**Noch nicht dokumentiert.** Für dieses Konzept gibt es keinen Abschnitt `## … {#" + cid +
                   "}` in einer theory.md.\n")
    out.append("## Rückverfolgbarkeit\n")
    out.append(f"- Implementierungen: {', '.join(f'[`{i}`]({linker.impl(i)})' for i in c.implementations) or '–'}")
    out.append(f"- Komponenten: {', '.join(f'[`{x}`]({linker.comp(x)})' for x in c.components) or '–'}")
    out.append(f"- Pakete: {', '.join(f'[{p}]({linker.pkg(p)})' for p in c.packages) or '–'}")
    out.append(f"- Quellen: {ref_links(kb, c.references, linker) or '–'}\n")
    return "\n".join(out)


def node_page(kb, graph, node_id, linker=None):
    # generic page for any graph node (modules, classes, functions, references, tests, ...)
    linker = linker or Linker(kb, "gui")
    node = graph.nodes.get(node_id)
    if node is None:
        return f"# {node_id}\n\nNicht gefunden.\n"
    t, key = node.type, node.key
    if t == "concept":
        return concept_page(kb, key, linker)
    if t in ("component", "model") and key in kb.components:
        return component_page(kb, key, linker)
    if t == "package" and key in kb.packages:
        return package_page(kb, key, "index", linker)
    out = [f"# {node.label}", "", f"*{NODE_LABELS.get(t, t)}* `{node_id}`\n"]
    if t == "reference" and key in kb.references:
        ref = kb.references[key]
        out.append(ref.full() + "\n")
        out.append(f"Typ: {TYPE_LABELS.get(ref.type, ref.type)} · Datei: `docs/references/{ref.source_file}`\n")
        if ref.notes:
            out.append(ref.notes + "\n")
        out.append("```bibtex\n" + ref.bibtex() + "\n```\n")
    elif t in ("function", "class"):
        fn = kb.function(key)
        module, _ = kb.split_implementation(key)
        mod = kb.modules.get(module)
        if mod:
            out.append(f"Modul [`{module}`]({linker.module(module)}) · [{mod.path}]({linker.source(mod.path, fn.lineno if fn else None)})\n")
        if fn is not None:
            if t == "function":
                out.append(f"```python\n{fn.qualname}({', '.join(fn.args)})\n```\n")
            if fn.doc:
                out.append(fn.doc.strip() + "\n")
        traces = [x for x in kb.traces if x["implementation"] == key]
        if traces:
            out.append("## Rückverfolgbarkeit\n\n" + table(["Implementierung", "Gleichung", "Konzept", "Quelle", "Tests",
                                                             "Herkunft"], trace_rows(kb, traces, linker)))
    elif t == "module" and key in kb.modules:
        mod = kb.modules[key]
        out.append(f"Datei [{mod.path}]({linker.source(mod.path)}) · {mod.lines} Zeilen\n")
        if mod.doc:
            out.append("```text\n" + mod.doc.strip() + "\n```\n")
        rows = [(f"[`{c.qualname}`]({linker.impl(c.id)})", "Klasse", first_sentence(c.doc) or "–") for c in mod.classes]
        rows += [(f"[`{f.qualname}`]({linker.impl(f.id)})", "Funktion", first_sentence(f.doc) or "–") for f in mod.functions]
        out.append(table(["Name", "Art", "Beschreibung"], rows))
    elif t == "datatype" and key in kb.datatypes:
        dt = kb.datatypes[key]
        out.append((dt.description or "") + (f"\n\nDefiniert in `{dt.module}.{dt.qualname}`." if dt.module else "") + "\n")
        if dt.fields:
            out.append(table(["Feld", "Typ", "Default"], [(f"`{f[0]}`", f[1], f[2] or "–") for f in dt.fields]))
    elif t == "test" and key in kb.tests:
        usage = kb.tests[key]
        if usage.doc:
            out.append(usage.doc + "\n")
        out.append(table(["Testfunktion", "Beschreibung"], [(f"`{n}`", d or "–") for n, d in usage.functions]))
    if node.data.get("summary") and t not in ("reference",):
        out.insert(3, str(node.data["summary"]) + "\n")
    nbs = graph.neighbors(node_id)
    if nbs:
        out.append("## Beziehungen\n")
        rows = []
        for e, other, direction in nbs[:200]:
            o = graph.nodes[other]
            rel = EDGE_LABELS.get(e.type, e.type) if direction == "out" else f"← {EDGE_LABELS.get(e.type, e.type)}"
            rows.append((rel, f"[{o.label}](node:{other})", NODE_LABELS.get(o.type, o.type), e.note or "–"))
        out.append(table(["Beziehung", "Knoten", "Typ", "Hinweis"], rows))
    return "\n".join(out)


# ---------------------------------------------------------------------------- global pages
def readme(kb, graph, linker):
    out = ["# vdsim – generierte Dokumentation", "", GENERATED_NOTE, "",
           "Einstieg in die automatisch erzeugte Dokumentation aller Pakete. Bedienung und Konzept: "
           f"[docs/KNOWLEDGE.md]({linker.any('docs/KNOWLEDGE.md')}). Interaktiver Wissensgraph: "
           "[knowledge_graph.html](knowledge_graph.html), GUI: `python -m vdsim.knowledge.gui`.\n",
           "## Pakete\n"]
    rows = []
    for pkg in sorted(kb.packages.values(), key=lambda p: p.name):
        status = "handgeschrieben" if pkg.has_meta else "Stub"
        if pkg.theory is not None:
            status += " + Theorie"
        rows.append((f"[{pkg.name}]({linker.pkg(pkg.name)})", pkg.title if pkg.has_meta else "–",
                     first_sentence(pkg.summary) or "–", len(pkg.components), len(pkg.concepts), len(pkg.traces),
                     len(pkg.tests), status))
    out.append(table(["Paket", "Titel", "Kurzfassung", "Komponenten", "Konzepte", "Traces", "Tests", "Doku"], rows))
    out.append("## Verfahren und Konzepte\n")
    rows = []
    for c in sorted(kb.concepts.values(), key=lambda c: c.id):
        rows.append((f"[{c.title}]({linker.concept(c.id)})", f"`{c.id}`", c.package or "–",
                     len(c.implementations) + len(c.components), ref_links(kb, c.references, linker) or "–",
                     "ja" if c.documented else "nein"))
    out.append(table(["Verfahren", "ID", "Paket", "Implementierungen", "Quellen", "dokumentiert"], rows))
    undocumented = [c.id for c in kb.concepts.values() if not c.documented]
    out.append("### Konzepte ohne Dokumentation {#konzepte-ohne-dokumentation}\n")
    out.append(", ".join(f"`{c}`" for c in sorted(undocumented)) + "\n" if undocumented else "_Keine._\n")
    out.append("## Wissensgraph\n")
    st = graph.stats()
    out.append(f"{st['nodes']} Knoten, {st['edges']} Kanten.\n")
    out.append(table(["Knotentyp", "Anzahl"], [(NODE_LABELS.get(k, k), v) for k, v in st["node_types"].items()]))
    out.append(table(["Kantentyp", "Anzahl"], [(EDGE_LABELS.get(k, k), v) for k, v in st["edge_types"].items()]))
    out.append("## Weitere Seiten\n")
    out.append("- [Rückverfolgbarkeitsmatrix](traceability_matrix.md)\n- [Literaturverzeichnis](references.md) "
               "und [BibTeX](references.bib)\n- [Prüfbericht (Referenzen, Hinweise des Sammlers)](report.md)\n"
               "- [Wissensgraph (HTML)](knowledge_graph.html), [JSON](knowledge_graph.json)\n")
    return "\n".join(out)


def traceability_matrix(kb, linker):
    out = ["# Rückverfolgbarkeitsmatrix", "", GENERATED_NOTE, "",
           "Alle Einträge aus `@trace` im Code und aus `traceability` in den module.yaml-Dateien. "
           "Kette: Implementierung → Gleichung → Konzept → Quelle → Test.\n"]
    out.append(table(["Paket", "Implementierung", "Gleichung", "Konzept", "Quelle", "Tests", "Herkunft"],
                     trace_rows(kb, kb.traces, linker, with_package=True)))
    out.append("## Abdeckung\n")
    rows = []
    for pkg in sorted(kb.packages.values(), key=lambda p: p.name):
        concepts = [c for c in pkg.concepts if c in kb.concepts]
        with_impl = [c for c in concepts if kb.concepts[c].implementations or kb.concepts[c].components]
        documented = [c for c in concepts if kb.concepts[c].documented]
        tested = [t for t in pkg.traces if trace_tests(kb, t)]
        rows.append((pkg.name, len(pkg.traces), len(tested), len(concepts), len(documented), len(with_impl)))
    out.append(table(["Paket", "Traces", "davon mit Test", "Konzepte", "davon dokumentiert", "davon implementiert"], rows))
    return "\n".join(out)


def bibliography(kb, linker):
    out = ["# Literaturverzeichnis", "", GENERATED_NOTE, "",
           "Alle Einträge aus `docs/references/*.yaml` (inkl. `user.yaml`). Zitierschlüssel in Klammern.\n"]
    used = kb.used_reference_ids()
    by_type = {}
    for ref in kb.references:
        by_type.setdefault(ref.type, []).append(ref)
    for rtype in sorted(by_type, key=lambda t: TYPE_LABELS.get(t, t)):
        out.append(f"## {TYPE_LABELS.get(rtype, rtype)}\n")
        for ref in by_type[rtype]:
            where = used.get(ref.id, [])
            out.append(f"### {ref.short()} {{#{ref.id}}}\n")
            out.append(f"{ref.full()} `[{ref.id}]`" + (" *(Benutzerreferenz)*" if ref.user else "") + "\n")
            if ref.notes:
                out.append(f"_{ref.notes}_\n")
            out.append(f"Verwendet in: {', '.join(f'`{w}`' for w in where) if where else '– (noch nicht verknüpft)'}\n")
    return "\n".join(out)


def report(kb):
    rep = kb.reference_report()
    out = ["# Prüfbericht", "", GENERATED_NOTE, "",
           f"{rep['defined']} Referenzen definiert, {rep['used']} verwendet.\n", "## Fehlende Referenz-IDs\n",
           "IDs, die in `ComponentDoc.references`, `@trace`, module.yaml, theory.md oder links.yaml vorkommen, aber in "
           "`docs/references/*.yaml` fehlen. Das ist ein Hinweis, kein Fehler (Pakete sind teils noch in Arbeit).\n"]
    if rep["missing"]:
        out.append(table(["ID", "verwendet in"], [(f"`{k}`", ", ".join(v)) for k, v in rep["missing"].items()]))
    else:
        out.append("_Keine._\n")
    out.append("## Prüfung der Referenzdatenbank\n")
    out.append(bullet([f"`{i}`" for i in rep["issues"]]) or "_Keine Befunde._\n")
    out.append("## Hinweise des Sammlers\n")
    out.append(bullet([f"`{w}`" for w in kb.warnings]) or "_Keine._\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------- writing
def write_if_changed(path, content):
    path = Path(path)
    data = content if content.endswith("\n") else content + "\n"
    if path.exists():
        try:
            if path.read_text(encoding="utf-8") == data:
                return False
        except (OSError, UnicodeDecodeError):
            pass
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
    return True


def render_all(kb, graph=None):
    # {relative path inside docs/generated: content}
    graph = graph or build_graph(kb)
    linker = Linker(kb)
    files = {}
    for name in sorted(kb.packages):
        for page in PAGES:
            files[f"{name}/{page}.md"] = package_page(kb, name, page, linker)
        for cid in kb.packages[name].components:
            files[f"{name}/components/{component_file(cid)}"] = component_page(kb, cid, linker)
    files["README.md"] = readme(kb, graph, linker.at("docs/generated"))
    files["traceability_matrix.md"] = traceability_matrix(kb, linker.at("docs/generated"))
    files["references.md"] = bibliography(kb, linker.at("docs/generated"))
    files["references.bib"] = kb.references.bibtex()
    files["report.md"] = report(kb)
    files["knowledge_graph.json"] = graph.to_json()
    files["knowledge_graph.html"] = graph.to_html()
    return files


def generate(kb, out_dir=None, graph=None, clean=True, check=False):
    # write docs/generated; returns {"written": [...], "unchanged": [...], "removed": [...], "stats": {...}}
    out_dir = Path(out_dir) if out_dir is not None else generated_dir(kb.root)
    graph = graph or build_graph(kb)
    files = render_all(kb, graph)
    result = {"written": [], "unchanged": [], "removed": [], "out_dir": str(out_dir), "stats": graph.stats()}
    for relpath in sorted(files):
        target = out_dir / relpath
        content = files[relpath] if files[relpath].endswith("\n") else files[relpath] + "\n"
        if check:
            same = target.exists() and target.read_text(encoding="utf-8") == content
            result["unchanged" if same else "written"].append(relpath)
        elif write_if_changed(target, content):
            result["written"].append(relpath)
        else:
            result["unchanged"].append(relpath)
    if clean and out_dir.exists():
        keep = set(files) | {"_meta.json"}
        for path in sorted(out_dir.rglob("*")):
            if path.is_file() and path.relative_to(out_dir).as_posix() not in keep \
                    and path.suffix in (".md", ".json", ".html", ".bib"):
                result["removed"].append(path.relative_to(out_dir).as_posix())
                if not check:
                    path.unlink()
        if not check:
            for d in sorted((p for p in out_dir.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
                if not any(d.iterdir()):
                    d.rmdir()
    if not check:
        meta = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "files": len(files),
                "written": len(result["written"]), "stats": result["stats"], "warnings": len(kb.warnings)}
        (out_dir / "_meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


# ---------------------------------------------------------------------------- templates for new packages
MODULE_TEMPLATE = """# Paketdoku nach docs/templates/MODULE_DOCS.md (erzeugt von tools/build_docs.py --init)
id: {name}
title: {title}
summary: {summary}
purpose: |
  Warum es das Modul gibt und welches Problem es löst.
architecture: |
  Innere Struktur (Klassen, Datenfluss).
design_decisions:
  - decision: ...
    reason: ...
    alternatives: ...
implementation:
  - ...
configuration: []
examples: []
limitations:
  - ...
validation: []
references: {references}
concepts: {concepts}
related_modules: []
extension_points: []
"""


def init_package_docs(kb, name, overwrite=False):
    # write template module.yaml / theory.md for a package without hand-written docs
    pkg = kb.packages[name]
    docs = kb.root / pkg.docs_dir
    docs.mkdir(parents=True, exist_ok=True)
    written = []
    concepts = sorted({t["concept"] for t in pkg.traces if t.get("concept")} | set(pkg.concepts))
    refs = sorted({t["source"] for t in pkg.traces if t.get("source")})
    meta_path = docs / "module.yaml"
    if overwrite or not meta_path.exists():
        meta_path.write_text(MODULE_TEMPLATE.format(name=name, title=name, summary=first_sentence(pkg.doc) or "...",
                                                    references=json.dumps(refs), concepts=json.dumps(concepts)),
                             encoding="utf-8")
        written.append(meta_path)
    theory_path = docs / "theory.md"
    if overwrite or not theory_path.exists():
        parts = [f"# Theorie: {name}\n"]
        for cid in concepts or ["verfahren"]:
            parts.append(f"## {humanize(cid)} {{#{cid}}}\n")
            parts += [f"### {s}\n\n...\n" for s in THEORY_SUBSECTIONS]
        theory_path.write_text("\n".join(parts), encoding="utf-8")
        written.append(theory_path)
    return written
