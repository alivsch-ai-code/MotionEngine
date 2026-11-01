# Fahrzeugmodelle – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `model` | Szenario-Feld: bicycle_kinematic, bicycle_linear, bicycle_nonlinear, double_track, multibody | – | – |
| `vehicle.*, chassis.*` | Masse, Geometrie, Trägheiten, Federn, Dämpferkennlinien, Stabilisatoren, Rollzentren, Sturz, Rolllenken, Anti-Dive/-Squat | – | – |

## Parametersatz `WerlingParameters` (`vdsim.vehicle_models.werling_models`)

vehicle and axle tire parameters of the Werling design models (SI)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `m` | – | – | – | – | – |
| `J` | – | – | – | – | – |
| `lv` | – | – | – | – | – |
| `lh` | – | – | – | – | – |
| `R` | – | – | – | – | – |
| `max_steer` | – | – | – | – | – |
| `Av` | – | – | – | – | – |
| `Bv` | – | – | – | – | – |
| `Cv` | – | – | – | – | – |
| `Ah` | – | – | – | – | – |
| `Bh` | – | – | – | – | – |
| `Ch` | – | – | – | – | – |
| `mu` | – | – | 1 | – | – |

## Konfigurationsdateien, die Komponenten dieses Pakets verwenden

| Datei | Titel | Komponenten |
|---|---|---|
| [configs/scenarios/acht_30.json](../../../configs/scenarios/acht_30.json) | Acht 30 km/h | `vehicle_model/double_track` |
| [configs/scenarios/autobahn_acc.json](../../../configs/scenarios/autobahn_acc.json) | Autobahn mit ACC | `vehicle_model/bicycle_nonlinear` |
| [configs/scenarios/autobahn_spurhalteassistent.json](../../../configs/scenarios/autobahn_spurhalteassistent.json) | Autobahn mit Spurhalteassistent | `vehicle_model/double_track` |
| [configs/scenarios/beschleunigen_0_100_ev.json](../../../configs/scenarios/beschleunigen_0_100_ev.json) | Beschleunigung 0-100 km/h (E-Antrieb) | `vehicle_model/double_track` |
| [configs/scenarios/bremsen_100_abs.json](../../../configs/scenarios/bremsen_100_abs.json) | Vollbremsung 100 km/h (ABS) | `vehicle_model/double_track` |
| [configs/scenarios/bremsen_in_der_kurve.json](../../../configs/scenarios/bremsen_in_der_kurve.json) | Bremsen in der Kurve | `vehicle_model/double_track` |
| [configs/scenarios/bremsen_split_mu.json](../../../configs/scenarios/bremsen_split_mu.json) | Bremsen auf Split-µ | `vehicle_model/double_track` |
| [configs/scenarios/frequenzgang_80.json](../../../configs/scenarios/frequenzgang_80.json) | Frequenzgang 80 km/h | `vehicle_model/double_track` |
| [configs/scenarios/iso_ausweichtest_60.json](../../../configs/scenarios/iso_ausweichtest_60.json) | ISO-Ausweichtest 60 km/h | `vehicle_model/double_track` |
| [configs/scenarios/iso_doppelspurwechsel_80.json](../../../configs/scenarios/iso_doppelspurwechsel_80.json) | ISO-Doppelspurwechsel 80 km/h | `vehicle_model/double_track` |
| [configs/scenarios/iso_doppelspurwechsel_mpc.json](../../../configs/scenarios/iso_doppelspurwechsel_mpc.json) | ISO-Doppelspurwechsel 80 km/h (MPC) | `vehicle_model/double_track` |
| [configs/scenarios/komfort_strasse_klasse_c.json](../../../configs/scenarios/komfort_strasse_klasse_c.json) | Komfort Straße Klasse C | `vehicle_model/multibody` |
| [configs/scenarios/kreisfahrt_r40.json](../../../configs/scenarios/kreisfahrt_r40.json) | Kreisfahrt R = 40 m | `vehicle_model/double_track` |
| [configs/scenarios/lenkwinkelsprung_80.json](../../../configs/scenarios/lenkwinkelsprung_80.json) | Lenkwinkelsprung 80 km/h | `vehicle_model/double_track` |
| [configs/scenarios/notausweichen_60.json](../../../configs/scenarios/notausweichen_60.json) | Notausweichen 60 km/h | `vehicle_model/double_track` |
| [configs/scenarios/notbremsassistent_70.json](../../../configs/scenarios/notbremsassistent_70.json) | Notbremsassistent 70 km/h | `vehicle_model/double_track` |
| [configs/scenarios/rennstrecke_sportwagen.json](../../../configs/scenarios/rennstrecke_sportwagen.json) | Rennstrecke Sportwagen | `vehicle_model/double_track` |
| [configs/scenarios/sinus_haltezeit_esp.json](../../../configs/scenarios/sinus_haltezeit_esp.json) | Sinus mit Haltezeit (ESP) | `vehicle_model/double_track` |
| [configs/scenarios/slalom_45.json](../../../configs/scenarios/slalom_45.json) | Slalom 45 km/h | `vehicle_model/double_track` |
| [configs/scenarios/spurwechsel_latenzkette.json](../../../configs/scenarios/spurwechsel_latenzkette.json) | Spurwechsel mit Latenzkette | `vehicle_model/bicycle_kinematic` |
| [configs/scenarios/stadtverkehr.json](../../../configs/scenarios/stadtverkehr.json) | Stadtverkehr | `vehicle_model/double_track` |
| [configs/scenarios/testzyklus_kunde.json](../../../configs/scenarios/testzyklus_kunde.json) | Kundenspezifischer Testzyklus | `vehicle_model/double_track` |
| [configs/stabilization/vehicle_layers_default.json](../../../configs/stabilization/vehicle_layers_default.json) | vehicle_layers_default | `vehicle_model/werling_desm` |
