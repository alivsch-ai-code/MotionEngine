"""Knowledge browser widget: navigation tree, documents with rendered formulas, expert mode, knowledge
graph, traceability table, sources (search, create, link) and full-text search.

    from vdsim.gui.knowledge import KnowledgeBrowser
    browser = KnowledgeBrowser()            # collects the knowledge base of the repository
    browser.navigate("concept:frenet_transformation")
"""

from __future__ import annotations

import html
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from ...knowledge.collector import collect
from ...knowledge.generator import PAGE_TITLES, PAGES, Linker, node_page, package_page, trace_tests
from ...knowledge.graph import NODE_LABELS, NODE_TYPES, build_graph
from ...knowledge.markdown import markdown_to_html
from ...knowledge.references import REFERENCE_TYPES, TYPE_LABELS, ReferenceDB
from .graph_view import GraphView

ROLE_ID = QtCore.Qt.UserRole
DEFAULT_GRAPH_TYPES = {"package", "component", "model", "concept", "reference", "datatype", "function", "class",
                       "test", "document", "module", "example", "config"}


def _theme_qss():
    try:
        from ..theme import QSS
        return QSS
    except Exception:  # theme needs pyqtgraph; the browser works without it
        return ""


class KnowledgeBrowser(QtWidgets.QWidget):
    node_selected = QtCore.Signal(str)

    def __init__(self, root=None, knowledge=None, graph=None, parent=None, import_modules=True):
        super().__init__(parent)
        self.root = root
        self.kb = knowledge if knowledge is not None else collect(root, import_modules=import_modules)
        self.graph = graph if graph is not None else build_graph(self.kb)
        self.linker = Linker(self.kb, "gui")
        self.current = None                 # ("node", id) | ("page", pkg, page) | ("src", path)
        self.history = []
        self.setStyleSheet(_theme_qss())
        self._build_ui()
        self._fill_tree()
        self._fill_traceability()
        self._fill_references()
        self.navigate("page:" + ("knowledge/index" if "knowledge" in self.kb.packages else
                                 f"{next(iter(sorted(self.kb.packages)), '')}/index"))

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        bar = QtWidgets.QHBoxLayout()
        self.back_button = QtWidgets.QPushButton("◀ Zurück")
        self.back_button.clicked.connect(self.back)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Suche über Pakete, Komponenten, Verfahren, Funktionen, Quellen, Theorie …")
        self.search.textChanged.connect(self._search)
        self.expert = QtWidgets.QCheckBox("Expertenmodus")
        self.expert.setToolTip("Herleitungen, Stabilitätsbetrachtungen, Designentscheidungen, Erweiterungspunkte "
                               "und ComponentDoc.expert einblenden")
        self.expert.toggled.connect(lambda _: self._render_current())
        bar.addWidget(self.back_button)
        bar.addWidget(self.search, 1)
        bar.addWidget(self.expert)
        layout.addLayout(bar)

        split = QtWidgets.QSplitter()
        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.results = QtWidgets.QListWidget()
        self.results.setVisible(False)
        self.results.itemActivated.connect(lambda it: self.navigate(it.data(ROLE_ID)))
        self.results.itemClicked.connect(lambda it: self.navigate(it.data(ROLE_ID)))
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Navigation"])
        self.tree.itemClicked.connect(lambda it, _c: it.data(0, ROLE_ID) and self.navigate(it.data(0, ROLE_ID)))
        left_layout.addWidget(self.results)
        left_layout.addWidget(self.tree)
        split.addWidget(left)

        self.tabs = QtWidgets.QTabWidget()
        self.doc = QtWidgets.QTextBrowser()
        self.doc.setOpenLinks(False)
        self.doc.anchorClicked.connect(self._link)
        self.tabs.addTab(self.doc, "Dokument")
        self.tabs.addTab(self._graph_tab(), "Wissensgraph")
        self.tabs.addTab(self._trace_tab(), "Rückverfolgbarkeit")
        self.tabs.addTab(self._sources_tab(), "Quellen")
        split.addWidget(self.tabs)
        split.setStretchFactor(1, 3)
        split.setSizes([330, 1000])
        layout.addWidget(split, 1)
        st = self.graph.stats()
        self.status = QtWidgets.QLabel(f"{len(self.kb.packages)} Pakete · {len(self.kb.components)} Komponenten · "
                                       f"{len(self.kb.concepts)} Verfahren · {len(self.kb.references)} Quellen · "
                                       f"Wissensgraph {st['nodes']} Knoten / {st['edges']} Kanten · "
                                       f"{len(self.kb.warnings)} Hinweise")
        self.status.setStyleSheet("color: #9a9ca3;")
        layout.addWidget(self.status)

    def _graph_tab(self):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        controls = QtWidgets.QHBoxLayout()
        self.graph_mode = QtWidgets.QComboBox()
        self.graph_mode.addItems(["Nachbarschaft Tiefe 1", "Nachbarschaft Tiefe 2", "Übersicht (Pakete, Verfahren, Quellen)"])
        self.graph_mode.currentIndexChanged.connect(lambda _: self._update_graph())
        controls.addWidget(QtWidgets.QLabel("Ansicht:"))
        controls.addWidget(self.graph_mode)
        self.type_button = QtWidgets.QToolButton()
        self.type_button.setText("Knotentypen ▾")
        self.type_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        menu = QtWidgets.QMenu(self.type_button)
        self.type_actions = {}
        for t in NODE_TYPES:
            act = menu.addAction(NODE_LABELS[t])
            act.setCheckable(True)
            act.setChecked(t in DEFAULT_GRAPH_TYPES)
            act.toggled.connect(lambda _: self._update_graph())
            self.type_actions[t] = act
        self.type_button.setMenu(menu)
        controls.addWidget(self.type_button)
        self.graph_info = QtWidgets.QLabel("")
        self.graph_info.setStyleSheet("color: #9a9ca3;")
        controls.addWidget(self.graph_info, 1)
        lay.addLayout(controls)
        self.graph_view = GraphView()
        self.graph_view.node_clicked.connect(self._graph_click)
        self.graph_view.node_activated.connect(lambda nid: (self.navigate(nid), self.tabs.setCurrentIndex(0)))
        lay.addWidget(self.graph_view, 1)
        return w

    def _trace_tab(self):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        self.trace_filter = QtWidgets.QLineEdit()
        self.trace_filter.setPlaceholderText("Filter (Paket, Funktion, Konzept, Quelle …)")
        self.trace_filter.textChanged.connect(self._filter_traces)
        lay.addWidget(self.trace_filter)
        self.trace_table = QtWidgets.QTableWidget(0, 8)
        self.trace_table.setHorizontalHeaderLabels(["Paket", "Implementierung", "Abschnitt", "Gleichung", "Konzept",
                                                    "Quelle", "Tests", "Herkunft"])
        self.trace_table.horizontalHeader().setStretchLastSection(True)
        self.trace_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.trace_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.trace_table.cellDoubleClicked.connect(self._trace_activated)
        lay.addWidget(self.trace_table, 1)
        return w

    def _sources_tab(self):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(w)
        left = QtWidgets.QVBoxLayout()
        self.ref_search = QtWidgets.QLineEdit()
        self.ref_search.setPlaceholderText("Quellen suchen (Autor, Titel, Jahr, Norm …)")
        self.ref_search.textChanged.connect(self._fill_references)
        left.addWidget(self.ref_search)
        self.ref_table = QtWidgets.QTableWidget(0, 4)
        self.ref_table.setHorizontalHeaderLabels(["ID", "Zitat", "Typ", "Titel"])
        self.ref_table.horizontalHeader().setStretchLastSection(True)
        self.ref_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ref_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.ref_table.currentCellChanged.connect(lambda r, *_: self._show_reference(r))
        left.addWidget(self.ref_table, 2)
        self.ref_detail = QtWidgets.QTextBrowser()
        self.ref_detail.setOpenLinks(False)
        self.ref_detail.anchorClicked.connect(self._link)
        left.addWidget(self.ref_detail, 1)
        lay.addLayout(left, 3)

        form_box = QtWidgets.QGroupBox("Neue Referenz anlegen (docs/references/user.yaml)")
        form = QtWidgets.QFormLayout(form_box)
        self.new_ref = {}
        for key, label in (("id", "ID"), ("authors", "Autoren (; getrennt)"), ("title", "Titel"), ("year", "Jahr"),
                           ("venue", "Zeitschrift/Tagung"), ("publisher", "Verlag/Institution"), ("number", "Nummer (Norm/Bericht)"),
                           ("organization", "Organisation"), ("url", "URL"), ("doi", "DOI"), ("isbn", "ISBN"), ("notes", "Notiz")):
            edit = QtWidgets.QLineEdit()
            self.new_ref[key] = edit
            form.addRow(label, edit)
        self.new_ref_type = QtWidgets.QComboBox()
        for t in REFERENCE_TYPES:
            self.new_ref_type.addItem(TYPE_LABELS[t], t)
        form.insertRow(1, "Typ", self.new_ref_type)
        save = QtWidgets.QPushButton("Referenz speichern")
        save.clicked.connect(self._save_reference)
        form.addRow(save)
        self.link_target = QtWidgets.QComboBox()
        self.link_target.setEditable(True)
        targets = ([f"package:{p}" for p in sorted(self.kb.packages)] + [f"component:{c}" for c in sorted(self.kb.components)]
                   + [f"concept:{c}" for c in sorted(self.kb.concepts)])
        self.link_target.addItems(targets)
        form.addRow("Verknüpfen mit", self.link_target)
        link = QtWidgets.QPushButton("Ausgewählte Referenz verknüpfen")
        link.clicked.connect(self._link_reference)
        form.addRow(link)
        self.ref_message = QtWidgets.QLabel("")
        self.ref_message.setWordWrap(True)
        form.addRow(self.ref_message)
        lay.addWidget(form_box, 2)
        return w

    # ------------------------------------------------------------------ navigation tree
    def _item(self, parent, text, target=None, tooltip=""):
        item = QtWidgets.QTreeWidgetItem(parent, [text])
        if target:
            item.setData(0, ROLE_ID, target)
        if tooltip:
            item.setToolTip(0, tooltip[:300])
        return item

    def _fill_tree(self):
        self.tree.clear()
        kb = self.kb
        for name in sorted(kb.packages):
            pkg = kb.packages[name]
            top = self._item(self.tree, f"{name}" + ("" if pkg.has_meta else "  (Stub)"), f"page:{name}/index", pkg.summary)
            pages = self._item(top, "Seiten")
            for page in PAGES:
                self._item(pages, PAGE_TITLES[page], f"page:{name}/{page}")
            if pkg.components:
                comps = self._item(top, f"Komponenten ({len(pkg.components)})")
                for cid in pkg.components:
                    comp = kb.components[cid]
                    self._item(comps, comp.label or cid, f"{'model' if comp.is_model else 'component'}:{cid}",
                               comp.doc.get("summary", ""))
            concepts = [c for c in pkg.concepts if c in kb.concepts]
            if concepts:
                group = self._item(top, f"Verfahren ({len(concepts)})")
                for cid in concepts:
                    self._item(group, kb.concepts[cid].title, f"concept:{cid}")
            mods = self._item(top, f"Module ({len(pkg.modules)})")
            for mname in pkg.modules:
                mod = kb.modules[mname]
                mi = self._item(mods, mname.split(".", 1)[-1] if "." in mname else mname, f"module:{mname}", mod.doc)
                for cls in mod.classes:
                    ci = self._item(mi, cls.name, f"class:{cls.id}", cls.doc)
                    for m in cls.methods:
                        if f"function:{m.id}" in self.graph.nodes:
                            self._item(ci, m.name + "()", f"function:{m.id}", m.doc)
                for fn in mod.functions:
                    if f"function:{fn.id}" in self.graph.nodes:
                        self._item(mi, fn.name + "()", f"function:{fn.id}", fn.doc)
        refs = self._item(self.tree, f"Quellen ({len(kb.references)})")
        for ref in kb.references:
            self._item(refs, f"{ref.short()} – {ref.title[:60]}", f"reference:{ref.id}", ref.full())

    # ------------------------------------------------------------------ documents
    def navigate(self, target, record=True):
        if not target:
            return
        target = str(target)
        if target.startswith("page:"):
            pkg, _, page = target[5:].partition("/")
            page, _, anchor = (page or "index").partition("#")
            state = ("page", pkg, page or "index", anchor)
        elif target.startswith("src:"):
            state = ("src", target[4:])
        else:
            nid = target[5:] if target.startswith("node:") else target
            nid = self.graph.resolve(nid) or nid
            state = ("node", nid)
        if record and self.current is not None and self.current != state:
            self.history.append(self.current)
        self.current = state
        self._render_current()
        if state[0] == "node":
            self.node_selected.emit(state[1])
            self._update_graph()
        elif state[0] == "page" and f"package:{state[1]}" in self.graph.nodes:
            self._update_graph()

    def back(self):
        if self.history:
            self.current = self.history.pop()
            self._render_current()

    def current_markdown(self):
        state = self.current
        if state is None:
            return ""
        if state[0] == "page":
            if state[1] not in self.kb.packages:
                return f"# {state[1]}\n\nUnbekanntes Paket.\n"
            return package_page(self.kb, state[1], state[2], self.linker)
        if state[0] == "src":
            path, _, line = state[1].partition("#L")
            full = Path(self.kb.root) / path
            try:
                text = full.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                return f"# {path}\n\nDatei nicht lesbar.\n"
            lang = "python" if path.endswith(".py") else ""
            return f"# {path}\n\n" + (f"Zeile {line}\n\n" if line else "") + f"```{lang}\n{text}\n```\n"
        return node_page(self.kb, self.graph, state[1], self.linker)

    def _render_current(self):
        md = self.current_markdown()
        refs = self.kb.references

        def cite(rid, loc):
            return (refs.cite(rid, loc) if rid in refs else f"{rid}?"), f"node:reference:{rid}"
        html_text = markdown_to_html(md, expert=self.expert.isChecked(), cite=cite)
        self.doc.setHtml(html_text)
        if self.current and self.current[0] == "page" and len(self.current) > 3 and self.current[3]:
            self.doc.scrollToAnchor(self.current[3])

    def _link(self, url):
        text = url.toString()
        if text.startswith(("node:", "page:", "src:")):
            self.navigate(text)
            self.tabs.setCurrentIndex(0)
        elif text.startswith("ref:"):
            self.navigate("reference:" + text[4:])
        elif text.startswith("#"):
            self.doc.scrollToAnchor(text[1:])
        elif text.startswith(("http://", "https://")):
            QtGui.QDesktopServices.openUrl(url)

    # ------------------------------------------------------------------ search
    def search_all(self, query, limit=80):
        # [(target, text)] over graph nodes, references and theory text
        q = query.strip()
        if not q:
            return []
        out, seen = [], set()
        for node in self.graph.search(q, limit=limit):
            out.append((node.id, f"{node.label}  [{NODE_LABELS.get(node.type, node.type)}]"))
            seen.add(node.id)
        for ref in self.kb.references.search(q, limit=20):
            if f"reference:{ref.id}" not in seen:
                out.append((f"reference:{ref.id}", f"{ref.short()} – {ref.title[:60]}  [Quelle]"))
                seen.add(f"reference:{ref.id}")
        low = q.lower()
        for c in self.kb.concepts.values():
            if c.section is not None and low in c.section.text.lower() and f"concept:{c.id}" not in seen:
                out.append((f"concept:{c.id}", f"{c.title}  [Volltext Theorie]"))
        return out[:limit]

    def _search(self, text):
        self.results.clear()
        hits = self.search_all(text)
        self.results.setVisible(bool(text.strip()))
        for target, label in hits:
            item = QtWidgets.QListWidgetItem(label)
            item.setData(ROLE_ID, target)
            self.results.addItem(item)
        if text.strip() and not hits:
            self.results.addItem("Keine Treffer")

    # ------------------------------------------------------------------ graph
    def _graph_click(self, nid):
        node = self.graph.nodes.get(nid)
        if node is not None:
            self.graph_info.setText(f"{node.label} · {NODE_LABELS.get(node.type, node.type)} · Doppelklick öffnet das Dokument")
            self.navigate(nid)

    def _visible_types(self):
        return [t for t, a in self.type_actions.items() if a.isChecked()]

    def _update_graph(self):
        types = self._visible_types()
        mode = self.graph_mode.currentIndex()
        center = None
        if self.current and self.current[0] == "node":
            center = self.current[1]
        elif self.current and self.current[0] == "page":
            center = f"package:{self.current[1]}"
        if mode == 2 or center not in self.graph.nodes:
            keep = [nid for nid, n in self.graph.nodes.items() if n.type in ("package", "concept", "reference")
                    and n.type in types]
            sub = self.graph.subgraph(keep)
        else:
            sub = self.graph.neighborhood(center, depth=mode + 1, node_types=types, limit=180)
            sub = self.graph.subgraph([n for n in sub.nodes if self.graph.nodes[n].type in types or n == center])
        self.graph_view.show_graph(sub, center, iterations=120 if len(sub.nodes) < 150 else 60)
        if not self.graph_info.text():
            self.graph_info.setText(f"{len(sub.nodes)} Knoten, {len(sub.edges)} Kanten")

    # ------------------------------------------------------------------ traceability
    def _fill_traceability(self):
        traces = self.kb.traces
        self.trace_table.setRowCount(len(traces))
        for r, t in enumerate(traces):
            tests = ", ".join(p.rsplit("/", 1)[-1] for p in trace_tests(self.kb, t))
            source = self.kb.references.cite(t["source"]) if t.get("source") in self.kb.references else t.get("source", "")
            values = [t["package"], t["implementation"], t.get("section", ""), t.get("equation", ""), t.get("concept", ""),
                      source, tests, "Code (@trace)" if t.get("origin") != "module.yaml" else "module.yaml"]
            for c, v in enumerate(values):
                item = QtWidgets.QTableWidgetItem(str(v))
                if c == 1:
                    item.setData(ROLE_ID, t["implementation"])
                self.trace_table.setItem(r, c, item)
        self.trace_table.resizeColumnsToContents()

    def _filter_traces(self, text):
        low = text.lower()
        for r in range(self.trace_table.rowCount()):
            row = " ".join(self.trace_table.item(r, c).text() for c in range(self.trace_table.columnCount())).lower()
            self.trace_table.setRowHidden(r, bool(low) and low not in row)

    def _trace_activated(self, row, column):
        item = self.trace_table.item(row, column)
        impl = self.trace_table.item(row, 1).data(ROLE_ID)
        if column == 4 and item.text():
            self.navigate(f"concept:{item.text()}")
        elif column == 5:
            t = self.kb.traces[row]
            self.navigate(f"reference:{t.get('source')}")
        else:
            self.navigate(f"function:{impl}" if f"function:{impl}" in self.graph.nodes else f"class:{impl}")
        self.tabs.setCurrentIndex(0)

    # ------------------------------------------------------------------ references
    def _fill_references(self, *_):
        refs = self.kb.references.search(self.ref_search.text()) if self.ref_search.text().strip() else list(self.kb.references)
        self._ref_rows = refs
        self.ref_table.setRowCount(len(refs))
        for r, ref in enumerate(refs):
            for c, v in enumerate((ref.id, ref.short(), TYPE_LABELS.get(ref.type, ref.type), ref.title)):
                self.ref_table.setItem(r, c, QtWidgets.QTableWidgetItem(v))
        self.ref_table.resizeColumnsToContents()

    def selected_reference(self):
        row = self.ref_table.currentRow()
        rows = getattr(self, "_ref_rows", [])
        return rows[row] if 0 <= row < len(rows) else None

    def _show_reference(self, row):
        rows = getattr(self, "_ref_rows", [])
        if 0 <= row < len(rows):
            md = node_page(self.kb, self.graph, f"reference:{rows[row].id}", self.linker)
            self.ref_detail.setHtml(markdown_to_html(md, render_math=False))

    def add_reference(self, ref_id, data, target=None):
        # programmatic API used by the form: create a user reference and optionally link it
        db = self.kb.references
        db.add_user_reference(ref_id, data)
        if target:
            db.link(ref_id, target)
        self._references_changed()
        return db[ref_id]

    def _save_reference(self):
        data = {k: e.text().strip() for k, e in self.new_ref.items() if k != "id" and e.text().strip()}
        data["type"] = self.new_ref_type.currentData()
        if "authors" in data:
            data["authors"] = [a.strip() for a in data["authors"].split(";") if a.strip()]
        try:
            ref = self.add_reference(self.new_ref["id"].text().strip(), data)
            self.ref_message.setText(f"Gespeichert: {ref.short()}")
            for e in self.new_ref.values():
                e.clear()
        except ValueError as exc:
            self.ref_message.setText(f"Fehler: {exc}")

    def _link_reference(self):
        ref = self.selected_reference()
        target = self.link_target.currentText().strip()
        if ref is None or not target:
            self.ref_message.setText("Bitte eine Referenz in der Tabelle und ein Ziel wählen.")
            return
        try:
            self.kb.references.link(ref.id, target)
            self._references_changed()
            self.ref_message.setText(f"{ref.short()} verknüpft mit {target}")
        except ValueError as exc:
            self.ref_message.setText(f"Fehler: {exc}")

    def _references_changed(self):
        self.kb.references = ReferenceDB(self.kb.references.directory)
        self.graph = build_graph(self.kb)
        self._fill_references()
        self._fill_tree()
