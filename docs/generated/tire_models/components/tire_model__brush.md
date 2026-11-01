# tire_model/brush

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [tire_models](../index.md) · `tire_model/brush` · klassische Registry

**Bürstenmodell mit parabolischer Druckverteilung und isotropem kombiniertem Schlupf.**

## Zweck

Physikalisch motiviertes Modell, das kombinierten Schlupf ohne empirische Gewichtungsfaktoren abbildet.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tire_model` |
| Name | `brush` |
| Versionen | legacy |
| Implementierung | [`vdsim.tire_models.brush_model.BrushTire`](../../../../vdsim/tire_models/brush_model.py#L16) |
| Schnittstelle | `vdsim.core.interfaces.TireModel` |
| Sprache | python |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `alpha` | `float` | – | Schräglaufwinkel in rad | – |
| `camber` | `float` | – | Sturzwinkel in rad | – |
| `fz` | `float` | – | Radlast in N | – |
| `kappa` | `float` | – | Längsschlupf (-) | – |
| `mu` | `float` | – | Reibwert (-) | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `fx` | `float` | – | Längskraft in N | – |
| `fy` | `float` | – | Seitenkraft in N | – |
| `mz` | `float` | – | Rückstellmoment in N m | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `cornering_stiffness` | – | – | – | – | – |
| `longitudinal_stiffness` | Längssteifigkeit (je Reifen, Nennlast) | N | – | 1000 | – |
| `nominal_load` | Nennlast | N | – | 500 | – |
| `load_sensitivity_stiffness` | Lastabhängigkeit Schräglaufsteifigkeit (Pacejka p_Ky2) | - | 2 | 0.5 | 5 |
| `load_sensitivity_mu` | Lastabhängigkeit Reibwert | - | -0.1 | -0.5 | 0 |
| `camber_stiffness` | Sturzsteifigkeit (je Reifen) | N/rad | 5000 | 0 | – |
| `pneumatic_trail` | Reifennachlauf | m | 0.04 | 0 | 0.2 |

## Verfahren

[Bürstenmodell](../theory.md#brush_model)

## Annahmen

- Parabolische Druckverteilung
- gleiche Haft- und Gleitreibung
- isotrope Borstensteifigkeit (über theta_x
- theta_y normiert)

## Einschränkungen

- Haft- und Gleitreibwert identisch
- daher kein Kraftabfall nach dem Maximum

## Quellen

[Pacejka (2012)](../../references.md#pacejka2012)

## Verwendung

Tests: [tests/test_tire_models.py](../../../../tests/test_tire_models.py)
