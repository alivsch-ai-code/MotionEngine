# Theorie: Trajektorien

## Pfadkonstruktion aus Krümmungssegmenten {#path_construction}

### Ziel und Zweck
Glatte, fahrbare Referenzpfade aus Geraden, Kreisbögen, Klothoiden und Spurversätzen; Eckenverrundung im Wegpunkt-Editor.

### Theorie
Ein Pfad ist durch seine Krümmung $\kappa(s)$ bestimmt:

$$\psi(s) = \psi_0 + \int_0^s \kappa\, \mathrm{d}\sigma, \qquad x(s) = x_0 + \int_0^s \cos\psi\, \mathrm{d}\sigma, \qquad y(s) = y_0 + \int_0^s \sin\psi\, \mathrm{d}\sigma$$

Segmente: Gerade $\kappa = 0$, Bogen $\kappa = \pm 1/R$, Klothoide $\kappa(s) = \kappa_0 + (\kappa_1 - \kappa_0) s/L$, Versatz um $w$ auf Länge $L$ mit $\kappa(s) = \frac{2\pi w}{L^2} \sin\frac{2\pi s}{L}$. Eine Kurve mit Übergang besteht aus Klothoide – Bogen – Klothoide, die Klothoiden übernehmen den Winkel $L_{Ü}/R$. Eckenverrundung (Fillet) im Editor: Tangentenlänge $R \tan(\Delta\psi/2)$.

### Herleitung
Für den sinusförmigen Versatz ist $\psi(L) = 0$ und $y(L) \approx \int_0^L \psi\, \mathrm{d}s = w$ (kleine Winkel); die maximale Querbeschleunigung bei Geschwindigkeit $v$ ist $2\pi w v^2/L^2$. Bei der Klothoide wächst die Krümmung linear mit dem Weg, deshalb wächst bei konstanter Geschwindigkeit der Lenkwinkel linear mit der Zeit.

### Annahmen
Ebene Fahrbahn; Integration mit der Trapezregel auf einem um den Faktor 8 verfeinerten Raster.

### Randbedingungen
Abtastung `ds` = 0,25 m (Standard); Krümmung am Segmentübergang stetig, wenn Klothoiden verwendet werden.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\kappa(s)$ | Krümmung | 1/m | `kappa`, `fn` |
| $L$ | Segmentlänge | m | `length` |
| $L_{Ü}$ | Übergangslänge | m | `transition` |
| $w$ | Querversatz | m | `lateral` |

### Anwendungsgrenzen
Kleine-Winkel-Näherung des Versatzes: bei großem $w/L$ weicht der tatsächliche Versatz leicht ab.

### Vor- und Nachteile
- Vorteil: Krümmung (und damit Lenkbedarf) wird direkt kontrolliert.
- Nachteil: Endpunkte ergeben sich erst nach der Integration.

### Numerische Aspekte
Integrationsfehler $O(\Delta s^2)$ auf dem feinen Raster; vernachlässigbar.

### Praktische Auswirkungen
Alle Strecken- und Fahrmanöver (Autobahn, Stadt, Kreisfahrt, Notausweichen) nutzen den PathBuilder.

### In einfachen Worten
Statt Punkte zu setzen, sagt man dem Pfad, wie stark er sich wo krümmen soll – wie beim Straßenbau mit Übergangsbögen.

### Quellen
[@mitschke2014]

## GGV-begrenztes Geschwindigkeitsprofil {#ggv_speed_profile}

### Ziel und Zweck
Höchste fahrbare Geschwindigkeit entlang eines Pfads unter Quer- und Längsbeschleunigungsgrenzen.

### Theorie
$$v_{lim}(s) = \min\left(\sqrt{\frac{a_{y,max}}{\vert\kappa\vert}},\ v_{max}\right), \qquad a_{x,verf} = \vert a_{x,lim}\vert \sqrt{1 - \min\left(\left(\frac{v^2 \vert\kappa\vert}{a_{y,max}}\right)^2, 1\right)}$$

Vorwärtsdurchlauf (Beschleunigen) und Rückwärtsdurchlauf (Bremsen):

$$v_{i+1} \le \sqrt{v_i^2 + 2 a_{x,verf}^{+} \Delta s_i}, \qquad v_i \le \sqrt{v_{i+1}^2 + 2 a_{x,verf}^{-} \Delta s_i}$$

