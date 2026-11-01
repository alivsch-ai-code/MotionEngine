# Auswertung und Berichte

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.reporting` · Quellcode: [vdsim/reporting/](../../../vdsim/reporting) · Paketdoku: [vdsim/reporting/docs/](../../../vdsim/reporting/docs)

## Übersicht

**Automatische Kennwerte (Fahrdynamik, Bahnführung, Komfort nach ISO 2631, Energie, Normtest-Kriterien), Laufvergleich, PDF-Bericht und Engineering Summary.**

Ein Simulationslauf ist erst mit objektiven Kennwerten bewertbar. `KPIEvaluator` erkennt das Manöver aus
den Trajektorien-Metadaten und berechnet neben allgemeinen Kennwerten die Kriterien der jeweiligen Norm
(ISO 3888, ISO 4138, ISO 7401, FMVSS 126, Bremsweg/MFDD). Berichte fassen Läufe für Menschen zusammen.

Paket-Docstring:

```text
Reporting: KPI evaluation, run comparison, PDF / Markdown reports.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 3 |
| Komponenten | 0 |
| Verfahren/Konzepte | 4 |
| @trace-Einträge | 9 |
| Tests | 2 |
| Beispiele | 1 |

## Architektur

- `kpi_evaluator.py`: `KPI` (Schlüssel, Bezeichnung, Wert, Einheit, Gruppe, Bewertung ok/warn/fail),
  `KPIEvaluator.evaluate(result)` mit allgemeinen, Komfort-, Energie- und manöverspezifischen Kennwerten,
  `iso2631_weighted_rms`, `iso2631_rating`, `compare(results)`.
- `report_generator.py`: PDF (matplotlib PdfPages) mit Titelseite, KPI-Tabellen und Diagrammen;
  Markdown-Engineering-Summary mit automatischen Befunden.

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.reporting`](../../../vdsim/reporting/__init__.py) | 6 | – | Reporting: KPI evaluation, run comparison, PDF / Markdown reports. |
| [`vdsim.reporting.kpi_evaluator`](../../../vdsim/reporting/kpi_evaluator.py) | 339 | KPI, KPIEvaluator | Automatic KPI evaluation of simulation results. |
| [`vdsim.reporting.report_generator`](../../../vdsim/reporting/report_generator.py) | 157 | – | Reports: PDF report (matplotlib PdfPages), Markdown engineering summary, KPI comparison. |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [visualization](../visualization/index.md)
- genutzt von: [gui](../gui/index.md)
- externe Bibliotheken: `dataclasses`, `datetime`, `matplotlib`, `numpy`, `pathlib`, `scipy`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Manöverspezifische Kennwerte über die Metadaten der Trajektorie (maneuver) auswählen | neue Manöver bringen ihre Auswertung über den Namen mit; der Simulator bleibt unabhängig | – |
| Bewertung je KPI (ok, warn, fail) mit festen, normnahen Grenzen | schneller Überblick im KPI-Dashboard und im Bericht | – |

## Implementierung

- Querruck aus der Querbeschleunigung nach gleitendem Mittel über 0,1 s (etwa 4-Hz-Tiefpass), dann numerisch differenziert.
- Kegeltreffer über die vier Fahrzeugecken gegen die Gassen (oder, ohne Gassen, Pylone im Fahrzeugrechteck).
- Die Engineering Summary enthält einen Zeitstempel im Kopf (nicht deterministisch, bewusst für Berichte).

### Verfahren und Konzepte

- [Frequenzgang aus dem Sinus-Sweep](theory.md#frequency_response_estimation)
- [Reibwertausnutzung und Stabilitätsreserve](theory.md#friction_utilization)
- [Komfortbewertung nach ISO 2631-1](theory.md#iso2631_comfort)
- [Kennwerte der Normversuche](theory.md#iso_test_kpis)

## Erweiterungspunkte

- Neuer Kennwert als Methode in KPIEvaluator und Eintrag in der Manöver-Zuordnung von evaluate()

## Verwandte Module

[simulation](../simulation/index.md), [analysis](../analysis/index.md), [visualization](../visualization/index.md), [gui](../gui/index.md)

## Hauptquellen

[FMVSS No. 126 (49 CFR 571.126) (2007)](../references.md#fmvss126), [ISO 2631-1:1997 (1997)](../references.md#iso2631_1), [ISO 3888-1:2018 (2018)](../references.md#iso3888_1), [ISO 3888-2:2011 (2011)](../references.md#iso3888_2), [ISO 4138:2021 (2021)](../references.md#iso4138), [ISO 7401:2011 (2011)](../references.md#iso7401), [ISO 7975:2019 (2019)](../references.md#iso7975), [UN-ECE-Regelung Nr. 13-H](../references.md#unece_r13h), [Welch (1967)](../references.md#welch1967)
