# Geometrie – Referenzkurven und Frenet-Koordinaten – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Datentypen

### `FrenetState`

Bahnkoordinaten eines Punktes

Definiert in `vdsim.geometry.reference_line.FrenetState`.

| Feld | Typ | Default |
|---|---|---|
| `s` | float | 0.0 |
| `s_d` | float | 0.0 |
| `s_dd` | float | 0.0 |
| `d` | float | 0.0 |
| `d_d` | float | 0.0 |
| `d_dd` | float | 0.0 |
| `d_p` | float | 0.0 |
| `d_pp` | float | 0.0 |

## Öffentliche API

### `vdsim.geometry.reference_line`

| Name | Art | Beschreibung |
|---|---|---|
| [`FrenetState`](../../../vdsim/geometry/reference_line.py#L32) | Klasse | Frenet coordinates of a point moving relative to the reference curve |
| [`ReferenceLine`](../../../vdsim/geometry/reference_line.py#L55) | Klasse | – |
| [`wrap_angle(a)`](../../../vdsim/geometry/reference_line.py#L27) | Funktion | – |
| [`curvature_profile(bounds, curvatures, transition)`](../../../vdsim/geometry/reference_line.py#L420) | Funktion | piecewise constant curvature with smoothstep ramps centered at the inner boundaries |
