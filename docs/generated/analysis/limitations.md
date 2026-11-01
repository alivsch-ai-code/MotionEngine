# Fahrzeuganalyse – linear und quasi-statisch – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Linear – keine Aussage über den Grenzbereich; Lastverlagerung und Reifendegression fehlen in der linearen Analyse.
- Quasi-statisch – keine Dynamik der Wankbewegung, keine Elastokinematik.
- Der Wendekreis nutzt eine einfache Geometrie (äußeres Vorderrad, Fahrzeugüberhang).

## Anwendungsgrenzen der Verfahren

### [Ackermann-Lenkgeometrie und Wendekreis](theory.md#ackermann_steering)

Nur bei sehr kleiner Geschwindigkeit.

### [Lineare Stabilitäts- und Frequenzganganalyse](theory.md#linear_stability_analysis)

Für reelle Eigenwerte (überdämpft) ist $\omega_n$ das geometrische Mittel; die Interpretation als Schwingung entfällt.

### [Quasi-statische Radlasten und Wankgradient](theory.md#quasi_static_wheel_loads)

Stationär; Abheben eines Rades beendet die Gültigkeit (Abhebegrenze wird ausgewiesen).

### [Eigenlenkgradient und charakteristische Geschwindigkeit](theory.md#understeer_gradient)

Nur im linearen Bereich; im Versuch (ISO 4138) wird der Gradient über der Querbeschleunigung gemessen und ist nichtlinear.
