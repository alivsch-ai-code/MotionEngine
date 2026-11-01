"""Knowledge, documentation and traceability system of vdsim.

    references   reference database (docs/references/*.yaml), citations, BibTeX, user references and links
    collector    collects packages, modules, components, @trace entries, module.yaml, theory.md, tests,
                 examples and configurations into a KnowledgeBase
    graph        knowledge graph (nodes / edges, queries, JSON and standalone HTML export, force layout)
    generator    generates docs/generated/<package>/ (deterministic, idempotent)
    markdown     small Markdown -> HTML converter for the GUI (formulas via mathrender)
    mathrender   LaTeX formulas -> PNG / SVG with matplotlib mathtext (cached per user)

Command line: python tools/build_docs.py   (or python -m vdsim.knowledge)
GUI:          python -m vdsim.knowledge.gui
See docs/KNOWLEDGE.md.
"""

from .collector import KnowledgeBase, collect
from .references import Reference, ReferenceDB

__all__ = ["KnowledgeBase", "Reference", "ReferenceDB", "build_graph", "collect", "generate_docs"]


def build_graph(kb=None, **kwargs):
    from .graph import build_graph as _build
    return _build(kb if kb is not None else collect(**kwargs))


def generate_docs(kb=None, out_dir=None, **kwargs):
    from .generator import generate
    return generate(kb if kb is not None else collect(**kwargs), out_dir)
