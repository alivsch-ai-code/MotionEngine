# Fahrzeugmodelle

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.vehicle_models` · Quellcode: [vdsim/vehicle_models/](../../../vdsim/vehicle_models) · Paketdoku: [vdsim/vehicle_models/docs/](../../../vdsim/vehicle_models/docs)

## Übersicht

**Bewegungsgleichungen vom kinematischen Einspurmodell bis zum Mehrkörpermodell mit 24 Zuständen.**

Je nach Fragestellung braucht man unterschiedlich detaillierte Modelle: Bahnplanung und Latenzstudien
kommen mit Kinematik aus, Reglerauslegung mit dem linearen Einspurmodell, Grenzbereich und
Fahrdynamikregelsysteme brauchen Radlastverlagerung und Raddrehung, Komfortbewertung braucht
Vertikaldynamik. Alle Modelle implementieren `vdsim.core.interfaces.VehicleModel` und sind über die
Registry (`vehicle_model`) austauschbar.

Paket-Docstring:

```text
Vehicle models: single-track (kinematic, linear, nonlinear), double-track, multibody.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 6 |
| Komponenten | 7 |
| Verfahren/Konzepte | 10 |
| @trace-Einträge | 15 |
| Tests | 8 |
| Beispiele | 1 |

## Architektur

- `bicycle_model.py`: `KinematicBicycleModel` (4 Zustände), `LinearBicycleModel` (6, Zustandsraum A, B),
  `NonlinearBicycleModel` (6, Reifenmodell je Achse, Längslastverlagerung, Reibellipse).
- `double_track_model.DoubleTrackModel`: 12 Zustände mit Wanken und vier Raddrehzahlen.
- `multibody_model.MultibodyModel`: 24 Zustände mit Hub, Wanken, Nicken, vier ungefederten Massen und Raddrehung.
- `common.py`: Luftwiderstand, Rollwiderstand, Längskraft aus Radmomenten, Achs-Schräglaufsteifigkeit.
Jedes Modell liefert `derivatives(t, x, u, env, with_outputs)` und `vehicle_state()`; Modelle mit Raddynamik
zusätzlich `stable_dt()` für die Teilschrittwahl des Simulators.

### Datenfluss

