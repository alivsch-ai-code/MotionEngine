# Stanley

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `tracking_controller/stanley` · Version 1.0.0

**Querregler auf Vorderachs-Querfehler und Kurswinkelfehler (Stanley, DARPA Grand Challenge).**

## Zweck

Vergleichsregler mit guter Spurtreue bei mittleren Geschwindigkeiten.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tracking_controller` |
| Name | `stanley` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.classic_lateral.Stanley`](../../../../vdsim/stabilization/classic_lateral.py#L202) |
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
| `with_speed_control` | eigene Geschwindigkeitsführung (FF + FB) | – | True | – | – |
| `k_v` | Speed loop: Verstärkung Geschwindigkeitsfehler | 1/s | 1 | 0 | – |
| `k_s` | Speed loop: Verstärkung Längsfehler | 1/s² | 0.3 | 0 | – |
| `gain` | Stanley-Verstärkung k | 1/s | 1.5 | 0 | – |
| `softening` | Weichmachung k_soft | m/s | 1 | 0 | – |
| `yaw_damping` | Gierratendämpfung | s | 0.08 | 0 | – |
| `feedforward` | Krümmungsvorsteuerung | – | True | – | – |

## Theorie

$\delta=\theta_e+\arctan(-k e_{fa}/(k_{soft}+v))+\delta_{ff}-k_r(r-v\kappa)$.

## Verfahren

[Stanley](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Vorwärtsfahrt

## Einschränkungen

- Keine Rückwärtsfahrt, kinematische Herleitung

## Validierung

- tests/stabilization/test_stabilization_classic.py

## Quellen

[Hoffmann et al. (2007)](../../references.md#hoffmann2007), [Snider (2009)](../../references.md#snider2009)

## Expertenmodus: Herleitungen und Hinweise

Für das kinematische Modell konvergiert der Vorderachsfehler exponentiell, $\dot e=-v\sin(\arctan(ke/v))$ (Hoffmann et al. 2007).
