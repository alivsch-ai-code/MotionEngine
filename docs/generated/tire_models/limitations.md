# Reifenmodelle – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Stationäre Kräfte ohne Einlaufverhalten (Relaxationslänge); bei sehr schnellen Lenkeingaben reagiert das Modell zu schnell.
- Keine Temperatur-, Druck- oder Verschleißabhängigkeit.
- Das Rückstellmoment ist eine Näherung über einen abklingenden Reifennachlauf, ohne Restmoment und ohne Anteil der Längskraft.
- Der Sturz wirkt nur als Verschiebung des Schräglaufwinkels (Sturzseitenkraft), nicht auf Steifigkeit oder Reibwert.

## [tire_model/brush](components/tire_model__brush.md)

Annahmen:

- Parabolische Druckverteilung
- gleiche Haft- und Gleitreibung
- isotrope Borstensteifigkeit (über theta_x
- theta_y normiert)

Grenzen:

- Haft- und Gleitreibwert identisch
- daher kein Kraftabfall nach dem Maximum

## [tire_model/linear](components/tire_model__linear.md)

Annahmen:

- Kräfte proportional zu Schlupf und Radlast
- Rückstellmoment über konstanten Nachlauf

Grenzen:

- Keine Sättigungsform – der Übergang zum Gleiten ist ein harter Knick am Reibkreis

## [tire_model/pacejka](components/tire_model__pacejka.md)

Annahmen:

- Stationäres Reifenverhalten
- Symmetrie (keine Verschiebungen S_H
- S_V außer Sturz)

Grenzen:

- Kein Einlaufverhalten
- kein MF-6.2-Datensatz

## Anwendungsgrenzen der Verfahren

### [Bürstenmodell](theory.md#brush_model)

Kein Kraftabfall nach dem Maximum (Haft = Gleitreibung); keine Karkassenelastizität.

### [Kombinierter Schlupf (Gewichtungsfunktionen)](theory.md#combined_slip)

Die Summe der Kräfte kann den Reibkreis geringfügig überschreiten, weil die Gewichtung nicht exakt am Reibkreis normiert ist.

### [Lineares Reifenmodell mit Reibkreis](theory.md#linear_tire)

Bis etwa 40–50 % der Kraftschlussausnutzung realistisch; danach überschätzt das Modell die Kräfte bis zum harten Knick am Reibkreis.

### [Pacejka Magic Formula](theory.md#magic_formula)

Gültig für trockene und nasse Fahrbahn bei stationärem Schlupf. Für Stillstand und sehr kleine Geschwindigkeiten ist der Schlupf schlecht definiert; die Fahrzeugmodelle begrenzen den Nenner.
