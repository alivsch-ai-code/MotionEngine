# Auswertung und Berichte – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Datentypen

### `KPI`

Kennwert mit Einheit und Bewertung

Definiert in `vdsim.reporting.kpi_evaluator.KPI`.

| Feld | Typ | Default |
|---|---|---|
| `key` | str | – |
| `label` | str | – |
| `value` | float | – |
| `unit` | str | '' |
| `group` | str | 'Fahrdynamik' |
| `rating` | str | '' |

## Öffentliche API

### `vdsim.reporting.kpi_evaluator`

| Name | Art | Beschreibung |
|---|---|---|
| [`KPI`](../../../vdsim/reporting/kpi_evaluator.py#L18) | Klasse | – |
| [`KPIEvaluator`](../../../vdsim/reporting/kpi_evaluator.py#L65) | Klasse | – |
| [`iso2631_weighted_rms(acc, fs)`](../../../vdsim/reporting/kpi_evaluator.py#L43) | Funktion | Frequency-weighted RMS of vertical acceleration (ISO 2631-1, weighting Wk, band limit 0.4 Hz) |
| [`iso2631_rating(a_w)`](../../../vdsim/reporting/kpi_evaluator.py#L57) | Funktion | – |
| [`evaluate(result)`](../../../vdsim/reporting/kpi_evaluator.py#L325) | Funktion | – |
| [`compare(results)`](../../../vdsim/reporting/kpi_evaluator.py#L329) | Funktion | KPI comparison table: {key: {"label", "unit", "values": [per result]}} |

### `vdsim.reporting.report_generator`

| Name | Art | Beschreibung |
|---|---|---|
| [`generate_pdf(results, path, title)`](../../../vdsim/reporting/report_generator.py#L73) | Funktion | – |
| [`engineering_summary(results)`](../../../vdsim/reporting/report_generator.py#L104) | Funktion | Markdown summary with KPI tables and short automatic findings |
| [`save_summary(results, path)`](../../../vdsim/reporting/report_generator.py#L154) | Funktion | – |
