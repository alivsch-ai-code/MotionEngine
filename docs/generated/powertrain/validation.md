# Antriebsstrang, Bremse und Längsaktuierung – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/test_vehicle_models.py](../../../tests/test_vehicle_models.py) | Bremsweg aus 100 km/h im erwarteten Bereich, Radblockieren ohne ABS |
| [tests/test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | Energie-KPIs und Beschleunigungsmanöver 0–100 km/h |

## Tests, die dieses Paket verwenden

### [tests/test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py)

**Zeigt:** Energie-KPIs und Beschleunigungsmanöver 0–100 km/h

| Testfunktion | Beschreibung |
|---|---|
| `test_vehicle_config_json_roundtrip` | – |
| `test_scenario_library_builds` | – |
| `test_scenario_roundtrip` | – |
| `test_solvers_agree` | – |
| `test_results_save_load` | – |
| `test_maneuver_kpis` | – |
| `test_iso2631_weighting` | – |
| `test_report_and_comparison` | – |

### [tests/test_vehicle_models.py](../../../tests/test_vehicle_models.py)

**Zeigt:** Bremsweg aus 100 km/h im erwarteten Bereich, Radblockieren ohne ABS

| Testfunktion | Beschreibung |
|---|---|
| `test_linear_model_matches_linear_analysis` | – |
| `test_nonlinear_models_close_to_linear_in_linear_range` | – |
| `test_double_track_roll_and_loads_match_quasi_static` | – |
| `test_multibody_wheel_loads_and_static_equilibrium` | – |
| `test_kinematic_model_drives_kinematic_circle` | – |
| `test_wheel_lock_without_abs_and_abs_keeps_slip` | – |
