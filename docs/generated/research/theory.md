# Forschungsmodus – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


Übernommen aus [vdsim/research/docs/theory.md](../../../vdsim/research/docs/theory.md).

## Surrogate Safety Measures {#surrogate_safety_measures}

### Ziel und Zweck
Kollisionen sind seltene Ereignisse. Um die Sicherheit einer Fahrfunktion auch ohne Unfall zu bewerten, misst man, wie knapp Situationen waren.

### Theorie
- **Time-to-Collision (TTC):** Zeit bis zum Zusammenstoß, wenn beide Fahrzeuge ihre momentane Geschwindigkeit beibehalten (Hayward 1972).
- **Zeitlücke (THW):** Zeit, bis das Ego die heutige Position des Hecks des Vorderfahrzeugs erreicht.
- **DRAC:** die Verzögerung, die nötig wäre, um die Kollision gerade noch zu vermeiden.
- **Post-Encroachment-Time (PET):** zeitlicher Abstand, mit dem zwei Verkehrsteilnehmer denselben Ort belegen (Allen et al. 1978). PET ist besonders für kreuzende Bahnen in Kreuzungen und Kreisverkehren aussagekräftig.

$$TTC = \frac{g}{v_{ego} - v_{obj,\parallel}}, \quad v_{ego} > v_{obj,\parallel}$$

$$THW = \frac{g}{v_{ego}}, \qquad DRAC = \frac{(v_{ego} - v_{obj,\parallel})^2}{2 g}$$

### Herleitung
- **TTC:** Bei konstanten Geschwindigkeiten schrumpft die Lücke $g$ mit der Relativgeschwindigkeit; die Lücke ist null nach $g / \Delta v$.
- **DRAC:** Eine konstante Verzögerung $a$ baut $\Delta v$ in der Zeit $\Delta v / a$ ab. Dabei wird die Strecke $\Delta v^2 / (2a)$ verbraucht. Setzt man diese gleich $g$, folgt die Formel für DRAC.

### Annahmen
- Lücke $g$ von Stoßstange zu Stoßstange in Ego-Längsrichtung.
- Relevante Objekte liegen im Korridor $|y_{rel}| < (b_{ego} + b_{obj})/2 + 0.3\,m$.

### Randbedingungen
- TTC und DRAC gibt es nur, wenn sich das Ego annähert ($\Delta v > 0.1\,m/s$).
- THW gibt es nur bei $v_{ego} > 1\,m/s$.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $g$ | Lücke | m | `gap` |
| $v_{ego}$ | Ego-Längsgeschwindigkeit | m/s | `ego_vx` |
| $v_{obj,\parallel}$ | Objektgeschwindigkeit in Ego-Richtung | m/s | `v_obj_long` |

### Anwendungsgrenzen
TTC unterstellt konstante Geschwindigkeiten. Bei stark bremsendem Vorderfahrzeug unterschätzt sie das Risiko.

### Vor- und Nachteile
- Einfach, etabliert und vergleichbar.
- Bildet Kurvenfahrt und Querverkehr (außer über PET) nicht ab.

### Numerische Aspekte
Die Objekthistorien werden auf die Ego-Zeitbasis interpoliert. PET wird auf 0.2 s unterabgetastet, damit die Distanzmatrix klein bleibt.

### Praktische Auswirkungen
Eine kleine minimale TTC (< 1.5 s) zeigt kritische Situationen auch dann, wenn keine Kollision auftrat. Damit sind Regler und Planer feiner vergleichbar.

### In einfachen Worten
Wie viele Sekunden hätte es noch gedauert, bis es kracht? Und wie stark hätte man bremsen müssen? Je größer die erste Zahl und je kleiner die zweite, desto entspannter war die Situation.

