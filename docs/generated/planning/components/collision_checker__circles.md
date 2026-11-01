# Kreisapproximation (Ziegler/Stiller)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `collision_checker/circles` · Version 1.0.0

**Kollisionsprüfung mit Kreisüberdeckung der Fahrzeugumrisse, statisch und dynamisch über die Prädiktion.**

## Zweck

Schnelle Überlappungsprüfung tausender Kandidaten (Werling 3.5.4).

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `collision_checker` |
| Name | `circles` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.collision.CircleCollisionChecker`](../../../../vdsim/planning/collision.py#L97) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `n_circles_ego` | Kreise Ego (< 0: aus Planer-Einstellung) | – | -1 | -1 | 10 |

## Verfahren

[Kollisionsprüfung mit Kreisen](../theory.md#collision_circles), [Rampe des Sicherheitsabstands](../theory.md#safety_margin_ramp)

## Annahmen

- Schwimmwinkel am Referenzpunkt = 0 (Ausrichtung = Trajektorienrichtung)
- Objekte als Rechtecke entlang ihrer prädizierten Ausrichtung

## Einschränkungen

- zeitdiskrete Prüfung: bei sehr hohen Relativgeschwindigkeiten kann ein Durchtunneln zwischen zwei Abtastpunkten auftreten (Raster collision.dt verkleinern)

## Umgesetzte Gleichungen

- `werling2011:Abb. 3.10`

## Quellen

[Werling (2011)](../../references.md#werling2011), [Ziegler und Stiller (2010)](../../references.md#ziegler2010iv)

## Verwendung

Tests: [tests/planning/test_planning_collision.py](../../../../tests/planning/test_planning_collision.py), [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)

Beispiele: [examples/custom_nodes/python/my_collision_checker.py](../../../../examples/custom_nodes/python/my_collision_checker.py)
