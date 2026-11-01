# world – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`sat_overlap`](../../../vdsim/world/collision.py#L28) | – | [Sat collision](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [gottschalk1996 (fehlt in docs/references)](../references.md#gottschalk1996) | [test_world_actors.py](../../../tests/world/test_world_actors.py) | Code (@trace) |
| [`RoadNetwork.corridor`](../../../vdsim/world/road.py#L405) | Abschn. 5.3.1 | [Box restriction](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_world_actors.py](../../../tests/world/test_world_actors.py) | Code (@trace) |
| [`RoadNetwork.route_line`](../../../vdsim/world/road.py#L482) | Abschn. 3.5.3 | [Continuous curvature road](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_world_actors.py](../../../tests/world/test_world_actors.py) | Code (@trace) |
| [`connect_poses`](../../../vdsim/world/road.py#L582) | Abschn. 3.5.3 | [Continuous curvature road](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_world_actors.py](../../../tests/world/test_world_actors.py) | Code (@trace) |
| [`idm_acceleration`](../../../vdsim/world/traffic_models.py#L44) | Abschn. 2 IDM: a = a[1-(v/v0)^δ-(s*/s)^2] | [Idm](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [treiber2000 (fehlt in docs/references)](../references.md#treiber2000) | – | Code (@trace) |
| [`mobil_incentive`](../../../vdsim/world/traffic_models.py#L75) | Abschn. 3 (3), (4), (8) | [Mobil](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [kesting2007 (fehlt in docs/references)](../references.md#kesting2007) | – | Code (@trace) |
