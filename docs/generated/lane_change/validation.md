# Spurwechsel-Latenzstudie – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py) | Regression der Studienergebnisse (y_end ideal 3,500 m, ohne Korrektur 3,849 m, mit Korrektur 3,627 m, geschätzter Fehlerfaktor 1,088) |

## Tests, die dieses Paket verwenden

### [tests/test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py)

**Zeigt:** Regression der Studienergebnisse (y_end ideal 3,500 m, ohne Korrektur 3,849 m, mit Korrektur 3,627 m, geschätzter Fehlerfaktor 1,088)

Importiert: `lane_change.latency`, `lane_change.simulation`

| Testfunktion | Beschreibung |
|---|---|
| `test_lane_change_study_regression` | results of the original latency study (run_lane_change.py) must not change |
| `test_gui_smoke` | – |