Rundenzeit $T = \sum \Delta s_i / \bar v_i$.

### Herleitung
Aus $v^2 = v_0^2 + 2 a \Delta s$ bei konstanter Beschleunigung über $\Delta s$. Die verfügbare Längsbeschleunigung folgt aus der Reibellipse $(a_x/a_{x,lim})^2 + (a_y/a_{y,max})^2 \le 1$ mit $a_y = v^2 \kappa$ (g-g-Diagramm).

### Annahmen
Punktmasse, konstante Grenzen (kein Abtrieb, keine Antriebsleistungsgrenze).

### Randbedingungen
Optionale Start- und Endgeschwindigkeit.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $a_{y,max}$ | maximale Querbeschleunigung | m/s² | `ay_max` |
| $a_{x,lim}^{+}, a_{x,lim}^{-}$ | Längsgrenzen | m/s² | `ax_max`, `ax_min` |
| $v_{max}$ | Höchstgeschwindigkeit | m/s | `v_max` |

### Anwendungsgrenzen
Keine Fahrzeugdynamik (Lastverlagerung, Gierträgheit).

### Vor- und Nachteile
- Vorteil: O(n), robust, Standardverfahren.
- Nachteil: Grenzen müssen vorgegeben werden.

### Numerische Aspekte
Krümmung auf $10^{-9}$ nach unten begrenzt (gerade Abschnitte).

### Praktische Auswirkungen
Sollgeschwindigkeit für Rennstrecke, Autobahn, Stadt und Wegpunkt-Editor.

### In einfachen Worten
In Kurven langsam genug, auf Geraden so schnell wie möglich – und rechtzeitig vor der Kurve bremsen.

### Quellen
[@kapania2016], [@milliken1995]

## Ideallinie mit minimaler Krümmung {#racing_line}

### Ziel und Zweck
Linie innerhalb der Streckenbreite, die die Krümmung minimiert und damit höhere Kurvengeschwindigkeiten erlaubt.

### Theorie
Pfad als Mittellinie plus Querversatz $d_i$ entlang der Normalen $\mathbf{n}_i$: $\mathbf{p}_i = \mathbf{c}_i + d_i \mathbf{n}_i$. Krümmung linearisiert um die aktuelle Linie (Ableitungen $x', y'$ fest):

