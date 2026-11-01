# Spurwechsel-Latenzstudie – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`lane_change_curvature`](../../../lane_change/profiles.py#L6) | – | [Krümmungsprofil des Spurwechsels](theory.md#lane_change_curvature_profile) | – | [test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py) | module.yaml |
| [`simulate`](../../../lane_change/simulation.py#L10) | – | [Korrekturstudie](theory.md#lane_change_correction_study) | [Ljung (1999)](../references.md#ljung1999) | [test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py) | module.yaml |
| [`simulate`](../../../lane_change/simulation.py#L10) | – | [Umlauflatenz der Wirkkette](theory.md#latency_round_trip) | – | [test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py) | module.yaml |
| [`vehicle_step`](../../../lane_change/vehicle_model.py#L6) | – | [Kinematisches Einspurmodell](../vehicle_models/theory.md#kinematic_bicycle) | [Rajamani (2012)](../references.md#rajamani2012) | [test_lane_change_study_and_gui.py](../../../tests/test_lane_change_study_and_gui.py) | module.yaml |

## Warum es diese Implementierungen gibt

### `lane_change_curvature`

- **Warum:** Soll-Krümmung für einen Spurwechsel um die Breite $w$ in der Dauer $T$, bei dem der Kurswinkel am Ende wieder null ist.
- **Theorie:** [Krümmungsprofil des Spurwechsels](theory.md#lane_change_curvature_profile)
- **Annahmen:** Konstante Geschwindigkeit, kleine Kurswinkel.
- **Quelle:** –

### `simulate`

- **Warum:** Quantifizierung des Querversatzes durch den Kennlinienfehler und der Wirkung der Rückkanal-Korrektur.
- **Theorie:** [Korrekturstudie](theory.md#lane_change_correction_study)
- **Annahmen:** Latenz bekannt, Rauschen gaußsch (0,1 °/s Gierrate), Seed 0.
- **Quelle:** [Ljung (1999)](../references.md#ljung1999)

### `simulate`

- **Warum:** Bestimmung, wann der Planer einen Aktuatorfehler frühestens sehen kann.
- **Theorie:** [Umlauflatenz der Wirkkette](theory.md#latency_round_trip)
- **Annahmen:** Konstante Latenzen, Vielfache von 5 ms.
- **Quelle:** –

### `vehicle_step`

- **Warum:** Beschreibt die Fahrzeugbewegung allein aus der Lenkgeometrie, ohne Reifenschlupf.
- **Theorie:** [Kinematisches Einspurmodell](../vehicle_models/theory.md#kinematic_bicycle)
- **Annahmen:** - Kein Schräglauf, starre Räder, ebene Fahrbahn.
- **Quelle:** [Rajamani (2012)](../references.md#rajamani2012)
