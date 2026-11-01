# Aktorik – Latenzkette, Lenkaktor, Kennlinienfehler – Konfiguration

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · **Konfiguration** · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Konfigurationsmöglichkeiten (Paketdoku)

| Name | Beschreibung | Einheit | Default |
|---|---|---|---|
| `steering_actuator.dead_time` | Totzeit Stellpfad (Gateway + Aktuator) | s | 0 |
| `steering_actuator.tau` | PT1-Zeitkonstante Aktuator + Fahrzeug | s | 0 |
| `steering_actuator.sensor_delay` | Totzeit Rückkanal (Odometrie + Gateway) | s | 0 |
| `steering_actuator.rate_limit` | Lenkratenbegrenzung, 0 = unbegrenzt | rad/s | 0 |
| `steering_actuator.characteristic_error` | verfälschte Kennlinie ein/aus | – | False |
| `steering_actuator.k_full_lock` | tatsächliche Krümmung bei Volleinschlag | 1/m | 0.3 |
| `steering_actuator.k_full_lock_assumed` | Krümmung, die der Planer für Volleinschlag annimmt | 1/m | 0.2 |
| `steering_actuator.error_at_zero` | relativer Fehler bei kleiner Krümmung | – | 0.1 |
| `steering_actuator.feedback_correction` | Rückkanal-Korrektur ein/aus | – | False |

## Parametersatz `SteeringActuatorParameters` (`vdsim.actuators.steering_actuator`)

| Name | Bezeichnung | Einheit | Default | Min | Max |
|---|---|---|---|---|---|
| `dead_time` | – | – | 0 | – | – |
| `tau` | – | – | 0 | – | – |
| `sensor_delay` | – | – | 0 | – | – |
| `rate_limit` | – | – | 0 | – | – |
| `characteristic_error` | – | – | False | – | – |
| `k_full_lock` | – | – | 0.3 | – | – |
| `k_full_lock_assumed` | – | – | 0.2 | – | – |
| `error_at_zero` | – | – | 0.1 | – | – |
| `feedback_correction` | – | – | False | – | – |
