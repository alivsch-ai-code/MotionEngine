# Stanley

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Paket [controllers](../index.md) · `lateral_controller/stanley` · klassische Registry

**Stanley-Bahnregler mit Kurswinkelfehler, Querablage an der Vorderachse, Krümmungsvorsteuerung und Gierdämpfung.**

## Steckbrief

| Eigenschaft | Wert |
|---|---|
| Art (KIND) | `lateral_controller` |
| Name | `stanley` |
| Versionen | legacy |
| Implementierung | [`vdsim.controllers.stanley_controller.StanleyController`](../../../../vdsim/controllers/stanley_controller.py#L17) |
| Schnittstelle | `vdsim.core.interfaces.LateralController` |
| Sprache | python |

## Ports

Eingänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `reference` | `Trajectory` | – | – | – |
| `state` | `VehicleState` | – | – | – |

Ausgänge:

| Port | Typ | Einheit | Beschreibung | Merkmale |
|---|---|---|---|---|
| `steer` | `float` | – | Radlenkwinkel-Anforderung vorne in rad | – |

## Parameter

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `gain` | Verstärkung der Querablage k | - | 1.2 | – | – |
| `softening` | Softening-Geschwindigkeit im Nenner | m/s | 2 | – | – |
| `yaw_damping` | Gewicht der Gierratenabweichung | s | 0.05 | – | – |
| `feedforward` | Krümmungsvorsteuerung ein/aus | – | True | – | – |

## Verfahren

[Stanley-Bahnregler](../theory.md#stanley_controller)

## Annahmen

- Vorwärtsfahrt
- Referenzbahn mit Krümmung

## Einschränkungen

- Bei sehr kleiner Geschwindigkeit begrenzt nur die Softening-Konstante die Verstärkung

## Quellen

[Hoffmann et al. (2007)](../../references.md#hoffmann2007), [Snider (2009)](../../references.md#snider2009), [Thrun et al. (2006)](../../references.md#thrun2006)

## Verwendung

Tests: [tests/knowledge/test_knowledge_collector.py](../../../../tests/knowledge/test_knowledge_collector.py)

Konfigurationen: [configs/scenarios/acht_30.json](../../../../configs/scenarios/acht_30.json), [configs/scenarios/autobahn_acc.json](../../../../configs/scenarios/autobahn_acc.json), [configs/scenarios/beschleunigen_0_100_ev.json](../../../../configs/scenarios/beschleunigen_0_100_ev.json), [configs/scenarios/bremsen_100_abs.json](../../../../configs/scenarios/bremsen_100_abs.json), [configs/scenarios/bremsen_in_der_kurve.json](../../../../configs/scenarios/bremsen_in_der_kurve.json), [configs/scenarios/bremsen_split_mu.json](../../../../configs/scenarios/bremsen_split_mu.json), [configs/scenarios/frequenzgang_80.json](../../../../configs/scenarios/frequenzgang_80.json), [configs/scenarios/iso_ausweichtest_60.json](../../../../configs/scenarios/iso_ausweichtest_60.json), [configs/scenarios/iso_doppelspurwechsel_80.json](../../../../configs/scenarios/iso_doppelspurwechsel_80.json), [configs/scenarios/komfort_strasse_klasse_c.json](../../../../configs/scenarios/komfort_strasse_klasse_c.json), [configs/scenarios/kreisfahrt_r40.json](../../../../configs/scenarios/kreisfahrt_r40.json), [configs/scenarios/lenkwinkelsprung_80.json](../../../../configs/scenarios/lenkwinkelsprung_80.json), [configs/scenarios/notausweichen_60.json](../../../../configs/scenarios/notausweichen_60.json), [configs/scenarios/notbremsassistent_70.json](../../../../configs/scenarios/notbremsassistent_70.json), [configs/scenarios/rennstrecke_sportwagen.json](../../../../configs/scenarios/rennstrecke_sportwagen.json), [configs/scenarios/sinus_haltezeit_esp.json](../../../../configs/scenarios/sinus_haltezeit_esp.json), [configs/scenarios/slalom_45.json](../../../../configs/scenarios/slalom_45.json), [configs/scenarios/testzyklus_kunde.json](../../../../configs/scenarios/testzyklus_kunde.json)
