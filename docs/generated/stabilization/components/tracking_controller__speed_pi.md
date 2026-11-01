# Fahrzeug-Geschwindigkeitsregler (PI mit Anti-Windup)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/speed_pi` · Version 1.0.0

**PI-Geschwindigkeitsregler mit Back-Calculation-Anti-Windup und Vorsteuerung.**

## Zweck

Robuster Geschwindigkeitsregler bei Stellgrößensättigung.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `speed_pi` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.classic_longitudinal.VehicleSpeedController`](../../../../vdsim/stabilization/classic_longitudinal.py#L202) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `a_max` | max. Beschleunigung | m/s² | 3 | 0 | – |
| `a_min` | max. Verzögerung (negativ) | m/s² | -8 | – | 0 |
| `kp` | K_P | 1/s | 1.2 | 0 | – |
| `ki` | K_I | 1/s² | 0.4 | 0 | – |
| `k_aw` | Anti-Windup Rückrechnung | 1/s | 2 | 0 | – |
| `feedforward` | Beschleunigungsvorsteuerung a_d | – | True | – | – |

## Theorie

$a=a_d+K_Pe_v+K_II$, $\dot I=e_v+k_{aw}(a_{sat}-a)/K_I$

## Verfahren

[Anti windup](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Vorwärtsfahrt

## Einschränkungen

- Kein Positionsfehler

## Validierung

- tests/stabilization/test_stabilization_classic.py

## Quellen

[Åström und Hägglund (2006)](../../references.md#astrom2006)

## Expertenmodus: Herleitungen und Hinweise

Die Rückrechnung begrenzt den Integrator in der Sättigung (Åström/Hägglund).
