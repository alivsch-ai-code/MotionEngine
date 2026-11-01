# Antriebsstrang, Bremse und Längsaktuierung – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`ElectricMotor.max_torque`](../../../vdsim/powertrain/engine.py#L63) | – | [Antriebsgrenzen von Motor und Getriebe](theory.md#drive_torque_limits) | – | – | module.yaml |
| [`BrakeSystem.front_share`](../../../vdsim/powertrain/powertrain.py#L74) | – | [Ideale Bremskraftverteilung (EBV)](theory.md#ideal_brake_distribution) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | – | module.yaml |
| [`LongitudinalActuation.actuate`](../../../vdsim/powertrain/powertrain.py#L109) | – | [Rekuperation und Bremsmischung](theory.md#regenerative_braking) | [Reif (2010)](../references.md#reif2010) | – | module.yaml |
| [`Powertrain.account_energy`](../../../vdsim/powertrain/powertrain.py#L53) | – | [Energiebilanz](theory.md#energy_balance) | – | [test_simulation_and_reporting.py](../../../tests/test_simulation_and_reporting.py) | module.yaml |
| [`Powertrain.max_drive_force`](../../../vdsim/powertrain/powertrain.py#L34) | – | [Antriebsgrenzen von Motor und Getriebe](theory.md#drive_torque_limits) | – | – | module.yaml |

## Warum es diese Implementierungen gibt

### `ElectricMotor.max_torque`

- **Warum:** Maximale Antriebskraft am Rad in Abhängigkeit von der Geschwindigkeit.
- **Theorie:** [Antriebsgrenzen von Motor und Getriebe](theory.md#drive_torque_limits)
- **Annahmen:** Stationäre Kennlinien, keine Motordynamik.
- **Quelle:** –

### `BrakeSystem.front_share`

- **Warum:** Die Bremskraft so auf die Achsen verteilen, dass die Hinterachse nicht vor der Vorderachse blockiert (Stabilität).
- **Theorie:** [Ideale Bremskraftverteilung (EBV)](theory.md#ideal_brake_distribution)
- **Annahmen:** Starrer Aufbau (kein Nicken in der Lastverlagerung), gleicher Reibwert an allen Rädern.
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `LongitudinalActuation.actuate`

- **Warum:** Energie beim Bremsen zurückgewinnen, ohne die Bremsstabilität zu gefährden.
- **Theorie:** [Rekuperation und Bremsmischung](theory.md#regenerative_braking)
- **Annahmen:** Rekuperation nur oberhalb 1 m/s; ideale Momentenstellung.
- **Quelle:** [Reif (2010)](../references.md#reif2010)

### `Powertrain.account_energy`

- **Warum:** Energiebedarf, Rückgewinnung und Verbrauch eines Laufs.
- **Theorie:** [Energiebilanz](theory.md#energy_balance)
- **Annahmen:** Konstante Wirkungsgrade; Verbrenner mit 30 % effektivem Wirkungsgrad.
- **Quelle:** –

### `Powertrain.max_drive_force`

- **Warum:** Maximale Antriebskraft am Rad in Abhängigkeit von der Geschwindigkeit.
- **Theorie:** [Antriebsgrenzen von Motor und Getriebe](theory.md#drive_torque_limits)
- **Annahmen:** Stationäre Kennlinien, keine Motordynamik.
- **Quelle:** –
