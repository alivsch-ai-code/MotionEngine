# Forschungsmodus – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/research/test_research_metrics.py](../../../tests/research/test_research_metrics.py) | Rechteckabstand, TTC/THW/DRAC gegen analytische Folgefahrt, Konsistenzmaß, Kostenanalyse, Speichern/Laden, deterministische Sweeps und Monte Carlo, Sensitivität |

## Tests, die dieses Paket verwenden

### [tests/research/test_research_metrics.py](../../../tests/research/test_research_metrics.py)

**Zeigt:** Rechteckabstand, TTC/THW/DRAC gegen analytische Folgefahrt, Konsistenzmaß, Kostenanalyse, Speichern/Laden, deterministische Sweeps und Monte Carlo, Sensitivität

Importiert: `vdsim.research.experiments`, `vdsim.research.metrics`

| Testfunktion | Beschreibung |
|---|---|
| `test_rectangle_distance_and_overlap` | – |
| `test_ttc_thw_and_min_distance` | – |
| `test_consistency_deviation_detects_replanning_jumps` | – |
| `test_evaluate_and_save_load_roundtrip` | – |
| `test_sweep_and_monte_carlo_jobs_are_deterministic` | – |
| `test_batch_statistics_and_sensitivity` | – |
