from vdsim.knowledge.markdown import filter_expert, markdown_to_html
from vdsim.knowledge.mathrender import can_render, extract_formulas, render_formula

FORMULAS = [r"F = D \sin\left(C \arctan\left(B s - E (B s - \arctan(B s))\right)\right)",
            r"\dot\psi = \frac{v \cos\beta}{l}\left(\tan\delta_v - \tan\delta_h\right)",
            r"\text{TTC} = \frac{d}{v - v_{lead}}"]


def test_render_png_and_svg(tmp_path):
    for latex in FORMULAS:
        png = render_formula(latex, "png", cache=tmp_path)
        assert png is not None and png.path.read_bytes()[:4] == b"\x89PNG" and png.width > 10 and png.height > 5
    svg = render_formula(FORMULAS[0], "svg", cache=tmp_path)
    assert svg is not None and b"<svg" in svg.path.read_bytes()
    again = render_formula(FORMULAS[0], "png", cache=tmp_path)
    assert again.path == render_formula(FORMULAS[0], "png", cache=tmp_path).path      # cached
    assert render_formula(r"\begin{aligned}x\end{aligned}", cache=tmp_path) is None


def test_markdown_converter():
    md = ("# Titel {#t}\n\nText mit **fett**, *kursiv*, `code` und [Link](node:concept:x) [@werling2011, A.1].\n\n"
          "- a\n  - b\n1. c\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n```python\nx = 1 < 2\n```\n\n"
          "$$a = b$$ (3.8)\n\n## Herleitung\n\ngeheim\n\n## Weiter\n\n> Zitat\n")
    html = markdown_to_html(md, render_math=False, css=False)
    for part in ('<h1 id="t">', "<b>fett</b>", "<i>kursiv</i>", "<code>code</code>", 'href="node:concept:x"',
                 'href="ref:werling2011"', "<ul><li>a</li><ul><li>b</li></ul></ul><ol><li>c</li></ol>",
                 "<th>A</th>", "x = 1 &lt; 2", '<span class="eqno">(3.8)</span>', "Expertenmodus", "<blockquote>"):
        assert part in html, part
    hidden = markdown_to_html(md, render_math=False, css=False, expert=False)
    assert "geheim" not in hidden and "Weiter" in hidden
    assert "geheim" not in filter_expert("## Herleitung\ngeheim\n## X\n", False)


def test_markdown_with_rendered_math():
    html = markdown_to_html("Inline $x^2$ und\n\n$$\\frac{a}{b}$$\n", css=False)
    assert html.count("<img src=\"file:") == 2


def test_all_theory_formulas_render(kb):
    failures = []
    for pkg in kb.packages.values():
        docs = ([pkg.theory] if pkg.theory else [])
        for doc in docs:
            for _, latex in extract_formulas(doc.text):
                if not can_render(latex):
                    failures.append((doc.path, latex))
    own = [f for f in failures if not f[0].startswith(("vdsim/planning", "vdsim/stabilization", "vdsim/world",
                                                         "vdsim/runtime", "vdsim/matlab", "vdsim/perception",
                                                         "vdsim/prediction", "vdsim/behavior", "vdsim/ad",
                                                         "vdsim/api", "vdsim/research"))]
    assert own == [], own
