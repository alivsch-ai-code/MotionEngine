# PI-Geschwindigkeitsregler

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/pi` · Version 1.0.0

**PI-Regler auf den Geschwindigkeitsfehler.**

## Zweck

Klassischer Längsregler.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `pi` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.classic_longitudinal.PI`](../../../../vdsim/stabilization/classic_longitudinal.py#L87) |
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
| `kp` | K_P | 1/s | 1.5 | 0 | – |
| `ki` | K_I | 1/s² | 0.5 | 0 | – |

## Theorie

$a=K_Pe_v+K_I\int e_v$

## Verfahren

[Pid](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Vorwärtsfahrt

## Einschränkungen

- Keine Vorsteuerung

## Validierung

- tests/stabilization/test_stabilization_classic.py

## Quellen

[Åström und Hägglund (2006)](../../references.md#astrom2006)

## Expertenmodus: Herleitungen und Hinweise

PT2-ähnlicher geschlossener Kreis, stabil für $K_P,K_I>0$.
