# Theorie: Auswertung

## Komfortbewertung nach ISO 2631-1 {#iso2631_comfort}

### Ziel und Zweck
Bewertung der Ganzkörperschwingungen über einen frequenzbewerteten Effektivwert der Vertikalbeschleunigung.

### Theorie
Bewertungsfilter $W_k(s) = H_h(s)\, H_t(s)\, H_s(s)$ (Hochpass, Beschleunigungs-Geschwindigkeits-Übergang, Stufe):

$$H_h = \frac{s^2}{s^2 + \frac{\omega_1}{Q_1} s + \omega_1^2}, \qquad H_t = \frac{(1 + s/\omega_3)\, \omega_4^2}{s^2 + \frac{\omega_4}{Q_4} s + \omega_4^2}, \qquad H_s = \frac{s^2 + \frac{\omega_5}{Q_5} s + \omega_5^2}{s^2 + \frac{\omega_6}{Q_6} s + \omega_6^2}$$

mit $f_1$ = 0,4 Hz, $f_3 = f_4$ = 12,5 Hz, $f_5$ = 2,37 Hz, $f_6$ = 3,35 Hz, $Q_1 = 1/\sqrt{2}$, $Q_4$ = 0,63, $Q_5 = Q_6$ = 0,91. Bewerteter Effektivwert:

$$a_w = \sqrt{\frac{1}{T}\int_0^T a_{z,w}^2(t)\, \mathrm{d}t}$$

Komfortstufen: $< 0.315$ nicht unkomfortabel, $< 0.63$ etwas, $< 1$ ziemlich, $< 1.6$ unkomfortabel, $< 2.5$ sehr unkomfortabel, sonst extrem unkomfortabel (m/s²).

### Herleitung
Die Filterkoeffizienten sind die der Norm. Die analoge Übertragungsfunktion wird mit der bilinearen Transformation (`scipy.signal.bilinear`) in ein digitales Filter überführt und auf das mittelwertfreie Signal angewendet.

### Annahmen
Sitzende Person, vertikale Richtung, Aufbauschwerpunkt als Messort.

### Randbedingungen
Mindestens 50 Abtastwerte; nur Modelle mit Vertikaldynamik (`body_az`, Mehrkörpermodell).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $a_w$ | bewerteter Effektivwert | m/s² | `iso2631_aw` |
| $f_i, Q_i$ | Filtereckfrequenzen und Güten | Hz, – | `w1` … `w6`, `q1` … `q6` |
| $a_z$ | Vertikalbeschleunigung des Aufbaus | m/s² | `body_az` |

### Anwendungsgrenzen
Bandbegrenzung bei 100 Hz ($f_2$) fehlt; keine Sitzübertragung, keine Mehrachsen-Gesamtbewertung, kein Crest-Faktor/VDV.

### Vor- und Nachteile
- Vorteil: normnah, eine verständliche Zahl.
- Nachteil: Effektivwert unterbewertet einzelne Stöße.

### Numerische Aspekte
Die bilineare Transformation verzerrt Frequenzen nahe der Nyquist-Frequenz; bei 100 Hz Abtastung ist der relevante Bereich bis etwa 20 Hz unkritisch.

### Praktische Auswirkungen
KPIs „Bewertete Vertikalbeschl. a_w“ und „Komfortbewertung“ im Szenario „Komfort auf Straßenklasse C“.

### In einfachen Worten
Schwingungen werden so gewichtet, wie Menschen sie spüren (am stärksten um 4–8 Hz), und zu einer Zahl zusammengefasst.

### Quellen
[@iso2631_1]

## Kennwerte der Normversuche {#iso_test_kpis}

### Ziel und Zweck
Objektive Bewertung der genormten Fahrmanöver.

### Theorie
- ISO 3888-1/-2: Gassenverletzungen der Fahrzeugecken; bestanden, wenn keine Verletzung und $\vert\beta\vert < 15°$.
- ISO 4138 (Kreisfahrt, Lenkrampe): Eigenlenkgradient als Steigung der Regression $\vert\delta\vert - l\, r/v$ über $\vert a_y\vert$ im Bereich 1–4 m/s².
- ISO 7401 (Lenkwinkelsprung): stationäre Gier- und Querbeschleunigungsverstärkung, Ansprechzeit $t_{90,r} - t_{50,\delta}$, Zeit bis zum Gierratenmaximum, Überschwingen.
- FMVSS 126 (Sinus mit Haltezeit): Gierrate 1,0 s nach Lenkende $\le 35\,\%$ und 1,75 s nach Lenkende $\le 20\,\%$ des Maximums, Querversatz 1,07 s nach Lenkbeginn $\ge 1.83$ m.
- Bremsen: Bremsweg und mittlere Vollverzögerung

$$MFDD = \frac{v_b^2 - v_e^2}{2 (s_e - s_b)}, \qquad v_b = 0.8\, v_0, \quad v_e = 0.1\, v_0$$

### Herleitung
Definitionen der jeweiligen Norm; der Eigenlenkgradient folgt aus $\delta = l/R + EG\, a_y$ mit $l/R = l r/v$.

### Annahmen
Manöver laut Metadaten korrekt gefahren; ISO 7401 mit Lenkrampe ~0,15 s.