$$\kappa = \frac{x' y'' - y' x''}{\vert\mathbf{r}'\vert^3} \approx \kappa_c + A\, \mathbf{d}, \qquad \min_{\mathbf{d}} \Vert A \mathbf{d} + \kappa_c\Vert^2, \qquad \vert d_i\vert \le \frac{b}{2} - m$$

Drei Iterationen mit Neulinearisierung; zentrale periodische Differenzen auf 3-m-Raster.

### Herleitung
Mit festen ersten Ableitungen ist die Krümmung linear in den zweiten Ableitungen und damit im Versatz. Die beschränkte Kleinste-Quadrate-Aufgabe ist konvex und wird mit `lsq_linear` gelöst.

### Annahmen
Geschlossener Rundkurs, konstante Breite, Krümmung als Ersatz für die Rundenzeit.

### Randbedingungen
Sicherheitsabstand `margin` = 1 m zum Rand.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $d_i$ | Querversatz zur Mittellinie | m | `offset` |
| $A$ | linearisierte Krümmungsmatrix | 1/m² | `A` |
| $b$ | Streckenbreite | m | `width` |

### Anwendungsgrenzen
Minimale Krümmung ist nicht gleich minimaler Rundenzeit (kürzester Weg wird ignoriert).

### Vor- und Nachteile
- Vorteil: schnell, robust, gute Näherung der Ideallinie.
- Nachteil: keine Fahrzeugdynamik.

### Numerische Aspekte
Dichte Matrizen (n × n mit n ≈ Länge/3 m); für lange Strecken speicherintensiv.

### Praktische Auswirkungen
Manöver „Rennstrecke (Ideallinie)“ mit GGV-Geschwindigkeitsprofil.

### In einfachen Worten
Kurven werden so weit wie möglich „gerade gezogen“: außen anfahren, innen am Scheitelpunkt, außen hinaus.

### Quellen
[@braghin2008]

## Projektion auf die Polylinie {#polyline_projection}

### Ziel und Zweck
Lotfußpunkt, Bogenlänge, Querablage, Kurswinkel und Krümmung der Referenz für jede Fahrzeugposition.

### Theorie
Für das nächstgelegene Segment $[\mathbf{p}_k, \mathbf{p}_{k+1}]$:

$$\tau = \mathrm{clip}\left(\frac{(\mathbf{p} - \mathbf{p}_k)\cdot(\mathbf{p}_{k+1} - \mathbf{p}_k)}{\Vert\mathbf{p}_{k+1} - \mathbf{p}_k\Vert^2}, 0, 1\right), \qquad e = \frac{\Delta x (y - y_F) - \Delta y (x - x_F)}{\Vert\Delta\mathbf{p}\Vert}$$

$s = s_k + \tau \Vert\Delta\mathbf{p}\Vert$; Kurswinkel linear interpoliert. $e > 0$: Fahrzeug links der Bahn.

### Herleitung
Orthogonale Projektion auf eine Strecke; Vorzeichen über das Kreuzprodukt.

### Annahmen
Suche im Fenster ±60 Stützstellen um den letzten Index; globale Suche nur, wenn der lokale Abstand > 3 m und die globale Lösung mindestens 1 m näher ist.

### Randbedingungen
Jeder Aufrufer (Regler, Logger) hat einen eigenen Suchhinweis.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\tau$ | Segmentparameter | – | `tau` |
| $e$ | Querablage | m | `lateral_error` |
| $s$ | Bogenlänge | m | `Projection.s` |

### Anwendungsgrenzen
Kurswinkel und Krümmung sind stückweise linear; für Werling-Planung ist die Hermite-Referenzkurve in vdsim.geometry vorgesehen.

### Vor- und Nachteile
- Vorteil: schnell, eindeutig auf geschlossenen Strecken.
- Nachteil: Ablage hat Knicke an den Stützstellen.

### Numerische Aspekte
Segmentlängen mit $10^{-12}$ nach unten begrenzt.

### Praktische Auswirkungen
Basis aller Bahnregler und der KPIs Bahnabweichung.

### In einfachen Worten
Sucht den Punkt auf der Strecke, der dem Auto am nächsten ist, und misst, wie weit das Auto daneben liegt.

### Quellen
[@deboor2001]

## Import von GPS- und OpenDRIVE-Daten {#trajectory_import}

### Ziel und Zweck
Referenzen aus Messfahrten (GPX, NMEA, CSV mit lat/lon), MATLAB, ROS-Pfaden und Straßenkarten (OpenDRIVE).

### Theorie
Äquirektanguläre Projektion um den ersten Punkt:

$$x = R_E\, (\lambda - \lambda_0) \cos\varphi_0, \qquad y = R_E\, (\varphi - \varphi_0)$$

OpenDRIVE-Geometrien: `line`, `arc` (konstante Krümmung), `spiral` (linear veränderliche Krümmung, numerisch integriert), `poly3` $v(u) = a + b u + c u^2 + d u^3$ und `paramPoly3` im lokalen $(u, v)$-System, gedreht um `hdg`. Fahrstreifenmitte über die Breitenpolynome. Geschwindigkeit aus Zeitstempeln: $v = \Delta s/\Delta t$, zentral gemittelt.

### Herleitung
Lokale Tangentialebene der Kugel: Längengradabstand schrumpft mit $\cos\varphi$.

### Annahmen
Kugelerde mit $R_E$ = 6 371 km; Ausdehnung wenige Kilometer.

### Randbedingungen
Zeitstempel streng monoton für die Geschwindigkeitsberechnung.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\varphi, \lambda$ | Breite, Länge | rad | `lat`, `lon` |
| $R_E$ | Erdradius | m | `EARTH_RADIUS` |

### Anwendungsgrenzen
Fehler wachsen mit der Entfernung vom Bezugspunkt; Höhen werden ignoriert.

### Vor- und Nachteile
- Vorteil: keine Geodäsie-Bibliothek nötig.
- Nachteil: keine UTM-/Ellipsoid-Genauigkeit.

### Numerische Aspekte
Spiralen mit 8-fach verfeinertem Raster integriert.

### Praktische Auswirkungen
Beispieldateien in `configs/trajectories/` für alle Formate.

### In einfachen Worten
GPS-Koordinaten werden auf eine flache Karte in Metern umgerechnet; Straßenkarten werden Stück für Stück in eine Linie übersetzt.

### Quellen
[@asam_opendrive]
