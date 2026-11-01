# Aktorik – Latenzkette, Lenkaktor, Kennlinienfehler – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Öffentliche API

### `vdsim.actuators.latency`

| Name | Art | Beschreibung |
|---|---|---|
| [`DeadTime`](../../../vdsim/actuators/latency.py#L19) | Klasse | Outputs the input delayed by `delay` seconds |
| [`PT1`](../../../vdsim/actuators/latency.py#L31) | Klasse | First-order lag with time constant tau (tau = 0: pass-through) |
| [`LatencyChain`](../../../vdsim/actuators/latency.py#L42) | Klasse | Actuator path (dead time + PT1) and sensor path (dead time) |

### `vdsim.actuators.steering_actuator`

| Name | Art | Beschreibung |
|---|---|---|
| [`SteeringActuatorParameters`](../../../vdsim/actuators/steering_actuator.py#L19) | Klasse | – |
| [`SteeringActuator`](../../../vdsim/actuators/steering_actuator.py#L34) | Klasse | – |

### `vdsim.actuators.steering_characteristic`

| Name | Art | Beschreibung |
|---|---|---|
| [`steering_characteristic(k_full_lock_assumed, k_full_lock, error_at_zero)`](../../../vdsim/actuators/steering_characteristic.py#L6) | Funktion | Symmetric for left/right. |
| [`correction_factor(characteristic, k_full_lock_assumed, k_des)`](../../../vdsim/actuators/steering_characteristic.py#L21) | Funktion | Theoretical correction factor k_sent / k_des, so that characteristic(k_sent) = k_des. |
