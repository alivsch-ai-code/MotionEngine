# Fahrzeugmodelle – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`KinematicBicycleModel.derivatives`](../../../vdsim/vehicle_models/bicycle_model.py#L42) | Abschn. 2 | [Kinematisches Einspurmodell](theory.md#kinematic_bicycle) | [Rajamani (2012)](../references.md#rajamani2012) | [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`LinearBicycleModel.state_space`](../../../vdsim/vehicle_models/bicycle_model.py#L77) | Abschn. 2 | [Lineares Einspurmodell](theory.md#linear_bicycle) | [Rajamani (2012)](../references.md#rajamani2012) | [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`LinearBicycleModel.understeer_gradient`](../../../vdsim/vehicle_models/bicycle_model.py#L87) | – | [Eigenlenkgradient und charakteristische Geschwindigkeit](../analysis/theory.md#understeer_gradient) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`NonlinearBicycleModel.derivatives`](../../../vdsim/vehicle_models/bicycle_model.py#L127) | – | [Nichtlineares Einspurmodell](theory.md#nonlinear_bicycle) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`aero_drag`](../../../vdsim/vehicle_models/common.py#L8) | – | [Fahrwiderstände](theory.md#driving_resistances) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | – | module.yaml |
| [`axle_cornering_stiffness`](../../../vdsim/vehicle_models/common.py#L23) | – | [Lineares Einspurmodell](theory.md#linear_bicycle) | – | – | module.yaml |
| [`rolling_resistance`](../../../vdsim/vehicle_models/common.py#L13) | – | [Fahrwiderstände](theory.md#driving_resistances) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | – | module.yaml |
| [`DoubleTrackModel.derivatives`](../../../vdsim/vehicle_models/double_track_model.py#L77) | – | [Zweispurmodell mit Wanken und Raddrehung](theory.md#double_track) | [Schramm et al. (2018)](../references.md#schramm2018) | [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`DoubleTrackModel.stable_dt`](../../../vdsim/vehicle_models/double_track_model.py#L65) | – | [Stabilitätsbegrenzte Teilschritte (stable_dt)](../simulation/theory.md#stable_substeps) | [Hairer und Wanner (1996)](../references.md#hairer1996) | – | module.yaml |
| [`MultibodyModel.derivatives`](../../../vdsim/vehicle_models/multibody_model.py#L89) | – | [Mehrkörpermodell mit Vertikaldynamik](theory.md#multibody) | [Schramm et al. (2018)](../references.md#schramm2018) | [test_vehicle_models.py](../../../tests/test_vehicle_models.py) | module.yaml |
| [`MultibodyModel.stable_dt`](../../../vdsim/vehicle_models/multibody_model.py#L78) | – | [Stabilitätsbegrenzte Teilschritte (stable_dt)](../simulation/theory.md#stable_substeps) | [Hairer und Wanner (1996)](../references.md#hairer1996) | – | module.yaml |
| [`desm_forces`](../../../vdsim/vehicle_models/werling_models.py#L120) | Abschn. 4.3.1 (4.39) | [Desm](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py), [test_stabilization_kinematic.py](../../../tests/stabilization/test_stabilization_kinematic.py), [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py) | Code (@trace) |
| [`slip_angles`](../../../vdsim/vehicle_models/werling_models.py#L108) | Abschn. 4.3.2 (4.44), (4.45) | [Desm](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py), [test_stabilization_kinematic.py](../../../tests/stabilization/test_stabilization_kinematic.py), [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py) | Code (@trace) |
| [`werling_model1`](../../../vdsim/vehicle_models/werling_models.py#L156) | Abschn. 4.2.1 (4.2) | [Erweitertes kinematisches Einspurmodell](../stabilization/theory.md#kesm) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py), [test_stabilization_kinematic.py](../../../tests/stabilization/test_stabilization_kinematic.py), [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py) | Code (@trace) |
| [`werling_model4`](../../../vdsim/vehicle_models/werling_models.py#L141) | Abschn. 4.3.1 (4.39) | [Desm](../README.md#konzepte-ohne-dokumentation) (undokumentiert) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_dynamic.py](../../../tests/stabilization/test_stabilization_dynamic.py), [test_stabilization_kinematic.py](../../../tests/stabilization/test_stabilization_kinematic.py), [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py) | Code (@trace) |

## Warum es diese Implementierungen gibt

### `KinematicBicycleModel.derivatives`

- **Warum:** Beschreibt die Fahrzeugbewegung allein aus der Lenkgeometrie, ohne Reifenschlupf.
- **Theorie:** [Kinematisches Einspurmodell](theory.md#kinematic_bicycle)
- **Annahmen:** - Kein Schräglauf, starre Räder, ebene Fahrbahn.
- **Quelle:** [Rajamani (2012)](../references.md#rajamani2012)

### `LinearBicycleModel.state_space`

- **Warum:** Lineares Modell der Quer- und Gierdynamik für Reglerentwurf, Frequenzgang und Stabilitätsanalyse.
- **Theorie:** [Lineares Einspurmodell](theory.md#linear_bicycle)
- **Annahmen:** - Konstante Längsgeschwindigkeit für die Analyse, kleine Winkel, keine Wank- und Nickbewegung.
- **Quelle:** [Rajamani (2012)](../references.md#rajamani2012)

### `LinearBicycleModel.understeer_gradient`

- **Warum:** Kennzahl für das stationäre Eigenlenkverhalten: Wie viel zusätzlicher Lenkwinkel ist pro Querbeschleunigung nötig?
- **Theorie:** [Eigenlenkgradient und charakteristische Geschwindigkeit](../analysis/theory.md#understeer_gradient)
- **Annahmen:** Lineare Reifen, statische Achslasten, kleine Winkel.
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `NonlinearBicycleModel.derivatives`

- **Warum:** Einspurmodell für den Grenzbereich ohne Wanken: nichtlineare Reifen je Achse, Längslastverlagerung und Kopplung von Längs- und Seitenkraft.
- **Theorie:** [Nichtlineares Einspurmodell](theory.md#nonlinear_bicycle)
- **Annahmen:** - $a_{x,est}$ aus Momentenanforderung minus Fahrwiderständen, begrenzt auf $\pm 1.5 g$ (keine algebraische Schleife).
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `aero_drag`

- **Warum:** Luft- und Rollwiderstand für alle Modelle und für die Vorsteuerung der Längsregelung.
- **Theorie:** [Fahrwiderstände](theory.md#driving_resistances)
- **Annahmen:** Gegenwind $v_W > 0$; konstanter Rollwiderstandsbeiwert; Luftdichte 1,204 kg/m³ (20 °C).
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `axle_cornering_stiffness`

- **Warum:** Lineares Modell der Quer- und Gierdynamik für Reglerentwurf, Frequenzgang und Stabilitätsanalyse.
- **Theorie:** [Lineares Einspurmodell](theory.md#linear_bicycle)
- **Annahmen:** - Konstante Längsgeschwindigkeit für die Analyse, kleine Winkel, keine Wank- und Nickbewegung.
- **Quelle:** –

### `rolling_resistance`

- **Warum:** Luft- und Rollwiderstand für alle Modelle und für die Vorsteuerung der Längsregelung.
- **Theorie:** [Fahrwiderstände](theory.md#driving_resistances)
- **Annahmen:** Gegenwind $v_W > 0$; konstanter Rollwiderstandsbeiwert; Luftdichte 1,204 kg/m³ (20 °C).
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `DoubleTrackModel.derivatives`

- **Warum:** Radindividuelles Modell für Grenzbereich und Fahrdynamikregelsysteme (ABS, ASR, ESP, Torque Vectoring, Split-µ) mit Wankdynamik, Raddrehzahlen, Sturz und Rolllenken.
- **Theorie:** [Zweispurmodell mit Wanken und Raddrehung](theory.md#double_track)
- **Annahmen:** - Rollachse fest, gerade Verbindung der Rollzentren; kein Nicken, keine Hubbewegung.
- **Quelle:** [Schramm et al. (2018)](../references.md#schramm2018)

### `DoubleTrackModel.stable_dt`

- **Warum:** Wahl der Modellschrittweite so, dass der explizite RK4 bei der steifen Raddrehdynamik stabil bleibt, ohne bei Autobahntempo unnötig klein zu werden.
- **Theorie:** [Stabilitätsbegrenzte Teilschritte (stable_dt)](../simulation/theory.md#stable_substeps)
- **Annahmen:** - Maximale Längssteifigkeit bei doppelter statischer Radlast: $C_{\kappa,max} = 2 C_\kappa F_{z,stat,max}/F_{z0}$.
- **Quelle:** [Hairer und Wanner (1996)](../references.md#hairer1996)

### `MultibodyModel.derivatives`

- **Warum:** Gesamtfahrzeugmodell für Komfort (ISO 2631), Radlastschwankungen, aktives Fahrwerk und Fahrbahnanregung.
- **Theorie:** [Mehrkörpermodell mit Vertikaldynamik](theory.md#multibody)
- **Annahmen:** - Kleine Aufbauwinkel, lineare Federn und Reifen, Dämpfer als Kennlinien.
- **Quelle:** [Schramm et al. (2018)](../references.md#schramm2018)

### `MultibodyModel.stable_dt`

- **Warum:** Wahl der Modellschrittweite so, dass der explizite RK4 bei der steifen Raddrehdynamik stabil bleibt, ohne bei Autobahntempo unnötig klein zu werden.
- **Theorie:** [Stabilitätsbegrenzte Teilschritte (stable_dt)](../simulation/theory.md#stable_substeps)
- **Annahmen:** - Maximale Längssteifigkeit bei doppelter statischer Radlast: $C_{\kappa,max} = 2 C_\kappa F_{z,stat,max}/F_{z0}$.
- **Quelle:** [Hairer und Wanner (1996)](../references.md#hairer1996)

### `werling_model1`

- **Warum:** Entwurfsmodell für langsame Fahrt (vorwärts, rückwärts, Stand), das neben der Lenkwinkelrate die Reifenlängskräfte als Eingang enthält, damit keine unterlagerte Geschwindigkeitsregelung nötig ist.
- **Theorie:** [Erweitertes kinematisches Einspurmodell](../stabilization/theory.md#kesm)
- **Annahmen:** Keine Schräglaufwinkel (geringe Querbeschleunigung), ebene Fahrbahn, schnelle unterlagerte Antriebs-/Bremsregelung.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
