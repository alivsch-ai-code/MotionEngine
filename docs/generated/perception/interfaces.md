# perception – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


> **Automatischer Stub:** Für `vdsim.perception` gibt es noch keine handgeschriebene Dokumentation (`vdsim/perception/docs/module.yaml`). Diese Seite zeigt nur, was aus dem Code erkannt wurde. Vorlage anlegen: `python tools/build_docs.py --init perception`


## Komponenten

### [Ground Truth (ungestört)](components/perception__ground_truth.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `perception/ground_truth`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.perception.sensor.GroundTruthPerception` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `world` | `WorldState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego_estimate` | `EgoState` | – | geschätzter Eigenzustand | – |
| `objects` | `ObjectList` | – | – | – |

### [Objektsensor (Reichweite, Rauschen, Latenz)](components/perception__object_sensor.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `perception/object_sensor`@1.0.0 |
| Versionen | 1.0.0 |
| Registry | versioniert (`vdsim.framework.plugins`) |
| Klasse | `vdsim.perception.sensor.ObjectSensor` |
| Schnittstelle | – |
| Periode | jeder Schritt |
| Direkter Durchgriff | ja |
| Sprache | python |

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego` | `EgoState` | – | – | – |
| `world` | `WorldState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `ego_estimate` | `EgoState` | – | geschätzter Eigenzustand | – |
| `objects` | `ObjectList` | – | – | – |

## Öffentliche API

### `vdsim.perception.sensor`

| Name | Art | Beschreibung |
|---|---|---|
| [`ObjectSensorParams`](../../../vdsim/perception/sensor.py#L27) | Klasse | – |
| [`ObjectSensor`](../../../vdsim/perception/sensor.py#L93) | Klasse | – |
| [`GroundTruthPerception`](../../../vdsim/perception/sensor.py#L175) | Klasse | – |
| [`visibility(sx, sy, heading, objects, rng_max, fov, occlusion, frac, rays)`](../../../vdsim/perception/sensor.py#L52) | Funktion | boolean mask of the objects inside range / field of view and (optionally) not occluded |
