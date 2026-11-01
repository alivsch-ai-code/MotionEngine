# Theorie: Simulationskern

## Explizite Runge-Kutta-Verfahren (Euler, Heun, RK4) {#runge_kutta}

### Ziel und Zweck
Numerische Lösung der Bewegungsgleichungen $\dot{\mathbf{x}} = f(t, \mathbf{x}, \mathbf{u})$ bei während eines Reglerschritts konstanter Stellgröße $\mathbf{u}$.

### Theorie
Klassisches Runge-Kutta-Verfahren vierter Ordnung mit Schrittweite $h$:

$$k_1 = f(t, x), \quad k_2 = f(t + \tfrac{h}{2}, x + \tfrac{h}{2} k_1), \quad k_3 = f(t + \tfrac{h}{2}, x + \tfrac{h}{2} k_2), \quad k_4 = f(t + h, x + h k_3)$$

$$x(t + h) \approx x + \frac{h}{6}\left(k_1 + 2 k_2 + 2 k_3 + k_4\right)$$

Euler: $x + h f(t, x)$ (Ordnung 1). Heun: $x + \frac{h}{2}(k_1 + f(t + h, x + h k_1))$ (Ordnung 2). Der adaptive Löser nutzt `scipy.integrate.solve_ivp` (RK45, rtol $10^{-6}$, atol $10^{-8}$) über jeden Reglerschritt.

### Herleitung
Die Koeffizienten folgen aus dem Abgleich der Taylor-Reihe der exakten Lösung mit der des Verfahrens bis zur Ordnung $p$. Für RK4 sind die Ordnungsbedingungen bis $p = 4$ erfüllt; der lokale Fehler ist $O(h^5)$, der globale $O(h^4)$.

### Annahmen
- $f$ hinreichend glatt (die Modelle glätten Unstetigkeiten mit $\tanh$).
- Stellgrößen während des Reglerschritts konstant (Halteglied nullter Ordnung).

