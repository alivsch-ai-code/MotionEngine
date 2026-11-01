# Zweispurmodell (12 Zustände)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [vehicle_models](../index.md) · `vehicle_model/double_track` · klassische Registry

**Zweispurmodell mit 12 Zuständen – Wanken, Raddrehung, radindividuelle Lasten, Sturz und Rolllenken.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `vehicle_model` |
| Name | `double_track` |
| Versionen | legacy |
| Implementierung | [`vdsim.vehicle_models.double_track_model.DoubleTrackModel`](../../../../vdsim/vehicle_models/double_track_model.py#L23) |
| Schnittstelle | `vdsim.core.interfaces.VehicleModel` |
| Sprache | python |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `u` | `ControlInput` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `state` | `VehicleState` | – | – | – |

## Parameter

_Keine Parameter._

## Verfahren

[Zweispurmodell mit Wanken und Raddrehung](../theory.md#double_track), [Fahrwiderstände](../theory.md#driving_resistances)

## Annahmen

- Wanken um eine feste Rollachse
- Längslastverlagerung quasistatisch

## Einschränkungen

- Kein Nicken und keine Hubbewegung

## Validierung

- Wankgradient und Radlasten innerhalb 2–3 % der quasi-statischen Analyse

## Quellen

[Mitschke und Wallentowitz (2014)](../../references.md#mitschke2014), [Schramm et al. (2018)](../../references.md#schramm2018)

## Verwendung

Tests: [tests/knowledge/test_knowledge_collector.py](../../../../tests/knowledge/test_knowledge_collector.py), [tests/stabilization/test_stabilization_layers.py](../../../../tests/stabilization/test_stabilization_layers.py), [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py), [tests/test_simulation_and_reporting.py](../../../../tests/test_simulation_and_reporting.py), [tests/test_vehicle_models.py](../../../../tests/test_vehicle_models.py)

Konfigurationen: [configs/scenarios/acht_30.json](../../../../configs/scenarios/acht_30.json), [configs/scenarios/autobahn_spurhalteassistent.json](../../../../configs/scenarios/autobahn_spurhalteassistent.json), [configs/scenarios/beschleunigen_0_100_ev.json](../../../../configs/scenarios/beschleunigen_0_100_ev.json), [configs/scenarios/bremsen_100_abs.json](../../../../configs/scenarios/bremsen_100_abs.json), [configs/scenarios/bremsen_in_der_kurve.json](../../../../configs/scenarios/bremsen_in_der_kurve.json), [configs/scenarios/bremsen_split_mu.json](../../../../configs/scenarios/bremsen_split_mu.json), [configs/scenarios/frequenzgang_80.json](../../../../configs/scenarios/frequenzgang_80.json), [configs/scenarios/iso_ausweichtest_60.json](../../../../configs/scenarios/iso_ausweichtest_60.json), [configs/scenarios/iso_doppelspurwechsel_80.json](../../../../configs/scenarios/iso_doppelspurwechsel_80.json), [configs/scenarios/iso_doppelspurwechsel_mpc.json](../../../../configs/scenarios/iso_doppelspurwechsel_mpc.json), [configs/scenarios/kreisfahrt_r40.json](../../../../configs/scenarios/kreisfahrt_r40.json), [configs/scenarios/lenkwinkelsprung_80.json](../../../../configs/scenarios/lenkwinkelsprung_80.json), [configs/scenarios/notausweichen_60.json](../../../../configs/scenarios/notausweichen_60.json), [configs/scenarios/notbremsassistent_70.json](../../../../configs/scenarios/notbremsassistent_70.json), [configs/scenarios/rennstrecke_sportwagen.json](../../../../configs/scenarios/rennstrecke_sportwagen.json), [configs/scenarios/sinus_haltezeit_esp.json](../../../../configs/scenarios/sinus_haltezeit_esp.json), [configs/scenarios/slalom_45.json](../../../../configs/scenarios/slalom_45.json), [configs/scenarios/stadtverkehr.json](../../../../configs/scenarios/stadtverkehr.json), [configs/scenarios/testzyklus_kunde.json](../../../../configs/scenarios/testzyklus_kunde.json)
