"""Reports: PDF report (matplotlib PdfPages), Markdown engineering summary, KPI comparison."""

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

from ..core.conventions import G
from ..visualization import plotter
from .kpi_evaluator import compare, evaluate
from .texts_en import KPI_GROUPS_EN, KPI_LABELS_EN, RATINGS_EN, STOP_REASONS_EN, english, translate_figure

RATING_SYMBOL = {"ok": "OK", "warn": "Hinweis", "fail": "nicht erfüllt", "": ""}
RATING_COLORS = {"OK": "#1a7f37", "nicht erfüllt": "#b42318", "Hinweis": "#9a6700"}
RATING_COLORS.update({RATINGS_EN[k]: v for k, v in list(RATING_COLORS.items())})

# texts of the report itself: (German, English)
TEXTS = {
    "title": ("Fahrdynamik-Simulationsbericht", "Vehicle dynamics simulation report"),
    "created": ("Erstellt {date:%d.%m.%Y %H:%M} mit vdsim", "Created {date:%Y-%m-%d %H:%M} with vdsim"),
    "run": ("Lauf", "Run"), "vehicle": ("Fahrzeug", "Vehicle"), "mass": ("Masse", "mass"), "wheelbase": ("Radstand", "wheelbase"),
    "model": ("Modell", "Model"), "maneuver": ("Manöver", "Maneuver"), "lateral": ("Querregler", "Lateral controller"),
    "longitudinal": ("Längsregler", "Longitudinal controller"), "end": ("Simulationsende", "End of the simulation"),
    "wall": ("Rechenzeit", "computing time"), "kpis": ("Kennwerte", "Key figures"),
    "columns": (["Gruppe", "Kennwert", "Wert", "Einheit", "Bewertung"], ["Group", "Key figure", "Value", "Unit", "Rating"]),
    "end_short": ("Ende", "end"), "findings": ("Befunde", "Findings"), "comparison": ("Vergleich", "Comparison"),
    "utilization": ("Reibwertausnutzung bis {v:.0%}", "Friction utilization up to {v:.0%}"),
    "at_limit": (" - Fahrzeug im Grenzbereich.", " - vehicle at the limit."),
    "max_ay": ("Maximale Querbeschleunigung {v:.2f} m/s² ({g:.2f} g).", "Largest lateral acceleration {v:.2f} m/s² ({g:.2f} g)."),
    "beta": ("Schwimmwinkel bis {v:.1f}° - Stabilität kritisch prüfen.", "Side-slip angle up to {v:.1f}° - check the stability."),
    "gradient": ("Eigenlenkgradient {v:.3f} °/(m/s²): ", "Understeer gradient {v:.3f} °/(m/s²): "),
    "understeer": ("untersteuernd.", "understeering."), "oversteer": ("übersteuernd!", "oversteering!"),
    "deviation": ("Maximale Bahnabweichung {v:.2f} m.", "Largest path deviation {v:.2f} m."),
}


def _lang(lang):
    if lang not in ("de", "en"):
        raise ValueError(f"unknown report language: {lang!r} (de or en)")
    return lang == "en"


def _t(key, lang):
    return TEXTS[key][1 if _lang(lang) else 0]


def _kpi_label(kpi, key, lang):
    return KPI_LABELS_EN.get(key, kpi["label"]) if _lang(lang) else kpi["label"]


def _kpi_rows(result, lang="de"):
    kpis = result.kpis or {k.key: k.to_dict() for k in evaluate(result)}
    rows = []
    en = _lang(lang)
    for key, kpi in kpis.items():
        value = kpi["value"]
        text = (english(value) if en else value) if isinstance(value, str) else ("-" if value is None or not np.isfinite(value)
                                                    else f"{value:.3f}" if abs(value) < 10 else f"{value:.1f}")
        rating = RATING_SYMBOL.get(kpi["rating"], "")
        rows.append([KPI_GROUPS_EN.get(kpi["group"], kpi["group"]) if en else kpi["group"], _kpi_label(kpi, key, lang), text,
                     kpi["unit"], RATINGS_EN.get(rating, rating) if en else rating])
    return rows


def _title_page(pdf, results, title, lang="de"):
    fig = plt.figure(figsize=(11.7, 8.3))
    fig.text(0.05, 0.92, title, fontsize=20, weight="bold")
    fig.text(0.05, 0.88, _t("created", lang).format(date=datetime.now()), fontsize=10, color="#555555")
    y = 0.80
    for result in results:
        scenario = result.metadata.get("scenario", {})
        vehicle = result.metadata.get("vehicle", {}).get("vehicle", {})
        lines = [f"{_t('run', lang)}: {result.name}",
                 f"{_t('vehicle', lang)}: {vehicle.get('name', '-')}   {_t('mass', lang)} {vehicle.get('mass', 0):.0f} kg   "
                 f"{_t('wheelbase', lang)} {vehicle.get('wheelbase', 0):.2f} m",
                 f"{_t('model', lang)}: {scenario.get('model', '-')}   {_t('maneuver', lang)}: {scenario.get('maneuver', '-')}   "
                 f"{_t('lateral', lang)}: {result.metadata.get('lateral_controller', '-')}   "
                 f"{_t('longitudinal', lang)}: {scenario.get('longitudinal_controller', '-')}",
                 f"{_t('end', lang)}: {_stop_reason(result, lang)}   "
                 f"{_t('wall', lang)} {result.metadata.get('wall_time', 0):.1f} s"]
        for line in lines:
            fig.text(0.05, y, line, fontsize=10)
            y -= 0.03
        y -= 0.02
    pdf.savefig(fig)
    plt.close(fig)


