# Trajektorienplanung nach Werling – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


Übernommen aus [vdsim/planning/docs/theory.md](../../../vdsim/planning/docs/theory.md).

Grundlage ist Werling (2011), Kap. 2–3 und Anhang A. Die Abschnitte folgen dem Algorithmus aus 3.5.5. Die Anker entsprechen den `concept`-IDs der `@trace`-Markierungen im Code.

## Quintische Optimalpolynome {#quintic_polynomial}

### Ziel und Zweck
Ruckoptimale Bewegung $\xi_1(t)$ (Querablage $d$ oder Längsposition $s$) zwischen festem Anfangs- und Endzustand.

### Theorie
Die Integratorkette $\dot\xi = A\xi + b\,u$ mit $u = \dddot\xi_1$ (3.3) und den Kosten $J = \int_0^\tau \frac{1}{2}u^2\,dt + h(\xi(\tau),\tau)$ (3.4) hat bei festem Endzustand quintische Polynome als Lösung (Satz 1):
$$\xi_1(t) = c_0 + c_1 t + c_2 t^2 + c_3 t^3 + c_4 t^4 + c_5 t^5$$
$$c_{012} = M_1(0)^{-1}\xi(0),\quad c_{345} = M_2(\tau)^{-1}[\xi(\tau) - M_1(\tau)c_{012}]\quad (3.8)$$

### Herleitung
Mit der Lagrangefunktion $L = \frac{1}{2}u^2 + \sum_i \psi_i(\dot\xi_i - f_i)$ liefert $\partial L/\partial u = 0$ den Zusammenhang $u = \psi_3$. Die Euler-Lagrange-Gleichungen (3.5) ergeben $\psi_1 = $ konst., also ist $\psi_3$ quadratisch in $t$ und $\xi_1$ ein Polynom fünften Grades (3.6). Die sechs Koeffizienten folgen aus den sechs Randbedingungen. Mit $\Delta p$, $\Delta v$, $\Delta a$ als Abweichungen des Endzustands von der Extrapolation des Anfangszustands gilt geschlossen:
$$c_3 = (10\Delta p - 4\Delta v\,\tau + \frac{1}{2}\Delta a\,\tau^2)/\tau^3$$
$$c_4 = (-15\Delta p + 7\Delta v\,\tau - \Delta a\,\tau^2)/\tau^4$$
$$c_5 = (6\Delta p - 3\Delta v\,\tau + \frac{1}{2}\Delta a\,\tau^2)/\tau^5$$

### Annahmen
Der Eingang ist unbeschränkt (freies Problem). Die Bewegung wird als Integratorkette in Frenet-Koordinaten modelliert.

### Randbedingungen
$\tau > 0$; der Anfangszustand ist stetig bis zur Beschleunigung.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\xi_1,\xi_2,\xi_3$ | Position, Geschwindigkeit, Beschleunigung | m, m/s, m/s² | `x0, v0, a0` |
| $\tau$ | Endzeit relativ zum Start | s | `tau` |
| $c_0 \dots c_5$ | Koeffizienten | – | `coeffs` |

### Anwendungsgrenzen
Für sehr kleine $\tau$ werden die Koeffizienten numerisch extrem ($\tau^{-5}$). Solche Kandidaten sortiert der Vorfilter aus.

### Vor- und Nachteile
Die Lösung ist geschlossen, schnell und exakt. Die Funktionenklasse ist aber auf etwa eine doppelte Kursänderung beschränkt.

### Numerische Aspekte
Die Formeln sind vektorisiert für alle $(\delta_i,\tau_j)$. Die Auswertung nutzt das Horner-Schema.

### Praktische Auswirkungen
Tausende Kandidaten lassen sich in Millisekunden berechnen.

### In einfachen Worten
Zwischen zwei Bewegungszuständen gibt es genau eine „sanfteste“ Verbindung. Sie lässt sich mit einer einfachen Formel ausrechnen.

