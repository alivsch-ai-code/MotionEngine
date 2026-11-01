# Aktorik – Latenzkette, Lenkaktor, Kennlinienfehler

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.actuators` · Quellcode: [vdsim/actuators/](../../../vdsim/actuators) · Paketdoku: [vdsim/actuators/docs/](../../../vdsim/actuators/docs)

## Übersicht

**Bildet die Wirkkette zwischen Planer und Fahrzeug nach – Totzeiten, PT1-Verzögerung, verfälschte Aktuator-Kennlinie, Ratenbegrenzung und Rückkanal-Korrektur.**

Reale Lenkanforderungen erreichen das Fahrzeug verzögert (Gateway, Aktuator) und verfälscht (Kennlinie),
und der Planer sieht die Wirkung erst nach dem Rückkanal (Odometrie, Gateway). Das Paket macht diese
Effekte für jedes Szenario einstellbar und ist die Plattform-Umsetzung der ursprünglichen
Spurwechsel-Latenzstudie (Paket lane_change).

Paket-Docstring:

```text
Actuators: latency chain, steering characteristic, steering actuator.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 4 |
| Komponenten | 0 |
| Verfahren/Konzepte | 3 |
| @trace-Einträge | 6 |
| Tests | 2 |
| Beispiele | 1 |

## Architektur

- `latency.py`: `DeadTime` (Ringpuffer), `PT1` (Verzögerung erster Ordnung), `LatencyChain`
  (Stellpfad Totzeit + PT1, Rückkanal Totzeit) und die vordefinierten Fälle `LATENCY_CASES`.
- `steering_characteristic.py`: `steering_characteristic()` (quadratisch ansteigender Krümmungsfehler bis
  Volleinschlag) und `correction_factor()` (theoretische Inverse).
- `steering_actuator.py`: `SteeringActuator` und `SteeringActuatorParameters`; Kette
  Anforderung → Korrektur → Latenz → Kennlinie → Ratenbegrenzung.

### Datenfluss

delta_req → kappa = tan(delta)/L → kappa_sent = kappa/g_hat → Totzeit, PT1 → Kennlinie → delta = atan(kappa L)
→ Ratenbegrenzung → Fahrzeug. Rückkanal: kappa_mess = r/v → Totzeit → Schätzer.

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.actuators`](../../../vdsim/actuators/__init__.py) | 9 | – | Actuators: latency chain, steering characteristic, steering actuator. |
| [`vdsim.actuators.latency`](../../../vdsim/actuators/latency.py) | 54 | DeadTime, PT1, LatencyChain | Latency in the effect chain: planner -> gateway -> actuator -> vehicle -> odometry -> gateway -> planner. |
| [`vdsim.actuators.steering_actuator`](../../../vdsim/actuators/steering_actuator.py) | 64 | SteeringActuatorParameters, SteeringActuator | Steering actuator for the platform simulator. |
| [`vdsim.actuators.steering_characteristic`](../../../vdsim/actuators/steering_characteristic.py) | 27 | – | Steering characteristic: requested curvature -> curvature the vehicle actually drives. |

### Abhängigkeiten

- nutzt: [controllers](../controllers/index.md)
- genutzt von: [lane_change](../lane_change/index.md), [simulation](../simulation/index.md), [stabilization](../stabilization/index.md)
- externe Bibliotheken: `collections`, `dataclasses`, `numpy`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Kennlinie und Korrektur auf der Krümmung statt auf dem Lenkwinkel | identisch zur Spurwechsel-Studie; die Krümmung ist die Schnittstelle zwischen Planer und Aktor | Lenkwinkel- oder Lenkmomentschnittstelle |
| Totzeit als ganzzahliges Vielfaches des Reglertakts (Ringpuffer) | exakt, deterministisch, ohne Interpolation | Padé-Approximation (verfälscht den Frequenzgang), Interpolation zwischen Abtastwerten |

## Implementierung

- Die PT1 ist mit dem impliziten Euler-Verfahren diskretisiert (alpha = dt/(tau + dt)); tau = 0 ergibt Durchgriff.
- Der Lenkaktor führt ein zweites, identisches LatencyChain-Objekt als internes Modell für die zeitliche Ausrichtung des Schätzers.

### Verfahren und Konzepte

- [Latenzkette aus Totzeit und PT1](theory.md#latency_chain)
- [Wirkkette des Lenkaktors](theory.md#steering_actuator_chain)
- [Kennlinienfehler des Lenkaktors](theory.md#steering_characteristic_error)

## Erweiterungspunkte

- Weitere Latenzfälle in LATENCY_CASES
- Eigene Kennlinie als Funktion kappa -> kappa (Rückgabewert von steering_characteristic ersetzen)

## Verwandte Module

[controllers](../controllers/index.md), [lane_change](../lane_change/index.md), [simulation](../simulation/index.md)

## Hauptquellen

[Ljung (1999)](../references.md#ljung1999), [comma.ai](../references.md#openpilot), [Smith (1957)](../references.md#smith1957)