### Randbedingungen
Explizite Verfahren sind nur stabil, wenn $h \lambda$ für alle Eigenwerte $\lambda$ der Jacobi-Matrix im Stabilitätsgebiet liegt (siehe [Teilschritte](#stable_substeps)).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $h$ | interne Schrittweite | s | `h` |
| $k_1 \dots k_4$ | Stufen | – | `k1` … `k4` |
| $n$ | Teilschritte je Reglerschritt | – | `substeps` |

### Anwendungsgrenzen
Für steife Systeme (Raddrehung bei sehr kleiner Geschwindigkeit) sind sehr kleine Schritte nötig; ein impliziter Löser wäre effizienter.

### Vor- und Nachteile
- Vorteil: RK4 ist einfach, deterministisch und für die nicht steifen Anteile sehr genau.
- Nachteil: keine Fehlerschätzung; die Schrittweite muss vorgegeben werden.

### Numerische Aspekte
Vier Auswertungen von $f$ je Teilschritt. Der adaptive Löser dient als genaue Referenz (Test `test_solvers_agree`).

### Praktische Auswirkungen
Mit 2 ms Modellschritt und RK4 sind die Fehler kleiner als Modellunsicherheiten; Rechenzeit skaliert linear mit der Zahl der Teilschritte.

### In einfachen Worten
Statt die Bewegung exakt auszurechnen, schaut das Verfahren vier Mal kurz nach, wohin sich das Auto bewegt, und mittelt daraus den nächsten kleinen Schritt.

### Quellen
[@hairer1993], [@butcher2016], [@virtanen2020]

## Stabilitätsbegrenzte Teilschritte (stable_dt) {#stable_substeps}

### Ziel und Zweck
Wahl der Modellschrittweite so, dass der explizite RK4 bei der steifen Raddrehdynamik stabil bleibt, ohne bei Autobahntempo unnötig klein zu werden.

### Theorie
Linearisierung der Raddrehgleichung $J \dot\omega = \dots - F_x R$ mit $F_x \approx C_\kappa (\omega R - v)/v$ ergibt den Eigenwert

$$\lambda_{slip} = -\frac{C_{\kappa,max} R^2}{J\, \max(v, v_{min})}, \qquad \lambda_{brake} = -\frac{T_{B,max}}{\omega_s J}$$

Das Mehrkörpermodell ergänzt $\lambda_{D} = c_{D,max}/m_u$ und $\lambda_{hop} = \sqrt{(k + k_t)/m_u}$. Die Schrittweite und die Zahl der Teilschritte sind

$$h \le \frac{2}{\max \vert\lambda\vert}, \qquad n = \left\lceil \frac{\Delta t_{control}}{\min(h, h_{rec})} \right\rceil$$

### Herleitung
Für die Testgleichung $\dot y = \lambda y$ liefert RK4 $y_{k+1} = R(h\lambda)\, y_k$ mit $R(z) = 1 + z + z^2/2 + z^3/6 + z^4/24$. Stabilität erfordert $\vert R(z)\vert \le 1$; auf der negativen reellen Achse gilt das bis $z \approx -2.785$, auf der imaginären Achse bis etwa $\vert z\vert \approx 2.83$. Der Code verwendet die konservative Grenze $\vert h\lambda\vert \le 2$. Der Bremsterm $T_B \tanh(\omega/\omega_s)$ hat bei $\omega = 0$ die Steigung $T_B/\omega_s$.

### Annahmen
- Maximale Längssteifigkeit bei doppelter statischer Radlast: $C_{\kappa,max} = 2 C_\kappa F_{z,stat,max}/F_{z0}$.
- Die dominanten Eigenwerte sind näherungsweise entkoppelt.

### Randbedingungen
$v_{min}$ = `slip_speed_floor` = 3 m/s, $h_{rec}$ = `recommended_dt` = 2 ms.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $C_{\kappa,max}$ | maximale Längsschlupfsteifigkeit | N | `long_stiffness_max` |
| $T_{B,max}$ | maximales Bremsmoment | N m | `brake_max` |
| $\omega_s$ | Glättungsdrehzahl Bremse | rad/s | `brake_smoothing` |
| $h$ | stabile Schrittweite | s | `stable_dt()` |
| $n$ | Teilschritte | – | `_substeps()` |

### Anwendungsgrenzen
Die Schätzung gilt für die eingebauten Modelle. Eigene Modelle ohne `stable_dt` laufen mit `recommended_dt` oder `dt_control`.

### Vor- und Nachteile
- Vorteil: automatische, zustandsabhängige Wahl; schnell bei hoher Geschwindigkeit, stabil beim Anfahren und Bremsen.
- Nachteil: konservativ; bei Stillstand sehr viele Teilschritte.

### Numerische Aspekte
Die Schrittweite wird je Reglerschritt neu bestimmt, nicht innerhalb der Teilschritte. Divergenz wird als „numerisch instabil (NaN)“ erkannt und beendet den Lauf.

### Praktische Auswirkungen
ABS-Bremsungen bis in den Stillstand bleiben stabil; die Rechenzeit steigt bei kleinen Geschwindigkeiten deutlich.

### In einfachen Worten
Die sich drehenden Räder reagieren extrem schnell. Damit die Rechnung nicht „explodiert“, macht der Simulator dann entsprechend viele, sehr kleine Zwischenschritte.

### Quellen
[@hairer1996], [@hairer1993]

## Ablauf eines Simulationsschritts {#simulation_loop}

### Ziel und Zweck
Reproduzierbarer, zeitdiskreter Regelkreis wie im Fahrzeug: Regler rechnen im festen Takt, die Strecke kontinuierlich.

### Theorie
Je Reglerschritt $\Delta t$:

1. Querregler: $\delta_{req} = \mathrm{steer}(t, \mathbf{s}, \mathrm{Trajektorie})$
2. Längsregler: $a_{req}$, Längsaktuierung: Antriebs- und Bremsmomente je Rad
3. Lenkaktor: $\delta = \mathrm{Aktor}(\delta_{req}, \kappa_{mess} = r / \max(v_x, 1))$
4. Regelsysteme in fester Reihenfolge: Hinterachslenkung, Torque Vectoring, ESP, ASR, ABS, Wankstabilisierung, Skyhook
5. Integration $\mathbf{x}(t) \to \mathbf{x}(t + \Delta t)$ mit $n$ Teilschritten
6. Ausgangsgrößen, Projektion auf die Referenz, Logging, Abbruchprüfung

### Herleitung
Abtastsystem mit Halteglied nullter Ordnung: Die Stellgrößen werden zu Beginn des Schritts berechnet und während der Integration konstant gehalten. Damit entsteht systematisch eine Verzögerung von einem Reglertakt, wie in realen Steuergeräten.

### Annahmen
Alle Regler sehen den wahren Zustand (keine Sensorik), außer der verzögerten Krümmung im Lenkaktor.

### Randbedingungen
Reihenfolge der Regelsysteme aus `enabled_systems()`; spätere Systeme sehen die Änderungen früherer.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\Delta t$ | Reglertakt | s | `dt`, `dt_control` |
| $\mathbf{s}$ | Fahrzeugzustand (gemeinsame Sicht) | – | `VehicleState` |
| $\mathbf{u}$ | Stellgrößen | – | `ControlInput` |

### Anwendungsgrenzen
Ein einziger Takt für alle Regler; Mehrfachraten und Komponentengraphen bietet die AD-Plattform (`vdsim.runtime`).

### Vor- und Nachteile
- Vorteil: deterministisch, einfach nachvollziehbar, alle Signale werden protokolliert.
- Nachteil: Reihenfolge der Regelsysteme ist fest verdrahtet.

### Numerische Aspekte
Die Ausgangsgrößen werden nach der Integration mit einem zusätzlichen Aufruf `derivatives(..., with_outputs=True)` berechnet.

### Praktische Auswirkungen
Latenzen und Takte lassen sich realistisch studieren; Ergebnisse sind bitgenau reproduzierbar.

### In einfachen Worten
Alle zehn Millisekunden schauen die Regler auf das Auto und entscheiden, wie gelenkt, gebremst und beschleunigt wird. Dazwischen rechnet der Simulator die Bewegung des Autos fein aus.

### Quellen
[@hairer1993]

## Fahrbahnprofil nach ISO 8608 {#iso8608_road_profile}

### Ziel und Zweck
Stochastische Fahrbahnunebenheit einer genormten Straßenklasse als Anregung für Komfort- und Radlastuntersuchungen.

### Theorie
Leistungsdichte der Höhe über der Wegkreisfrequenz $n$ (Zyklen/m):

$$G_d(n) = G_d(n_0) \left(\frac{n}{n_0}\right)^{-2}, \qquad n_0 = 0.1\ \mathrm{m^{-1}}$$

Realisierung als Summe harmonischer Anteile mit zufälligen Phasen $\varphi_k$:

$$z(x) = \sum_k \sqrt{2 G_d(n_k) \Delta n} \cos\left(2\pi n_k x + \varphi_k\right)$$

mit $n_k$ von 0,011 bis 2,83 m⁻¹ in Schritten $\Delta n = 0.01$ m⁻¹ und $G_d(n_0) = 16, 64, 256, 1024, 4096 \cdot 10^{-6}\ \mathrm{m^3}$ für die Klassen A bis E.

### Herleitung
Die Varianz eines Kosinus mit Amplitude $a$ ist $a^2/2$; damit die Summe die Leistungsdichte $G_d$ trifft, muss $a_k^2/2 = G_d(n_k) \Delta n$ gelten.

### Annahmen
Stationäres, ergodisches, gaußsches Profil; die Werte $G_d(n_0)$ sind die geometrischen Klassenmitten der Norm. Gleiches Profil für linke und rechte Spur.

### Randbedingungen
Diskretisierung des Profils mit $\Delta x$ = 5 cm, lineare Interpolation; Länge `length` (Standard 2000 m), Zufallsstartwert `seed`.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $G_d(n_0)$ | Unebenheitsdichte bei $n_0$ | m³ | `gd_n0` |
| $n_k$ | Wegkreisfrequenzen | 1/m | `n` |
| $\varphi_k$ | Zufallsphasen | rad | `phase` |
| $z(x)$ | Fahrbahnhöhe | m | `RoadProfile.height()` |

### Anwendungsgrenzen
Wellenlängen zwischen etwa 0,35 m und 90 m; Klassen F–H der Norm sind nicht vorgesehen.

### Vor- und Nachteile
- Vorteil: reproduzierbar (Seed), normkonform, beliebig lang.
- Nachteil: keine Korrelation zwischen linker und rechter Spur.

### Numerische Aspekte
Vektorisierte Summe über rund 280 Frequenzen; einmalig bei der Erzeugung.

### Praktische Auswirkungen
Grundlage der Komfort-KPIs (ISO 2631) im Szenario „Komfort auf Straßenklasse C“.

### In einfachen Worten
Eine künstliche Straße mit Unebenheiten, die statistisch so rau ist wie eine echte Straße einer bestimmten Güteklasse.

### Quellen
[@iso8608]
