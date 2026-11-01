"""Small Markdown -> HTML converter for the knowledge browser (no external dependency).

Supported: ATX headings with anchors ("## Titel {#concept-id}"), paragraphs, nested
unordered / ordered lists, pipe tables, fenced code blocks, inline code, bold / italic,
links, block quotes, horizontal rules, citations "[@werling2011, Abschn. 3.4]" and
formulas ($...$ inline, $$...$$ display, rendered via mathrender as images).

Expert mode: sections whose heading names a derivation, stability analysis, design
decision, optimization problem, research context or extension point (EXPERT_KEYWORDS),
and blocks between "<!-- expert -->" and "<!-- /expert -->", are expert content.
filter_expert(text, False) removes them; with expert=True they are marked in the HTML.
"""

from __future__ import annotations

import html
import re

from .references import CITATION_PATTERN, parse_citations

EXPERT_KEYWORDS = ("herleitung", "stabilität", "stabilitätsbetrachtung", "designentscheidung", "erweiterungspunkt",
                   "expert", "optimierungsproblem", "forschungsbez")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*(?:\{#([A-Za-z0-9_.:\-]+)\})?\s*$")
LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
INLINE_MATH = re.compile(r"(?<![\\$])\$(?!\$)(.+?)(?<![\\$])\$(?!\$)")

CSS = """
body { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #e6e6e6; background: #1e1f22; }
h1 { font-size: 20px; color: #ffffff; margin-top: 4px; }
h2 { font-size: 16px; color: #ffffff; border-bottom: 1px solid #3a3d43; padding-bottom: 2px; margin-top: 18px; }
h3 { font-size: 14px; color: #c8d3e0; margin-top: 12px; }
h4 { font-size: 13px; color: #c8d3e0; }
a { color: #6cb0ff; text-decoration: none; }
code { font-family: Consolas, 'Courier New', monospace; background: #2b2d31; color: #f0c674; }
pre { font-family: Consolas, 'Courier New', monospace; background: #26282c; border: 1px solid #3a3d43; padding: 6px; }
table { border-collapse: collapse; margin: 6px 0; }
th { background: #2b2d31; color: #ffffff; padding: 4px 8px; border: 1px solid #3a3d43; }
td { padding: 3px 8px; border: 1px solid #3a3d43; }
blockquote { color: #9a9ca3; border-left: 3px solid #3987e5; margin-left: 4px; padding-left: 8px; }
.expert { background: #24262f; border-left: 3px solid #a371f7; padding-left: 8px; }
.badge { color: #a371f7; font-size: 11px; font-weight: normal; }
.cite { color: #e3b341; }
.eqno { color: #9a9ca3; }
.muted { color: #9a9ca3; }
.math { color: #f0c674; }
"""


def is_expert_heading(title):
    t = title.lower()
    return any(k in t for k in EXPERT_KEYWORDS)


def filter_expert(text, expert):
    # remove (expert=False) or keep expert sections / blocks
    if expert:
        return text
    text = re.sub(r"<!--\s*expert\s*-->.*?<!--\s*/expert\s*-->", "", text or "", flags=re.S)
    out, skip_level, fenced = [], None, False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fenced = not fenced
        m = None if fenced else HEADING.match(line)
        if m:
            level = len(m.group(1))
            if skip_level is not None and level <= skip_level:
                skip_level = None
            if skip_level is None and is_expert_heading(m.group(2)):
                skip_level = level
                continue
        if skip_level is None:
            out.append(line)
    return "\n".join(out)


def slugify(text):
    s = re.sub(r"[^\w\- ]", "", text.lower(), flags=re.U).strip()
    return re.sub(r"[\s]+", "-", s)


class MarkdownRenderer:
    def __init__(self, render_math=True, math_color="#e6e6e6", math_fontsize=13, cite=None, link=None,
                 expert=True, mark_expert=True):
        self.render_math = render_math
        self.math_color, self.math_fontsize = math_color, math_fontsize
        self.cite = cite                # callable(ref_id, locator) -> (text, href)
        self.link = link                # callable(href) -> href
        self.expert, self.mark_expert = expert, mark_expert

    # ------------------------------------------------------------------ inline
    def _math_html(self, latex, display=False):
        if self.render_math:
            try:
                from .mathrender import render_formula
                res = render_formula(latex, "png", self.math_fontsize + (2 if display else 0), self.math_color)
            except Exception:
                res = None
            if res is not None:
                src = res.path.as_uri()
                return (f'<img src="{src}" width="{int(round(res.width))}" height="{int(round(res.height))}" '
                        f'style="vertical-align: middle" alt="{html.escape(latex, quote=True)}">')
        return f'<code class="math">{html.escape(latex)}</code>'

    def inline(self, text):
        holders = []

        def hold(fragment):
            holders.append(fragment)
            return f"\x00{len(holders) - 1}\x00"

        text = re.sub(r"`([^`]+)`", lambda m: hold(f"<code>{html.escape(m.group(1))}</code>"), text)
        text = INLINE_MATH.sub(lambda m: hold(self._math_html(m.group(1))), text)

        def cite(m):
            parts = []
            for ref_id, locator in parse_citations(m.group(0)):
                label, href = (self.cite(ref_id, locator) if self.cite else
                               (f"{ref_id}{', ' + locator if locator else ''}", f"ref:{ref_id}"))
                parts.append(f'<a class="cite" href="{html.escape(href, quote=True)}">{html.escape(label)}</a>')
            return hold("[" + "; ".join(parts) + "]") if parts else m.group(0)
        text = CITATION_PATTERN.sub(cite, text)

        def link(m):
            label, href = m.group(1), m.group(2).strip()
            if self.link:
                href = self.link(href)
            # the label may contain placeholders of this call (code, math); they are resolved at the end
            label = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(label, quote=False))
            return hold(f'<a href="{html.escape(href, quote=True)}">{label}</a>')
        text = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)", link, text)
        text = re.sub(r"<(https?://[^>\s]+)>", lambda m: hold(f'<a href="{m.group(1)}">{html.escape(m.group(1))}</a>'),
                      text)
        text = html.escape(text, quote=False)
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
        text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
        text = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<i>\1</i>", text)
        text = re.sub(r"  $", "<br>", text)
        while "\x00" in text:
            text = re.sub(r"\x00(\d+)\x00", lambda m: holders[int(m.group(1))], text)
        return text

    # ------------------------------------------------------------------ blocks
    def convert(self, text, css=True):
        text = filter_expert(text or "", self.expert)
        lines = text.replace("\r\n", "\n").split("\n")
        out = []
        i, n = 0, len(lines)
        expert_level = None
        while i < n:
            line = lines[i]
            stripped = line.strip()
            if not stripped:
                i += 1
                continue
            if re.match(r"^<!--.*-->$", stripped):
                if "/expert" in stripped and self.mark_expert:
                    out.append("</div>")
                elif "expert" in stripped and self.mark_expert:
                    out.append('<div class="expert"><span class="badge">Expertenmodus</span>')
                i += 1
                continue
            if stripped.startswith("```"):
                lang = stripped[3:].strip()
                j = i + 1
                body = []
                while j < n and not lines[j].strip().startswith("```"):
                    body.append(lines[j])
                    j += 1
                out.append(f'<pre class="{html.escape(lang)}"><code>{html.escape(chr(10).join(body))}</code></pre>')
                i = j + 1
                continue
            if stripped.startswith("$$"):
                j, body = i, stripped[2:]
                if body.rstrip().endswith("$$") and len(body.strip()) >= 2:
                    content, tail = body.rstrip()[:-2], ""
                elif "$$" in body:
                    content, tail = body.split("$$", 1)
                else:
                    parts = [body]
                    j = i + 1
                    while j < n and "$$" not in lines[j]:
                        parts.append(lines[j])
                        j += 1
                    last = lines[j] if j < n else "$$"
                    head, _, tail = last.partition("$$")
                    parts.append(head)
                    content = "\n".join(parts)
                eq = f'<p align="center">{self._math_html(content.strip(), True)}'
                if tail.strip():
                    eq += f' <span class="eqno">{self.inline(tail.strip())}</span>'
                out.append(eq + "</p>")
                i = j + 1
                continue
            m = HEADING.match(line)
            if m:
                level, title, anchor = len(m.group(1)), m.group(2), m.group(3) or slugify(m.group(2))
                if expert_level is not None and level <= expert_level:
                    out.append("</div>")
                    expert_level = None
                badge = ""
                if self.mark_expert and is_expert_heading(title) and expert_level is None:
                    out.append('<div class="expert">')
                    expert_level = level
                    badge = ' <span class="badge">Expertenmodus</span>'
                out.append(f'<a name="{html.escape(anchor)}"></a><h{level} id="{html.escape(anchor)}">'
                           f'{self.inline(title)}{badge}</h{level}>')
                i += 1
                continue
            if re.match(r"^(\*\s*){3,}$|^(-\s*){3,}$|^(_\s*){3,}$", stripped):
                out.append("<hr>")
                i += 1
                continue
            if stripped.startswith("|") and i + 1 < n and TABLE_SEP.match(lines[i + 1]):
                header = _cells(stripped)
                aligns = [("center" if c.startswith(":") and c.endswith(":") else "right" if c.endswith(":")
                           else "left") for c in _cells(lines[i + 1].strip())]
                rows = []
                j = i + 2
                while j < n and lines[j].strip().startswith("|"):
                    rows.append(_cells(lines[j].strip()))
                    j += 1
                h = "".join(f"<th>{self.inline(c)}</th>" for c in header)
                body = "".join("<tr>" + "".join(
                    f'<td align="{aligns[k] if k < len(aligns) else "left"}">{self.inline(c)}</td>'
                    for k, c in enumerate(r)) + "</tr>" for r in rows)
                out.append(f"<table><tr>{h}</tr>{body}</table>")
                i = j
                continue
            if stripped.startswith(">"):
                j, body = i, []
                while j < n and lines[j].strip().startswith(">"):
                    body.append(lines[j].strip()[1:].lstrip())
                    j += 1
                out.append(f"<blockquote>{self.convert(chr(10).join(body), css=False)}</blockquote>")
                i = j
                continue
            if LIST_ITEM.match(line):
                html_list, i = self._list(lines, i)
                out.append(html_list)
                continue
            j, para = i, []
            while j < n and lines[j].strip() and not (HEADING.match(lines[j]) or LIST_ITEM.match(lines[j])
                                                      or lines[j].strip().startswith(("```", "$$", "|", ">"))):
                para.append(lines[j].rstrip() if lines[j].endswith("  ") else lines[j].strip())
                j += 1
            if not para:
                para, j = [stripped], i + 1
            out.append(f"<p>{self.inline(chr(10).join(para)).replace(chr(10), ' ')}</p>")
            i = j
        if expert_level is not None:
            out.append("</div>")
        body = "\n".join(out)
        return f"<html><head><style>{CSS}</style></head><body>{body}</body></html>" if css else body

    def _list(self, lines, i):
        # nested lists by indentation
        out, stack = [], []          # stack of (indent, tag)
        n = len(lines)
        while i < n:
            line = lines[i]
            if not line.strip():
                if i + 1 < n and LIST_ITEM.match(lines[i + 1]):
                    i += 1
                    continue
                break
            m = LIST_ITEM.match(line)
            if not m:
                if stack and line.startswith(" "):
                    out[-1] = out[-1][:-5] + " " + self.inline(line.strip()) + "</li>"
                    i += 1
                    continue
                break
            indent = len(m.group(1).replace("\t", "    "))
            tag = "ol" if m.group(2)[0].isdigit() else "ul"
            while stack and indent < stack[-1][0]:
                out.append(f"</{stack.pop()[1]}>")
            if stack and indent == stack[-1][0] and tag != stack[-1][1]:
                out.append(f"</{stack.pop()[1]}>")
            if not stack or indent > stack[-1][0]:
                stack.append((indent, tag))
                out.append(f"<{tag}>")
            out.append(f"<li>{self.inline(m.group(3))}</li>")
            i += 1
        while stack:
            out.append(f"</{stack.pop()[1]}>")
        return "".join(out), i


def _cells(row):
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", row)]


def markdown_to_html(text, render_math=True, expert=True, cite=None, link=None, css=True, math_color="#e6e6e6",
                     mark_expert=True):
    return MarkdownRenderer(render_math, math_color, cite=cite, link=link, expert=expert,
                            mark_expert=mark_expert).convert(text, css=css)
