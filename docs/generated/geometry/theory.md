# Geometrie – Referenzkurven und Frenet-Koordinaten – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


Übernommen aus [vdsim/geometry/docs/theory.md](../../../vdsim/geometry/docs/theory.md).

Referenzkurve $\mathbf{r}(s) = (x_r(s), y_r(s))$ mit Kurswinkel $\theta_r$, Krümmung $\kappa_r$ und Krümmungsableitung $\kappa_r' = \mathrm{d}\kappa_r/\mathrm{d}s$. Ein Punkt wird durch die Bogenlänge $s$ seines Lotfußpunkts und den vorzeichenbehafteten Querabstand $d$ (links positiv) beschrieben. Ableitungen nach der Zeit: $\dot{(\cdot)}$, nach der Bogenlänge: $(\cdot)'$. Die Gleichungsnummern entsprechen den Annotationen im Code (Werling 2011, Anhang A).

## Frenet-Transformation in geschlossener Form {#frenet_transformation}

### Ziel und Zweck
Umrechnung des Bewegungszustands eines Punktes zwischen Weltkoordinaten $[x, y, \theta, \kappa, v, a]$ und Bahnkoordinaten $[s, \dot s, \ddot s, d, d', d'']$ ohne numerisches Differenzieren. Die Trajektorienplanung nach Werling plant Längs- und Querbewegung getrennt in diesen Koordinaten.

### Theorie
Mit dem Kurswinkelfehler $\Delta\theta = \theta - \theta_r$ und $q = 1 - \kappa_r d$:

$$d' = q \tan\Delta\theta \qquad (A.3)$$

$$d'' = -\left(\kappa_r' d + \kappa_r d'\right)\tan\Delta\theta + \frac{q}{\cos^2\Delta\theta}\left(\frac{\kappa\, q}{\cos\Delta\theta} - \kappa_r\right) \qquad (A.5)$$

$$\dot s = \frac{v \cos\Delta\theta}{q} \qquad (A.1)$$

$$\ddot s = \left(a - \frac{\dot s^2}{\cos\Delta\theta}\, Z\right)\frac{\cos\Delta\theta}{q}, \qquad Z = q \tan\Delta\theta\left(\frac{\kappa\, q}{\cos\Delta\theta} - \kappa_r\right) - \left(\kappa_r' d + \kappa_r d'\right) \qquad (A.6)$$

$$\dot d = \dot s\, d', \qquad \ddot d = \ddot s\, d' + \dot s^2 d'' \qquad (A.7), (A.8)$$

Rücktransformation: $x = x_r - d \sin\theta_r$, $y = y_r + d\cos\theta_r$, $\Delta\theta = \mathrm{atan2}(d', q)$, $\theta = \theta_r + \Delta\theta$,

$$\kappa = \left(\left(d'' + (\kappa_r' d + \kappa_r d')\tan\Delta\theta\right)\frac{\cos^2\Delta\theta}{q} + \kappa_r\right)\frac{\cos\Delta\theta}{q}, \qquad v = \dot s\, \frac{q}{\cos\Delta\theta}, \qquad a = \ddot s\, \frac{q}{\cos\Delta\theta} + \frac{\dot s^2}{\cos\Delta\theta} Z$$

### Herleitung
Ausgangspunkt ist $\mathbf{x}(s, d) = \mathbf{r}(s) + d\, \mathbf{n}_r(s)$ mit den Frenet-Formeln $\mathbf{t}_r' = \kappa_r \mathbf{n}_r$, $\mathbf{n}_r' = -\kappa_r \mathbf{t}_r$. Ableiten nach $s$ ergibt $\mathbf{x}' = q\, \mathbf{t}_r + d' \mathbf{n}_r$, daraus $\tan\Delta\theta = d'/q$ (A.3) und $\Vert\mathbf{x}'\Vert = q/\cos\Delta\theta$, also $v = \dot s\, q/\cos\Delta\theta$ (A.1). Eine weitere Ableitung und die Krümmungsdefinition $\kappa = \mathrm{d}\theta/\mathrm{d}\sigma$ liefern (A.5); das Ableiten von $v$ nach der Zeit liefert (A.6). (A.7) und (A.8) sind die Kettenregel für $d(s(t))$.

### Annahmen
- Referenzkurve zweimal stetig differenzierbar mit stetigem $\kappa_r'$ (sonst springt $d''$).
- Der Punkt liegt im Gültigkeitsbereich der Bahnkoordinaten ($q > 0$, eindeutiger Lotfußpunkt).

### Randbedingungen
$\vert\Delta\theta\vert < \pi/2$ und $q > 0$; für $\dot s \to 0$ wird in `time_to_arc` $\dot s$ auf $10^{-6}$ begrenzt. Die Rücktransformation ist für $v = 0$ singularitätsfrei (sie nutzt $d'$, $d''$).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $s, \dot s, \ddot s$ | Bogenlänge und Ableitungen | m, m/s, m/s² | `s`, `s_d`, `s_dd` |
| $d, \dot d, \ddot d$ | Querabstand und Zeitableitungen | m, m/s, m/s² | `d`, `d_d`, `d_dd` |
| $d', d''$ | Ableitungen nach $s$ | –, 1/m | `d_p`, `d_pp` |
| $\theta_r, \kappa_r, \kappa_r'$ | Referenzkurswinkel, -krümmung, -krümmungsableitung | rad, 1/m, 1/m² | `th_r`, `k_r`, `dk_r` |
| $\Delta\theta$ | Kurswinkelfehler | rad | `dth` |
| $q$ | $1 - \kappa_r d$ | – | `one_m` |
| $\kappa, v, a$ | Krümmung, Bahngeschwindigkeit, -beschleunigung | 1/m, m/s, m/s² | `kappa`, `v`, `a` |

### Anwendungsgrenzen
Nahe dem Krümmungsmittelpunkt ($d \to 1/\kappa_r$) und bei Querfahrt ($\Delta\theta \to \pm 90°$) singulär; Rückwärtsfahrt wird über die Bewegungsrichtung $\theta$ und die Fahrtrichtung der Trajektorie behandelt.

### Vor- und Nachteile
- Vorteil: exakt, schnell, vektorisiert, keine Differenzenquotienten (rauschfrei).
- Nachteil: braucht eine glatte Referenzkurve mit bekanntem $\kappa_r'$.

### Numerische Aspekte
`to_cartesian` arbeitet auf Arrays (alle Kandidatentrajektorien des Planers auf einmal). Die Genauigkeit hängt von der Hermite-Interpolation von $\kappa_r$ und $\kappa_r'$ ab.

### Praktische Auswirkungen
Grundlage der Kandidatenauswertung in vdsim.planning: Längs- und Querpolynome werden in Bahnkoordinaten erzeugt und mit dieser Transformation in Weltkoordinaten für Kollisionsprüfung und Krümmungsgrenzen umgerechnet.

### In einfachen Worten
Statt „wo auf der Karte“ sagt man „wie weit entlang der Straße und wie weit links von der Mittellinie“. Diese Formeln rechnen exakt zwischen beiden Beschreibungen hin und her – auch für Geschwindigkeit und Beschleunigung.

### Quellen
[[Werling (2011, Anhang A.1)](../references.md#werling2011)], [[Werling et al. (2010)](../references.md#werling2010icra)]

## Projektion auf die Referenzkurve {#curve_projection}

### Ziel und Zweck
Lotfußpunkt $(s, d)$ eines beliebigen Punktes auf der kontinuierlichen Referenzkurve.

### Theorie
Zwischen zwei Stützstellen werden $[x, y, \theta]$ linear in $\alpha \in [0, 1]$ interpoliert; gesucht ist die Nullstelle

$$f(\alpha) = \left(\mathbf{p} - \mathbf{x}_c(\alpha)\right)\cdot \mathbf{t}(\theta(\alpha)) = 0$$

mit dem Sekantenverfahren (höchstens 8 Schritte). Anschließend Newton-Verfeinerung auf der Hermite-Kurve:

$$s_{k+1} = s_k + \frac{(\mathbf{p} - \mathbf{r}(s_k))\cdot\mathbf{t}_r(s_k)}{1 - \kappa_r(s_k)\, d_k}$$

### Herleitung
Der Lotfußpunkt ist dadurch definiert, dass der Verbindungsvektor senkrecht auf der Tangente steht. Die Ableitung dieser Bedingung nach $s$ ist $-(1 - \kappa_r d)$, daraus folgt der Newton-Schritt. Das Sekantenverfahren auf der linearisierten Darstellung entspricht Werling, Anhang A.2.

### Annahmen
Nächste Stützstelle liegt im richtigen Ast (Suchhinweis `hint` mit Fenster ±40 Stützstellen).

### Randbedingungen
Newton bricht ab, wenn $\vert 1 - \kappa_r d\vert < 10^{-3}$; bei offenen Kurven wird $s$ auf ±50 m über die Enden hinaus begrenzt.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\alpha$ | Segmentparameter | – | `alpha` |
| $s, d$ | Lotfußpunkt, Querabstand | m | `s`, `d` |
| hint | Startindex | – | `hint`, `last_index` |

### Anwendungsgrenzen
Mehrdeutig bei Punkten, die mehreren Kurvenästen gleich nahe sind.

### Vor- und Nachteile
- Vorteil: genau auf der glatten Kurve, schnell bei sequentiellen Aufrufen.
- Nachteil: lokal; globale Suche über alle Stützstellen ist O(n).

### Numerische Aspekte
`project_many` projiziert viele Punkte vektorisiert in Blöcken von 512 (Hindernisse, Hüllkurven).

### Praktische Auswirkungen
Bestimmt den Startzustand jedes Planungszyklus und die Trackingfehler.

### In einfachen Worten
Findet den Punkt auf der Straßenmitte, der dem Auto genau gegenüberliegt.

### Quellen
[[Werling (2011, Anhang A.2)](../references.md#werling2011)]

## Hermite-interpolierte Referenzkurve {#hermite_reference_curve}

### Ziel und Zweck
Glatte Auswertung von Position, Kurswinkel und Krümmung zwischen Stützstellen.

### Theorie
Kubische Hermite-Basis auf $u \in [0, 1]$ mit Segmentlänge $h$:

$$p(u) = (2u^3 - 3u^2 + 1)\, p_0 + (u^3 - 2u^2 + u)\, h\, m_0 + (-2u^3 + 3u^2)\, p_1 + (u^3 - u^2)\, h\, m_1$$

$x$ mit $m = \cos\theta$, $y$ mit $m = \sin\theta$, $\theta$ mit $m = \kappa$, $\kappa$ mit $m = \kappa'$; $\kappa'$ linear.

### Herleitung
Die vier Basispolynome erfüllen die Interpolationsbedingungen für Werte und erste Ableitungen an beiden Enden. Da $\mathrm{d}x/\mathrm{d}s = \cos\theta$ exakt bekannt ist, ist die Kurve $C^1$ in Position und Kurswinkel und stetig in der Krümmung.

### Annahmen
Stützstellen mit konsistenten Ableitungen (die Konstruktoren liefern sie).

### Randbedingungen
Mindestens zwei Stützstellen, streng monotones $s$.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $u$ | normierte Position im Segment | – | `u`, `uc` |
| $h$ | Segmentlänge | m | `h` |
| $m_0, m_1$ | Ableitungen an den Enden | – | Argumente von `_hermite` |

### Anwendungsgrenzen
Die Bogenlänge der interpolierten Kurve weicht bei grober Abtastung minimal von $s$ ab.

### Vor- und Nachteile
- Vorteil: lokal, schnell, glatt.
- Nachteil: $\kappa'$ nur stückweise linear.

### Numerische Aspekte
Bei gleichmäßiger Abtastung O(1) Segmentsuche.

### Praktische Auswirkungen
Stetige Solltrajektorien ohne Krümmungssprünge.

### In einfachen Worten
Zwischen den gespeicherten Punkten wird die Straße so ergänzt, dass Richtung und Krümmung ohne Knicke weiterlaufen.

### Quellen
[[de Boor (2001)](../references.md#deboor2001)]

## Glatte Krümmungsübergänge {#smooth_curvature_profile}

### Ziel und Zweck
Straßengeometrie aus Geraden und Bögen mit stetiger Krümmungsableitung (Werling, Bemerkung 4).

### Theorie
An jeder Segmentgrenze $s_i$ mit Rampenbreite $w$:

$$u = \frac{s - (s_i - w/2)}{w}, \qquad \kappa(s) = \kappa_{i-1} + (\kappa_i - \kappa_{i-1})(3u^2 - 2u^3), \qquad \kappa'(s) = (\kappa_i - \kappa_{i-1})\frac{6u - 6u^2}{w}$$

### Herleitung
Die Smoothstep-Funktion hat an beiden Enden die Ableitung null, damit ist $\kappa$ stetig differenzierbar. Weil die Rampe symmetrisch um die Grenze liegt, bleibt das Integral der Krümmung jedes Bogens gleich $\kappa_i L_i$.

### Annahmen
Rampenbreite höchstens 90 % der angrenzenden Segmentlängen.

### Randbedingungen
`transition` Standard 10 m.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $w$ | Rampenbreite | m | `ramp_width()` |
| $\kappa_i$ | Segmentkrümmung | 1/m | `curvatures` |

### Anwendungsgrenzen
Keine echten Klothoiden (die Krümmung ändert sich nicht linear).

### Vor- und Nachteile
- Vorteil: exakte Winkel, $C^1$-Krümmung.
- Nachteil: höhere Krümmungsänderungsrate in der Rampenmitte als eine Klothoide gleicher Länge.

### Numerische Aspekte
Integration der Kurve auf einem 2-cm-Raster mit Mittelpunkt-Kurswinkel (Ordnung 2).

### Praktische Auswirkungen
Ermöglicht stetige Beschleunigungen und Krümmungen der geplanten Trajektorien.

### In einfachen Worten
Kurven beginnen weich, damit das Lenkrad nicht ruckartig gedreht werden muss.

### Quellen
[[Werling (2011, Abschn. 3.5.3)](../references.md#werling2011)]

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Projektion auf die Referenzkurve](theory.md#curve_projection) | [`reference_line.ReferenceLine.project`](../../../vdsim/geometry/reference_line.py#L148) | – | [Werling (2011)](../references.md#werling2011) |
| [Frenet-Transformation in geschlossener Form](theory.md#frenet_transformation) | [`reference_line.ReferenceLine.to_cartesian`](../../../vdsim/geometry/reference_line.py#L269), [`reference_line.ReferenceLine.to_frenet`](../../../vdsim/geometry/reference_line.py#L251), [`combination.time_to_arc`](../../../vdsim/planning/combination.py#L50) | – | [Werling et al. (2010)](../references.md#werling2010icra), [Werling (2011)](../references.md#werling2011) |
| [Hermite-interpolierte Referenzkurve](theory.md#hermite_reference_curve) | [`reference_line.ReferenceLine.evaluate`](../../../vdsim/geometry/reference_line.py#L113) | – | [de Boor (2001)](../references.md#deboor2001) |
| [Glatte Krümmungsübergänge](theory.md#smooth_curvature_profile) | [`reference_line.ReferenceLine.from_points`](../../../vdsim/geometry/reference_line.py#L384), [`reference_line.curvature_profile`](../../../vdsim/geometry/reference_line.py#L420) | – | [Werling (2011)](../references.md#werling2011) |
