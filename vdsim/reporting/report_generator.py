"""Reports: PDF report (matplotlib PdfPages), Markdown engineering summary, KPI comparison."""

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

from ..core.conventions import G
from ..visualization import plotter
from .kpi_evaluator import compare, evaluate

RATING_SYMBOL = {"ok": "OK", "warn": "Hinweis", "fail": "nicht erfüllt", "": ""}


def _kpi_rows(result):
    kpis = result.kpis or {k.key: k.to_dict() for k in evaluate(result)}
    rows = []
    for kpi in kpis.values():
        value = kpi["value"]
        text = value if isinstance(value, str) else ("-" if value is None or not np.isfinite(value)
                                                    else f"{value:.3f}" if abs(value) < 10 else f"{value:.1f}")
        rows.append([kpi["group"], kpi["label"], text, kpi["unit"], RATING_SYMBOL.get(kpi["rating"], "")])
    return rows


def _title_page(pdf, results, title):
    fig = plt.figure(figsize=(11.7, 8.3))
    fig.text(0.05, 0.92, title, fontsize=20, weight="bold")
    fig.text(0.05, 0.88, f"Erstellt {datetime.now():%d.%m.%Y %H:%M} mit vdsim", fontsize=10, color="#555555")
    y = 0.80
    for result in results:
        scenario = result.metadata.get("scenario", {})
        vehicle = result.metadata.get("vehicle", {}).get("vehicle", {})
        lines = [f"Lauf: {result.name}",
                 f"Fahrzeug: {vehicle.get('name', '-')}   Masse {vehicle.get('mass', 0):.0f} kg   "
                 f"Radstand {vehicle.get('wheelbase', 0):.2f} m",
                 f"Modell: {scenario.get('model', '-')}   Manöver: {scenario.get('maneuver', '-')}   "
                 f"Querregler: {result.metadata.get('lateral_controller', '-')}   "
                 f"Längsregler: {scenario.get('longitudinal_controller', '-')}",
                 f"Simulationsende: {result.metadata.get('stop_reason', '-')}   "
                 f"Rechenzeit {result.metadata.get('wall_time', 0):.1f} s"]
        for line in lines:
            fig.text(0.05, y, line, fontsize=10)
            y -= 0.03
        y -= 0.02
    pdf.savefig(fig)
    plt.close(fig)


def _kpi_page(pdf, result):
    rows = _kpi_rows(result)
    for start in range(0, len(rows), 30):
        fig, ax = plt.subplots(figsize=(11.7, 8.3))
        ax.axis("off")
        ax.set_title(f"Kennwerte - {result.name}", loc="left", fontsize=14)
        table = ax.table(cellText=rows[start:start + 30], colLabels=["Gruppe", "Kennwert", "Wert", "Einheit", "Bewertung"],
                         loc="upper left", colWidths=[0.15, 0.45, 0.12, 0.12, 0.14])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.3)
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(weight="bold")
            elif col == 4:
                text = cell.get_text().get_text()
                cell.set_text_props(color={"OK": "#1a7f37", "nicht erfüllt": "#b42318", "Hinweis": "#9a6700"}.get(text, "black"))
        pdf.savefig(fig)
        plt.close(fig)


def generate_pdf(results, path, title="Fahrdynamik-Simulationsbericht"):
    results = results if isinstance(results, (list, tuple)) else [results]
    for result in results:
        if not result.kpis:
            evaluate(result)
    with PdfPages(path) as pdf:
        _title_page(pdf, results, title)
        for result in results:
            _kpi_page(pdf, result)
            figures = [plotter.overview_figure(result), plotter.tire_figure(result), plotter.heatmap_figure(result),
                       plotter.energy_figure(result)]
            if "suspension_travel" in result:
                figures.append(plotter.suspension_figure(result))
            for fig in figures:
                pdf.savefig(fig)
                plt.close(fig)
            fig, ax = plt.subplots(figsize=(8, 7), layout="constrained")
            mu = result.metadata.get("vehicle", {}).get("tires", {}).get("mu", 1.0)
            plotter.plot_ggv(ax, result, mu)
            pdf.savefig(fig)
            plt.close(fig)
        if len(results) > 1:
            fig = plotter.compare_figure(results)
            pdf.savefig(fig)
            plt.close(fig)
        info = pdf.infodict()
        info["Title"] = title
        info["Creator"] = "vdsim"
    return Path(path)


def engineering_summary(results):
    # Markdown summary with KPI tables and short automatic findings
    results = results if isinstance(results, (list, tuple)) else [results]
    lines = ["# Engineering Summary", "", f"Erstellt {datetime.now():%d.%m.%Y %H:%M}", ""]
    for result in results:
        kpis = result.kpis or {k.key: k.to_dict() for k in evaluate(result)}
        scenario = result.metadata.get("scenario", {})
        lines += [f"## {result.name}", "",
                  f"Modell `{scenario.get('model', '-')}`, Manöver `{scenario.get('maneuver', '-')}`, "
                  f"Ende: {result.metadata.get('stop_reason', '-')}", "",
                  "| Gruppe | Kennwert | Wert | Einheit | Bewertung |", "|---|---|---|---|---|"]
        for row in _kpi_rows(result):
            lines.append("| " + " | ".join(str(c) for c in row) + " |")
        lines += ["", "**Befunde:**", ""] + [f"- {text}" for text in _findings(kpis)] + [""]
    if len(results) > 1:
        table = compare(results)
        lines += ["## Vergleich", "", "| Kennwert | Einheit | " + " | ".join(r.name for r in results) + " |",
                  "|---|---|" + "---|" * len(results)]
        for row in table.values():
            values = [("-" if v is None else v if isinstance(v, str) else f"{v:.3g}") for v in row["values"]]
            lines.append(f"| {row['label']} | {row['unit']} | " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def _findings(kpis):
    def value(key):
        return kpis.get(key, {}).get("value")

    findings = []
    util = value("max_friction_utilization")
    if util is not None and np.isfinite(util):
        findings.append(f"Reibwertausnutzung bis {util:.0%}" + (" - Fahrzeug im Grenzbereich." if util > 0.95 else "."))
    ay = value("max_ay")
    if ay is not None:
        findings.append(f"Maximale Querbeschleunigung {ay:.2f} m/s² ({ay / G:.2f} g).")
    beta = value("max_beta")
    if beta is not None and beta > 5:
        findings.append(f"Schwimmwinkel bis {beta:.1f}° - Stabilität kritisch prüfen.")
    eg = value("understeer_gradient")
    if eg is not None:
        findings.append(f"Eigenlenkgradient {eg:.3f} °/(m/s²): " + ("untersteuernd." if eg > 0 else "übersteuernd!"))
    err = value("max_lateral_error")
    if err is not None:
        findings.append(f"Maximale Bahnabweichung {err:.2f} m.")
    for key in ("test_passed", "collision", "lane_departure"):
        if key in kpis:
            findings.append(f"{kpis[key]['label']}: {kpis[key]['value']}.")
    return findings


def save_summary(results, path):
    Path(path).write_text(engineering_summary(results), encoding="utf-8")
    return Path(path)
