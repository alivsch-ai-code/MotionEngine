# Fahrzeugmodell (vdsim)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `vehicle_plant/vehicle_model` · Version 1.0.0

**Umschließt ein registriertes vdsim-Fahrzeugmodell als Strecke der Wirkkette (ohne Durchgriff).**

## Zweck

Beliebige Fahrzeugmodelle (Werling-Entwurfsmodelle, Einspur-, Zweispur-, Mehrkörpermodell) als Strecke für Reglerentwicklung und Robustheitsuntersuchungen.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `vehicle_plant` |
| Name | `vehicle_model` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.plant.VehicleModelPlant`](../../../../vdsim/stabilization/plant.py#L47) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | nein |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `control` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `model` | Fahrzeugmodell (vdsim vehicle_model) | – | werling_desm | – | – |
| `solver` | Integrator | – | rk4 | – | – |
| `dt_model` | Modellschrittweite (0: Empfehlung des Modells) | s | 0 | 0 | – |
| `x0` | Startposition x (falls kein Szenario) | m | 0 | – | – |
| `y0` | Startposition y | m | 0 | – | – |
| `psi0` | Start-Gierwinkel | rad | 0 | – | – |
| `v0` | Startgeschwindigkeit (vorzeichenbehaftet) | m/s | 0 | – | – |
| `delta0` | Start-Lenkwinkel | rad | 0 | – | – |
| `disturbances` | Störkräfte [{t, duration, fx, fy, mz}] | – | [] | – | – |

## Verfahren

[Vehicle plant](../../README.md#konzepte-ohne-dokumentation) (undokumentiert)

## Annahmen

- Stellgrößen über einen Executor-Schritt konstant (Halteglied)

## Einschränkungen

- Rückwärtsfahrt nur mit werling_kesm, bicycle_kinematic (werling_desm nur langsam)
- Störkräfte nur bei Modellen mit Zuständen vy und r

## Validierung

- tests/stabilization/test_stabilization_layers.py

## Umgesetzte Gleichungen

- `werling2011:(4.2)`
- `werling2011:(4.39)`

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Expertenmodus: Herleitungen und Hinweise

Explizite Integration (Euler/Heun/RK4) mit Teilschritten; die Teilschrittweite ist durch die Empfehlung bzw. stable_dt des Modells begrenzt (z. B. DESM: $h<2/\max(\lambda_i)$ mit $\lambdapprox(c_v+c_h)/(mv)$), damit RK4 numerisch stabil bleibt.

## Verwendung

Tests: [tests/stabilization/test_stabilization_layers.py](../../../../tests/stabilization/test_stabilization_layers.py)
