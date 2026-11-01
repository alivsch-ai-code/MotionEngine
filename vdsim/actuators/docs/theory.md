# Theorie: Aktorik

## Latenzkette aus Totzeit und PT1 {#latency_chain}

### Ziel und Zweck
Nachbildung der Signallaufzeiten in der Wirkkette Planer → Gateway → Aktuator → Fahrzeug → Odometrie → Gateway → Planer.

### Theorie
Totzeit um $n = \mathrm{round}(T_t/\Delta t)$ Abtastschritte und PT1 mit Zeitkonstante $\tau$:

$$y_k = u_{k-n}, \qquad y_k = y_{k-1} + \frac{\Delta t}{\tau + \Delta t}\left(u_k - y_{k-1}\right)$$

Übertragungsfunktion des Stellpfads im Kontinuierlichen: $G(s) = e^{-T_t s} / (1 + \tau s)$; Rückkanal $e^{-T_s s}$. Umlauflatenz $T_t + \tau + T_s$.

### Herleitung
Die PT1-Differentialgleichung $\tau \dot y + y = u$ wird mit dem impliziten Euler-Verfahren diskretisiert: $\tau (y_k - y_{k-1})/\Delta t + y_k = u_k$, aufgelöst nach $y_k$. Das Verfahren ist für jedes $\Delta t$ stabil und ergibt für $\tau = 0$ exakt den Durchgriff.

### Annahmen
Konstante, bekannte Latenzen; lineare Aktordynamik.

### Randbedingungen
Totzeiten werden auf Vielfache des Reglertakts gerundet; Anfangswerte der Puffer sind 0.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $T_t$ | Totzeit Stellpfad | s | `dead_time` |
| $\tau$ | PT1-Zeitkonstante | s | `tau` |
| $T_s$ | Totzeit Rückkanal | s | `sensor_delay` |
| $n$ | Puffertiefe | – | `len(buffer)` |

### Anwendungsgrenzen
Jitter und variable Buslast werden nicht abgebildet.

### Vor- und Nachteile
- Vorteil: exakt, deterministisch, leicht parametrierbar.
- Nachteil: Auflösung durch den Reglertakt begrenzt.

### Numerische Aspekte
Ringpuffer mit `deque`: O(1) je Schritt.

### Praktische Auswirkungen
Fälle „system“ (45 + 45 ms), „typical“ und „high“ (Annahmen, siehe README); die Größenordnung realer Lenkaktor-Latenzen liegt bei etwa 0,07–0,5 s (vgl. openpilot).

### In einfachen Worten
Jede Nachricht braucht eine Weile durch das Netzwerk, und der Aktor folgt einem Befehl nicht sofort, sondern nähert sich ihm an.

### Quellen
[@openpilot], [@smith1957]

## Kennlinienfehler des Lenkaktors {#steering_characteristic_error}

### Ziel und Zweck
Systematischer Fehler zwischen angeforderter und gestellter Krümmung, z. B. durch falsch angenommene Lenkübersetzung.

### Theorie
Relativer Fehler steigt quadratisch vom Wert $e_0$ bei kleiner Krümmung bis zum Fehler beim Volleinschlag:

$$e(\kappa) = e_0 + \left(e_{VE} - e_0\right)\left(\frac{\vert\kappa\vert}{\kappa_{VE,ann}}\right)^2, \qquad e_{VE} = \frac{\kappa_{VE}}{\kappa_{VE,ann}} - 1$$

$$\kappa_{gestellt} = \mathrm{sign}(\kappa)\, \min(\vert\kappa\vert, \kappa_{VE,ann}) \left(1 + e\right)$$

Theoretischer Korrekturfaktor: $\kappa_{sent}/\kappa_{des}$ mit $\kappa_{gestellt}(\kappa_{sent}) = \kappa_{des}$, numerisch durch Inversion auf einem Gitter.

