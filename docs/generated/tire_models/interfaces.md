# Reifenmodelle – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

### [tire_model/brush](components/tire_model__brush.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tire_model/brush` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.tire_models.brush_model.BrushTire` |
| Schnittstelle | `vdsim.core.interfaces.TireModel` |

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

### [tire_model/isotropic](components/tire_model__isotropic.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tire_model/isotropic` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.tire_models.isotropic.IsotropicPacejkaTire` |
| Schnittstelle | `vdsim.core.interfaces.TireModel` |

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

### [tire_model/linear](components/tire_model__linear.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tire_model/linear` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.tire_models.linear_tire.LinearTire` |
| Schnittstelle | `vdsim.core.interfaces.TireModel` |

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

### [tire_model/pacejka](components/tire_model__pacejka.md)

| Eigenschaft | Wert |
|---|---|
| Spec | `tire_model/pacejka` |
| Versionen | legacy |
| Registry | klassisch (`vdsim.core.registry`) |
| Klasse | `vdsim.tire_models.pacejka.PacejkaTire` |
| Schnittstelle | `vdsim.core.interfaces.TireModel` |

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

## Öffentliche API

### `vdsim.tire_models`

| Name | Art | Beschreibung |
|---|---|---|
| [`create_tires(tire_params)`](../../../vdsim/tire_models/__init__.py#L14) | Funktion | (front, rear) tire model instances from TireParameters |
| [`create_tire_set(tire_params)`](../../../vdsim/tire_models/__init__.py#L24) | Funktion | one tire model instance for all four wheels (FL, FR, RL, RR) with per-wheel stiffness |

### `vdsim.tire_models.brush_model`

| Name | Art | Beschreibung |
|---|---|---|
| [`BrushTire`](../../../vdsim/tire_models/brush_model.py#L16) | Klasse | – |

### `vdsim.tire_models.isotropic`

| Name | Art | Beschreibung |
|---|---|---|
| [`IsotropicPacejkaTire`](../../../vdsim/tire_models/isotropic.py#L151) | Klasse | Isotropic Magic Formula tire for the generic vehicle models (per wheel, vectorized). |
| [`peak_slip(B, C)`](../../../vdsim/tire_models/isotropic.py#L39) | Funktion | slip magnitude of the force maximum, B atan(C s) = pi/2 (infinite for B <= 1) |
| [`saturation_factor(S, B, C, n)`](../../../vdsim/tire_models/isotropic.py#L63) | Funktion | factor [1 + tan(pi/2 (S/s_max)^n)] of the modified characteristic (inf at and beyond the peak) |
| [`force_magnitude(S, A, B, C, mode, n)`](../../../vdsim/tire_models/isotropic.py#L71) | Funktion | \|F\|(\|s\|) of the isotropic tire with the selected saturation treatment |
| [`lateral_force(s_q, F_l, A, B, C, mode, n, tol, max_iter)`](../../../vdsim/tire_models/isotropic.py#L95) | Funktion | Lateral force F_q of the isotropic tire for lateral slip s_q and longitudinal force F_l. |
| [`slip_for_force(F, A, B, C)`](../../../vdsim/tire_models/isotropic.py#L144) | Funktion | inverse of the unmodified characteristic below the peak: \|s\|(\|F\|), \|F\| < A |

### `vdsim.tire_models.linear_tire`

| Name | Art | Beschreibung |
|---|---|---|
| [`LinearTire`](../../../vdsim/tire_models/linear_tire.py#L10) | Klasse | – |

### `vdsim.tire_models.pacejka`

| Name | Art | Beschreibung |
|---|---|---|
| [`PacejkaTire`](../../../vdsim/tire_models/pacejka.py#L24) | Klasse | – |
| [`magic_formula(slip, B, C, D, E)`](../../../vdsim/tire_models/pacejka.py#L18) | Funktion | – |
