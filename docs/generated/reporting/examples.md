# Auswertung und Berichte – Beispiele

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · **Beispiele** · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## [run_scenario.py](../../../run_scenario.py)

Command line: run scenarios, print KPIs, export results and reports.

python run_scenario.py --list
python run_scenario.py iso_doppelspurwechsel_80 --plot
python run_scenario.py kreisfahrt_r40 bremsen_100_abs --report bericht.pdf --summary bericht.md
python run_scenario.py configs/scenarios/slalom_60.json --csv slalom.csv
python run_scenario.py --all

Verwendet: `vdsim.reporting`, `vdsim.reporting.kpi_evaluator`, `vdsim.reporting.report_generator`

Ausführen: `python run_scenario.py`