### Herleitung
Die Randbedingungen $e(0) = e_0$ und $\kappa_{gestellt}(\kappa_{VE,ann}) = \kappa_{VE}$ legen die quadratische Fehlerkurve fest. Die Kennlinie ist bis zum Volleinschlag streng monoton und damit invertierbar.

### Annahmen
Symmetrisch links/rechts, zeitinvariant.

### Randbedingungen
Anforderungen über $\kappa_{VE,ann}$ sättigen beim Volleinschlag.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\kappa_{VE}$ | tatsächliche Krümmung bei Volleinschlag | 1/m | `k_full_lock` |
| $\kappa_{VE,ann}$ | angenommene Krümmung bei Volleinschlag | 1/m | `k_full_lock_assumed` |
| $e_0$ | Fehler bei kleiner Krümmung | – | `error_at_zero` |

### Anwendungsgrenzen
Nur multiplikative, statische Fehler.

### Vor- und Nachteile
- Vorteil: zwei anschauliche Parameter.
- Nachteil: kein Spiel, keine Hysterese.

### Numerische Aspekte
Inversion über 20001 Gitterpunkte und lineare Interpolation.

### Praktische Auswirkungen
Mit Standardwerten 10 % Fehler bei kleinen Krümmungen (Faktor 1,10, Korrektur 0,909) und 50 % beim Volleinschlag.

### In einfachen Worten
Der Aktor lenkt immer etwas stärker als verlangt – bei kleinen Lenkwinkeln um 10 %, bei vollem Einschlag um 50 %.

### Quellen
[@ljung1999]

## Wirkkette des Lenkaktors {#steering_actuator_chain}

### Ziel und Zweck
Verbindet Korrektur, Latenz, Kennlinie und Ratenbegrenzung zu einem Aktormodell für den Simulator.

### Theorie
$$\kappa_{req} = \frac{\tan\delta_{req}}{l}, \quad \kappa_{sent} = \frac{\kappa_{req}}{\hat g}, \quad \kappa_{app} = f_{KL}\left(\mathrm{PT1}(\mathrm{T_t}(\kappa_{sent}))\right), \quad \delta = \arctan(\kappa_{app} l)$$

$$\delta_k = \mathrm{clip}\left(\delta, \delta_{k-1} - \dot\delta_{max} \Delta t, \delta_{k-1} + \dot\delta_{max} \Delta t\right)$$

### Herleitung
Krümmung und Lenkwinkel sind über das kinematische Einspurmodell verknüpft ($\kappa = \tan\delta / l$). Die Schätzung $\hat g$ stammt aus der [Rückkanal-Korrektur](#curvature_feedback_correction) im Paket controllers.

### Annahmen
Gemessene Krümmung $r/\max(v_x, 1)$; Latenzmodell des Schätzers identisch zur realen Kette.

### Randbedingungen
Ratenbegrenzung nur bei $\dot\delta_{max} > 0$.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\kappa_{sent}$ | gesendete Krümmung | 1/m | `k_sent` |
| $\kappa_{app}$ | gestellte Krümmung | 1/m | `k_applied` |
| $\hat g$ | geschätzter Fehlerfaktor | – | `error_factor_est` |
| $\dot\delta_{max}$ | Lenkratengrenze | rad/s | `rate_limit` |

### Anwendungsgrenzen
Nur Vorderachslenkung; keine Lenkmomentschnittstelle.

### Vor- und Nachteile
- Vorteil: alle Effekte einzeln schaltbar.
- Nachteil: Krümmungsschnittstelle setzt kinematische Zusammenhänge voraus.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Szenario „Spurwechsel mit Latenzkette“; Signale `k_sent`, `k_meas_delayed`, `error_factor_est` im Ergebnis.

### In einfachen Worten
Der Lenkbefehl wird erst korrigiert, dann verzögert, dann vom ungenauen Aktor umgesetzt und darf sich nicht beliebig schnell ändern.

### Quellen
[@ljung1999], [@openpilot]
