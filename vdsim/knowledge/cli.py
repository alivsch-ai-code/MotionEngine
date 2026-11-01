"""Command line of the knowledge system (used by tools/build_docs.py and python -m vdsim.knowledge).

    python tools/build_docs.py                      generate docs/generated (idempotent)
    python tools/build_docs.py --check              exit code 1 if docs/generated is outdated
    python tools/build_docs.py --report             reference check and collector warnings
    python tools/build_docs.py --explain stanley    "Wie funktioniert X" as Markdown
    python tools/build_docs.py --path a b           shortest path in the knowledge graph
    python tools/build_docs.py --search frenet      search the knowledge graph and the references
    python tools/build_docs.py --bibtex out.bib     BibTeX export of all references
    python tools/build_docs.py --init <package>     template module.yaml / theory.md for a package
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(prog="build_docs", description="vdsim Wissens- und Dokumentationssystem")
    parser.add_argument("--root", help="Repository-Wurzel (Standard: dieses Repository)")
    parser.add_argument("--out", help="Zielordner (Standard: docs/generated)")
    parser.add_argument("--check", action="store_true", help="nur prüfen, ob die generierte Doku aktuell ist")
    parser.add_argument("--report", action="store_true", help="Referenzprüfung und Hinweise ausgeben")
    parser.add_argument("--explain", metavar="X", help="„Wie funktioniert X“ ausgeben")
    parser.add_argument("--path", nargs=2, metavar=("A", "B"), help="kürzester Pfad im Wissensgraph")
    parser.add_argument("--search", metavar="TEXT", help="Suche im Wissensgraph und in den Quellen")
    parser.add_argument("--bibtex", metavar="DATEI", help="BibTeX-Export aller Referenzen")
    parser.add_argument("--init", metavar="PAKET", help="Vorlage module.yaml/theory.md für ein Paket anlegen")
    parser.add_argument("--no-import", action="store_true", help="Module nicht importieren (nur statische Analyse)")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    from .collector import collect
    from .generator import generate, init_package_docs
    from .graph import build_graph

    start = time.perf_counter()
    kb = collect(args.root, import_modules=not args.no_import)
    graph = build_graph(kb)
    say = (lambda *a: None) if args.quiet else print

    if args.init:
        if args.init not in kb.packages:
            print(f"unbekanntes Paket '{args.init}'", file=sys.stderr)
            return 2
        for path in init_package_docs(kb, args.init):
            say(f"angelegt: {path}")
        return 0
    if args.explain:
        print(graph.explain_markdown(args.explain, kb.references))
        return 0
    if args.path:
        ids = graph.path(*args.path)
        print(" -> ".join(ids) if ids else "kein Pfad gefunden")
        return 0 if ids else 1
    if args.search:
        for node in graph.search(args.search, limit=30):
            print(f"{node.type:10s} {node.id}  {node.data.get('summary', '')[:80]}")
        for ref in kb.references.search(args.search, limit=10):
            print(f"{'quelle':10s} {ref.id}  {ref.short()}: {ref.title[:70]}")
        return 0
    if args.bibtex:
        Path(args.bibtex).write_text(kb.references.bibtex(), encoding="utf-8")
        say(f"{len(kb.references)} Referenzen nach {args.bibtex} exportiert")
        return 0
    if args.report:
        rep = kb.reference_report()
        print(f"Referenzen: {rep['defined']} definiert, {rep['used']} verwendet")
        for rid, where in rep["missing"].items():
            print(f"  fehlt: {rid}  ({', '.join(where)})")
        for issue in rep["issues"]:
            print(f"  {issue}")
        print(f"Hinweise des Sammlers: {len(kb.warnings)}")
        for w in kb.warnings:
            print(f"  {w}")
        return 0

    result = generate(kb, args.out, graph, check=args.check)
    st = result["stats"]
    if args.check:
        stale = result["written"] + result["removed"]
        say(f"{len(stale)} veraltete Dateien" + (": " + ", ".join(stale[:20]) if stale else ""))
        return 1 if stale else 0
    say(f"docs/generated: {len(result['written'])} geschrieben, {len(result['unchanged'])} unverändert, "
        f"{len(result['removed'])} entfernt; Wissensgraph {st['nodes']} Knoten / {st['edges']} Kanten; "
        f"{len(kb.warnings)} Hinweise; {time.perf_counter() - start:.1f} s")
    return 0
