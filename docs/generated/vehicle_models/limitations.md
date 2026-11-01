# Fahrzeugmodelle – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Kein Rückwärtsfahren; unter etwa 3 m/s wird der Schlupf mit einer Mindestgeschwindigkeit gebildet.
- Lastverlagerung über geschätzte Beschleunigungen; bei schnellen Transienten leicht phasenverschoben.
- Fahrbahnprofil links und rechts gleich (keine Wankanregung durch die Straße).
- Keine Elastokinematik-Kennfelder (K&C), keine Lenkungsdynamik, keine Aerodynamik mit Abtrieb.

## [Einspurmodell kinematisch](components/vehicle_model__bicycle_kinematic.md)

Annahmen:

- Kein Schräglauf
- Ackermann-Geometrie
- Längskraft auf mu m g begrenzt

Grenzen:

- Ungültig bei hoher Querbeschleunigung (etwa über 4 m/s²)

## [Einspurmodell linear](components/vehicle_model__bicycle_linear.md)

Annahmen:

- Kleine Winkel
- lineare Achs-Seitenkräfte
- statische Achslasten

Grenzen:

- Keine Sättigung der Seitenkräfte

## [Einspurmodell nichtlinear](components/vehicle_model__bicycle_nonlinear.md)

Annahmen:

- Keine Wankdynamik
- Seitenkraft je Achse aus einem Reifen mit halber Achslast mal zwei

## [Zweispurmodell (12 Zustände)](components/vehicle_model__double_track.md)

Annahmen:

- Wanken um eine feste Rollachse
- Längslastverlagerung quasistatisch

Grenzen:

- Kein Nicken und keine Hubbewegung

## [Mehrkörpermodell (24 Zustände)](components/vehicle_model__multibody.md)

Annahmen:

- Kleine Aufbauwinkel
- lineare Feder- und Reifensteifigkeiten
- Dämpferkennlinien als Tabellen

Grenzen:

- Fahrbahnprofil links und rechts gleich
- Reifen als Punktkontakt

## Anwendungsgrenzen der Verfahren

### [Zweispurmodell mit Wanken und Raddrehung](theory.md#double_track)

Grenzbereich, Regelsysteme und Split-µ; nicht für Komfortbewertung (keine Vertikaldynamik), nicht für Rückwärtsfahrt.

### [Fahrwiderstände](theory.md#driving_resistances)

Ebene Straße; kein Abtrieb, kein geschwindigkeitsabhängiger Rollwiderstand.

### [Kinematisches Einspurmodell](theory.md#kinematic_bicycle)

Bis etwa $a_y \approx 4\ \mathrm{m/s^2}$ (darüber dominiert der Schräglauf); kein Eigenlenkverhalten.

### [Lineares Einspurmodell](theory.md#linear_bicycle)

Lineare Reifen: gültig bis $a_y \approx 4\ \mathrm{m/s^2}$; keine Sättigung, daher keine Instabilität durch Haftungsverlust.

### [Mehrkörpermodell mit Vertikaldynamik](theory.md#multibody)

Komfort und Radlastschwankung bis etwa 20 Hz; Reifen als Punktkontakt ohne Latschfilterung (kurze Hindernisse werden überschätzt).

### [Nichtlineares Einspurmodell](theory.md#nonlinear_bicycle)

Ohne Wankdynamik fehlt der Einfluss der Querlastverteilung auf das Eigenlenkverhalten; für Split-µ und radindividuelle Eingriffe ist das Zweispurmodell nötig.
