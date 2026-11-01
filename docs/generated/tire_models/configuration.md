# Reifenmodelle – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `tires.model` | Auswahl linear / pacejka / brush | – | – |
| `tires.*` | alle Reifenparameter mit Einheit und Grenzen, siehe Parametersatz TireParameters im Paket core | – | – |

## Parameter von [tire_model/brush](components/tire_model__brush.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `cornering_stiffness` | – | – | – | – | – |
| `longitudinal_stiffness` | Längssteifigkeit (je Reifen, Nennlast) | N | – | 1000 | – |
| `nominal_load` | Nennlast | N | – | 500 | – |
| `load_sensitivity_stiffness` | Lastabhängigkeit Schräglaufsteifigkeit (Pacejka p_Ky2) | - | 2 | 0.5 | 5 |
| `load_sensitivity_mu` | Lastabhängigkeit Reibwert | - | -0.1 | -0.5 | 0 |
| `camber_stiffness` | Sturzsteifigkeit (je Reifen) | N/rad | 5000 | 0 | – |
| `pneumatic_trail` | Reifennachlauf | m | 0.04 | 0 | 0.2 |

## Parameter von [tire_model/isotropic](components/tire_model__isotropic.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `cornering_stiffness` | – | – | – | – | – |
| `nominal_load` | Nennlast | N | – | 500 | – |
| `shape_lateral` | Formfaktor C lateral | - | 1.3 | 1 | 2 |
| `pneumatic_trail` | Reifennachlauf | m | 0.04 | 0 | 0.2 |

## Parameter von [tire_model/linear](components/tire_model__linear.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `cornering_stiffness` | Schräglaufsteifigkeit bei Nennlast | N/rad | – | – | – |
| `longitudinal_stiffness` | Längssteifigkeit (je Reifen, Nennlast) – Längsschlupfsteifigkeit bei Nennlast | N | – | 1000 | – |
| `nominal_load` | Nennlast | N | – | 500 | – |
| `camber_stiffness` | Sturzsteifigkeit (je Reifen) | N/rad | 0 | 0 | – |
| `pneumatic_trail` | Reifennachlauf | m | 0.04 | 0 | 0.2 |
| `saturate` | Begrenzung am Reibkreis ein/aus | – | True | – | – |

## Parameter von [tire_model/pacejka](components/tire_model__pacejka.md)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `cornering_stiffness` | – | – | – | – | – |
| `longitudinal_stiffness` | Längssteifigkeit (je Reifen, Nennlast) | N | – | 1000 | – |
| `nominal_load` | Nennlast | N | – | 500 | – |
| `shape_lateral` | Formfaktor C lateral | - | 1.3 | 1 | 2 |
| `curvature_lateral` | Krümmungsfaktor E lateral | - | -0.5 | -5 | 1 |
| `shape_longitudinal` | Formfaktor C longitudinal | - | 1.65 | 1 | 2 |
| `curvature_longitudinal` | Krümmungsfaktor E longitudinal | - | 0 | -5 | 1 |
| `combined_lateral_reduction` | Kombinierter Schlupf: Abbau Fy durch kappa (B_yk) | - | 10 | 0 | – |
| `combined_longitudinal_reduction` | Kombinierter Schlupf: Abbau Fx durch alpha (B_xa) | - | 12 | 0 | – |
| `load_sensitivity_stiffness` | Lastabhängigkeit Schräglaufsteifigkeit (Pacejka p_Ky2) | - | 2 | 0.5 | 5 |
| `load_sensitivity_mu` | Lastabhängigkeit Reibwert | - | -0.1 | -0.5 | 0 |
| `camber_stiffness` | Sturzsteifigkeit (je Reifen) | N/rad | 5000 | 0 | – |
| `pneumatic_trail` | Reifennachlauf | m | 0.04 | 0 | 0.2 |

## Konfigurationsdateien, die Komponenten dieses Pakets verwenden

| Datei | Titel | Komponenten |
|---|---|---|
| [configs/vehicles/ev_sedan.json](../../../configs/vehicles/ev_sedan.json) | ev_sedan | `tire_model/pacejka` |
| [configs/vehicles/mid_size_sedan.json](../../../configs/vehicles/mid_size_sedan.json) | mid_size_sedan | `tire_model/pacejka` |
| [configs/vehicles/sports_car.json](../../../configs/vehicles/sports_car.json) | sports_car | `tire_model/pacejka` |
| [configs/vehicles/suv.json](../../../configs/vehicles/suv.json) | suv | `tire_model/pacejka` |