### Quellen
[[Hayward (1972)](../references.md#hayward1972)], [[Allen et al. (1978)](../references.md#allen1978)], [[Vogel (2003)](../references.md#vogel2003)]

## Abstand orientierter Rechtecke {#rectangle_distance}

### Ziel und Zweck
Den kleinsten Abstand der Fahrzeugumrisse bestimmen bzw. erkennen, ob sie sich überlappen.

### Theorie
Zwei konvexe Polygone überlappen genau dann nicht, wenn eine Kantennormale eine Trennachse ist (Separating Axis Theorem). Ohne Überlappung ist der Abstand das Minimum der Punkt-Kanten-Abstände aller Ecken zu allen Kanten des jeweils anderen Rechtecks.

### Herleitung
Für konvexe Polygone liegt das Abstandsminimum auf dem Rand, und zwar zwischen einer Ecke und einer Kante. Deshalb genügen 2·4·4 Punkt-Kanten-Abstände.

### Annahmen
Fahrzeuge sind Rechtecke (Länge × Breite) um den geometrischen Mittelpunkt.

### Randbedingungen
Bei Überlappung ist der Abstand null.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $P_a, P_b$ | Eckpunkte | m | `ca`, `cb` |

### Anwendungsgrenzen
Spiegel und Anhänger werden nicht abgebildet.

### Vor- und Nachteile
- Exakt für Rechtecke und vektorisiert über die Zeit.
- Für viele Objekte quadratischer Aufwand.

### Numerische Aspekte
Die Projektionen sind über alle Zeitschritte vektorisiert (numpy einsum).

### Praktische Auswirkungen
Grundlage für den minimalen Abstand und die Kollisionsprüfung in den Kennwerten.

### In einfachen Worten
Wir prüfen, ob zwischen zwei Autos eine Lücke ist, durch die man eine gerade Linie legen kann. Falls ja, messen wir die kürzeste Strecke zwischen ihren Ecken und Kanten.

### Quellen
[[Ericson (2004, Abschn. 4.4)](../references.md#ericson2004)]

## Zeitliche Konsistenz als Kennwert {#bellman_principle}

### Ziel und Zweck
Prüfen, ob der Planer das Bellman-Prinzip einhält (Werling 2011, Abschn. 3.2). Ohne Störung soll der neue Plan genau den Rest des alten Plans fortsetzen.

### Theorie
Für zwei aufeinanderfolgende Pläne $x_{k-1}(t)$ und $x_k(t)$ wird auf dem überlappenden Intervall der Länge $T_h$ gemessen:

$$\Delta_k = \max_{t \in [t_k, t_k + T_h]} \| x_k(t) - x_{k-1}(t) \|$$

Zyklen mit Reinitialisierung (High-level-Stabilisierung) werden ausgenommen.

### Herleitung
Nach dem Optimalitätsprinzip setzt sich jede Optimallösung aus optimalen Teillösungen zusammen. Bei unveränderter Situation und Start auf dem alten Plan ist deshalb der Rest des alten Plans optimal. Daraus folgt $\Delta_k = 0$.

### Annahmen
Der Planer startet bei aktiver Low-level-Stabilisierung vom alten Plan.

### Randbedingungen
Neue Hindernisinformation, aktive Restriktionen und Reinitialisierung erzeugen gewollte Abweichungen.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\Delta_k$ | Konsistenzabweichung | m | `consistency_deviation` |
| $T_h$ | Vergleichshorizont | s | `horizon` |

### Anwendungsgrenzen
Der Kennwert vermischt Konsistenzverlust durch neue Information und durch Planerschwächen. Für die Diagnose dienen Läufe ohne Verkehr.

### Vor- und Nachteile
- Macht eine sonst unsichtbare Eigenschaft messbar.
- Benötigt aufgezeichnete Pläne (Snapshots).

### Numerische Aspekte
Lineare Interpolation beider Pläne auf die Zeitpunkte des neuen Plans.

### Praktische Auswirkungen
Ein Planer ohne absolutes Zeitraster oder mit Neuplanung vom Messzustand zeigt deutlich größere $\Delta_k$. Typische Folgen sind Überschwinger und eine Abhängigkeit von der Planungsfrequenz (Werling Abb. 3.2).

### In einfachen Worten
Wenn sich nichts ändert, sollte der Planer jede Zehntelsekunde dasselbe planen wie vorher. Wie weit die Pläne voneinander abweichen, zeigt, wie „wankelmütig“ er ist.

### Quellen
[[Werling (2011, Abschn. 3.2, Satz 3)](../references.md#werling2011)]

## Vollfaktorieller Versuchsplan {#full_factorial_design}

### Ziel und Zweck
Den Einfluss weniger Parameter systematisch über alle Kombinationen untersuchen.

### Theorie
Bei $p$ Parametern mit $n_i$ Stufen entstehen $\prod n_i$ Läufe.

### Herleitung
Kartesisches Produkt der Stufenmengen.

### Annahmen
Die Parameter sind unabhängig einstellbar.

### Randbedingungen
Der Aufwand wächst exponentiell mit $p$.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $n_i$ | Stufen des Parameters $i$ | - | `grid[path]` |

### Anwendungsgrenzen
Ab etwa 3–4 Parametern ist Monte Carlo oder ein teilfaktorieller Plan sinnvoller.

### Vor- und Nachteile
- Wechselwirkungen bleiben sichtbar.
- Hoher Aufwand.

### Numerische Aspekte
Die Läufe sind unabhängig und werden parallel im Prozesspool ausgeführt.

### Praktische Auswirkungen
Heatmaps zeigen z. B. den Kompromiss zwischen Ruckgewicht und Spurwechseldauer.

### In einfachen Worten
Jede Einstellung wird mit jeder anderen ausprobiert.

### Quellen
[[Montgomery (2017)](../references.md#montgomery2017)]

## Monte-Carlo-Simulation und Sensitivität {#monte_carlo}

### Ziel und Zweck
Streuende Einflüsse wie Verkehr, Reibwert oder Sensorrauschen abbilden und die Verteilung der Kennwerte schätzen.

### Theorie
Die Eingänge $X \sim p(X)$ werden $N$-mal gezogen. Schätzer für Mittelwert und Perzentile der Kennwerte $Y = f(X)$ folgen aus der Stichprobe. Die Kollisionsrate ist der Anteil der Läufe mit Kollision.

Die standardisierten Regressionskoeffizienten

$$\tilde{y} = \sum_i \beta_i \tilde{x}_i + \varepsilon$$

mit z-standardisierten Größen zeigen den linearen Einfluss.

### Herleitung
Nach dem Gesetz der großen Zahlen konvergieren die Stichprobenmittel. Der Standardfehler des Mittelwerts ist $\sigma/\sqrt{N}$.

### Annahmen
Die Läufe sind unabhängig. Die Seeds werden deterministisch aus Basis-Seed und Laufindex abgeleitet.

### Randbedingungen
Seltene Ereignisse brauchen große $N$; bei Kollisionsrate $p$ ist der relative Fehler etwa $\sqrt{(1-p)/(pN)}$.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $N$ | Anzahl Läufe | - | `n` |
| $\beta_i$ | standardisierter Koeffizient | - | `sensitivity()` |

### Anwendungsgrenzen
Die Sensitivität ist linear. Nichtlineare Effekte erfordern varianzbasierte Indizes, z. B. Sobol.

### Vor- und Nachteile
- Einfach und beliebig parallelisierbar.
- Langsame Konvergenz für seltene Ereignisse.

### Numerische Aspekte
Die Reproduzierbarkeit ist unabhängig von der Worker-Anzahl, weil jeder Job seinen Seed trägt.

### Praktische Auswirkungen
Robustheitsaussagen der Art „in 95 % der Läufe bleibt der Querfehler unter 0.2 m“.

### In einfachen Worten
Viele Würfelwürfe statt eines einzelnen Tests. So sieht man, wie sicher eine Funktion im Durchschnitt und im ungünstigen Fall ist.

### Quellen
[[Saltelli et al. (2008)](../references.md#saltelli2008)]

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Zeitliche Konsistenz (Bellman-Prinzip)](../planning/theory.md#bellman_principle) | [`planner.WerlingPlanner._compose_output`](../../../vdsim/planning/planner.py#L419), [`metrics.consistency_deviation`](../../../vdsim/research/metrics.py#L264) | [`trajectory_planner/frenet_naive`](../planning/components/trajectory_planner__frenet_naive.md), [`trajectory_planner/werling`](../planning/components/trajectory_planner__werling.md) | [Bellman (1957)](../references.md#bellman1957), [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011), [Werling et al. (2012)](../references.md#werling2012ijrr), [Ziegler und Stiller (2010)](../references.md#ziegler2010iv) |
| [Vollfaktorieller Versuchsplan](theory.md#full_factorial_design) | [`experiments.parameter_sweep`](../../../vdsim/research/experiments.py#L98) | – | [Montgomery (2017)](../references.md#montgomery2017) |
| [Monte-Carlo-Simulation und Sensitivität](theory.md#monte_carlo) | [`experiments.monte_carlo`](../../../vdsim/research/experiments.py#L133) | – | [Saltelli et al. (2008)](../references.md#saltelli2008) |
| [Abstand orientierter Rechtecke](theory.md#rectangle_distance) | [`metrics.rectangle_distance`](../../../vdsim/research/metrics.py#L94) | – | [Ericson (2004)](../references.md#ericson2004) |
| [Surrogate Safety Measures](theory.md#surrogate_safety_measures) | [`metrics.safety_metrics`](../../../vdsim/research/metrics.py#L127) | – | [Allen et al. (1978)](../references.md#allen1978), [Hayward (1972)](../references.md#hayward1972), [Vogel (2003)](../references.md#vogel2003) |
