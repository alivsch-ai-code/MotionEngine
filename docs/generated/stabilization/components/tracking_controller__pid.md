# PID-Geschwindigkeitsregler

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/pid` · Version 1.0.0

**PID-Regler auf den Geschwindigkeitsfehler der Solltrajektorie.**

## Zweck

Klassischer Längsregler zum Vergleich.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `pid` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.classic_longitudinal.PID`](../../../../vdsim/stabilization/classic_longitudinal.py#L64) |
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
| `kd` | K_D | - | 0.05 | 0 | – |

## Theorie

$a=K_Pe_v+K_I\int e_v+K_D\dot e_v$

## Verfahren

[Pid](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Vorwärtsfahrt

## Einschränkungen

- Keine Vorsteuerung, Schleppfehler in e_t

## Validierung

- tests/stabilization/test_stabilization_classic.py

## Quellen

[Åström und Hägglund (2006)](../../references.md#astrom2006)

## Expertenmodus: Herleitungen und Hinweise

Stabil für positive Verstärkungen am Integrator $\dot v=a$.
