# Fahrzeuganalyse – linear und quasi-statisch – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


Übernommen aus [vdsim/analysis/docs/theory.md](../../../vdsim/analysis/docs/theory.md).

## Eigenlenkgradient und charakteristische Geschwindigkeit {#understeer_gradient}

### Ziel und Zweck
Kennzahl für das stationäre Eigenlenkverhalten: Wie viel zusätzlicher Lenkwinkel ist pro Querbeschleunigung nötig?

### Theorie
Stationäre Kreisfahrt des linearen Einspurmodells:

$$\delta = \frac{l}{R} + EG \cdot a_y, \qquad EG = \frac{1}{g}\left(\frac{F_{zv}}{C_v} - \frac{F_{zh}}{C_h}\right)$$

$EG > 0$: untersteuernd, $EG < 0$: übersteuernd. Charakteristische bzw. kritische Geschwindigkeit:

$$v_{ch} = \sqrt{\frac{l}{EG}} \ \ (EG > 0), \qquad v_{krit} = \sqrt{\frac{-l}{EG}} \ \ (EG < 0)$$

### Herleitung
Im stationären Zustand gilt $F_{yv} = m a_y\, l_h/l$, $F_{yh} = m a_y\, l_v/l$ und $\alpha_i = F_{yi}/C_i$. Aus der Geometrie $\delta - \alpha_v + \alpha_h = l/R$ folgt mit $m g\, l_h/l = F_{zv}$ die obige Formel. Die Gierverstärkung $r/\delta = v/(l + EG\, v^2)$ ist bei $v_{ch}$ maximal; bei Übersteuern wird sie bei $v_{krit}$ unendlich (Stabilitätsgrenze).

### Annahmen
Lineare Reifen, statische Achslasten, kleine Winkel.

### Randbedingungen
Achssteifigkeiten bei statischer Last aus dem eingestellten Reifenmodell.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $EG$ | Eigenlenkgradient | rad/(m/s²) | `understeer_gradient` |
| $F_{zv}, F_{zh}$ | statische Achslasten | N | `static_axle_loads` |
| $C_v, C_h$ | Achs-Schräglaufsteifigkeiten | N/rad | `c_front`, `c_rear` |
| $v_{ch}$ | charakteristische Geschwindigkeit | m/s | `characteristic_speed` |
| $v_{krit}$ | kritische Geschwindigkeit | m/s | `critical_speed` |

### Anwendungsgrenzen
Nur im linearen Bereich; im Versuch (ISO 4138) wird der Gradient über der Querbeschleunigung gemessen und ist nichtlinear.

### Vor- und Nachteile
- Vorteil: eine Zahl beschreibt das Grundverhalten.
- Nachteil: Wank- und Lastverlagerungseinflüsse fehlen.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Wird in Stanley-Vorsteuerung, ESP- und TV-Referenzgierrate verwendet; Ausgabe in °/g.

### In einfachen Worten
Ein untersteuerndes Auto braucht mit zunehmender Kurvengeschwindigkeit immer mehr Lenkeinschlag für denselben Kreis. Das ist gutmütig und gewollt.

