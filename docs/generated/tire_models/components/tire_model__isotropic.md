# tire_model/isotropic

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [tire_models](../index.md) · `tire_model/isotropic` · klassische Registry

**Isotropic Magic Formula tire for the generic vehicle models (per wheel, vectorized).**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `tire_model` |
| Name | `isotropic` |
| Versionen | legacy |
| Implementierung | [`vdsim.tire_models.isotropic.IsotropicPacejkaTire`](../../../../vdsim/tire_models/isotropic.py#L151) |
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
| `nominal_load` | Nennlast | N | – | 500 | – |
| `shape_lateral` | Formfaktor C lateral | - | 1.3 | 1 | 2 |
| `pneumatic_trail` | Reifennachlauf | m | 0.04 | 0 | 0.2 |

## Verwendung

Tests: [tests/stabilization/test_stabilization_models.py](../../../../tests/stabilization/test_stabilization_models.py)
