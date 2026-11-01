# tire_model/pacejka

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [tire_models](../index.md) · `tire_model/pacejka` · klassische Registry

**Magic Formula (reduzierter Parametersatz) mit lastabhängiger Steifigkeit und Reibung, Sturz, kombiniertem Schlupf und Rückstellmoment.**

## Zweck

Standardmodell für Simulationen im Grenzbereich.

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tire_model` |
| Name | `pacejka` |
| Versionen | legacy |
| Implementierung | [`vdsim.tire_models.pacejka.PacejkaTire`](../../../../vdsim/tire_models/pacejka.py#L24) |
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

## Verfahren

[Kombinierter Schlupf (Gewichtungsfunktionen)](../theory.md#combined_slip), [Pacejka Magic Formula](../theory.md#magic_formula)

## Annahmen

- Stationäres Reifenverhalten
- Symmetrie (keine Verschiebungen S_H
- S_V außer Sturz)

## Einschränkungen

- Kein Einlaufverhalten
- kein MF-6.2-Datensatz

## Validierung

- tests/test_tire_models.py prüft Steifigkeit
- Sättigung
- Lastdegression und kombinierten Schlupf

## Quellen

[Pacejka (2012)](../../references.md#pacejka2012)

## Verwendung

Tests: [tests/knowledge/test_knowledge_collector.py](../../../../tests/knowledge/test_knowledge_collector.py), [tests/test_tire_models.py](../../../../tests/test_tire_models.py)

Konfigurationen: [configs/vehicles/ev_sedan.json](../../../../configs/vehicles/ev_sedan.json), [configs/vehicles/mid_size_sedan.json](../../../../configs/vehicles/mid_size_sedan.json), [configs/vehicles/sports_car.json](../../../../configs/vehicles/sports_car.json), [configs/vehicles/suv.json](../../../../configs/vehicles/suv.json)