### Randbedingungen
Mindestens 20 Punkte im Regressionsbereich (ISO 4138); stationäre Werte aus der letzten Sekunde (ISO 7401).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $EG$ | gemessener Eigenlenkgradient | °/(m/s²) | `understeer_gradient` |
| $t_{50}, t_{90}$ | Zeitpunkte 50 % Lenkwinkel, 90 % Gierrate | s | `t50`, `t90` |
| $MFDD$ | mittlere Vollverzögerung | m/s² | `mfdd` |

### Anwendungsgrenzen
Hauptkriterien ohne vollständige Durchführungsregeln (Toleranzen, Wiederholungen, Fahrerkorrekturen).

### Vor- und Nachteile
- Vorteil: Vergleichbarkeit mit Versuchen.
- Nachteil: Ergebnis hängt von der genauen Manöverdurchführung ab.

### Numerische Aspekte
Zeitpunkte durch erste Überschreitung bzw. Interpolation; Regression per `numpy.polyfit`.

### Praktische Auswirkungen
Bewertung „bestanden/nicht erfüllt“ im KPI-Dashboard und im PDF-Bericht.

### In einfachen Worten
Für jeden genormten Test werden genau die Zahlen berechnet, auf die die Norm schaut, z. B. „wie schnell beruhigt sich das Auto nach dem Lenken“.

### Quellen
[@iso3888_1], [@iso3888_2], [@iso4138], [@iso7401], [@fmvss126], [@unece_r13h], [@iso7975]

## Frequenzgang aus dem Sinus-Sweep {#frequency_response_estimation}

### Ziel und Zweck
Schätzung der Übertragungsfunktion Gierrate/Lenkwinkel aus einem simulierten Versuch (ISO 7401, Sweep).

### Theorie
$$\hat H(f) = \frac{\hat S_{\delta r}(f)}{\hat S_{\delta\delta}(f)}$$

mit Kreuz- und Autoleistungsdichte nach Welch (Segmente von 10 s). Ausgegeben werden Verstärkung bei der kleinsten Frequenz, Resonanzfrequenz, Überhöhung und Verhältnis bei 1 Hz.

### Herleitung
Für ein lineares System mit Eingang $\delta$ und Ausgang $r$ gilt $S_{\delta r} = H\, S_{\delta\delta}$; der Schätzer ist unverzerrt gegenüber Rauschen am Ausgang (H1-Schätzer).

### Annahmen
Näherungsweise lineares, zeitinvariantes Verhalten während des Sweeps.

### Randbedingungen
Auswertung zwischen `f_start` und `f_end` der Manöver-Metadaten; mindestens 3 Frequenzpunkte.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\hat S_{\delta r}$ | Kreuzleistungsdichte | – | `p_xy` |
| $\hat S_{\delta\delta}$ | Autoleistungsdichte | – | `p_xx` |
| $\hat H$ | Frequenzgangschätzung | 1/s | `gain` |

### Anwendungsgrenzen
Im nichtlinearen Bereich (große Amplituden) ist der Frequenzgang amplitudenabhängig.

### Vor- und Nachteile
- Vorteil: robust, Standardverfahren der Messtechnik.
- Nachteil: Frequenzauflösung durch die Segmentlänge begrenzt.

### Numerische Aspekte
`scipy.signal.csd` und `welch` mit Hann-Fenster (Standard).

### Praktische Auswirkungen
Vergleich Simulation gegen lineare Analyse (Bode) im Tab „Analyse“.

### In einfachen Worten
Man lenkt immer schneller hin und her und misst, wie stark und wie verzögert das Auto bei jeder Frequenz antwortet.

### Quellen
[@welch1967], [@iso7401]

## Reibwertausnutzung und Stabilitätsreserve {#friction_utilization}

### Ziel und Zweck
Wie nah ist das Fahrzeug an der Haftgrenze?

### Theorie
$$\eta_i = \frac{\sqrt{F_{x,i}^2 + F_{y,i}^2}}{\max(\mu_i F_{z,i}, 1\ \mathrm{N})}, \qquad \eta_{max} = \max_{t, i} \eta_i, \qquad \mathrm{Reserve} = 1 - \eta_{max}$$

### Herleitung
Verhältnis der übertragenen Horizontalkraft zum Kraftschlusspotenzial am Reibkreis.

### Annahmen
Isotroper Reibkreis; $\mu$ aus Reifen- und Fahrbahnreibwert.

### Randbedingungen
Beim kinematischen Modell (ohne Reifenkräfte) nicht definiert (NaN).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\eta$ | Reibwertausnutzung | – | `max_friction_utilization` |

### Anwendungsgrenzen
Die Magic Formula kann Werte leicht über 1 erzeugen (kombinierter Schlupf).

### Vor- und Nachteile
- Vorteil: anschaulicher Grenzbereichsindikator.
- Nachteil: Maximum über alle Räder verdeckt die Verteilung (Heatmaps zeigen sie).

### Numerische Aspekte
Nenner nach unten begrenzt (abgehobene Räder).

### Praktische Auswirkungen
Bewertung „Hinweis“ ab 95 %; Heatmaps im Tab „Analyse“.

### In einfachen Worten
Zeigt in Prozent, wie viel der verfügbaren Haftung ausgenutzt wird.

### Quellen
[@milliken1995]
