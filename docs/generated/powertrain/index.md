# Antriebsstrang, Bremse und Längsaktuierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.powertrain` · Quellcode: [vdsim/powertrain/](../../../vdsim/powertrain) · Paketdoku: [vdsim/powertrain/docs/](../../../vdsim/powertrain/docs)

## Übersicht

**Setzt eine Beschleunigungsanforderung in Antriebs- und Bremsmomente je Rad um – mit Verbrennungsmotor und Automatikgetriebe oder E-Motor, Bremskraftverteilung (EBV), Rekuperation und Energiebilanz.**

Längsregler fordern eine Beschleunigung an; das Fahrzeugmodell braucht Momente je Rad. Dazwischen liegen
Fahrwiderstandskompensation, Antriebsgrenzen (Kennlinie, Leistung, Übersetzung), die Aufteilung auf
Achsen und Räder, die Bremskraftverteilung und bei E-Fahrzeugen das Zusammenspiel von Rekuperation und
Reibbremse. Die Energiebilanz liefert Verbrauchskennwerte.

Paket-Docstring:

```text
Powertrain: combustion engine, gearbox, electric motor, brakes, longitudinal actuation.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 3 |
| Komponenten | 0 |
| Verfahren/Konzepte | 4 |
| @trace-Einträge | 5 |
| Tests | 2 |
| Beispiele | 1 |

## Architektur

- `engine.py`: `CombustionEngine` (Volllastkennlinie), `Gearbox` (Übersetzungen, Schaltdrehzahlen),
  `ElectricMotor` (konstantes Moment, dann konstante Leistung; Rekuperationsgrenzen).
- `powertrain.py`: `Powertrain` (Layout fwd/rwd/awd, maximale Antriebs- und Rekuperationskraft,
  Radmomente, Energiekonto), `BrakeSystem` (EBV, Achsmomente), `LongitudinalActuation.actuate()`.

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.powertrain`](../../../vdsim/powertrain/__init__.py) | 7 | – | Powertrain: combustion engine, gearbox, electric motor, brakes, longitudinal actuation. |
| [`vdsim.powertrain.engine`](../../../vdsim/powertrain/engine.py) | 73 | CombustionEngine, Gearbox, ElectricMotor | Drive units: combustion engine with full-load curve, electric motor with torque/power limits. |
| [`vdsim.powertrain.powertrain`](../../../vdsim/powertrain/powertrain.py) | 136 | Powertrain, BrakeSystem, LongitudinalActuation | Powertrain, brakes and the longitudinal actuation (acceleration request -> wheel torques). |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [vehicle_models](../vehicle_models/index.md)
- genutzt von: [simulation](../simulation/index.md), [stabilization](../stabilization/index.md)
- externe Bibliotheken: `numpy`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Vorsteuerung der Fahrwiderstände in der Längsaktuierung | Längsregler arbeiten mit Beschleunigungen; stationär ist kein Integratoranteil nötig | – |
| Rekuperation zuerst, Reibbremse für den Rest, achsweise nach EBV-Verteilung | maximale Energierückgewinnung ohne Verletzung der stabilen Bremskraftverteilung | parallele Rekuperation mit fester Quote |

## Implementierung

- Die Gesamtkraft wird nach unten auf −1,3 m g begrenzt.
- Rekuperation nur oberhalb 1 m/s; die Rekuperation erscheint als negatives Antriebsmoment.
- Der Verbrenner nutzt einen pauschalen Wirkungsgrad von 30 % für die Kraftstoffenergie.

### Verfahren und Konzepte

- [Antriebsgrenzen von Motor und Getriebe](theory.md#drive_torque_limits)
- [Energiebilanz](theory.md#energy_balance)
- [Ideale Bremskraftverteilung (EBV)](theory.md#ideal_brake_distribution)
- [Rekuperation und Bremsmischung](theory.md#regenerative_braking)

## Erweiterungspunkte

- Wirkungsgradkennfelder für Motor und Getriebe, Batteriemodell mit SOC

## Verwandte Module

[controllers](../controllers/index.md), [simulation](../simulation/index.md), [vehicle_models](../vehicle_models/index.md)

## Hauptquellen

[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Reif (2010)](../references.md#reif2010)
