# Geometrie – Referenzkurven und Frenet-Koordinaten – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`ReferenceLine.evaluate`](../../../vdsim/geometry/reference_line.py#L113) | – | [Hermite-interpolierte Referenzkurve](theory.md#hermite_reference_curve) | [de Boor (2001)](../references.md#deboor2001) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py), [test_planning_modes.py](../../../tests/planning/test_planning_modes.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py), [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py), [test_runtime_native.py](../../../tests/runtime/test_runtime_native.py) | module.yaml |
| [`ReferenceLine.from_points`](../../../vdsim/geometry/reference_line.py#L384) | Abschn. 3.5.3 | [Glatte Krümmungsübergänge](theory.md#smooth_curvature_profile) | [Werling (2011)](../references.md#werling2011) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py), [test_planning_modes.py](../../../tests/planning/test_planning_modes.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py), [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py), [test_runtime_native.py](../../../tests/runtime/test_runtime_native.py) | module.yaml |
| [`ReferenceLine.project`](../../../vdsim/geometry/reference_line.py#L148) | Abschn. A.2 | [Projektion auf die Referenzkurve](theory.md#curve_projection) | [Werling (2011)](../references.md#werling2011) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py), [test_planning_modes.py](../../../tests/planning/test_planning_modes.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py), [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py), [test_runtime_native.py](../../../tests/runtime/test_runtime_native.py) | Code (@trace) |
| [`ReferenceLine.to_cartesian`](../../../vdsim/geometry/reference_line.py#L269) | Abschn. A.1 (A.1)-(A.6) | [Frenet-Transformation in geschlossener Form](theory.md#frenet_transformation) | [Werling (2011)](../references.md#werling2011) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py), [test_planning_modes.py](../../../tests/planning/test_planning_modes.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py), [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py), [test_runtime_native.py](../../../tests/runtime/test_runtime_native.py) | Code (@trace) |
| [`ReferenceLine.to_frenet`](../../../vdsim/geometry/reference_line.py#L251) | Abschn. A.1 (A.1)-(A.8) | [Frenet-Transformation in geschlossener Form](theory.md#frenet_transformation) | [Werling (2011)](../references.md#werling2011) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py), [test_planning_modes.py](../../../tests/planning/test_planning_modes.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py), [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py), [test_runtime_native.py](../../../tests/runtime/test_runtime_native.py) | Code (@trace) |
| [`curvature_profile`](../../../vdsim/geometry/reference_line.py#L420) | Abschn. 3.5.3 | [Glatte Krümmungsübergänge](theory.md#smooth_curvature_profile) | [Werling (2011)](../references.md#werling2011) | [test_planning_collision.py](../../../tests/planning/test_planning_collision.py), [test_planning_consistency.py](../../../tests/planning/test_planning_consistency.py), [test_planning_modes.py](../../../tests/planning/test_planning_modes.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py), [test_planning_polynomials.py](../../../tests/planning/test_planning_polynomials.py), [test_runtime_native.py](../../../tests/runtime/test_runtime_native.py) | module.yaml |

## Warum es diese Implementierungen gibt

### `ReferenceLine.evaluate`

- **Warum:** Glatte Auswertung von Position, Kurswinkel und Krümmung zwischen Stützstellen.
- **Theorie:** [Hermite-interpolierte Referenzkurve](theory.md#hermite_reference_curve)
- **Annahmen:** Stützstellen mit konsistenten Ableitungen (die Konstruktoren liefern sie).
- **Quelle:** [de Boor (2001)](../references.md#deboor2001)

### `ReferenceLine.from_points`

- **Warum:** Straßengeometrie aus Geraden und Bögen mit stetiger Krümmungsableitung (Werling, Bemerkung 4).
- **Theorie:** [Glatte Krümmungsübergänge](theory.md#smooth_curvature_profile)
- **Annahmen:** Rampenbreite höchstens 90 % der angrenzenden Segmentlängen.
- **Quelle:** [Werling (2011)](../references.md#werling2011)

### `ReferenceLine.project`

- **Warum:** Lotfußpunkt $(s, d)$ eines beliebigen Punktes auf der kontinuierlichen Referenzkurve.
- **Theorie:** [Projektion auf die Referenzkurve](theory.md#curve_projection)
- **Annahmen:** Nächste Stützstelle liegt im richtigen Ast (Suchhinweis `hint` mit Fenster ±40 Stützstellen).
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Interpolation von [x, y, theta] zwischen Stützstellen + Sekantenverfahren, Newton-Verfeinerung

### `ReferenceLine.to_cartesian`

- **Warum:** Umrechnung des Bewegungszustands eines Punktes zwischen Weltkoordinaten $[x, y, \theta, \kappa, v, a]$ und Bahnkoordinaten $[s, \dot s, \ddot s, d, d', d'']$ ohne numerisches Differenzieren.
- **Theorie:** [Frenet-Transformation in geschlossener Form](theory.md#frenet_transformation)
- **Annahmen:** - Referenzkurve zweimal stetig differenzierbar mit stetigem $\kappa_r'$ (sonst springt $d''$).
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Bahnkoordinaten -> Weltkoordinaten in geschlossener Form, singularitätsfrei für v = 0

### `ReferenceLine.to_frenet`

- **Warum:** Umrechnung des Bewegungszustands eines Punktes zwischen Weltkoordinaten $[x, y, \theta, \kappa, v, a]$ und Bahnkoordinaten $[s, \dot s, \ddot s, d, d', d'']$ ohne numerisches Differenzieren.
- **Theorie:** [Frenet-Transformation in geschlossener Form](theory.md#frenet_transformation)
- **Annahmen:** - Referenzkurve zweimal stetig differenzierbar mit stetigem $\kappa_r'$ (sonst springt $d''$).
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Weltkoordinaten -> Bahnkoordinaten in geschlossener Form

### `curvature_profile`

- **Warum:** Straßengeometrie aus Geraden und Bögen mit stetiger Krümmungsableitung (Werling, Bemerkung 4).
- **Theorie:** [Glatte Krümmungsübergänge](theory.md#smooth_curvature_profile)
- **Annahmen:** Rampenbreite höchstens 90 % der angrenzenden Segmentlängen.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** Bemerkung 4 – stetige Krümmungsableitung der Referenzkurve
