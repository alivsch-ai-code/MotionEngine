# Spurwechsel-Latenzstudie – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


Übernommen aus [lane_change/docs/theory.md](../../../lane_change/docs/theory.md).

Bausteine aus der Plattform: [Latenzkette](../actuators/theory.md#latency_chain), [Kennlinienfehler](../actuators/theory.md#steering_characteristic_error) (Paket actuators) und [Rückkanal-Korrektur](../controllers/theory.md#curvature_feedback_correction) (Paket controllers).

## Krümmungsprofil des Spurwechsels {#lane_change_curvature_profile}

### Ziel und Zweck
Soll-Krümmung für einen Spurwechsel um die Breite $w$ in der Dauer $T$, bei dem der Kurswinkel am Ende wieder null ist.

### Theorie
$$\kappa_{des}(t) = \frac{2\pi w}{v^2 T^2} \sin\left(\frac{2\pi (t - t_0)}{T}\right), \qquad t_0 \le t \le t_0 + T$$

Maximale Querbeschleunigung $a_{y,max} = v^2 \kappa_{max} = 2\pi w / T^2$ (0,61 m/s² für 3,5 m in 6 s).

### Herleitung
Mit $\dot\psi = v\kappa$ ist $\psi(t) = \frac{w}{vT}\left(1 - \cos\frac{2\pi\tau}{T}\right)$; über eine volle Periode ist $\psi(T) = 0$. Für kleine Winkel ist $\dot y \approx v \psi$, das Integral über $T$ ergibt $y(T) = w$.

### Annahmen
Konstante Geschwindigkeit, kleine Kurswinkel.

### Randbedingungen
Außerhalb $[t_0, t_0 + T]$ ist $\kappa_{des} = 0$.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $w$ | Querversatz | m | `width` |
| $T$ | Dauer | s | `duration` |
| $t_0$ | Beginn | s | `t_start` |
| $v$ | Geschwindigkeit | m/s | `v` |

### Anwendungsgrenzen
Kleine-Winkel-Näherung; der ideale Versatz ist 3,500 m (Regressionswert).

### Vor- und Nachteile
- Vorteil: analytisch, ruckarm an den Enden (Krümmung beginnt bei null).
- Nachteil: kein Optimum (z. B. ruckminimal nach Werling).

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Kleine Krümmungen (Betrag höchstens 0,00055 1/m bei 120 km/h): der Kennlinienfehler liegt dort bei etwa 10 %.

### In einfachen Worten
Erst sanft nach links, dann genauso sanft zurück – und das Auto fährt eine Spur weiter links geradeaus.

### Quellen
[[Rajamani (2012, Kap. 2)](../references.md#rajamani2012)]

## Umlauflatenz der Wirkkette {#latency_round_trip}

### Ziel und Zweck
Bestimmung, wann der Planer einen Aktuatorfehler frühestens sehen kann.

### Theorie
$$T_{Umlauf} = (T_{GW} + T_{Akt}) + \tau + (T_{Odo} + T_{GW})$$

Systemarchitektur: $40 + 5 + 0 + 5 + 40 = 90$ ms; das Gateway trägt 80 ms bei. Fälle „typical“ (180 ms) und „high“ (400 ms) sind Was-wäre-wenn-Annahmen.

### Herleitung
Ein Befehl wirkt nach dem Stellpfad am Fahrzeug; die Messung dieser Wirkung braucht den Rückkanal. Zusätzlich muss genug Krümmung anliegen, damit der Fehler vom Sensorrauschen unterscheidbar ist.

### Annahmen
Konstante Latenzen, Vielfache von 5 ms.

### Randbedingungen
PT1 für Aktor und Fahrzeug nur in den Fällen typical und high.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $T_{Umlauf}$ | Umlauflatenz | s | `latency_label()` |
| $T_{GW}$ | Gateway-Latenz | s | in `dead_time`, `sensor_delay` |
| $\tau$ | PT1-Zeitkonstante | s | `tau` |

### Anwendungsgrenzen
Ohne Jitter und Paketverluste.

### Vor- und Nachteile
- Vorteil: klare Zuordnung der Latenzanteile.
- Nachteil: deterministische Vereinfachung.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Das Gateway dominiert; eine schnellere Gateway-Anbindung wirkt doppelt.

### In einfachen Worten
Ein Befehl braucht 45 ms bis zum Auto, die Rückmeldung nochmals 45 ms – erst nach 90 ms kann der Planer überhaupt etwas merken.

### Quellen
[[comma.ai](../references.md#openpilot)]

## Korrekturstudie {#lane_change_correction_study}

### Ziel und Zweck
Quantifizierung des Querversatzes durch den Kennlinienfehler und der Wirkung der Rückkanal-Korrektur.

### Theorie
Simulationsschleife je Schritt $\Delta t$ = 5 ms:

$$\kappa_{sent} = \frac{\kappa_{des}}{\hat g}, \quad \kappa_{app} = f_{KL}\left(\mathrm{Latenz}(\kappa_{sent})\right), \quad \kappa_{mess} = \mathrm{Latenz}(\kappa_{app}) + n, \quad n \sim \mathcal{N}\left(0, (\sigma_r / v)^2\right)$$

Fahrzeug: $x_{k+1} = x_k + v\cos\psi_k \Delta t$, $y_{k+1} = y_k + v\sin\psi_k \Delta t$, $\psi_{k+1} = \psi_k + v\kappa_{app} \Delta t$.

### Herleitung
Der Fehlerfaktor wird wie in der [Rückkanal-Korrektur](../controllers/theory.md#curvature_feedback_correction) geschätzt; durch die Division der Soll-Krümmung wird die Kennlinie im Arbeitspunkt näherungsweise invertiert.

### Annahmen
Latenz bekannt, Rauschen gaußsch (0,1 °/s Gierrate), Seed 0.

### Randbedingungen
Ergebnisse (Regression): ideal 3,500 m, ohne Korrektur 3,849 m, mit Korrektur 3,627 m, geschätzter Fehlerfaktor 1,088 (Soll 1,10).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\hat g$ | geschätzter Fehlerfaktor | – | `error_factor_est` |
| $\sigma_r$ | Gierratenrauschen | rad/s | `yaw_rate_noise_deg` |
| $\kappa_{app}$ | gestellte Krümmung | 1/m | `k_applied` |

### Anwendungsgrenzen
Die Korrektur wirkt erst, wenn genug Krümmung anliegt; der anfängliche Fehler bleibt im Versatz erhalten.

### Vor- und Nachteile
- Vorteil: reduziert den Endversatz um etwa zwei Drittel.
- Nachteil: Restfehler durch Schätzverzögerung.

### Numerische Aspekte
Explizites Euler-Verfahren; mit 5 ms und kleiner Krümmung ausreichend genau.

### Praktische Auswirkungen
Motivation für Latenzschätzung und Kennlinienkalibrierung in realen Systemen.

### In einfachen Worten
Ohne Korrektur landet das Auto 35 cm zu weit links, mit Korrektur nur noch knapp 13 cm.

### Quellen
[[Ljung (1999)](../references.md#ljung1999)], [[Smith (1957)](../references.md#smith1957)]

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Rückkanal-Korrektur des Krümmungsfehlers](../controllers/theory.md#curvature_feedback_correction) | [`curvature_feedback.CurvatureCorrection.update`](../../../vdsim/controllers/curvature_feedback.py#L18) | – | [Ljung (1999)](../references.md#ljung1999), [Smith (1957)](../references.md#smith1957) |
| [Kinematisches Einspurmodell](../vehicle_models/theory.md#kinematic_bicycle) | [`vehicle_step`](../../../lane_change/vehicle_model.py#L6), [`bicycle_model.KinematicBicycleModel.derivatives`](../../../vdsim/vehicle_models/bicycle_model.py#L42) | [`lateral_controller/curvature_feedforward`](../controllers/components/lateral_controller__curvature_feedforward.md), [`vehicle_model/bicycle_kinematic`](../vehicle_models/components/vehicle_model__bicycle_kinematic.md) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Rajamani (2012)](../references.md#rajamani2012) |
| [Korrekturstudie](theory.md#lane_change_correction_study) | [`simulate`](../../../lane_change/simulation.py#L10) | – | [Ljung (1999)](../references.md#ljung1999), [Smith (1957)](../references.md#smith1957) |
| [Krümmungsprofil des Spurwechsels](theory.md#lane_change_curvature_profile) | [`lane_change_curvature`](../../../lane_change/profiles.py#L6) | [`maneuver/lane_change`](../trajectory/components/maneuver__lane_change.md) | [Rajamani (2012)](../references.md#rajamani2012) |
| [Latenzkette aus Totzeit und PT1](../actuators/theory.md#latency_chain) | [`latency.DeadTime`](../../../vdsim/actuators/latency.py#L19), [`latency.LatencyChain`](../../../vdsim/actuators/latency.py#L42), [`latency.PT1`](../../../vdsim/actuators/latency.py#L31) | – | [comma.ai](../references.md#openpilot), [Smith (1957)](../references.md#smith1957) |
| [Umlauflatenz der Wirkkette](theory.md#latency_round_trip) | [`simulate`](../../../lane_change/simulation.py#L10) | – | [comma.ai](../references.md#openpilot) |
| [Kennlinienfehler des Lenkaktors](../actuators/theory.md#steering_characteristic_error) | [`steering_characteristic.correction_factor`](../../../vdsim/actuators/steering_characteristic.py#L21), [`steering_characteristic.steering_characteristic`](../../../vdsim/actuators/steering_characteristic.py#L6) | – | [Ljung (1999)](../references.md#ljung1999) |
