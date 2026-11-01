# Spurwechsel-Latenzstudie – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `V, LANE_WIDTH, DURATION, T_START, T_END, DT` | Szenarioparameter in run_lane_change.py (120 km/h, 3,5 m, 6 s, 1 s, 10 s, 5 ms) | – | – |
| `K_FULL_LOCK, K_FULL_LOCK_DISTORTED, ERROR_AT_ZERO` | Kennlinie (0,3 1/m, 0,2 1/m, 10 %) | – | – |
| `LATENCY_CASES` | none, system (45 + 45 ms), typical, high – definiert in vdsim/actuators/latency.py | – | – |
