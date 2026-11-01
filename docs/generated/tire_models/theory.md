# Reifenmodelle – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


Übernommen aus [vdsim/tire_models/docs/theory.md](../../../vdsim/tire_models/docs/theory.md).

Alle Modelle liefern aus Schräglaufwinkel $\alpha$, Längsschlupf $\kappa$, Radlast $F_z$, Reibwert $\mu$ und Sturz $\gamma$ die Kräfte $F_x$, $F_y$ und das Rückstellmoment $M_z$ (Vorzeichen siehe Paket core). Die Modelle sind stationär: Die Kräfte stellen sich ohne Verzögerung ein.

## Lineares Reifenmodell mit Reibkreis {#linear_tire}

### Ziel und Zweck
Einfachstes Modell für den linearen Fahrbereich (kleine Schräglaufwinkel). Es liefert die Referenz für Reglerauslegung, lineare Analyse und Plausibilitätsprüfungen.

### Theorie
$$F_y = \left(C_\alpha \alpha + C_\gamma \gamma\right) \frac{F_z}{F_{z0}}, \qquad F_x = C_\kappa \kappa \frac{F_z}{F_{z0}}$$

Mit Sättigung werden beide Kräfte gemeinsam auf den Reibkreis skaliert:

$$s = \min\left(1, \frac{\mu F_z}{\sqrt{F_x^2 + F_y^2}}\right), \qquad (F_x, F_y) \leftarrow s\,(F_x, F_y), \qquad M_z = -t_0 F_y$$

### Herleitung
Taylor-Entwicklung der Reifenkennlinie um $\alpha = \kappa = 0$ bis zum linearen Glied. Die Steifigkeiten skalieren proportional mit der Last. Die Reibkreisbegrenzung folgt aus $\sqrt{F_x^2 + F_y^2} \le \mu F_z$ (Coulomb).

### Annahmen
- Kleine Schlupfwerte, lineare Lastabhängigkeit der Steifigkeiten.
- Isotrope Reibung (Kreis statt Ellipse).

### Randbedingungen
$F_z \ge 0$ (negative Lasten werden auf 0 gesetzt).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $C_\alpha$ | Schräglaufsteifigkeit bei Nennlast | N/rad | `cornering_stiffness` |
| $C_\kappa$ | Längssteifigkeit bei Nennlast | N | `longitudinal_stiffness` |
| $C_\gamma$ | Sturzsteifigkeit | N/rad | `camber_stiffness` |
| $F_{z0}$ | Nennlast | N | `nominal_load` |
| $t_0$ | Reifennachlauf | m | `pneumatic_trail` |
| $s$ | Skalierung am Reibkreis | – | `scale` |

### Anwendungsgrenzen
Bis etwa 40–50 % der Kraftschlussausnutzung realistisch; danach überschätzt das Modell die Kräfte bis zum harten Knick am Reibkreis.

### Vor- und Nachteile
- Vorteil: analytisch auswertbar, schnell, Grundlage der linearen Einspuranalyse.
- Nachteil: kein degressiver Übergang, kein Kraftmaximum bei endlichem Schlupf.

### Numerische Aspekte
Der Nenner der Skalierung wird mit $10^{-9}$ nach unten begrenzt. Die Funktion ist am Reibkreis nicht differenzierbar, was explizite Integratoren aber nicht stört.

### Praktische Auswirkungen
Ideal für Frequenzgänge, Eigenlenkgradient und Reglerentwurf; für Grenzbereichsmanöver (Elchtest, ABS) ungeeignet.

### In einfachen Worten
Der Reifen schiebt umso stärker zur Seite, je schräger er läuft – bis die Haftgrenze erreicht ist. Dann bleibt die Kraft konstant.

