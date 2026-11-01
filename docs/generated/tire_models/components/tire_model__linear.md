# tire_model/linear

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [tire_models](../index.md) · `tire_model/linear` · klassische Registry

**Lineares Reifenmodell mit Lastproportionalität und optionaler Begrenzung am Reibkreis.**

## Zweck

Reglerauslegung, lineare Analyse und Referenz für den linearen Fahrbereich.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tire_model` |
| Name | `linear` |
| Versionen | legacy |
| Implementierung | [`vdsim.tire_models.linear_tire.LinearTire`](../../../../vdsim/tire_models/linear_tire.py#L10) |
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
| `cornering_stiffness` | Schräglaufsteifigkeit bei Nennlast | N/rad | – | – | – |
| `longitudinal_stiffness` | Längssteifigkeit (je Reifen, Nennlast) – Längsschlupfsteifigkeit bei Nennlast | N | – | 1000 | – |
| `nominal_load` | Nennlast | N | – | 500 | – |
| `camber_stiffness` | Sturzsteifigkeit (je Reifen) | N/rad | 0 | 0 | – |
| `pneumatic_trail` | Reifennachlauf | m | 0.04 | 0 | 0.2 |
| `saturate` | Begrenzung am Reibkreis ein/aus | – | True | – | – |

## Verfahren

[Lineares Reifenmodell mit Reibkreis](../theory.md#linear_tire)

## Annahmen

- Kräfte proportional zu Schlupf und Radlast
- Rückstellmoment über konstanten Nachlauf

## Einschränkungen

- Keine Sättigungsform – der Übergang zum Gleiten ist ein harter Knick am Reibkreis

## Quellen

[Mitschke und Wallentowitz (2014)](../../references.md#mitschke2014)

## Verwendung

Tests: [tests/knowledge/test_knowledge_collector.py](../../../../tests/knowledge/test_knowledge_collector.py), [tests/test_tire_models.py](../../../../tests/test_tire_models.py)