### Quellen
[[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)], [[Milliken und Milliken (1995)](../references.md#milliken1995)], [[ISO 4138:2021 (2021)](../references.md#iso4138)]

## Lineare Stabilitäts- und Frequenzganganalyse {#linear_stability_analysis}

### Ziel und Zweck
Stationäre Verstärkungen, Eigenwerte (Eigenfrequenz, Dämpfung) und Frequenzgang der Gier- und Querdynamik.

### Theorie
$$\left(\frac{v_y}{\delta}, \frac{r}{\delta}\right)_{stat} = -A^{-1} B_{:,1}, \qquad \lambda_{1,2} = \mathrm{eig}(A), \qquad \omega_n = \sqrt{\vert\lambda_1 \lambda_2\vert}, \qquad \zeta = -\frac{\lambda_1 + \lambda_2}{2 \omega_n}$$

$$H(j\omega) = \left(j\omega I - A\right)^{-1} B_{:,1}, \qquad \frac{a_y}{\delta}(j\omega) = j\omega H_{v_y} + v H_r$$

### Herleitung
Für ein System zweiter Ordnung gilt $\lambda_1 \lambda_2 = \det A = \omega_n^2$ und $\lambda_1 + \lambda_2 = \mathrm{tr} A = -2\zeta\omega_n$. Der Frequenzgang folgt aus der Laplace-Transformation des Zustandsraummodells. Die Querbeschleunigung im Schwerpunkt ist $a_y = \dot v_y + v r$.

### Annahmen
Konstante Geschwindigkeit, lineares Modell.

### Randbedingungen
Frequenzbereich standardmäßig 0,05–10 Hz (200 Punkte, logarithmisch).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\omega_n$ | ungedämpfte Eigenkreisfrequenz | rad/s | `wn` |
| $\zeta$ | Dämpfungsgrad | – | `damping` |
| $H$ | Frequenzgang | – | `yaw_gain`, `yaw_phase` |

### Anwendungsgrenzen
Für reelle Eigenwerte (überdämpft) ist $\omega_n$ das geometrische Mittel; die Interpretation als Schwingung entfällt.

### Vor- und Nachteile
- Vorteil: schnelle, exakte Aussagen zur Fahrzeugreaktion.
- Nachteil: keine Lenkungs- und Reifendynamik.

### Numerische Aspekte
Lineares Gleichungssystem je Frequenz; Phase mit `unwrap` stetig gemacht.

### Praktische Auswirkungen
Bode-Diagramme im Tab „Analyse“; Vergleich mit dem Frequenzgang-KPI aus dem Sinus-Sweep (ISO 7401).

### In einfachen Worten
Man fragt: Wie schnell und wie stark dreht sich das Auto, wenn man unterschiedlich schnell hin- und herlenkt?

### Quellen
[[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)], [[Rajamani (2012, Kap. 2)](../references.md#rajamani2012)]

## Quasi-statische Radlasten und Wankgradient {#quasi_static_wheel_loads}

### Ziel und Zweck
Radlasten, Wankwinkel und Querlastverteilung bei konstanter Längs- und Querbeschleunigung.

### Theorie
Rollachshöhe im Schwerpunkt und Wankgradient:

$$h_{RA} = h_{RZ,v} + (h_{RZ,h} - h_{RZ,v}) \frac{l_v}{l}, \qquad h' = h - h_{RA}, \qquad \frac{\varphi}{a_y} = \frac{m_s h'}{c_{\varphi v} + c_{\varphi h} - m_s g h'}$$

Querlastverlagerung je Achse (elastisch + geometrisch + ungefederte Massen):

$$\Delta F_{z,v} = \frac{c_{\varphi v} \varphi + m_s a_y \frac{l_h}{l} h_{RZ,v} + 2 m_{u,v} a_y R}{t_v}$$

Längslastverlagerung $\Delta F_{z,x} = m a_x h/(2l)$ je Rad. LLTD = Anteil der Vorderachse an der gesamten Querlastverlagerung (Moment).

### Herleitung
Momentengleichgewicht der gefederten Masse um die Rollachse mit Schwerkraftanteil $m_s g h' \varphi$ (destabilisierend) und Wankfedermoment $c_\varphi \varphi$; Kräfte an den Rollzentren werden direkt über die Lenker übertragen. Wanksteifigkeit je Achse $c_\varphi = k\, t^2/2 + c_{Stab}$.

### Annahmen
Kleine Wankwinkel, lineare Federn, feste Rollzentren.

### Randbedingungen
Linkskurve: $a_y > 0$; Radreihenfolge FL, FR, RL, RR.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $h_{RA}$ | Rollachshöhe im Schwerpunkt | m | `roll_axis_height` |
| $h'$ | Wankhebelarm | m | `roll_arm` |
| $\varphi / a_y$ | Wankgradient | rad/(m/s²) | `roll_gradient` |
| $c_{\varphi v}, c_{\varphi h}$ | Wanksteifigkeiten | N m/rad | `k_front`, `k_rear` |
| LLTD | Querlastverteilung vorn | – | `lltd_front` |

### Anwendungsgrenzen
Stationär; Abheben eines Rades beendet die Gültigkeit (Abhebegrenze wird ausgewiesen).

### Vor- und Nachteile
- Vorteil: schnelle Auslegungsgröße für Stabilisatorabstimmung.
- Nachteil: keine Dämpfer- und Trägheitseffekte.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Mehr Wanksteifigkeit vorn erhöht die Querlastverlagerung vorn und damit (über die Reifendegression) das Untersteuern.

### In einfachen Worten
In der Kurve lehnt sich das Auto nach außen, die äußeren Räder tragen mehr, die inneren weniger. Wie das verteilt wird, bestimmen Federn, Stabilisatoren und Rollzentren.

### Quellen
[[Milliken und Milliken (1995)](../references.md#milliken1995)], [[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)]

## Ackermann-Lenkgeometrie und Wendekreis {#ackermann_steering}

### Ziel und Zweck
Lenkwinkel der Vorderräder ohne Schräglauf und Wendekreisdurchmesser.

### Theorie
$$\delta_{i} = \arctan\frac{l}{R - t/2}, \qquad \delta_{a} = \arctan\frac{l}{R + t/2}$$

Wendekreis (Wand zu Wand) bei maximalem Lenkwinkel mit $R_h = l / \tan\delta_{max}$:

$$D = 2 \sqrt{\left(R_h + \frac{b}{2}\right)^2 + \left(l + \frac{L_{Fzg} - l}{2}\right)^2}$$

### Herleitung
Alle Radnormalen schneiden sich im Momentanpol auf der Verlängerung der Hinterachse (Abstand $R$ zur Fahrzeugmitte).

### Annahmen
Kein Schräglauf, Überhänge vorn und hinten gleich groß.

### Randbedingungen
$R > t/2$.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $R$ | Kurvenradius an der Hinterachse | m | `radius` |
| $t$ | Spurweite vorn | m | `track_front` |
| $\delta_{max}$ | maximaler Radlenkwinkel | rad | `max_steer_angle` |
| $D$ | Wendekreisdurchmesser | m | `turning_circle()` |

### Anwendungsgrenzen
Nur bei sehr kleiner Geschwindigkeit.

### Vor- und Nachteile
- Vorteil: einfache geometrische Kennwerte.
- Nachteil: reale Lenkkinematik weicht vom idealen Ackermann ab.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Kennwert „Wendekreis“ im Tab „Kennwerte“.

### In einfachen Worten
Das innere Vorderrad muss stärker einschlagen als das äußere, weil es einen engeren Kreis fährt.

### Quellen
[[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)]

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Ackermann-Lenkgeometrie und Wendekreis](theory.md#ackermann_steering) | [`quasi_static.QuasiStaticAnalysis.ackermann_angles`](../../../vdsim/analysis/quasi_static.py#L74), [`quasi_static.QuasiStaticAnalysis.turning_circle`](../../../vdsim/analysis/quasi_static.py#L79) | – | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) |
| [Lineare Stabilitäts- und Frequenzganganalyse](theory.md#linear_stability_analysis) | [`linear_analysis.LinearSingleTrackAnalysis.eigen`](../../../vdsim/analysis/linear_analysis.py#L40), [`linear_analysis.LinearSingleTrackAnalysis.frequency_response`](../../../vdsim/analysis/linear_analysis.py#L48), [`linear_analysis.LinearSingleTrackAnalysis.steady_state_gains`](../../../vdsim/analysis/linear_analysis.py#L31) | – | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Rajamani (2012)](../references.md#rajamani2012) |
| [Quasi-statische Radlasten und Wankgradient](theory.md#quasi_static_wheel_loads) | [`quasi_static.QuasiStaticAnalysis.roll_gradient`](../../../vdsim/analysis/quasi_static.py#L28), [`quasi_static.QuasiStaticAnalysis.wheel_loads`](../../../vdsim/analysis/quasi_static.py#L41) | – | [Milliken und Milliken (1995)](../references.md#milliken1995), [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) |
| [Eigenlenkgradient und charakteristische Geschwindigkeit](theory.md#understeer_gradient) | [`linear_analysis.LinearSingleTrackAnalysis.characteristic_speed`](../../../vdsim/analysis/linear_analysis.py#L20), [`linear_analysis.LinearSingleTrackAnalysis.critical_speed`](../../../vdsim/analysis/linear_analysis.py#L26), [`esp_controller.understeer_gradient`](../../../vdsim/controllers/esp_controller.py#L12), [`bicycle_model.LinearBicycleModel.understeer_gradient`](../../../vdsim/vehicle_models/bicycle_model.py#L87) | [`chassis_system/esp`](../controllers/components/chassis_system__esp.md) | [ISO 4138:2021 (2021)](../references.md#iso4138), [Milliken und Milliken (1995)](../references.md#milliken1995), [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Rajamani (2012)](../references.md#rajamani2012), [Reif (2010)](../references.md#reif2010), [van Zanten et al. (1995)](../references.md#vanzanten1995) |
