# Reifenmodelle – Validierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · **Validierung** · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Validierung laut Paketdoku

| Test | Zeigt |
|---|---|
| [tests/test_tire_models.py](../../../tests/test_tire_models.py) | Anfangssteigung gleich Parameter, Ungeradheit und Sättigung bei mu Fz, Lastdegression, Abbau von Fy durch kombinierten Schlupf, Nullkraft bei Nulllast, Vektorisierung |

## Tests, die dieses Paket verwenden

### [tests/knowledge/test_knowledge_collector.py](../../../tests/knowledge/test_knowledge_collector.py)

Komponenten: `tire_model/linear`, `tire_model/pacejka`

| Testfunktion | Beschreibung |
|---|---|
| `test_collects_whole_repository` | – |
| `test_legacy_and_framework_components` | – |
| `test_traces_from_code_and_module_yaml` | – |
| `test_handwritten_docs_complete` | – |
| `test_tests_examples_and_configs_linked` | – |
| `test_tolerant_against_broken_files` | – |

### [tests/stabilization/test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py)

Importiert: `vdsim.tire_models.isotropic`

| Testfunktion | Beschreibung |
|---|---|
| `test_models_registered` | – |
| `test_kesm_lagrange_and_singularity_free` | Euler-Lagrange equation of the derivation: s_dd (m + M tan^2 delta) + 2 M v delta_dot tan(delta)/cos^2 = Q, i.e. power balance E_dot = Q v - M v^2 tan(delta) delta_dot / cos^2 (rheonomic steering constraint) |
| `test_kesm_plant_reverses_and_holds_at_standstill` | – |
| `test_desm_matches_model4_and_linear_gain` | vx/vy plant form equals model 4 in (beta, v) coordinates |
| `test_kesm_runs_in_old_simulator` | – |
| `test_desm_standstill_and_low_speed` | – |
| `test_isotropic_tire_inversion` | – |
| `test_isotropic_tire_saturation` | – |

### [tests/test_tire_models.py](../../../tests/test_tire_models.py)

**Zeigt:** Anfangssteigung gleich Parameter, Ungeradheit und Sättigung bei mu Fz, Lastdegression, Abbau von Fy durch kombinierten Schlupf, Nullkraft bei Nulllast, Vektorisierung

Importiert: `vdsim.tire_models`, `vdsim.tire_models.brush_model`, `vdsim.tire_models.linear_tire`, `vdsim.tire_models.pacejka`

| Testfunktion | Beschreibung |
|---|---|
| `test_small_slip_stiffness_equals_parameter` | – |
| `test_forces_are_odd_and_saturate` | – |
| `test_pacejka_load_degressive_stiffness` | – |
| `test_combined_slip_reduces_lateral_force` | – |
| `test_zero_load_gives_zero_force` | – |
| `test_vectorized_and_factory` | – |

## Validierung von [tire_model/pacejka](components/tire_model__pacejka.md)

- tests/test_tire_models.py prüft Steifigkeit
- Sättigung
- Lastdegression und kombinierten Schlupf