### Quellen
[[Werling (2011, Abschn. 3.4, Satz 1, (3.3)–(3.8))](../references.md#werling2011)], [[Werling et al. (2010)](../references.md#werling2010icra)]

## Quartische Optimalpolynome {#quartic_polynomial}

### Ziel und Zweck
Optimale Geschwindigkeitswechsel ohne vorgegebene Endposition (Geschwindigkeithalten).

### Theorie
Ist die Endposition frei und hängen die Endkosten nicht von $\xi_1$ ab, so gilt die Transversalitätsbedingung $\psi_1 = -\partial h/\partial\xi_1 = 0$. Damit ist $c_5 = 0$ (Satz 2), und es gilt $c_{34} = q_{34}(\xi_2(\tau),\xi_3(\tau))$.

### Herleitung
Aus $3c_3\tau^2 + 4c_4\tau^3 = \Delta v$ und $6c_3\tau + 12c_4\tau^2 = \Delta a$ folgen:
$$c_3 = (3\Delta v - \Delta a\,\tau)/(3\tau^2),\quad c_4 = (-2\Delta v + \Delta a\,\tau)/(4\tau^3)$$

### Annahmen
Die Endkosten sind unabhängig von der Endposition.

### Randbedingungen
$\tau > 0$, Endgeschwindigkeit $\geq 0$.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\dot s_{ref}+\nu$ | Endgeschwindigkeit | m/s | `target.v_ref + offset` |

### Anwendungsgrenzen
Nur für den Modus Geschwindigkeithalten.

### Vor- und Nachteile
Ein Freiheitsgrad weniger als beim quintischen Polynom, daher kleinere Kandidatensätze. Eine Position lässt sich damit nicht vorgeben.

### Numerische Aspekte
Nach $\tau$ setzt sich die Lösung mit konstanter Geschwindigkeit fort (`continuation="velocity"`).

### Praktische Auswirkungen
Ein Geschwindigkeitswechsel dauert unabhängig von der Ausgangsgeschwindigkeit gleich lang (Geschwindigkeitsinvarianz, 3.6).

### In einfachen Worten
Wenn nur die Zielgeschwindigkeit zählt und nicht der genaue Ort, genügt eine etwas einfachere Kurve.

### Quellen
[[Werling (2011, Abschn. 3.4, Satz 2)](../references.md#werling2011)]

## Ruckintegral in geschlossener Form {#jerk_integral}

### Ziel und Zweck
Kosten (3.4) ohne numerische Integration (Algorithmus-Schritt 3).

### Theorie
$$\int_0^\tau (6c_3 + 24c_4 t + 60c_5 t^2)^2 dt = 36c_3^2\tau + 144c_3c_4\tau^2 + (192c_4^2 + 240c_3c_5)\tau^3 + 720c_4c_5\tau^4 + 720c_5^2\tau^5$$

### Herleitung
Man quadriert das Polynom zweiten Grades und integriert gliedweise.

### Annahmen
Polynomdarstellung bis höchstens fünften Grades.

### Randbedingungen
Integration nur über $[0,\tau]$; auf der Mannigfaltigkeit ist der Ruck null.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $J_{jerk}$ | $\int u^2 dt$ (ohne Faktor ½) | m²/s⁵ | `jerk_integral()` |

### Anwendungsgrenzen
Im d(s)-Modus ist es ein Integral über die Bogenlänge mit der Einheit m⁻³.

### Vor- und Nachteile
Exakt und $O(1)$ je Kandidat.

### Numerische Aspekte
Der Test vergleicht gegen die Trapezregel mit relativem Fehler $<10^{-6}$.

### Praktische Auswirkungen
Die Kosten aller Kandidaten liegen vor der Rücktransformation fest. Das ist die Voraussetzung für die lazy Prüfung.

### In einfachen Worten
Wie „ruckelig“ eine Bewegung ist, lässt sich direkt ausrechnen, ohne sie Schritt für Schritt nachzusimulieren.

### Quellen
[[Werling (2011, Abschn. 3.5.5, Schritt 3)](../references.md#werling2011)]

## Zielmannigfaltigkeit und Endkosten {#continuous_manifold}

### Ziel und Zweck
Endzeit und Endposition so wählen, dass das Fahrzeug zügig, aber komfortabel auf eine Referenzbewegung $\xi_{ref}(t)$ einschwenkt.

### Theorie
Die Zielmannigfaltigkeit (3.9) lautet $\xi_2(\tau)=\dot\xi_{ref}(\tau)$, $\xi_3(\tau)=\ddot\xi_{ref}(\tau)$, mit den Endkosten (3.10):
$$h = k_\tau\tau + \frac{1}{2}k_{\xi_1}[\xi_1(\tau)-\xi_{ref}(\tau)]^2$$
Aus der Transversalität folgen $\xi_1(\tau)-\xi_{ref}(\tau) = -\frac{120}{k_{\xi_1}}c_5$ (3.11) und die kontinuierliche Lösung
$$c_{345} = M_3(\tau)^{-1}[\xi_{ref}(\tau) - M_1(\tau)c_{012}]\quad (3.12)$$
Dabei ist $M_3$ gleich $M_2$, ergänzt um $120/k_{\xi_1}$ in der $c_5$-Spalte der ersten Zeile. Die optimale Endzeit erfüllt
$$-\frac{1}{2}\psi_3^2 - \psi_1\dot\xi_{ref} - \psi_2\ddot\xi_{ref} + k_\tau = 0\quad (3.13)$$

### Herleitung
Die Transversalitätsbedingung $(\partial h/\partial\xi)_\tau + \psi(\tau) - (\partial z/\partial\xi)^T\mu = 0$ liefert nur in der ersten Zeile neue Information (3.11). Die Hamilton-Bedingung für die freie Endzeit ergibt (3.13). Die $\psi_i$ folgen aus (3.6).

### Annahmen
$k_\tau, k_{\xi_1} > 0$.

### Randbedingungen
(3.13) ist nur notwendig. `optimal_end_time()` sucht daher das globale Minimum auf einem Raster und verfeinert es mit dem Goldenen Schnitt.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $k_\tau$ | Gewicht Endzeit | 1/s | `cost.terminal_time.k_tau_*` |
| $k_\delta, k_\sigma, k_\nu$ | Gewichte Endabweichung | 1/m², s²/m² | `cost.terminal_deviation.*` |

### Anwendungsgrenzen
(3.13) ist für allgemeine $\xi_{ref}$ nicht geschlossen lösbar. Der Planer verwendet daher die diskretisierte Mannigfaltigkeit, `analysis` die kontinuierliche Lösung.

### Vor- und Nachteile
Die Kompromissbildung aus Schnelligkeit und Komfort wird über zwei intuitive Gewichte eingestellt.

### Numerische Aspekte
Der Test bestätigt (3.11) und das Residuum von (3.13) im Optimum.

### Praktische Auswirkungen
Kleines $k_\tau$ führt zu langsamen Manövern, großes $k_\tau$ zu schnellen.

### In einfachen Worten
Das Ziel ist kein Punkt, sondern „irgendwann sauber auf der Spur bzw. auf Sollgeschwindigkeit“. Wann genau, ergibt sich aus der Abwägung zwischen Zeit und Komfort.

### Quellen
[[Werling (2011, Abschn. 3.4.1, (3.9)–(3.13))](../references.md#werling2011)], [[Bryson und Ho (1975)](../references.md#bryson1975)]

## Abschätzung des Sampling-Horizonts {#sampling_horizon}

### Ziel und Zweck
Bemerkung 1: Prüfen, ob $\tau_{max}$ lang genug ist, damit Satz 3 gilt.

### Theorie
Für repräsentative Manöver (Spurwechsel 3.5 m, Positionsänderung 8 m, Geschwindigkeitsänderung 10 m/s) wird die kontinuierlich optimale Endzeit $\tau^*$ aus (3.12)/(3.13) bestimmt. Empfohlen wird $\tau_{max} \geq 1.2\,\tau^*$.

### Herleitung
Für den Geschwindigkeitswechsel gilt $\frac{1}{2}\int u^2 = 6\Delta v^2/\tau^3$. Das Minimum von $6\Delta v^2/\tau^3 + k_\tau\tau$ wird numerisch bestimmt.

### Annahmen
Ruhe-zu-Ruhe-Manöver als Worst Case.

### Randbedingungen
Die Gewichte sind aus der Konfiguration übernommen.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\tau^*$ | optimale Endzeit | s | `estimate_sampling_horizon()["tau_opt"]` |

### Anwendungsgrenzen
Heuristische Wahl der Repräsentanten.

### Vor- und Nachteile
Die Prüfung ist günstig und erkennt Fehlparametrierung beim `reset()`.

### Numerische Aspekte
Rasterabtastung mit Goldenem Schnitt.

### Praktische Auswirkungen
Bei zu kurzem Horizont gibt `config_report["warnings"]` eine Warnung aus.

### In einfachen Worten
Man prüft vorab, ob der Planer weit genug in die Zukunft schaut, um seine eigene beste Lösung überhaupt zu kennen.

### Quellen
[[Werling (2011, Abschn. 3.4.2, Bemerkung 1)](../references.md#werling2011)]

## Einrasten auf der Referenz {#lock_in}

### Ziel und Zweck
Bemerkung 2: Vermeiden, dass das Fahrzeug dauerhaft parallel zur Referenz fährt.

### Theorie
Für $\xi_2(0)=\xi_3(0)=0$ und eine konstante Referenz bleibt im kontinuierlichen Optimum der Restabstand
$$\xi_1(\tau)-\xi_{ref} = \frac{\xi_1(0)-\xi_{ref}}{1+\frac{1}{720}\tau^5 k_{\xi_1}}\quad (3.14)$$
Im diskreten Satz wird geprüft, ob von jedem Rasterversatz $\delta_i \ne 0$ aus eine Bewegung näher an die Referenz billiger ist als das Verharren:
$$\min_{k,j}[\frac{360(\delta_i-\delta_k)^2}{\tau_j^5} + k_\tau\tau_j + \frac{1}{2}k_\delta\delta_k^2] < \frac{1}{2}k_\delta\delta_i^2 + k_\tau\tau_{min}$$

### Herleitung
Eingesetzt in (3.11) ergibt die letzte Komponente von (3.12) die Formel (3.14). Der Ruck eines Ruhe-zu-Ruhe-Quintikpolynoms ist $\int u^2 = 720\Delta^2/\tau^5$. Die Formel im extrahierten Text hat das Vorzeichen von $\xi_{ref}(0)$ falsch; umgesetzt ist $\xi_1(0)-\xi_{ref}$.

### Annahmen
Stillstand auf der Mannigfaltigkeit. Das Verharren kostet nur $k_\tau\tau_{min}$.

### Randbedingungen
Die Prüfung erfolgt für d(t), d(s), s(t) und ṡ(t) (quartisch: $6\Delta v^2/\tau^3$).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\delta_i$ | Rasterversatz | m | `sampling.lat_d_step` |
| – | einrastgefährdete Versätze | m | `lock_in_check()[...]["locked_offsets"]` |

### Anwendungsgrenzen
Die Prüfung ist konservativ, weil das Verharren mit $\tau_{min}$ angesetzt wird.

### Vor- und Nachteile
Die Prüfung findet Fehlparametrierungen, bevor sie im Fahrversuch auffallen.

### Numerische Aspekte
Es wird das gesamte Raster durchsucht. Das ist günstig, weil es nur einmal je `reset()` geschieht.

### Praktische Auswirkungen
Standardwerte: $k_\delta=200$, $k_\tau=5$ bei $\Delta\delta = 0.5$ m (nötig: $k_\delta > 102$). `sporty.json` wurde damit korrigiert.

### In einfachen Worten
Sind die Gewichte ungünstig, lohnt sich die letzte kleine Korrektur zur Spurmitte nie, und das Auto fährt etwas versetzt weiter. Die Prüfung warnt davor.

### Quellen
[[Werling (2011, Abschn. 3.4.2, Bemerkung 2, (3.14))](../references.md#werling2011)]

## Absolutes Endzeitraster {#absolute_time_grid}

### Ziel und Zweck
Diskretisierung der Zielmannigfaltigkeit, sodass der Rest der alten Optimaltrajektorie im nächsten Zyklus wieder im Satz liegt.

### Theorie
$T_k = k\,\Delta\tau$ und $\tau_j = T_k - t_0$, mit $\tau_{min}\leq\tau_j\leq\tau_{max}$. Die Endversätze $\delta_i,\sigma_i,\nu_i$ sind relativ zur Referenz. Im d(s)-Modus gilt analog $S_k = k\,\Delta s$.

### Herleitung
Wird der Start um $\Delta t$ verschoben, bleibt die Menge der absoluten Endzeiten gleich. Die Endkosten $k_\tau\tau_j$ ändern sich für alle Kandidaten um dieselbe Konstante.

### Annahmen
Der Startzustand liegt exakt auf der alten Trajektorie.

### Randbedingungen
Absinken des kleinsten $\tau$: Liegt die alte Endzeit $T_{k^*}$ weniger als $\tau_{min}$ in der Zukunft, wird sie dennoch in den Satz aufgenommen (`keep_k`). Nach Erreichen der Mannigfaltigkeit setzt sich die Trajektorie auf ihr fort.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\Delta\tau$ | Rasterabstand | s | `sampling.lat_tau_step`, `lon_tau_step` |
| $k^*$ | Rasterindex des Optimums | – | `TrajectoryPlan.lat_k`, `lon_k` |

### Anwendungsgrenzen
Die Konsistenz bleibt nur bei gleicher Referenzkurve und gleichem Quermodus erhalten.

### Vor- und Nachteile
Die Erweiterung kostet nichts und bringt große Wirkung. Die Zahl der $\tau_j$ schwankt um ±1.

### Numerische Aspekte
Die Indizes werden ganzzahlig verglichen, Gleitkommavergleiche entfallen.

### Praktische Auswirkungen
Die Bahn ist unabhängig von der Planungsperiode (Test `test_cycle_time_independence`).

### In einfachen Worten
Die Ankunftszeiten werden nach der Uhr gewählt, nicht relativ zu „jetzt“. So findet der Planer seinen alten Plan im nächsten Takt wieder.

### Quellen
[[Werling (2011, Abschn. 3.4.2, Satz 3)](../references.md#werling2011)]

## Zeitliche Konsistenz (Bellman-Prinzip) {#bellman_principle}

### Ziel und Zweck
Bei zyklischer Neuplanung soll sich die verbleibende Trajektorie nur verkürzen, nicht verändern.

### Theorie
Optimierungsheuristik (3.2): Gewählt wird die beste Lösung in der Funktionenklasse der unrestringierten Optimallösung, die die Restriktionen einhält. Bei inaktiven Restriktionen ist das die Lösung des freien Problems mit diskretisierter Mannigfaltigkeit, und die gilt das Bellman-Prinzip.

### Herleitung
Angenommen, ab $x(t_1)$ gäbe es einen billigeren Kandidaten. Dann wäre die Verkettung aus dem alten Stück auf $[t_0,t_1]$ und diesem Kandidaten billiger als das alte Optimum, und das quintische Polynom zum gleichen Endpunkt wäre noch billiger. Das widerspricht der Optimalität. Voraussetzung ist, dass der Endpunkt schon im alten Satz lag (ausreichender Horizont).

### Annahmen
Die Restriktionen sind inaktiv, und nur konsistente Kostenterme sind aktiv. Der Startzustand wird exakt aus den Polynomen ausgewertet (`TrajectoryPlan`). Bei Folgen und Einfädeln ist die Prädiktion korrekt.

### Randbedingungen
Zusammensetzung der Ausgabe: alte Trajektorie auf $[t, t_0+t_{comp}]$, danach die neue.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $t_{comp}$ | konservative Rechenzeit | s | `timing.t_comp` |

### Anwendungsgrenzen
Aktive Restriktionen, Änderungen der Referenzkurve, Reinitialisierung und Zusatzkostenterme brechen die Konsistenz.

### Vor- und Nachteile
Die Planung ist stabil, weil die Trajektorie nicht aufschaukeln kann. Geprüft wird die tatsächlich gefahrene Trajektorie. Dafür muss die Kostenfunktion zur Funktionenklasse passen.

### Numerische Aspekte
Der gemessene Konsistenzfehler liegt bei etwa $10^{-14}$ m.

### Praktische Auswirkungen
Die Trajektorienregelung kann sich auf eine unveränderliche Solltrajektorie verlassen (Low-level-Stabilisierung).

### In einfachen Worten
Wer immer wieder neu plant, soll nicht ständig seine Meinung ändern. Ist der alte Plan noch gut, wird er einfach weitergeführt.

### Quellen
[[Werling (2011, Abschn. 3.2, 3.4.2, 3.5.5 Schritt 1)](../references.md#werling2011)], [[Bellman (1957)](../references.md#bellman1957)]

## Frenet-Transformation {#frenet_transformation}

### Ziel und Zweck
Umrechnung von $[s,\dot s,\ddot s,d,d',d'']$ in $[x,y,\theta,\kappa,v,a]$ ohne numerische Differentiation.

### Theorie
$$\dot s(1-\kappa_r d) = v\cos\Delta\theta,\quad d' = (1-\kappa_r d)\tan\Delta\theta\quad (A.1),(A.3)$$
$\kappa$ folgt aus (A.5), $a$ aus (A.6). Für d(t) gelten $d' = \dot d/\dot s$ und $d'' = (\ddot d - \ddot s d')/\dot s^2$ (A.7), (A.8).

### Herleitung
Die Herleitung folgt der invarianten Fehlerdynamik mit $e_t \equiv 0$ (Anh. A.1). Umgesetzt ist sie in `ReferenceLine.to_cartesian`.

### Annahmen
$|\Delta\theta| < \pi/2$, $1-\kappa_r d > 0$, die Referenzkurve hat ein stetiges $\kappa_r'$ (Bemerkung 4).

### Randbedingungen
Im d(t)-Modus ist $\dot s \to 0$ singulär. Abgesichert wird mit $\dot s \geq 0.05$ m/s; die Kandidaten werden dann über die Krümmungsrestriktion verworfen.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\kappa_r, \kappa_r'$ | Krümmung der Referenz | 1/m, 1/m² | `ReferenceLine.kappa, dkappa` |
| $\Delta\theta$ | Winkel zur Referenz | rad | `heading_error` |

### Anwendungsgrenzen
Große Differenzwinkel (z. B. Einparken) sind nicht abgedeckt.

### Vor- und Nachteile
Exakt und vektorisiert. Bei langer Referenzkurve ist die Projektion aufwendig.

### Numerische Aspekte
Die Referenz wird je Längssatz nur einmal ausgewertet, $\theta_r,\kappa_r$ werden zwischengespeichert. dκ/dℓ wird aus der exakten Zeitableitung von κ berechnet, im d(s)-Modus geometrisch.

### Praktische Auswirkungen
Krümmung und Beschleunigung sind glatt, wenn die Referenzkurve es ist.

### In einfachen Worten
Geplant wird „relativ zur Straße“. Diese Formeln rechnen das in echte Positionen, Lenkkrümmungen und Beschleunigungen um.

### Quellen
[[Werling (2011, Anh. A.1, (A.1)–(A.8))](../references.md#werling2011)]

## Querkandidaten d(t) und d(s) {#lateral_sampling}

### Ziel und Zweck
Fächer der Querbewegungen zur Referenzkurve, z. B. für Spurhalten, Spurwechsel und Ausweichen.

### Theorie
Tab. 3.1: $\delta_i\times\tau_j$ mit $q_{345}(d_{ref}+\delta_i,0,0,\tau_j)$ und den Kosten $k_\tau\tau_j + \frac{1}{2}k_\delta\delta_i^2$. Im d(s)-Modus werden Punktgrößen zu Strichgrößen, aus $k_\tau\tau$ wird $k_s[s(\tau)-s(0)]$, das Kostenintegral läuft über $s$, und es gilt $d(t) = d(s(t))$.

### Herleitung
Die Herleitung ist identisch zu Satz 1 mit der Bogenlänge als unabhängiger Variable.

### Annahmen
Spurwechsel: Die Referenzkurve liegt auf der Mitte der Zielspur, der Versatz $d_{ref}$ kommt aus `BehaviorCommand`.

### Randbedingungen
Es werden nur Endlagen gesampelt, bei denen der Fahrzeugumriss in $[d_{min},d_{max}]$ passt. Vorfilter: $|\ddot d|$ bzw. $|d''|$.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\delta_i$ | Endversatz | m | `LateralSet.delta` |
| $k_s$ | Gewicht Bogenlänge d(s) | 1/m | `cost.terminal_time.k_s_arc` |

### Anwendungsgrenzen
d(s) erzeugt nur Querbewegung bei Längsbewegung; im Stillstand bleibt d konstant.

### Vor- und Nachteile
d(s) ist bei langsamer Fahrt nichtholonom-verträglich, verliert aber die Geschwindigkeitsinvarianz.

### Numerische Aspekte
Der Quersatz wird je Zyklus einmal gebildet und für alle Längsmodi genutzt.

### Praktische Auswirkungen
Ein Spurwechsel dauert mit den Standardwerten etwa 4 s, unabhängig von der Geschwindigkeit.

### In einfachen Worten
Der Planer probiert viele mögliche Schwenks zur Seite aus: unterschiedlich weit und unterschiedlich schnell.

### Quellen
[[Werling (2011, Abschn. 3.5.1, Tab. 3.1)](../references.md#werling2011)]

## Referenzpunkt und Geschwindigkeitsregime {#reference_point}

### Ziel und Zweck
Wahl von Referenzpunkt und Quermodus passend zum Trackingregler.

### Theorie
Bei schneller Fahrt ($v > v_s$) gelten Schwerpunkt und d(t), bei langsamer Fahrt und rückwärts gelten Hinterachsmitte und d(s). Die Hysterese beträgt ±0.5 m/s.

### Herleitung
Für den Kollisionstest wird der Schwimmwinkel am Referenzpunkt zu null gesetzt. Der Schwerpunkt liegt nahe der Fahrzeugmitte. An der Hinterachse ist die Ausrichtung kinematisch exakt.

### Annahmen
Beim Regimewechsel wird die Position um $l_h$ entlang der Fahrzeugachse verschoben; $\theta,\kappa,v,a$ werden übernommen.

### Randbedingungen
Die Umrechnung erzeugt einen kleinen Sprung von der Ordnung $l_h\kappa$, der die Konsistenz einmalig bricht. Das ist dokumentiert und zulässig.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $v_s$ | Umschaltgeschwindigkeit | m/s | `stabilization.v_switch` |
| $l_h$ | Schwerpunkt–Hinterachse | m | `EgoGeometry.cg_to_rear` |

### Anwendungsgrenzen
Der Schwimmwinkel wird für die Geometrie vernachlässigt.

### Vor- und Nachteile
Planer und Regler bleiben konsistent (contracts.md, Abschn. 7).

### Numerische Aspekte
Der Abstand zur Haltelinie bezieht sich auf die Fahrzeugfront und bleibt beim Wechsel erhalten.

### Praktische Auswirkungen
`PlannedTrajectory.reference_point` und `lateral_mode` zeigen den Regler-Typ an.

### In einfachen Worten
Schnell fahrend plant man die Bahn der Fahrzeugmitte, beim Rangieren die der Hinterachse, weil das Auto sich um sie dreht.

### Quellen
[[Werling (2011, Abschn. 3.5.1, 3.5.4)](../references.md#werling2011)]

## Längskandidaten {#longitudinal_sampling}

### Ziel und Zweck
Längsbewegungen für die Modi Geschwindigkeithalten, Folgen, Einfädeln und Anhalten.

### Theorie
Positionsmodi verwenden $q_{345}(s_{ref}(\tau_j)+\sigma_i,\dot s_{ref}(\tau_j),\ddot s_{ref}(\tau_j),\tau_j)$ mit den Kosten $k_\tau\tau_j+\frac{1}{2}k_\sigma\sigma_i^2$. Geschwindigkeithalten verwendet $q_{34}(\dot s_{ref}+\nu_i,0,\tau_j)$ mit den Kosten $k_\tau\tau_j+\frac{1}{2}k_\nu\nu_i^2$. Anhalten: $s_{ref} = s_{stop} - l_{front}$, $\dot s_{ref}=\ddot s_{ref}=0$.

### Herleitung
Siehe Satz 1 und 2 mit der jeweiligen Referenztrajektorie.

### Annahmen
Nach $\tau$ folgt die Lösung exakt der Referenz $s_{ref}(t)+\sigma$ (bzw. konstanter Geschwindigkeit).

### Randbedingungen
Beim Anhalten wird $\sigma \leq 0$ gesampelt (kein Überfahren). Kandidaten, die rückwärts fahren, entfernt der Vorfilter. Im v-Modus ergänzt ein grobes Raster die Endgeschwindigkeiten bis zum Stillstand.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\sigma_i$ | Positionsversatz | m | `LongitudinalSet.offset` |
| $\nu_i$ | Geschwindigkeitsversatz | m/s | `LongitudinalSet.offset` |

### Anwendungsgrenzen
Ein Modus ohne Prädiktion des Bezugsobjekts entfällt (`PlannerDebug.modes[...]["reason"]`).

### Vor- und Nachteile
Ein einheitliches Rahmenwerk für alle Modi; dafür steigt der Rechenaufwand mit der Zahl der Modi.

### Numerische Aspekte
Die Referenzzustände werden für alle $\tau_j$ vektorisiert ausgewertet.

### Praktische Auswirkungen
Die Fahrzeugfront steht nach dem Anhalten exakt an der Haltelinie (Test < 1 mm).

### In einfachen Worten
Für das Gas- und Bremsverhalten gibt es ebenfalls viele Varianten: schneller oder langsamer, früher oder später am Ziel.

### Quellen
[[Werling (2011, Abschn. 3.5.2, Tab. 3.1)](../references.md#werling2011)]

## Folgemodus {#following_mode}

### Ziel und Zweck
Geschwindigkeitsabhängigen Abstand zum Vorderfahrzeug halten.

### Theorie
$$s_{ref} = s_v - [k_0 + k_v\dot s_v],\quad \dot s_{ref} = \dot s_v - k_v\ddot s_v,\quad \ddot s_{ref} = \ddot s_v$$
Das Vorderfahrzeug wird mit konstanter Beschleunigung prädiziert und nach dem Stillstand geklemmt.

### Herleitung
Die Ableitung von $s_{ref}$ ergibt bei $\dddot s_v=0$ die angegebenen Ausdrücke.

### Annahmen
$s_v$ stammt aus der Projektion der Prädiktion auf die Referenzkurve oder aus `PredictedObject.s` bei passender `lane_id`. $(s_v,\dot s_v,\ddot s_v)$ werden per quadratischer Ausgleichsrechnung über 1 s geschätzt. Der Abstand gilt Stoßstange zu Stoßstange.

### Randbedingungen
Nach dem Stillstand des Vorderfahrzeugs springt $\dot s_{ref}$ von $-k_v\ddot s_v$ auf null.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $k_0$ | Mindestabstand | m | `longitudinal.k0`, `params["k0"]` |
| $k_v$ | Zeitlücke | s | `longitudinal.kv` |

### Anwendungsgrenzen
Die Annahme konstanter Beschleunigung verliert bei langen Horizonten an Genauigkeit.

### Vor- und Nachteile
Einfach und StVO-nah (halber Tacho).

### Numerische Aspekte
Bei exakter Prädiktion bleibt die Planung konsistent (Test).

### Praktische Auswirkungen
Der Abstand konvergiert exakt auf $k_0+k_v v$.

### In einfachen Worten
Je schneller der Vordermann fährt, desto größer der Sollabstand.

### Quellen
[[Werling (2011, Abschn. 3.5.2)](../references.md#werling2011)]

## Einfädeln {#merging_mode}

### Ziel und Zweck
Positionierung in der Mitte einer Lücke auf der Zielspur.

### Theorie
$$s_{ref} = \frac{1}{2}[s_a + s_b]\quad (3.15)$$
Umgesetzt ist die Mitte zwischen dem Heck von a und der Front von b. Die Fahrzeugmitte des Ego-Fahrzeugs wird darauf gelegt; bei gleichen Längen entspricht das genau (3.15).

### Herleitung
Die Mitte der Lücke ist eine lineare Kombination zweier prädizierter Bewegungen.

### Annahmen
Beide Fahrzeuge bewegen sich mit konstanter Beschleunigung.

### Randbedingungen
Der Spurwechsel ergibt sich über die Referenzkurve auf der Zielspur.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $s_a, s_b$ | Fahrzeuge vor/hinter der Lücke | m | `front_id`, `rear_id` |

### Anwendungsgrenzen
Ob die Lücke ausreicht, bewertet die Verhaltensebene.

### Vor- und Nachteile
Längs- und Querbewegung werden gemeinsam optimiert (Spurwechsel während der Synchronisation).

### Numerische Aspekte
Wie im Folgemodus.

### Praktische Auswirkungen
Mit der Ablösestrategie übernimmt der Einfädelmodus stoßfrei, sobald er konservativer ist.

### In einfachen Worten
Das Auto setzt sich genau in die Mitte der Lücke und fährt dann rüber.

### Quellen
[[Werling (2011, Abschn. 3.5.2, (3.15))](../references.md#werling2011)]

## Kombination und Rücktransformation {#candidate_combination}

### Ziel und Zweck
Jede Längs- mit jeder Quertrajektorie kombinieren und in Weltkoordinaten bewerten.

### Theorie
$$x(s(t),d(t)) = r(s(t)) + d(t)\,n_r(s(t))\quad (3.1)$$
$$J = J_d + k_s J_s\quad (3.2)$$
Hier verallgemeinert als $J = k_{lat}J_d + k_{lon}J_s$.

### Herleitung
Das quer-längs-kombinierte Ruckintegral zerfällt in Quer- und Längsanteil.

### Annahmen
Die Kosten sind separierbar.

### Randbedingungen
Rücktransformation lazy in Batches, nur für die geprüften Kandidaten.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $k_{lat}, k_{lon}$ | Gewichte | – | `cost.k_lat`, `cost.k_lon` |

### Anwendungsgrenzen
Bei $N_d\cdot N_s$ Kombinationen (etwa 10⁴) entscheidet die Lazy-Strategie über die Laufzeit.

### Vor- und Nachteile
Gemeinsame Optimierung beider Richtungen, z. B. Bremsen statt starkem Lenken.

### Numerische Aspekte
Die Sortierung erfolgt über einen kombinierten Index $c = i N_s + j$ (`argsort`).

### Praktische Auswirkungen
Siehe Vergleich mit `trajectory_planner/sequential` in `examples/planning/evasion.py`.

### In einfachen Worten
Lenk- und Gasvarianten werden miteinander kombiniert, die Kombinationen werden der Reihe nach geprüft.

### Quellen
[[Werling (2011, Abschn. 3.3, 3.5.5 Schritt 4)](../references.md#werling2011)]

## Mehrzielige Kostenfunktion {#multi_objective_cost}

### Ziel und Zweck
Werling-Kosten um weitere Ziele erweitern (Komfort, Fahrzeit, Energie, Sicherheitsabstand, Kollisionsrisiko …).

### Theorie
Konsistente Terme sind Ruck, $k_\tau\tau$ und Endabweichung. Separierbare Zusatzterme (`acceleration`, `lane_deviation`, `travel_time`, `energy`) gehen in die Sortierung ein. Nicht separierbare Terme (`comfort`, `curvature`, `safety_distance`, `collision_risk`) werden in einem Re-Ranking-Fenster über die ersten gültigen Kandidaten berechnet.

### Herleitung
Nur die konsistenten Terme definieren das Optimalsteuerproblem, dessen Lösungen die Polynome sind. Jeder Zusatzterm verschiebt das Optimum gegenüber dieser Funktionenklasse. Dann gilt die Bellman-Garantie nicht mehr.

### Annahmen
Alle Gewichte stehen in Parametern, nie im Code.

### Randbedingungen
Das Re-Ranking-Fenster ist nur aktiv, wenn nicht separierbare Terme ein Gewicht ungleich null haben (sonst Fenster = 1).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $w$ | Gewicht des Terms | je Term | `cost.<term>.weight` |
| – | Kostenaufteilung | – | `PlannerDebug.cost_terms` |

### Anwendungsgrenzen
Das Re-Ranking optimiert nur innerhalb des Fensters.

### Vor- und Nachteile
Flexibel, kostet aber Konsistenz. Beim `reset()` wird davor gewarnt.

### Numerische Aspekte
Separierbare Terme kosten $O(N_d + N_s)$, nicht separierbare nur Fenster × Prüfhorizont.

### Praktische Auswirkungen
`comfort.json` nutzt den Komfortterm; `default.json` und `sporty.json` sind rein konsistent.

### In einfachen Worten
Außer „sanft“ kann man dem Planer weitere Wünsche mitgeben. Jeder Zusatzwunsch macht ihn aber etwas weniger vorhersehbar.

### Quellen
[[Werling (2011, Abschn. 3.2, 3.3)](../references.md#werling2011)]

## Lazy-Auswahl {#lazy_selection}

### Ziel und Zweck
Die beste zulässige Trajektorie finden, ohne alle Kandidaten zu prüfen.

### Theorie
Prüfung in aufsteigender Kostenreihenfolge; die erste gültige ist die beste (Schritt 5).

### Herleitung
Die Kosten hängen nicht von der Gültigkeit ab, also beendet die erste gültige Trajektorie die Suche optimal.

### Annahmen
Die Kosten sind vor der Prüfung bekannt (separierbar).

### Randbedingungen
Budget `search.max_checks`; die Batches wachsen von 32 auf 1024. Kollisionen werden nur für restriktionskonforme Kandidaten geprüft.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| – | Status je Kandidat | – | `ModeResult.status` (0 gültig, 1 Restriktion, 2 Kollision, 3 ungeprüft) |

### Anwendungsgrenzen
Bei blockierter freier Lösung werden Tausende Kandidaten geprüft (Werling: z. B. Trajektorie 3621 von 4847).

### Vor- und Nachteile
Bei freier Fahrt ist die Auswahl sehr schnell (ein Batch).

### Numerische Aspekte
Gemessen: Median 7–10 ms bei freier Fahrt, 15–30 ms mit Verkehr, bis etwa 300 ms in blockierten Situationen.

### Praktische Auswirkungen
`PlannerDebug.n_checked` zeigt die Schwierigkeit der Situation.

### In einfachen Worten
Man probiert die Varianten von der bequemsten an durch und nimmt die erste, die passt.

### Quellen
[[Werling (2011, Abschn. 3.2, 3.5.5 Schritt 5)](../references.md#werling2011)]

## Ablösestrategie {#replacement_strategy}

### Ziel und Zweck
Auswahl zwischen den aktiven Längsmodi.

### Theorie
Es gewinnt die beste gültige Trajektorie mit dem kleinsten vorzeichenbehafteten Anfangsruck $\dot a(0)$, also die am stärksten verzögernde.

### Herleitung
Position, Geschwindigkeit und Beschleunigung sind bei allen Kandidaten gleich, der Ruck ist die erste unterscheidende Ableitung. Dadurch ist der Wechsel stoßfrei.

### Annahmen
$\dot a(0)$ wird als Weltgröße aus den exakten Polynomen per zentraler Differenz ($h$ = 1 ms) bestimmt.

### Randbedingungen
Nur Modi mit gültiger Trajektorie nehmen teil.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\dot a(0)$ | Anfangsruck | m/s³ | `PlannerDebug.modes[m]["initial_jerk"]` |

### Anwendungsgrenzen
Kann ein Modus wegen grober Abtastung nur stark bremsen, setzt er sich durch. Deshalb gibt es das grobe ν-Raster bis zum Stillstand.

### Vor- und Nachteile
Die konservativste Strategie gewinnt immer; dafür entfällt eine explizite Zustandsmaschine.

### Numerische Aspekte
Zwei Auswertungen je Modus.

### Praktische Auswirkungen
Die besten Kosten je Modus dienen als Gefahrenindikator (3.6) in `PlannedTrajectory.metadata["danger"]`.

### In einfachen Worten
Wenn mehrere Fahrstrategien gleichzeitig mitreden, setzt sich die vorsichtigste durch.

### Quellen
[[Werling (2011, Abschn. 3.5.5 Schritt 6, 3.6)](../references.md#werling2011)]

## Rückfallebene {#fallback}

### Ziel und Zweck
Verhalten, wenn keine Trajektorie alle Restriktionen erfüllt.

### Theorie
Gefolgt wird der Trajektorie, die am längsten kollisionsfrei bleibt. Bevorzugt werden Kandidaten, die die Fahrzeugrestriktionen einhalten. Bei Gleichstand (Kollisionszeiten auf dem Raster) wird die mit der kleinsten Geschwindigkeit zu diesem Zeitpunkt gewählt, also die mit maximal zulässiger Verzögerung. Die Trajektorie erhält `valid=False`.

### Herleitung
Werling 5.3: „jener Trajektorie bis in den Stand gefolgt …, die am längsten die Abstandsrestriktion einhält“, sowie Fußnote 10.

### Annahmen
Es wurden genügend Bremskandidaten geprüft; ist das Budget erschöpft, werden die stärksten Bremskandidaten zusätzlich geprüft.

### Randbedingungen
Der Fallback-Zeitpunkt steht in `PlannerDebug.info["fallback_time"]`.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $t_{coll}$ | erste Kollision | s | `ModeResult.t_collision` |

### Anwendungsgrenzen
Ist eine Kollision physikalisch unvermeidbar, wird nur die Aufprallgeschwindigkeit reduziert.

### Vor- und Nachteile
Einfach und robust, aber ohne Optimierung der Unfallfolgen.

### Numerische Aspekte
Die Kollisionszeit ist auf das Prüfraster (0.1 s) quantisiert.

### Praktische Auswirkungen
Die Verhaltensebene erkennt den Fallback an `trajectory.valid`.

### In einfachen Worten
Wenn nichts mehr sicher ist, wird so stark gebremst wie erlaubt, um möglichst lange nichts zu berühren.

### Quellen
[[Werling (2011, Abschn. 5.3, Fußnote 10)](../references.md#werling2011)]

## Fahrphysikalische Restriktionen {#kinematic_constraints}

### Ziel und Zweck
Kandidaten verwerfen, die das Fahrzeug nicht fahren kann.

### Theorie
Geprüft werden: $|v^2\kappa|\leq a_{y,max}$; $-a_{dec}\leq a\leq a_{acc}$; $|\dot a|\leq j_{max}$; $|\kappa|\leq\kappa_{max}$; $|\arctan(l\kappa)|\leq\delta_{max}$; $|l\dot\kappa/(1+(l\kappa)^2)|\leq\dot\delta_{max}$; $|v\kappa|\leq r_{max}$; der Kammsche Kreis $\sqrt{a^2+(v^2\kappa)^2}\leq\eta\mu g$; die Stabilität über $|m l_v v^2\kappa/(c_h l)|\leq\beta_{max}$ und die lineare Querbeschleunigungsgrenze; außerdem $0\leq v\leq v_{max}$.

### Herleitung
Kinematisches Einspurmodell für den Lenkwinkel, lineares Einspurmodell für den stationären Schwimmwinkel $\beta = \kappa(l_h - m l_v v^2/(c_h l))$.

### Annahmen
Grenzwerte $\leq 0$ werden automatisch aus der VehicleConfig übernommen ($\kappa_{max}$, $\delta_{max}$, $\mu$).

### Randbedingungen
Geprüft wird punktweise auf dem einheitlichen Prüfhorizont (3 s, 0.1 s).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\eta$ | Ausnutzung Kammscher Kreis | – | `constraints.tire_force.eta` |
| $j_{max}$ | max. Ruck | m/s³ | `constraints.max_jerk.j_max` |

### Anwendungsgrenzen
Ruck und Lenkrate werden über Differenzenquotienten auf dem Raster bestimmt.

### Vor- und Nachteile
Jede Restriktion ist ein Plugin: einzeln abschaltbar und erweiterbar.

### Numerische Aspekte
Rückgabe je Batch: Gültigkeit, erste Verletzungszeit, Grund.

### Praktische Auswirkungen
`PlannerDebug.constraint_violations` zählt die verworfenen Kandidaten je Restriktion.

### In einfachen Worten
Zu enge Kurven, zu starkes Bremsen oder zu schnelles Lenken werden aussortiert.

### Quellen
[[Werling (2011, Abschn. 3.5.4)](../references.md#werling2011)], [[Kamm (1936)](../references.md#kamm1936)], [[Mitschke und Wallentowitz (2004)](../references.md#mitschke2004)]

## Korridor-Restriktion {#corridor_constraint}

### Ziel und Zweck
Der Fahrzeugumriss bleibt im befahrbaren Korridor $[d_{min},d_{max}]$.

### Theorie
Für die Ecken $(x_c,y_c)$ gilt $d_c = d + x_c\sin\Delta\psi + y_c\cos\Delta\psi$ und $d_{min}\leq d_c\leq d_{max}$.

### Herleitung
Rotation der Ecken in das lokale Frenet-System bei vernachlässigter Krümmung über die Fahrzeuglänge.

### Annahmen
$\Delta\psi = \psi-\theta_r$ mit $\psi = \theta$ (bzw. $\theta+\pi$ rückwärts).

### Randbedingungen
Die Box-Restriktion kommt von der Verhaltensebene (Werling 5.3, Fußnote 8).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $d_{min}, d_{max}$ | Korridor | m | `BehaviorCommand.d_min/d_max` |

### Anwendungsgrenzen
In engen Kurven mit großer Fahrzeuglänge ist die Prüfung ungenau.

### Vor- und Nachteile
Einfach; zusätzlich dient sie als Pruning der Endlagen im Quersatz.

### Numerische Aspekte
Vier Ecken, vektorisiert über (B, K).

### Praktische Auswirkungen
Startet das Fahrzeug außerhalb des Korridors, ist jede Trajektorie ungültig, und es greift der Fallback.

### In einfachen Worten
Das ganze Auto, nicht nur seine Mitte, muss auf der erlaubten Fläche bleiben.

### Quellen
[[Werling (2011, Abschn. 5.3, Fußnote 8)](../references.md#werling2011)]

## Kollisionsprüfung mit Kreisen {#collision_circles}

### Ziel und Zweck
Schnelle statische und dynamische Kollisionsprüfung.

### Theorie
Ein Rechteck $L\times W$ wird durch $n$ Kreise mit $r = \sqrt{(L/2n)^2+(W/2)^2}$ überdeckt. Eine Kollision liegt vor, wenn $|c_i-c_j| < r_i+r_j+m(t)$.

### Herleitung
Die Kreise sind rotationsinvariant, und die Überlappung reduziert sich auf einen Abstandsvergleich (Ziegler/Stiller).

### Annahmen
Schwimmwinkel am Referenzpunkt = 0. Objekte werden entlang ihrer prädizierten Ausrichtung platziert.

### Randbedingungen
Einheitlicher Prüfhorizont von 3 s: Lange Polynome werden abgeschnitten, kurze auf der Mannigfaltigkeit verlängert.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $n$ | Kreise Ego | – | `collision.n_circles_ego` |
| $r$ | Kreisradius | m | `PlannerDebug.collision_circles` |

### Anwendungsgrenzen
Die Prüfung ist zeitdiskret und konservativ an den Ecken.

### Vor- und Nachteile
Sehr schnell; als Alternative gibt es den exakten SAT-Prüfer in `examples/custom_nodes/python/my_collision_checker.py`.

### Numerische Aspekte
Quadrierte Abstände; die Wurzel wird erst nach dem Minimum über die Ego-Kreise gezogen.

### Praktische Auswirkungen
Zurückgegeben wird die erste Kollisionszeit je Kandidat (für den Fallback).

### In einfachen Worten
Autos werden als Ketten von Kreisen dargestellt; berühren sich zwei Kreise, gilt das als Unfall.

### Quellen
[[Ziegler und Stiller (2010)](../references.md#ziegler2010iv)], [[Werling (2011, Abschn. 3.5.4)](../references.md#werling2011)]

## Rampe des Sicherheitsabstands {#safety_margin_ramp}

### Ziel und Zweck
Robustheit gegen Messrauschen bei harten Kollisionsrestriktionen.

### Theorie
$m(t) = m_{typ}\min(1,(t-t_0)/\Delta t)$ (Abb. 3.10).

### Herleitung
Ein sofort voller Abstand würde bei Messschwankungen alle Trajektorien auf einmal ungültig machen. Der lineare Aufbau wirkt wie ein Tiefpass.

### Annahmen
Der Abstand hängt vom Objekttyp ab (Pkw, Lkw, Fußgänger, Radfahrer, statisch, unbekannt).

### Randbedingungen
$\Delta t = 0$ bedeutet sofort vollen Abstand.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\Delta t$ | Aufbauzeit | s | `collision.margin_ramp` |
| $m_{typ}$ | Abstand je Typ | m | `collision.margin_<typ>` |

### Anwendungsgrenzen
Ein zu kleines $\Delta t$ wirkt schreckhaft, ein zu großes träge.

### Vor- und Nachteile
Einfach und wirksam.

### Numerische Aspekte
Die Rampe wird einmal je Zyklus auf dem Prüfraster berechnet.

### Praktische Auswirkungen
Die Rampe wird in `PlannerDebug.collision_circles["margin_ramp"]` ausgegeben.

### In einfachen Worten
Den vollen Sicherheitsabstand verlangt der Planer erst etwas später auf der geplanten Bahn, damit kleine Messfehler ihn nicht aus dem Tritt bringen.

### Quellen
[[Werling (2011, Abschn. 3.5.4, Abb. 3.10)](../references.md#werling2011)]

## Bewegungsprädiktion für die Reinitialisierung {#motion_prediction}

### Ziel und Zweck
Den Fahrzustand zum zukünftigen Startzeitpunkt $t_0+t_{comp}$ schätzen.

### Theorie
Lokale Taylor-Reihen bei konstanter Beschleunigung $\dot v_0$ und Kurswinkelrate $\dot\theta_0$ (Abb. 4.14):
$$x_1 = v_0\Delta t + \frac{\dot v_0}{2}\Delta t^2 - \frac{v_0\dot\theta_0^2}{6}\Delta t^3 - \frac{\dot v_0\dot\theta_0^2}{8}\Delta t^4$$
$$x_2 = \frac{v_0\dot\theta_0}{2}\Delta t^2 + \frac{\dot v_0\dot\theta_0}{3}\Delta t^3 - \frac{v_0\dot\theta_0^3}{24}\Delta t^4$$

### Herleitung
Man integriert $\dot x = v\cos\theta$, $\dot y = v\sin\theta$ mit genäherten $\cos$ und $\sin$. Die Darstellung ist singularitätsfrei für $\dot\theta_0 \to 0$.

### Annahmen
Bei langsamer Fahrt wird $\dot\theta_0$ aus dem Lenkwinkel abgeleitet: $v\tan\delta/l$ (kinematisches Einspurmodell).

### Randbedingungen
Bevorzugt wird `ControllerStatus.prediction` (dict t, x, y, theta, v); fehlt sie, rechnet der Planer selbst aus dem EgoState.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\Delta t$ | Prädiktionszeit | s | `t_s - t_pred` |

### Anwendungsgrenzen
Nur kurze Zeiträume (Rechenzeit, etwa 0.1 s).

### Vor- und Nachteile
Sehr günstig und modellunabhängig.

### Numerische Aspekte
Funktioniert auch für negatives $\Delta t$; damit wird der Ausgabe-Prefix erzeugt.

### Praktische Auswirkungen
Nach einer Reinitialisierung sind die Regelfehler nahezu null.

### In einfachen Worten
Während der Planer rechnet, fährt das Auto weiter. Deshalb wird vorab geschätzt, wo es dann sein wird.

### Quellen
[[Werling (2011, Abschn. 4.5.2)](../references.md#werling2011)]

## Bi-level-Stabilisierung (Planerseite) {#bilevel_stabilization}

### Ziel und Zweck
Low-level-Stabilisierung gegen dauerhafte Störungen mit High-level-Reaktion auf Impulsstörungen kombinieren.

### Theorie
Im Normalfall startet die Planung auf der alten Trajektorie. Eine Reinitialisierung erfolgt beim Systemstart, bei `status.reinit_request`, bei `behavior.reinit` und beim Richtungswechsel. Dann kommen Position, Richtung und Geschwindigkeit aus der Prädiktion, Krümmung und Beschleunigung aber von der aktuellen Solltrajektorie (stoßfrei).

### Herleitung
Hintereinandergeschaltet wären beide Strategien wieder nur High-level-Stabilisierung. Die schwellwertbasierte, seltene Reinitialisierung erhält die Robustheit beider Ebenen (Tab. 2.1).

### Annahmen
Die Schwellwertüberwachung liegt im Regler (`ControllerStatus`).

### Randbedingungen
Strategien: `bilevel` (Standard), `low_level` (nie reinitialisieren), `high_level` (immer vom aktuellen Zustand). Optional `stabilization.reinit_distance` als Sicherheitsnetz.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| – | Strategie | – | `stabilization.strategy` |
| – | reinitialisiert | – | `PlannedTrajectory.reinitialized` |

### Anwendungsgrenzen
Ohne Reglerrückführung (Rückführungs-Port) gibt es nur Low-level-Verhalten.

### Vor- und Nachteile
Robust gegen Modellfehler und Impulsstörungen; erfordert die Abstimmung der Schwellwerte im Regler.

### Numerische Aspekte
Der Ausgabe-Prefix $[t,t_0+t_{comp}]$ wird bei Reinitialisierung aus der Prädiktion erzeugt.

### Praktische Auswirkungen
Planer-Vergleiche über `stabilization.strategy` und `trajectory_planner/frenet_naive`.

### In einfachen Worten
Normalerweise hält der Planer an seinem Plan fest und der Regler gleicht kleine Fehler aus. Nur nach einem „Schubser“ plant er vom tatsächlichen Zustand neu.

### Quellen
[[Werling (2011, Abschn. 2.3, 4.5)](../references.md#werling2011)]

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Absolutes Endzeitraster](theory.md#absolute_time_grid) | [`sampling.end_grid`](../../../vdsim/planning/sampling.py#L35) | [`trajectory_planner/frenet_naive`](components/trajectory_planner__frenet_naive.md), [`trajectory_planner/werling`](components/trajectory_planner__werling.md) | [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011), [Werling et al. (2012)](../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Zeitliche Konsistenz (Bellman-Prinzip)](theory.md#bellman_principle) | [`planner.WerlingPlanner._compose_output`](../../../vdsim/planning/planner.py#L419), [`metrics.consistency_deviation`](../../../vdsim/research/metrics.py#L264) | [`trajectory_planner/frenet_naive`](components/trajectory_planner__frenet_naive.md), [`trajectory_planner/werling`](components/trajectory_planner__werling.md) | [Bellman (1957)](../references.md#bellman1957), [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011), [Werling et al. (2012)](../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Bi-level-Stabilisierung (Planerseite)](theory.md#bilevel_stabilization) | [`planner.WerlingPlanner._start_state`](../../../vdsim/planning/planner.py#L313) | [`tracking_controller/werling_bilevel`](../stabilization/components/tracking_controller__werling_bilevel.md), [`trajectory_planner/werling`](components/trajectory_planner__werling.md) | [Werling et al. (2010)](../references.md#werling2010icra), [Werling et al. (2010)](../references.md#werling2010tro), [Werling (2011)](../references.md#werling2011), [Werling et al. (2012)](../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Kombination und Rücktransformation](theory.md#candidate_combination) | [`combination.CandidateEvaluator.batch`](../../../vdsim/planning/combination.py#L157) | – | [Werling (2011)](../references.md#werling2011) |
| [Kollisionsprüfung mit Kreisen](theory.md#collision_circles) | [`collision.CircleCollisionChecker.check`](../../../vdsim/planning/collision.py#L144) | [`collision_checker/circles`](components/collision_checker__circles.md) | [Werling (2011)](../references.md#werling2011), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Zielmannigfaltigkeit und Endkosten](theory.md#continuous_manifold) | [`analysis.continuous_solution`](../../../vdsim/planning/analysis.py#L23), [`analysis.transversality_residual`](../../../vdsim/planning/analysis.py#L41), [`cost.TerminalDeviationCost.lateral`](../../../vdsim/planning/cost.py#L141) | – | [Bryson und Ho (1975)](../references.md#bryson1975), [Werling (2011)](../references.md#werling2011) |
| [Korridor-Restriktion](theory.md#corridor_constraint) | [`constraints.VehicleEnvelope.violation`](../../../vdsim/planning/constraints.py#L260) | – | [Werling (2011)](../references.md#werling2011) |
| [Rückfallebene](theory.md#fallback) | [`selection.fallback_candidate`](../../../vdsim/planning/selection.py#L152) | – | [Werling (2011)](../references.md#werling2011) |
| [Folgemodus](theory.md#following_mode) | [`longitudinal.FollowingTarget.state`](../../../vdsim/planning/longitudinal.py#L98), [`longitudinal.ObjectMotion.state`](../../../vdsim/planning/longitudinal.py#L53) | – | [Werling (2011)](../references.md#werling2011) |
| [Frenet-Transformation in geschlossener Form](../geometry/theory.md#frenet_transformation) | [`reference_line.ReferenceLine.to_cartesian`](../../../vdsim/geometry/reference_line.py#L269), [`reference_line.ReferenceLine.to_frenet`](../../../vdsim/geometry/reference_line.py#L251), [`combination.time_to_arc`](../../../vdsim/planning/combination.py#L50) | – | [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011) |
| [Ruckintegral in geschlossener Form](theory.md#jerk_integral) | [`polynomials.jerk_integral`](../../../vdsim/planning/polynomials.py#L65) | [`cost_term/jerk`](components/cost_term__jerk.md) | [Werling (2011)](../references.md#werling2011) |
| [Fahrphysikalische Restriktionen](theory.md#kinematic_constraints) | [`constraints.MaxLateralAcceleration.violation`](../../../vdsim/planning/constraints.py#L95), [`constraints.TireForceConstraint.violation`](../../../vdsim/planning/constraints.py#L239) | – | [Kamm (1936)](../references.md#kamm1936), [Mitschke und Wallentowitz (2004)](../references.md#mitschke2004), [Werling (2011)](../references.md#werling2011) |
| [Querkandidaten d(t) und d(s)](theory.md#lateral_sampling) | [`lateral.build_lateral_set`](../../../vdsim/planning/lateral.py#L63) | [`trajectory_planner/werling`](components/trajectory_planner__werling.md) | [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011), [Werling et al. (2012)](../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Lazy-Auswahl](theory.md#lazy_selection) | [`selection.select_mode`](../../../vdsim/planning/selection.py#L71) | [`trajectory_planner/werling`](components/trajectory_planner__werling.md) | [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011), [Werling et al. (2012)](../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Einrasten auf der Referenz](theory.md#lock_in) | [`analysis.lock_in_distance`](../../../vdsim/planning/analysis.py#L83) | – | [Werling (2011)](../references.md#werling2011) |
| [Längskandidaten](theory.md#longitudinal_sampling) | [`longitudinal.build_longitudinal_set`](../../../vdsim/planning/longitudinal.py#L196) | [`trajectory_planner/werling`](components/trajectory_planner__werling.md) | [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011), [Werling et al. (2012)](../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Einfädeln](theory.md#merging_mode) | [`rule_based.RuleBasedBehavior._update_merge`](../../../vdsim/behavior/rule_based.py#L761), [`longitudinal.MergingTarget.state`](../../../vdsim/planning/longitudinal.py#L116) | [`behavior_planner/rule_based`](../behavior/components/behavior_planner__rule_based.md) | [kesting2007 (fehlt in docs/references)](../references.md#kesting2007), [stvo (fehlt in docs/references)](../references.md#stvo), [treiber2000 (fehlt in docs/references)](../references.md#treiber2000), [Werling (2011)](../references.md#werling2011) |
| [Bewegungsprädiktion für die Reinitialisierung](theory.md#motion_prediction) | [`kinematics.taylor_prediction`](../../../vdsim/planning/kinematics.py#L80), [`reinit.predict_motion`](../../../vdsim/stabilization/reinit.py#L65) | [`tracking_controller/werling_bilevel`](../stabilization/components/tracking_controller__werling_bilevel.md) | [Werling et al. (2010)](../references.md#werling2010tro), [Werling (2011)](../references.md#werling2011) |
| [Mehrzielige Kostenfunktion](theory.md#multi_objective_cost) | [`cost.CostModel`](../../../vdsim/planning/cost.py#L337) | – | [Werling (2011)](../references.md#werling2011) |
| [Quartische Optimalpolynome](theory.md#quartic_polynomial) | [`polynomials.quartic_coefficients`](../../../vdsim/planning/polynomials.py#L44) | [`trajectory_planner/werling`](components/trajectory_planner__werling.md) | [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011), [Werling et al. (2012)](../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Quintische Optimalpolynome](theory.md#quintic_polynomial) | [`polynomials.quintic_coefficients`](../../../vdsim/planning/polynomials.py#L27) | [`trajectory_planner/werling`](components/trajectory_planner__werling.md) | [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011), [Werling et al. (2012)](../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Referenzpunkt und Geschwindigkeitsregime](theory.md#reference_point) | [`kinematics.convert_reference`](../../../vdsim/planning/kinematics.py#L62) | – | [Werling (2011)](../references.md#werling2011) |
| [Ablösestrategie](theory.md#replacement_strategy) | [`selection.initial_jerk`](../../../vdsim/planning/selection.py#L175) | [`trajectory_planner/werling`](components/trajectory_planner__werling.md) | [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011), [Werling et al. (2012)](../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Rampe des Sicherheitsabstands](theory.md#safety_margin_ramp) | [`collision.CircleCollisionChecker.geometry_info`](../../../vdsim/planning/collision.py#L172) | [`collision_checker/circles`](components/collision_checker__circles.md) | [Werling (2011)](../references.md#werling2011), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Abschätzung des Sampling-Horizonts](theory.md#sampling_horizon) | [`analysis.estimate_sampling_horizon`](../../../vdsim/planning/analysis.py#L89) | – | [Werling (2011)](../references.md#werling2011) |
