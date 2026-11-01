# Spurwechsel-Latenzstudie – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Kinematisches Fahrzeugmodell ohne Schräglauf und mit konstanter Geschwindigkeit.
- Latenz dem Schätzer bekannt; keine Jitter.
- Nur ein Manöver (Spurwechsel), keine Regelung der Querablage (reine Vorsteuerung der Krümmung).

## Anwendungsgrenzen der Verfahren

### [Korrekturstudie](theory.md#lane_change_correction_study)

Die Korrektur wirkt erst, wenn genug Krümmung anliegt; der anfängliche Fehler bleibt im Versatz erhalten.

### [Krümmungsprofil des Spurwechsels](theory.md#lane_change_curvature_profile)

Kleine-Winkel-Näherung; der ideale Versatz ist 3,500 m (Regressionswert).

### [Umlauflatenz der Wirkkette](theory.md#latency_round_trip)

Ohne Jitter und Paketverluste.
