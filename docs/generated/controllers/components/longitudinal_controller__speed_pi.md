# Geschwindigkeitsregler (PI)

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `longitudinal_controller/speed_pi` · klassische Registry

**PI-Geschwindigkeitsregler mit Vorsteuerung aus dem Geschwindigkeitsprofil und Anti-Windup.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `longitudinal_controller` |
| Name | `speed_pi` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.speed_controller.SpeedController`](../../../../vdsim/controllers/speed_controller.py#L10) |
| Schnittstelle | `vdsim.core.interfaces.LongitudinalController` |
| Sprache | python |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `env` | `Environment` | – | – | – |
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `acceleration` | `float` | – | Beschleunigungsanforderung in m/s² | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `kp` | – | 1/s | 1.2 | – | – |
| `ki` | – | 1/s² | 0.3 | – | – |
| `a_max` | – | m/s² | 4 | – | – |
| `a_min` | – | m/s² | -9 | – | – |
| `preview` | Vorausschauzeit der Vorsteuerung | s | 0.6 | – | – |

## Verfahren

[Geschwindigkeitsregelung (PI mit Vorsteuerung)](../theory.md#speed_control)

## Verwendung

Tests: [tests/test_controllers_and_systems.py](../../../../tests/test_controllers_and_systems.py)

Konfigurationen: [configs/scenarios/acht_30.json](../../../../configs/scenarios/acht_30.json), [configs/scenarios/autobahn_spurhalteassistent.json](../../../../configs/scenarios/autobahn_spurhalteassistent.json), [configs/scenarios/beschleunigen_0_100_ev.json](../../../../configs/scenarios/beschleunigen_0_100_ev.json), [configs/scenarios/bremsen_100_abs.json](../../../../configs/scenarios/bremsen_100_abs.json), [configs/scenarios/bremsen_in_der_kurve.json](../../../../configs/scenarios/bremsen_in_der_kurve.json), [configs/scenarios/bremsen_split_mu.json](../../../../configs/scenarios/bremsen_split_mu.json), [configs/scenarios/frequenzgang_80.json](../../../../configs/scenarios/frequenzgang_80.json), [configs/scenarios/iso_ausweichtest_60.json](../../../../configs/scenarios/iso_ausweichtest_60.json), [configs/scenarios/iso_doppelspurwechsel_80.json](../../../../configs/scenarios/iso_doppelspurwechsel_80.json), [configs/scenarios/iso_doppelspurwechsel_mpc.json](../../../../configs/scenarios/iso_doppelspurwechsel_mpc.json), [configs/scenarios/komfort_strasse_klasse_c.json](../../../../configs/scenarios/komfort_strasse_klasse_c.json), [configs/scenarios/kreisfahrt_r40.json](../../../../configs/scenarios/kreisfahrt_r40.json), [configs/scenarios/lenkwinkelsprung_80.json](../../../../configs/scenarios/lenkwinkelsprung_80.json), [configs/scenarios/notausweichen_60.json](../../../../configs/scenarios/notausweichen_60.json), [configs/scenarios/notbremsassistent_70.json](../../../../configs/scenarios/notbremsassistent_70.json), [configs/scenarios/rennstrecke_sportwagen.json](../../../../configs/scenarios/rennstrecke_sportwagen.json), [configs/scenarios/sinus_haltezeit_esp.json](../../../../configs/scenarios/sinus_haltezeit_esp.json), [configs/scenarios/slalom_45.json](../../../../configs/scenarios/slalom_45.json), [configs/scenarios/spurwechsel_latenzkette.json](../../../../configs/scenarios/spurwechsel_latenzkette.json), [configs/scenarios/stadtverkehr.json](../../../../configs/scenarios/stadtverkehr.json), [configs/scenarios/testzyklus_kunde.json](../../../../configs/scenarios/testzyklus_kunde.json)
