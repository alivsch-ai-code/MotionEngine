# Kern – Konventionen, Parameter, Schnittstellen, Registry – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`VehicleParameters.static_axle_loads`](../../../vdsim/core/parameters.py#L54) | – | [Koordinatensysteme, Vorzeichen und Schlupfdefinition](theory.md#iso8855_conventions) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | [conftest.py](../../../tests/conftest.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`param`](../../../vdsim/core/parameters.py#L17) | – | [Parameterschema und klassische Registry](theory.md#parameter_schema) | – | [conftest.py](../../../tests/conftest.py), [test_planning_plugins.py](../../../tests/planning/test_planning_plugins.py), [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`register`](../../../vdsim/core/registry.py#L26) | – | [Parameterschema und klassische Registry](theory.md#parameter_schema) | – | [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py), [test_trajectory.py](../../../tests/test_trajectory.py), [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |

## Warum es diese Implementierungen gibt

### `VehicleParameters.static_axle_loads`

- **Warum:** Alle Modelle, Regler und Auswertungen verwenden dieselben Achsen, Vorzeichen und Größendefinitionen.
- **Theorie:** [Koordinatensysteme, Vorzeichen und Schlupfdefinition](theory.md#iso8855_conventions)
- **Annahmen:** - Starres, ebenes Fahrbahnkoordinatensystem.
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `param`

- **Warum:** Parameter und Plugins sollen sich selbst beschreiben, damit GUI-Masken, JSON-Dateien, Berichte und diese Dokumentation automatisch entstehen.
- **Theorie:** [Parameterschema und klassische Registry](theory.md#parameter_schema)
- **Annahmen:** Plugins werden beim Import registriert; die eingebauten Module werden beim ersten `get()` importiert.
- **Quelle:** –

### `register`

- **Warum:** Parameter und Plugins sollen sich selbst beschreiben, damit GUI-Masken, JSON-Dateien, Berichte und diese Dokumentation automatisch entstehen.
- **Theorie:** [Parameterschema und klassische Registry](theory.md#parameter_schema)
- **Annahmen:** Plugins werden beim Import registriert; die eingebauten Module werden beim ersten `get()` importiert.
- **Quelle:** –
