# Antriebsstrang, Bremse und Längsaktuierung – Einschränkungen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · **Einschränkungen** · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Bekannte Grenzen des Pakets

- Keine Motordynamik, kein Turboloch, keine Kupplung und kein Wandler; Schalten ist sofortig.
- Wirkungsgrade konstant (keine Kennfelder), keine Batteriezustände (SOC, Spannung).
- Bremse ohne Hydraulikdynamik und ohne Temperatureinfluss.

## Anwendungsgrenzen der Verfahren

### [Antriebsgrenzen von Motor und Getriebe](theory.md#drive_torque_limits)

Keine Zugkraftunterbrechung beim Schalten.

### [Energiebilanz](theory.md#energy_balance)

Kein Batteriemodell, keine Temperatur.

### [Ideale Bremskraftverteilung (EBV)](theory.md#ideal_brake_distribution)

Keine radindividuelle Verteilung (Kurvenbremsung); das übernehmen ABS/ESP.

### [Rekuperation und Bremsmischung](theory.md#regenerative_braking)

Keine Koordination mit ABS (ABS moduliert nur das Reibbremsmoment).
