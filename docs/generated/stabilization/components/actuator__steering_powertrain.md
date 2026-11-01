# Lenkaktor und Antrieb/Bremse

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `actuator/steering_powertrain` · Version 1.0.0

**Integriert die Lenkrate bzw. übernimmt den Lenkwinkel, bildet Lenkaktor (Latenz, Kennlinie, Ratenbegrenzung) sowie verzögerte Antriebs- und Bremsmomente nach.**

## Zweck

Verbindet die Stellgrößen der Trajektorienregelung mit der Strecke; die Latenzkette der ursprünglichen Spurwechsel-Latenzstudie bleibt in der Wirkkette nutzbar.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `actuator` |
| Name | `steering_powertrain` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.vehicle_layers.SteeringPowertrainActuator`](../../../../vdsim/stabilization/vehicle_layers.py#L178) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `demand` | `ActuatorCommand` | – | – | – |
| `ego` | `EgoState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `control` | `ControlInput` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `steering` | Lenkaktor (SteeringActuatorParameters) | – | {…} | – | – |
| `max_steer_angle` | Lenkwinkelgrenze (<0: aus Fahrzeug) | rad | -1 | – | – |
| `drive_dead_time` | Totzeit Antrieb | s | 0 | 0 | – |
| `drive_tau` | PT1 Antrieb | s | 0 | 0 | – |
| `brake_dead_time` | Totzeit Bremse | s | 0 | 0 | – |
| `brake_tau` | PT1 Bremse | s | 0 | 0 | – |

## Verfahren

[Steering actuator](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Konstanter Schritt dt (Komponentenperiode bzw. Executor-Schritt)

## Einschränkungen

- Kennlinienfehler wirkt auf die Krümmung tan(delta)/l (wie vdsim.actuators)

## Validierung

- tests/stabilization/test_stabilization_layers.py

## Umgesetzte Gleichungen

- `werling2011:5.1.2.1`

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Expertenmodus: Herleitungen und Hinweise

Die Integration von $\dot\delta$ erfolgt mit Begrenzung (Anti-Windup), damit der Integrator an der Lenkanschlaggrenze nicht wegläuft.

## Verwendung

Tests: [tests/stabilization/test_stabilization_layers.py](../../../../tests/stabilization/test_stabilization_layers.py)
