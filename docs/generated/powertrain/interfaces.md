# Antriebsstrang, Bremse und Längsaktuierung – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Öffentliche API

### `vdsim.powertrain.engine`

| Name | Art | Beschreibung |
|---|---|---|
| [`CombustionEngine`](../../../vdsim/powertrain/engine.py#L8) | Klasse | – |
| [`Gearbox`](../../../vdsim/powertrain/engine.py#L24) | Klasse | – |
| [`ElectricMotor`](../../../vdsim/powertrain/engine.py#L49) | Klasse | – |

### `vdsim.powertrain.powertrain`

| Name | Art | Beschreibung |
|---|---|---|
| [`Powertrain`](../../../vdsim/powertrain/powertrain.py#L10) | Klasse | Maps a requested total drive force to wheel torques (layout, limits) and tracks energy |
| [`BrakeSystem`](../../../vdsim/powertrain/powertrain.py#L70) | Klasse | – |
| [`LongitudinalActuation`](../../../vdsim/powertrain/powertrain.py#L98) | Klasse | Acceleration request -> drive/brake torques (feedforward of driving resistances, regen blending) |