`ControlInput` (Lenkwinkel vorn/hinten, Antriebs- und Bremsmoment je Rad, aktives Wankmoment, aktive
Dämpferkräfte) und `Environment` (Reibwert je Aufstandspunkt, Fahrbahnhöhe, Wind) → Zustandsableitung
und Ausgangsgrößen (Kräfte, Schlupf, Radlasten) → `VehicleState`.

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.vehicle_models`](../../../vdsim/vehicle_models/__init__.py) | 24 | – | Vehicle models: single-track (kinematic, linear, nonlinear), double-track, multibody. |
| [`vdsim.vehicle_models.bicycle_model`](../../../vdsim/vehicle_models/bicycle_model.py) | 182 | _BicycleBase, KinematicBicycleModel, LinearBicycleModel, NonlinearBicycleModel | Single-track (bicycle) models. |
| [`vdsim.vehicle_models.common`](../../../vdsim/vehicle_models/common.py) | 27 | – | Helpers shared by the vehicle models: resistances, longitudinal force estimate, axle stiffness. |
| [`vdsim.vehicle_models.double_track_model`](../../../vdsim/vehicle_models/double_track_model.py) | 155 | DoubleTrackModel | Double-track model with roll dynamics and wheel rotation (12 states). |
| [`vdsim.vehicle_models.multibody_model`](../../../vdsim/vehicle_models/multibody_model.py) | 185 | MultibodyModel | Multibody full-vehicle model (24 states): sprung body with heave, roll and pitch, four unsprung masses with vertical motion, four wheel spins and the planar motion. |
| [`vdsim.vehicle_models.werling_models`](../../../vdsim/vehicle_models/werling_models.py) | 322 | WerlingParameters, _WerlingBase, WerlingKinematicModel, WerlingDynamicModel | Design models of Werling (2011), chapter 4, as plant models of the vdsim simulator. |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [framework](../framework/index.md), [simulation](../simulation/index.md), [tire_models](../tire_models/index.md)
- genutzt von: [analysis](../analysis/index.md), [controllers](../controllers/index.md), [core](../core/index.md), [gui](../gui/index.md), [knowledge](../knowledge/index.md), [powertrain](../powertrain/index.md), [stabilization](../stabilization/index.md)
- externe Bibliotheken: `dataclasses`, `math`, `numpy`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Quasistatische Lastverlagerung aus geschätzten Beschleunigungen (a_x aus Momentenanforderung, a_y = v r) | vermeidet algebraische Schleifen zwischen Reifenkräften und Radlasten | iterative Lösung je Zeitschritt (teurer), zusätzliche Zustände mit Filter |
| Mindestgeschwindigkeit im Schlupfnenner (slip_speed_floor = 3 m/s) und tanh-Glättung des Bremsmoments | verhindert die Singularität bei Stillstand und begrenzt die Steifigkeit der Raddrehdynamik | Schlupfmodell mit Relaxationslänge (Ausbaustufe) |
| Achs-Schräglaufsteifigkeit des linearen Modells numerisch aus dem eingestellten Reifenmodell | lineares und nichtlineares Modell stimmen im linearen Bereich exakt überein | – |

## Implementierung

- Alle Kräfte werden radindividuell vektorisiert (numpy-Arrays der Länge 4) berechnet.
- Der Reibwert je Rad kommt aus `env.mu_at(x, y)` an der Aufstandspunktposition (Split-µ, Reibwertinseln).
- `with_outputs=True` liefert zusätzlich alle Zwischengrößen für Logging und KPIs, ohne einen zweiten Rechenweg.

### Komponenten

| Komponente | Bezeichnung | Version | Kurzbeschreibung |
|---|---|---|---|
| [`vehicle_model/bicycle_kinematic`](components/vehicle_model__bicycle_kinematic.md) | Einspurmodell kinematisch | legacy | Kinematisches Einspurmodell ohne Reifenschlupf mit Vorder- und Hinterachslenkung. |
| [`vehicle_model/bicycle_linear`](components/vehicle_model__bicycle_linear.md) | Einspurmodell linear | legacy | Lineares Einspurmodell (6 Zustände) mit Zustandsraumdarstellung für Analyse und Reglerentwurf. |
| [`vehicle_model/bicycle_nonlinear`](components/vehicle_model__bicycle_nonlinear.md) | Einspurmodell nichtlinear | legacy | Nichtlineares Einspurmodell mit Reifenmodell je Achse, Längslastverlagerung und Reibellipse. |
| [`vehicle_model/double_track`](components/vehicle_model__double_track.md) | Zweispurmodell (12 Zustände) | legacy | Zweispurmodell mit 12 Zuständen – Wanken, Raddrehung, radindividuelle Lasten, Sturz und Rolllenken. |
| [`vehicle_model/multibody`](components/vehicle_model__multibody.md) | Mehrkörpermodell (24 Zustände) | legacy | Mehrkörpermodell mit 24 Zuständen – Aufbau mit Hub, Wanken, Nicken, vier ungefederte Massen, Raddrehung, Fahrbahnanregung. |
| [`vehicle_model/werling_desm`](components/vehicle_model__werling_desm.md) | Dynamisches Einspurmodell, isotroper Reifen (Werling Modell 4) | legacy | – |
| [`vehicle_model/werling_kesm`](components/vehicle_model__werling_kesm.md) | Erweitertes kinematisches Einspurmodell (Werling Modell 1) | legacy | – |

### Verfahren und Konzepte

- [Desm](../README.md#konzepte-ohne-dokumentation) (undokumentiert)
- [Zweispurmodell mit Wanken und Raddrehung](theory.md#double_track)
- [Fahrwiderstände](theory.md#driving_resistances)
- [Erweitertes kinematisches Einspurmodell](../stabilization/theory.md#kesm)
- [Kinematisches Einspurmodell](theory.md#kinematic_bicycle)
- [Lineares Einspurmodell](theory.md#linear_bicycle)
- [Mehrkörpermodell mit Vertikaldynamik](theory.md#multibody)
- [Nichtlineares Einspurmodell](theory.md#nonlinear_bicycle)
- [Stabilitätsbegrenzte Teilschritte (stable_dt)](../simulation/theory.md#stable_substeps)
- [Eigenlenkgradient und charakteristische Geschwindigkeit](../analysis/theory.md#understeer_gradient)

## Erweiterungspunkte

- Neues Modell als Unterklasse von VehicleModel mit initial_state, derivatives, vehicle_state, optional stable_dt; "@register('vehicle_model', name)" und Eintrag in MODEL_LABELS

## Verwandte Module

[tire_models](../tire_models/index.md), [simulation](../simulation/index.md), [analysis](../analysis/index.md), [controllers](../controllers/index.md), [powertrain](../powertrain/index.md)

## Hauptquellen

[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Pacejka (2012)](../references.md#pacejka2012), [Rajamani (2012)](../references.md#rajamani2012), [Schramm et al. (2018)](../references.md#schramm2018)
