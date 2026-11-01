# Aktorik – Latenzkette, Lenkaktor, Kennlinienfehler – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py) | Szenario mit Latenzkette schätzt den Aktuatorfehler (Fehlerfaktor nahe 1,1) |
| [tests/test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py) | Ergebnisse der Spurwechsel-Latenzstudie unverändert (Regression) |

## Tests, die dieses Paket verwenden

### [tests/test_controllers_and_systems.py](../../../tests/test_controllers_and_systems.py)

**Zeigt:** Szenario mit Latenzkette schätzt den Aktuatorfehler (Fehlerfaktor nahe 1,1)

| Testfunktion | Beschreibung |
|---|---|
| `test_dlc_path_tracking` | – |
| `test_stanley_has_no_steady_state_offset_in_tight_turns` | – |
| `test_acc_keeps_time_gap` | – |
| `test_aeb_avoids_stationary_obstacle` | – |
| `test_lane_keeping_assist_prevents_departure` | – |
| `test_torque_vectoring_reduces_understeer` | – |
| `test_active_roll_reduces_roll_and_rear_steering_acts` | – |
| `test_esp_reduces_side_slip_in_sine_with_dwell` | – |
| `test_latency_chain_scenario_estimates_actuator_error` | – |

### [tests/test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py)

**Zeigt:** Ergebnisse der Spurwechsel-Latenzstudie unverändert (Regression)

| Testfunktion | Beschreibung |
|---|---|
| `test_lane_change_study_regression` | results of the original latency study (run_lane_change.py) must not change |
| `test_gui_smoke` | – |
