# Regler, Fahrerassistenz und Fahrwerksregelsysteme – Beispiele

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · **Beispiele** · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## [run_scenario.py](../../../run_scenario.py)

Command line: run scenarios, print KPIs, export results and reports.

python run_scenario.py --list
python run_scenario.py iso_doppelspurwechsel_80 --plot
python run_scenario.py kreisfahrt_r40 bremsen_100_abs --report bericht.pdf --summary bericht.md
python run_scenario.py configs/scenarios/slalom_60.json --csv slalom.csv
python run_scenario.py --all

Ausführen: `python run_scenario.py`

## Szenarien und Konfigurationen

| Datei | Titel | Beschreibung |
|---|---|---|
| [configs/scenarios/acht_30.json](../../../configs/scenarios/acht_30.json) | Acht 30 km/h | Liegende Acht R = 20 m |
| [configs/scenarios/autobahn_acc.json](../../../configs/scenarios/autobahn_acc.json) | Autobahn mit ACC | Vorausfahrendes Fahrzeug bremst von 100 auf 60 km/h |
| [configs/scenarios/autobahn_spurhalteassistent.json](../../../configs/scenarios/autobahn_spurhalteassistent.json) | Autobahn mit Spurhalteassistent | Abgelenkter Fahrer driftet, LKA korrigiert |
| [configs/scenarios/beschleunigen_0_100_ev.json](../../../configs/scenarios/beschleunigen_0_100_ev.json) | Beschleunigung 0-100 km/h (E-Antrieb) | Elektro-Limousine Allrad |
| [configs/scenarios/bremsen_100_abs.json](../../../configs/scenarios/bremsen_100_abs.json) | Vollbremsung 100 km/h (ABS) | Bremsweg, MFDD |
| [configs/scenarios/bremsen_in_der_kurve.json](../../../configs/scenarios/bremsen_in_der_kurve.json) | Bremsen in der Kurve | ISO 7975, R = 100 m, 80 km/h, -4 m/s² |
| [configs/scenarios/bremsen_split_mu.json](../../../configs/scenarios/bremsen_split_mu.json) | Bremsen auf Split-µ | Linke Fahrzeugseite auf Eis (µ 0,2), ABS + ESP |
| [configs/scenarios/frequenzgang_80.json](../../../configs/scenarios/frequenzgang_80.json) | Frequenzgang 80 km/h | Lenk-Sweep 0,1-3 Hz |
| [configs/scenarios/iso_ausweichtest_60.json](../../../configs/scenarios/iso_ausweichtest_60.json) | ISO-Ausweichtest 60 km/h | ISO 3888-2 (Elchtest) |
| [configs/scenarios/iso_doppelspurwechsel_80.json](../../../configs/scenarios/iso_doppelspurwechsel_80.json) | ISO-Doppelspurwechsel 80 km/h | ISO 3888-1, Zweispurmodell, Stanley-Regler |
| [configs/scenarios/iso_doppelspurwechsel_mpc.json](../../../configs/scenarios/iso_doppelspurwechsel_mpc.json) | ISO-Doppelspurwechsel 80 km/h (MPC) | ISO 3888-1 mit modellprädiktiver Querregelung |
| [configs/scenarios/komfort_strasse_klasse_c.json](../../../configs/scenarios/komfort_strasse_klasse_c.json) | Komfort Straße Klasse C | Mehrkörpermodell, ISO-8608-Klasse C, 80 km/h |
| [configs/scenarios/kreisfahrt_r40.json](../../../configs/scenarios/kreisfahrt_r40.json) | Kreisfahrt R = 40 m | ISO 4138, steigende Geschwindigkeit -> Eigenlenkgradient |
| [configs/scenarios/lenkwinkelsprung_80.json](../../../configs/scenarios/lenkwinkelsprung_80.json) | Lenkwinkelsprung 80 km/h | ISO 7401, Ansprechzeiten und Überschwingen |
| [configs/scenarios/notausweichen_60.json](../../../configs/scenarios/notausweichen_60.json) | Notausweichen 60 km/h | Ausweichen um ein Hindernis mit Rückkehr |
| [configs/scenarios/notbremsassistent_70.json](../../../configs/scenarios/notbremsassistent_70.json) | Notbremsassistent 70 km/h | Stehendes Hindernis, AEB |
| [configs/scenarios/rennstrecke_sportwagen.json](../../../configs/scenarios/rennstrecke_sportwagen.json) | Rennstrecke Sportwagen | Ideallinie, GGV-Profil |
| [configs/scenarios/sinus_haltezeit_esp.json](../../../configs/scenarios/sinus_haltezeit_esp.json) | Sinus mit Haltezeit (ESP) | FMVSS 126, Sportwagen mit ESP |
| [configs/scenarios/slalom_45.json](../../../configs/scenarios/slalom_45.json) | Slalom 45 km/h | 18 m Pylonenabstand, 1,3 m Versatz |
| [configs/scenarios/spurwechsel_latenzkette.json](../../../configs/scenarios/spurwechsel_latenzkette.json) | Spurwechsel mit Latenzkette | Gateway 40 ms, Aktuator 5 ms, Odometrie 5 ms; Aktuator-Kennlinienfehler (0,2 -> 0,3) mit Rückkanal-Korrektur |
| [configs/scenarios/stadtverkehr.json](../../../configs/scenarios/stadtverkehr.json) | Stadtverkehr | Innerstädtischer Rundkurs, MPC |
| [configs/scenarios/testzyklus_kunde.json](../../../configs/scenarios/testzyklus_kunde.json) | Kundenspezifischer Testzyklus | Segmentliste (Gerade, Kurve, Spurversatz) |
| [configs/vehicles/ev_sedan.json](../../../configs/vehicles/ev_sedan.json) | ev_sedan | – |
| [configs/vehicles/mid_size_sedan.json](../../../configs/vehicles/mid_size_sedan.json) | mid_size_sedan | – |
| [configs/vehicles/sports_car.json](../../../configs/vehicles/sports_car.json) | sports_car | – |
| [configs/vehicles/suv.json](../../../configs/vehicles/suv.json) | suv | – |
