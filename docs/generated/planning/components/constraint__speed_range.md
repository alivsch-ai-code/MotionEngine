# Geschwindigkeitsbereich

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [planning](../index.md) · `constraint/speed_range` · Version 1.0.0

**0 ≤ v ≤ v_max: keine Richtungsumkehr innerhalb einer Trajektorie.**

## Zweck

Die Fahrtrichtung ς wird von der Verhaltensebene festgelegt (Werling 2.1.1, Fußnote 3); quintische Anhaltetrajektorien mit Überschwingen werden verworfen.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `constraint` |
| Name | `speed_range` |
| Versionen | 1.0.0 |
| Implementierung | [`vdsim.planning.constraints.SpeedRange`](../../../../vdsim/planning/constraints.py#L316) |
| Schnittstelle | – |
| Sprache | python |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `enabled` | aktiv | – | True | – | – |
| `v_max` | Max. Bahngeschwindigkeit | m/s | 60 | 1 | 100 |
| `allow_reversal` | Richtungsumkehr innerhalb einer Trajektorie zulassen | – | False | – | – |

## Quellen

[Werling (2011)](../../references.md#werling2011)

## Verwendung

Tests: [tests/planning/test_planning_plugins.py](../../../../tests/planning/test_planning_plugins.py)
