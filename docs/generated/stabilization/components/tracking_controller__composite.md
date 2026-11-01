# Kombination Quer- + Längsregler

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/composite` · Version 1.0.0

**Kombiniert einen beliebigen Quer- und Längsregler zu einem Trackingregler.**

## Zweck

Klassische entkoppelte Quer-/Längsregelung als Vergleich zur gekoppelten Werling-Regelung.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `composite` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.composite.CompositeController`](../../../../vdsim/stabilization/composite.py#L34) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `objects` | `ObjectList` | – | Objekte (für ACC) | optional |
| `trajectory` | `PlannedTrajectory` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `status` | `ControllerStatus` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `lateral` | Querregler | – | stanley | – | – |
| `longitudinal` | Längsregler | – | ff_fb | – | – |
| `lateral_params` | Parameter Querregler | – | {…} | – | – |
| `longitudinal_params` | Parameter Längsregler | – | {…} | – | – |

## Verfahren

[Composite](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Quer- und Längsdynamik entkoppelt

## Einschränkungen

- Kopplung (Kammscher Kreis) unberücksichtigt

## Validierung

- tests/stabilization/test_stabilization_classic.py

## Quellen

[Rajamani (2012)](../../references.md#rajamani2012)

## Expertenmodus: Herleitungen und Hinweise

Stabilität folgt aus den Teilreglern nur bei schwacher Kopplung.

## Verwendung

Konfigurationen: [configs/stabilization/classic_controllers.json](../../../../configs/stabilization/classic_controllers.json)
