# Split-Range-Längskraftumsetzung (Werling 5.1.2.2)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [stabilization](../index.md) · `vehicle_dynamics/split_range` · Version 1.0.0

**Setzt die Solllängskraft bzw. Sollbeschleunigung über Antrieb oder Bremse in Radmomente um.**

## Zweck

Die Entwurfsmodelle der Trackingregler vernachlässigen Roll- und Luftwiderstand; die Ebene kompensiert F_W(v) und regelt Restfehler (Gegenwind, Steigung) mit einem Integrator aus.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `vehicle_dynamics` |
| Name | `split_range` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.stabilization.vehicle_layers.SplitRangeDynamics`](../../../../vdsim/stabilization/vehicle_layers.py#L47) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `command` | `ControlCommand` | – | – | – |
| `ego` | `EgoState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `demand` | `ActuatorCommand` | – | – | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `k_i` | Integratorverstärkung k_I (Beschleunigungsfehler) | 1/s | 0.5 | 0 | – |
| `integrator_limit` | Integratorgrenze (Anteil von m g) | - | 0.3 | 0 | 1 |
| `compensate_resistance` | Fahrwiderstand F_W(v) kompensieren | – | True | – | – |
| `gamma_brake` | Bremskraftverteilung vorne gamma | - | 0.75 | 0 | 1 |
| `max_decel` | max. Verzögerung | m/s² | 10 | 0 | – |
| `regen` | Rekuperation über den E-Antrieb (nur EV) | – | False | – | – |
| `systems` | Fahrdynamiksysteme (esp, abs, tcs, torque_vectoring) | – | [] | – | – |
| `integrator_min_speed` | Integrator nur oberhalb \|v\| bzw. bei Sollbeschleunigung | m/s | 0.3 | 0 | – |

## Theorie

$u=F_{ld}+F_W(v)+k_I\int m(a_{exp}-a)\,dt$; $u\varsigma\geq0$: Antrieb (Rückwärtsgang bei $\varsigma=-1$), sonst Bremse. Anti-Windup: Integration angehalten, wenn das Stellglied gesättigt ist und der Fehler weiter in die Sättigung treibt (Werling Abb. 5.3).

## Verfahren

[Anti windup](../../README.md#konzepte-ohne-dokumentation) (undokumentiert), [Split-Range-Längskraftumsetzung](../theory.md#split_range)

## Annahmen

- Antriebsstrangdynamik vernachlässigt (Momente wirken unverzögert, Werling 5.1.2.2)
- Bremskraftverteilung fest gamma (Standard 0.75)

## Einschränkungen

- Kein Motorkennfeld F_M^-1 / Getriebe-Schleppmoment (Momentenschnittstelle)

## Validierung

- tests/stabilization/test_stabilization_layers.py

## Umgesetzte Gleichungen

- `werling2011:5.1.2.2`
- `werling2011:Abb. 5.3`

## Quellen

[Åström und Hägglund (2006)](../../references.md#astrom2006), [Werling (2011)](../../references.md#werling2011)

## Expertenmodus: Herleitungen und Hinweise

Stationär (konstante Störung F_s) gilt mit aktivem Integrator $a\to a_{exp}$, da der Integrator die Störung vollständig übernimmt; bei Sättigung bleibt sein Zustand begrenzt, sodass nach dem Verlassen der Sättigung kein Überschwingen entsteht.

## Verwendung

Tests: [tests/stabilization/test_stabilization_layers.py](../../../../tests/stabilization/test_stabilization_layers.py)