def _stop_reason(result, lang):
    reason = result.metadata.get("stop_reason", "-")
    return STOP_REASONS_EN.get(reason, reason) if _lang(lang) else reason


def _kpi_page(pdf, result, lang="de"):
    rows = _kpi_rows(result, lang)
    for start in range(0, len(rows), 30):
        fig, ax = plt.subplots(figsize=(11.7, 8.3))
        ax.axis("off")
        ax.set_title(f"{_t('kpis', lang)} - {result.name}", loc="left", fontsize=14)
        table = ax.table(cellText=rows[start:start + 30], colLabels=_t("columns", lang),
                         loc="upper left", colWidths=[0.15, 0.45, 0.12, 0.12, 0.14])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.3)
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(weight="bold")
            elif col == 4:
                text = cell.get_text().get_text()
                cell.set_text_props(color=RATING_COLORS.get(text, "black"))
        pdf.savefig(fig)
        plt.close(fig)


def generate_pdf(results, path, title=None, lang="de"):
    """PDF report of one or several runs; `lang` is "de" (default) or "en"."""
    results = results if isinstance(results, (list, tuple)) else [results]
    en = _lang(lang)
    title = title or _t("title", lang)

    def save(fig):
        pdf.savefig(translate_figure(fig) if en else fig)
        plt.close(fig)

    for result in results:
        if not result.kpis:
            evaluate(result)
    with PdfPages(path) as pdf:
        _title_page(pdf, results, title, lang)
        for result in results:
            _kpi_page(pdf, result, lang)
            figures = [plotter.overview_figure(result), plotter.tire_figure(result), plotter.heatmap_figure(result),
                       plotter.energy_figure(result)]
            if "suspension_travel" in result:
                figures.append(plotter.suspension_figure(result))
            for fig in figures:
                save(fig)
            fig, ax = plt.subplots(figsize=(8, 7), layout="constrained")
            mu = result.metadata.get("vehicle", {}).get("tires", {}).get("mu", 1.0)
            plotter.plot_ggv(ax, result, mu)
            save(fig)
        if len(results) > 1:
            save(plotter.compare_figure(results))
        info = pdf.infodict()
        info["Title"] = title
        info["Creator"] = "vdsim"
    return Path(path)


def engineering_summary(results, lang="de"):
    # Markdown summary with KPI tables and short automatic findings
    results = results if isinstance(results, (list, tuple)) else [results]
    en = _lang(lang)
    lines = ["# Engineering Summary", "", _t("created", lang).format(date=datetime.now()).rsplit(" ", 2)[0], ""]
    for result in results:
        kpis = result.kpis or {k.key: k.to_dict() for k in evaluate(result)}
        scenario = result.metadata.get("scenario", {})
        lines += [f"## {result.name}", "",
                  f"{_t('model', lang)} `{scenario.get('model', '-')}`, {_t('maneuver', lang)} `{scenario.get('maneuver', '-')}`, "
                  f"{_t('end_short', lang)}: {_stop_reason(result, lang)}", "",
                  "| " + " | ".join(_t("columns", lang)) + " |", "|---|---|---|---|---|"]
        for row in _kpi_rows(result, lang):
            lines.append("| " + " | ".join(str(c) for c in row) + " |")
        lines += ["", f"**{_t('findings', lang)}:**", ""] + [f"- {text}" for text in _findings(kpis, lang)] + [""]
    if len(results) > 1:
        table = compare(results)
        columns = _t("columns", lang)
        lines += [f"## {_t('comparison', lang)}", "", f"| {columns[1]} | {columns[3]} | " + " | ".join(r.name for r in results) + " |",
                  "|---|---|" + "---|" * len(results)]
        for key, row in table.items():
            values = [("-" if v is None else (english(v) if en else v) if isinstance(v, str) else f"{v:.3g}") for v in row["values"]]
            lines.append(f"| {_kpi_label(row, key, lang)} | {row['unit']} | " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def _findings(kpis, lang="de"):
    def value(key):
        return kpis.get(key, {}).get("value")

    findings = []
    util = value("max_friction_utilization")
    if util is not None and np.isfinite(util):
        findings.append(_t("utilization", lang).format(v=util) + (_t("at_limit", lang) if util > 0.95 else "."))
    ay = value("max_ay")
    if ay is not None:
        findings.append(_t("max_ay", lang).format(v=ay, g=ay / G))
    beta = value("max_beta")
    if beta is not None and beta > 5:
        findings.append(_t("beta", lang).format(v=beta))
    eg = value("understeer_gradient")
    if eg is not None:
        findings.append(_t("gradient", lang).format(v=eg) + _t("understeer" if eg > 0 else "oversteer", lang))
    err = value("max_lateral_error")
    if err is not None:
        findings.append(_t("deviation", lang).format(v=err))
    for key in ("test_passed", "collision", "lane_departure"):
        if key in kpis:
            value = kpis[key]["value"]
            findings.append(f"{_kpi_label(kpis[key], key, lang)}: {english(value) if _lang(lang) else value}.")
    return findings


def save_summary(results, path, lang="de"):
    Path(path).write_text(engineering_summary(results, lang), encoding="utf-8")
    return Path(path)
