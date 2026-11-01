# Simulationskern – Löser, Regelkreis, Szenarien, Ergebnisse – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `dt_control` | Reglertakt in s (Standard 0,01) | s | 0.01 |
| `dt_model` | Schrittweite des Fahrzeugmodells, 0 = recommended_dt des Modells (2 ms), zusätzlich begrenzt durch stable_dt | s | – |
| `solver` | euler, heun, rk4 oder adaptive | – | rk4 |
| `environment` | friction (base, patches, grid), wind_speed, road (bumps, roughness_class A–E, seed), lead_vehicle (initial_gap, time, speed) | – | – |
