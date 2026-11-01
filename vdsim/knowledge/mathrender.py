r"""LaTeX formulas -> PNG / SVG images with matplotlib mathtext (no LaTeX installation needed).

    result = render_formula(r"F = D \sin(C \arctan(B s))", fmt="png")
    result.path, result.width, result.height       # cached file, size in logical pixels

Images are cached in the user cache folder (vdsim.knowledge.paths.cache_dir("math"),
VDSIM_CACHE_DIR overrides). The cache key covers formula, format, size, color and dpi.
Only the mathtext subset of LaTeX is supported; common LaTeX commands that mathtext lacks
(\text, \operatorname, \dfrac, \tfrac, \boldsymbol, \left. ...) are mapped to equivalents.
Formulas that cannot be rendered return None (callers show the source text instead).
"""

from __future__ import annotations

import hashlib
import re
import struct
import threading
from dataclasses import dataclass
from pathlib import Path

from .paths import cache_dir

_LOCK = threading.Lock()
VERSION = "1"
INLINE = re.compile(r"(?<![\\$])\$(?!\$)(.+?)(?<![\\$])\$(?!\$)")
DISPLAY = re.compile(r"\$\$(.+?)\$\$", re.S)


@dataclass
class RenderResult:
    path: Path
    width: float          # logical pixels (image is rendered at `scale` times this size)
    height: float
    fmt: str


def normalize(latex):
    # map LaTeX commands to the matplotlib mathtext subset
    s = " ".join(str(latex).strip().split())
    s = re.sub(r"\\(text|textrm|operatorname|mbox)\s*\{", r"\\mathrm{", s)
    s = re.sub(r"\\(textbf|boldsymbol|bm)\s*\{", r"\\mathbf{", s)
    s = re.sub(r"\\textit\s*\{", r"\\mathit{", s)
    s = re.sub(r"\\[dt]frac", r"\\frac", s)
    s = s.replace(r"\left.", "").replace(r"\right.", "")
    s = s.replace(r"\lVert", r"\Vert").replace(r"\rVert", r"\Vert")
    s = s.replace(r"\coloneqq", ":=").replace(r"\eqqcolon", "=:")
    s = s.replace(r"\le ", r"\leq ").replace(r"\ge ", r"\geq ")
    s = re.sub(r"\\(qquad)", r"\\quad\\quad", s)
    s = s.replace(r"\!", "")
    s = re.sub(r"\\tag\{[^}]*\}", "", s)
    s = s.replace("&", "")
    s = s.replace(r"\\", r"\quad ")
    return s


def _key(latex, fmt, fontsize, color, dpi):
    return hashlib.sha256(f"{VERSION}|{latex}|{fmt}|{fontsize}|{color}|{dpi}".encode()).hexdigest()[:24]


def _png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return 0, 0
    return struct.unpack(">II", head[16:24])


def _svg_size(path):
    text = Path(path).read_text(encoding="utf-8", errors="ignore")[:2000]
    w = re.search(r'width="([\d.]+)(pt|px)?"', text)
    h = re.search(r'height="([\d.]+)(pt|px)?"', text)
    if not (w and h):
        return 0.0, 0.0
    factor = 96.0 / 72.0 if (w.group(2) or "pt") == "pt" else 1.0
    return float(w.group(1)) * factor, float(h.group(1)) * factor


def render_formula(latex, fmt="png", fontsize=13, color="#e6e6e6", dpi=96, scale=2.0, cache=None):
    # Render one formula (without the surrounding $) and return a RenderResult or None
    fmt = fmt.lower()
    if fmt not in ("png", "svg"):
        raise ValueError("fmt must be 'png' or 'svg'")
    expr = normalize(latex)
    if not expr:
        return None
    folder = Path(cache) if cache is not None else cache_dir("math")
    folder.mkdir(parents=True, exist_ok=True)
    render_dpi = dpi * (scale if fmt == "png" else 1.0)
    path = folder / f"{_key(expr, fmt, fontsize, color, render_dpi)}.{fmt}"
    failed = path.with_suffix(".failed")
    if failed.exists():
        return None
    if not path.exists() or path.stat().st_size == 0:
        try:
            from matplotlib import mathtext
            from matplotlib.font_manager import FontProperties
            with _LOCK:
                tmp = path.with_suffix(f".tmp.{fmt}")
                mathtext.math_to_image(f"${expr}$", str(tmp), prop=FontProperties(size=fontsize), dpi=render_dpi,
                                       format=fmt, color=color)
                tmp.replace(path)
        except Exception:
            try:
                failed.write_text(str(latex), encoding="utf-8")
            except OSError:
                pass
            return None
    if fmt == "png":
        w, h = _png_size(path)
        return RenderResult(path, w / scale, h / scale, fmt)
    w, h = _svg_size(path)
    return RenderResult(path, w, h, fmt)


def can_render(latex):
    # True if mathtext can parse the formula (no file is written)
    try:
        from matplotlib.mathtext import MathTextParser
        MathTextParser("path").parse(f"${normalize(latex)}$")
        return True
    except Exception:
        return False


def extract_formulas(text):
    # [(display: bool, latex)] in document order
    out = []
    pos = 0
    for m in DISPLAY.finditer(text or ""):
        out += [(False, x.group(1)) for x in INLINE.finditer(text[pos:m.start()])]
        out.append((True, m.group(1).strip()))
        pos = m.end()
    out += [(False, x.group(1)) for x in INLINE.finditer((text or "")[pos:])]
    return out