### Quellen
[[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)], [[Pacejka (2012, Kap. 1)](../references.md#pacejka2012)]

## Pacejka Magic Formula {#magic_formula}

### Ziel und Zweck
Empirisches Standardmodell für Reifenkräfte bei reinem Schlupf, das die typische Form der Kennlinie (linearer Anstieg, Maximum, Abfall) mit wenigen Parametern wiedergibt.

### Theorie
$$F = D \sin\left(C \arctan\left(B s - E\left(B s - \arctan(B s)\right)\right)\right)$$

mit Maximalwert $D$, Formfaktor $C$, Krümmungsfaktor $E$ und Steifigkeitsfaktor $B$. Im Code gilt:

$$D = \mu(F_z)\, F_z, \qquad \mu(F_z) = \mu \max\left(1 + p_\mu \frac{F_z - F_{z0}}{F_{z0}},\ 0.2\right)$$

$$K_y(F_z) = C_\alpha \frac{\sin\left(2 \arctan\left(F_z / (p_{Ky2} F_{z0})\right)\right)}{\sin\left(2 \arctan(1/p_{Ky2})\right)}, \qquad K_x = C_\kappa \frac{F_z}{F_{z0}}$$

$$B = \frac{K}{C D}, \qquad \alpha_{eff} = \alpha + \frac{C_\gamma (F_z/F_{z0})\, \gamma}{K_y}$$

### Herleitung
Die Ableitung der Magic Formula im Ursprung ist $\mathrm{d}F/\mathrm{d}s\,(0) = B C D$. Mit $B = K/(CD)$ stimmt die Anfangssteigung damit exakt mit der vorgegebenen Steifigkeit $K$ überein. Die degressive Lastabhängigkeit $\sin(2\arctan(\cdot))$ ist der Ansatz von Pacejka für $K_{y\alpha}(F_z)$; sie ist so normiert, dass bei $F_z = F_{z0}$ genau $C_\alpha$ herauskommt. Der Sturz wird als äquivalenter Schräglaufwinkel eingebracht: Die Sturzseitenkraft $C_\gamma \gamma$ wird durch die Steifigkeit geteilt und zu $\alpha$ addiert.

### Annahmen
- Stationärer Reifen, keine horizontalen/vertikalen Verschiebungen $S_H$, $S_V$ außer durch Sturz.
- Reibwert fällt linear mit der Last ($p_\mu < 0$), mindestens 20 % des Nennreibwerts.
- Gleicher Maximalwert $D$ in Längs- und Querrichtung.

### Randbedingungen
$F_z \ge 0$; $1 \le C \le 2$ und $E \le 1$ (Grenzen der Parameter in `TireParameters`).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $B, C, D, E$ | Steifigkeits-, Form-, Maximal-, Krümmungsfaktor | –, –, N, – | `B_y`, `C_y`/`shape_lateral`, `D`, `E_y`/`curvature_lateral` |
| $C_\alpha$ | Schräglaufsteifigkeit bei Nennlast | N/rad | `c_alpha` (`cornering_stiffness`) |
| $C_\kappa$ | Längssteifigkeit bei Nennlast | N | `c_kappa` (`longitudinal_stiffness`) |
| $p_{Ky2}$ | Lastabhängigkeit der Schräglaufsteifigkeit | – | `p_ky2` (`load_sensitivity_stiffness`) |
| $p_\mu$ | Lastabhängigkeit des Reibwerts | – | `p_mu` (`load_sensitivity_mu`) |
| $C_\gamma$ | Sturzsteifigkeit | N/rad | `camber_stiffness` |
| $\gamma$ | Sturzwinkel | rad | `camber` |
| $F_{z0}$ | Nennlast | N | `fz0` (`nominal_load`) |

### Anwendungsgrenzen
Gültig für trockene und nasse Fahrbahn bei stationärem Schlupf. Für Stillstand und sehr kleine Geschwindigkeiten ist der Schlupf schlecht definiert; die Fahrzeugmodelle begrenzen den Nenner.

### Vor- und Nachteile
- Vorteil: gute Abbildung realer Kennlinien, glatt, wenige physikalisch interpretierbare Parameter.
- Nachteil: empirisch, extrapoliert unsicher außerhalb des Messbereichs; der reduzierte Satz kennt keine Asymmetrien.

### Numerische Aspekte
$D$ und $K$ erhalten $+10^{-9}$, damit $B$ auch bei $F_z = 0$ definiert bleibt. Die Funktion ist vektorisiert und glatt, also unkritisch für RK4.

### Praktische Auswirkungen
Die Lage des Kraftmaximums (über $C$, $E$) bestimmt, wie gutmütig ein Fahrzeug den Grenzbereich ankündigt. Die Lastdegression erzeugt den Einfluss der Wankabstützung auf das Eigenlenkverhalten.

### In einfachen Worten
Eine Formel, die wie eine gemessene Reifenkurve aussieht: erst steigt die Kraft gerade an, dann flacht sie ab und fällt nach dem Maximum leicht. Schwerer belastete Reifen werden relativ gesehen weniger steif.

### Quellen
[[Pacejka (2012, Kap. 4)](../references.md#pacejka2012)], [[Schramm et al. (2018)](../references.md#schramm2018)]

## Kombinierter Schlupf (Gewichtungsfunktionen) {#combined_slip}

### Ziel und Zweck
Gleichzeitiges Bremsen bzw. Antreiben und Kurvenfahren: Längs- und Seitenkraft teilen sich das Kraftschlusspotenzial.

### Theorie
$$F_x = F_{x0}(\kappa) \cos\left(\arctan(B_{x\alpha}\, \alpha)\right), \qquad F_y = F_{y0}(\alpha_{eff}) \cos\left(\arctan(B_{y\kappa}\, \kappa)\right)$$

Rückstellmoment über den abklingenden Reifennachlauf:

$$M_z = -t(\alpha) F_{y0}, \qquad t(\alpha) = t_0 \cos\left(1.2 \arctan(B_y \alpha)\right)$$

### Herleitung
Die Gewichtungsfunktion $G = \cos(\arctan(B x))$ ist 1 bei $x = 0$, fällt monoton und glatt und strebt für großen Schlupf gegen 0. Sie entspricht der vereinfachten Form der Gewichtungsfunktionen der Magic Formula ohne Formfaktoren und Verschiebungen.

### Annahmen
Die Reduktionsfaktoren $B_{x\alpha}$, $B_{y\kappa}$ sind konstant (nicht lastabhängig).

### Randbedingungen
$B_{x\alpha}, B_{y\kappa} \ge 0$.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $B_{x\alpha}$ | Abbau von $F_x$ durch Schräglauf | – | `B_xa` (`combined_longitudinal_reduction`) |
| $B_{y\kappa}$ | Abbau von $F_y$ durch Längsschlupf | – | `B_yk` (`combined_lateral_reduction`) |
| $t_0$ | Reifennachlauf bei $\alpha = 0$ | m | `trail` (`pneumatic_trail`) |

### Anwendungsgrenzen
Die Summe der Kräfte kann den Reibkreis geringfügig überschreiten, weil die Gewichtung nicht exakt am Reibkreis normiert ist.

### Vor- und Nachteile
- Vorteil: glatt, einfach parametrierbar.
- Nachteil: nur qualitativ richtig; genauere Ansätze nutzen lastabhängige Gewichtungsfaktoren.

### Numerische Aspekte
Unkritisch, alle Terme sind beschränkt und glatt.

### Praktische Auswirkungen
Bremsen in der Kurve reduziert die Seitenkraft – Grundlage für ABS/ESP-Studien und ISO 7975.

### In einfachen Worten
Ein Reifen kann nicht gleichzeitig voll bremsen und voll lenken. Je mehr er bremst, desto weniger Seitenkraft bleibt übrig.

### Quellen
[[Pacejka (2012, Kap. 4)](../references.md#pacejka2012)]

## Bürstenmodell {#brush_model}

### Ziel und Zweck
Physikalisches Modell der Kraftübertragung im Latsch: elastische Borsten haften im vorderen Bereich und gleiten im hinteren. Es erklärt Form der Kennlinie, Rückstellmoment und kombinierten Schlupf aus wenigen physikalischen Größen.

### Theorie
Theoretischer Schlupf und kombinierter Schlupfbetrag:

$$\sigma_x = \frac{\kappa}{1 + \kappa}, \qquad \sigma_y = \frac{\tan \alpha_{eff}}{1 + \kappa}, \qquad \theta_i = \frac{C_i}{3 \mu F_z}, \qquad \phi = \sqrt{(\theta_x \sigma_x)^2 + (\theta_y \sigma_y)^2}$$

$$F = \mu F_z \left(3\phi - 3\phi^2 + \phi^3\right) \ \ (\phi < 1), \qquad F = \mu F_z \ \ (\phi \ge 1)$$

$$F_x = F \frac{\theta_x \sigma_x}{\phi}, \qquad F_y = F \frac{\theta_y \sigma_y}{\phi}, \qquad M_z = -a\, \mu F_z\, \theta_y \sigma_y (1 - \phi)^3, \qquad a = 3 t_0$$

### Herleitung
Bei parabolischer Druckverteilung $q(x) \propto (1 - x^2/a^2)$ und linear elastischen Borsten wächst die Auslenkung linear über die Latschlänge. Haften gilt, solange die Borstenkraft unter $\mu q(x)$ bleibt. Die Integration von Haft- und Gleitbereich liefert das Polynom $3\phi - 3\phi^2 + \phi^3$; bei $\phi = 1$ gleitet der ganze Latsch. Für kleinen Schlupf ist $F \approx 3 \mu F_z \phi = C \sigma$, das Modell trifft also die vorgegebene Steifigkeit. Der Reifennachlauf bei kleinem Schlupf ist $a/3$, daher $a = 3 t_0$.

### Annahmen
- Parabolische Druckverteilung, starre Karkasse.
- Haft- und Gleitreibwert gleich ($\mu$).
- Steifigkeiten wie bei der Magic Formula lastabhängig (gleiche Ansätze für $C_y(F_z)$, $\mu(F_z)$).

### Randbedingungen
$1 + \kappa \ge 10^{-3}$ (blockierendes Rad: Nenner begrenzt).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\sigma_x, \sigma_y$ | theoretischer Schlupf | – | `sx`, `sy` |
| $\theta_x, \theta_y$ | Steifigkeit bezogen auf $3 \mu F_z$ | – | `theta_x`, `theta_y` |
| $\phi$ | kombinierter normierter Schlupf | – | `phi`, `phi_c` |
| $a$ | halbe Latschlänge | m | `half_length` |
| $C_x, C_y$ | Längs-/Quersteifigkeit bei aktueller Last | N, N/rad | `c_x`, `c_y` |

### Anwendungsgrenzen
Kein Kraftabfall nach dem Maximum (Haft = Gleitreibung); keine Karkassenelastizität.

### Vor- und Nachteile
- Vorteil: physikalisch begründet, kombinierter Schlupf ohne zusätzliche Faktoren, Rückstellmoment konsistent.
- Nachteil: weniger genau als eine angepasste Magic Formula, keine Reibwertabhängigkeit vom Gleitgeschwindigkeit.

### Numerische Aspekte
$\phi$ wird für die Richtungsaufteilung mit $10^{-12}$ nach unten begrenzt. Bei $\phi \ge 1$ wird für Betrag und Moment $\phi = 1$ gesetzt.

### Praktische Auswirkungen
Gut für Lehre und für Studien, bei denen kombinierter Schlupf ohne Kalibrierung plausibel sein muss.

### In einfachen Worten
Man stellt sich die Lauffläche als Bürste vor: vorn haften die Borsten und biegen sich, hinten rutschen sie. Je mehr Schlupf, desto größer der rutschende Teil – bis alles rutscht.

### Quellen
[[Pacejka (2012, Kap. 3)](../references.md#pacejka2012)]

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Bürstenmodell](theory.md#brush_model) | [`brush_model.BrushTire.forces`](../../../vdsim/tire_models/brush_model.py#L28) | [`tire_model/brush`](components/tire_model__brush.md) | [Pacejka (2012)](../references.md#pacejka2012) |
| [Kombinierter Schlupf (Gewichtungsfunktionen)](theory.md#combined_slip) | [`pacejka.PacejkaTire.forces`](../../../vdsim/tire_models/pacejka.py#L52) | [`tire_model/pacejka`](components/tire_model__pacejka.md) | [Pacejka (2012)](../references.md#pacejka2012) |
| [Dynamisches Einspurmodell mit isotropem Reifen](../stabilization/theory.md#isotropic_tire) | [`isotropic.force_magnitude`](../../../vdsim/tire_models/isotropic.py#L71), [`isotropic.lateral_force`](../../../vdsim/tire_models/isotropic.py#L95) | [`tracking_controller/werling_dynamic`](../stabilization/components/tracking_controller__werling_dynamic.md) | [Isidori (1995)](../references.md#isidori1995), [Khalil (2002)](../references.md#khalil2002), [Pacejka (2012)](../references.md#pacejka2012), [Werling (2011)](../references.md#werling2011) |
| [Lineares Reifenmodell mit Reibkreis](theory.md#linear_tire) | [`linear_tire.LinearTire.forces`](../../../vdsim/tire_models/linear_tire.py#L20) | [`tire_model/linear`](components/tire_model__linear.md) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Pacejka (2012)](../references.md#pacejka2012) |
| [Pacejka Magic Formula](theory.md#magic_formula) | [`pacejka.PacejkaTire.cornering_stiffness`](../../../vdsim/tire_models/pacejka.py#L43), [`pacejka.magic_formula`](../../../vdsim/tire_models/pacejka.py#L18) | [`tire_model/pacejka`](components/tire_model__pacejka.md) | [Pacejka (2012)](../references.md#pacejka2012), [Schramm et al. (2018)](../references.md#schramm2018) |
