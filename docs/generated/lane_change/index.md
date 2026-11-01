# Spurwechsel-Latenzstudie

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`lane_change` · Quellcode: [lane_change/](../../../lane_change) · Paketdoku: [lane_change/docs/](../../../lane_change/docs)

## Übersicht

**Ursprüngliche Studie – Spurwechsel bei 120 km/h mit kinematischem Einspurmodell, verfälschter Aktuator-Kennlinie, Latenzkette und Rückkanal-Korrektur der Soll-Krümmung.**

Die Studie beantwortet, wann ein Planer einen Kennlinienfehler des Lenkaktors frühestens bemerken kann,
wie groß der dadurch aufgebaute Querversatz ist und wie gut eine Rückkanal-Korrektur ihn reduziert.
Latenzkette, Kennlinie und Korrektur sind heute Plattformmodule (vdsim.actuators,
vdsim.controllers.curvature_feedback); das Paket enthält Szenario, Simulationsschleife und Plots.

Paket-Docstring:

```text
Lane-change simulation with a kinematic single-track model and a latency chain.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 8 |
| Komponenten | 0 |
| Verfahren/Konzepte | 7 |
| @trace-Einträge | 4 |
| Tests | 1 |
| Beispiele | 1 |

## Architektur

- `profiles.lane_change_curvature()`: sinusförmige Soll-Krümmung des Spurwechsels.
- `simulation.simulate()`: Schleife Planer (Soll-Krümmung, Korrektur) → Gateway/Aktuator (Latenz, Kennlinie)
  → Fahrzeug (Euler-Schritt des kinematischen Modells) → Odometrie/Gateway (Latenz, Rauschen) → Schätzer.
- `vehicle_model.vehicle_step()`: kinematisches Einspurmodell mit Krümmung als Eingang.
- `latency.py`, `steering.py`, `correction.py`: Re-Exporte der Plattformmodule.
- `plotting.py`: Übersicht, Kennlinie, Signale, Latenzvergleich.
Einstieg: `run_lane_change.py`.

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`lane_change`](../../../lane_change/__init__.py) | 2 | – | Lane-change simulation with a kinematic single-track model and a latency chain. |
| [`lane_change.correction`](../../../lane_change/correction.py) | 6 | – | Feedback correction of the lane-change study; implemented in vdsim.controllers.curvature_feedback. |
| [`lane_change.latency`](../../../lane_change/latency.py) | 6 | – | Latency chain of the lane-change study; implemented in the platform (vdsim.actuators.latency). |
| [`lane_change.plotting`](../../../lane_change/plotting.py) | 146 | – | matplotlib figures for the lane-change simulations. |
| [`lane_change.profiles`](../../../lane_change/profiles.py) | 13 | – | Desired curvature for the lane change. |
| [`lane_change.simulation`](../../../lane_change/simulation.py) | 47 | – | Simulation loop: planner (desired curvature + correction) -> gateway -> actuator (with error) -> vehicle -> odometry -> gateway -> planner. |
| [`lane_change.steering`](../../../lane_change/steering.py) | 6 | – | Steering characteristic of the lane-change study; implemented in vdsim.actuators.steering_characteristic. |
| [`lane_change.vehicle_model`](../../../lane_change/vehicle_model.py) | 13 | – | Kinematic single-track model with curvature as input. |

### Abhängigkeiten

- nutzt: [actuators](../actuators/index.md), [controllers](../controllers/index.md)
- genutzt von: –
- externe Bibliotheken: `matplotlib`, `numpy`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Krümmung als Schnittstelle zwischen Planer und Aktor | entspricht der Systemarchitektur der Studie (Planer sendet Soll-Krümmung) | – |
| Schätzer kennt die Latenz (internes Modell der Wirkkette) | trennt den Effekt der Korrektur vom Problem der Latenzschätzung; in der Praxis z. B. per Kreuzkorrelation | – |
| Simulationsschritt 5 ms | alle Latenzen der Fälle sind Vielfache davon | – |

## Implementierung

- Gierratenrauschen 0,1 °/s wird als Krümmungsrauschen r/v auf die gemessene Krümmung addiert (Seed 0).
- Der Fehlerfaktor wird je Schritt als characteristic(k_sent)/k_sent protokolliert.

### Verfahren und Konzepte

- [Rückkanal-Korrektur des Krümmungsfehlers](../controllers/theory.md#curvature_feedback_correction)
- [Kinematisches Einspurmodell](../vehicle_models/theory.md#kinematic_bicycle)
- [Korrekturstudie](theory.md#lane_change_correction_study)
- [Krümmungsprofil des Spurwechsels](theory.md#lane_change_curvature_profile)
- [Latenzkette aus Totzeit und PT1](../actuators/theory.md#latency_chain)
- [Umlauflatenz der Wirkkette](theory.md#latency_round_trip)
- [Kennlinienfehler des Lenkaktors](../actuators/theory.md#steering_characteristic_error)

## Erweiterungspunkte

- Weitere Latenzfälle in vdsim/actuators/latency.py, andere Manöver als Krümmungsprofil in profiles.py

## Verwandte Module

[actuators](../actuators/index.md), [controllers](../controllers/index.md)

## Hauptquellen

[Ljung (1999)](../references.md#ljung1999), [comma.ai](../references.md#openpilot), [Smith (1957)](../references.md#smith1957)
