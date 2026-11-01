# Fahrzeugmodelle – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


Übernommen aus [vdsim/vehicle_models/docs/theory.md](../../../vdsim/vehicle_models/docs/theory.md).

Bezeichnungen: Masse $m$, Gierträgheit $I_z$, Radstand $l = l_v + l_h$, Schwerpunktabstände $l_v$ (vorn), $l_h$ (hinten), Längs- und Quergeschwindigkeit $v_x$, $v_y$ im Fahrzeugsystem, Gierrate $r = \dot\psi$. Vorzeichen nach ISO 8855 (siehe Paket core).

## Kinematisches Einspurmodell {#kinematic_bicycle}

### Ziel und Zweck
Beschreibt die Fahrzeugbewegung allein aus der Lenkgeometrie, ohne Reifenschlupf. Grundlage für Bahnplanung, Latenzstudien und Fahrten mit geringer Querbeschleunigung.

### Theorie
$$\beta = \arctan\left(\frac{l_v \tan\delta_h + l_h \tan\delta_v}{l}\right), \qquad \dot\psi = \frac{v \cos\beta}{l}\left(\tan\delta_v - \tan\delta_h\right)$$

$$\dot x = v \cos(\psi + \beta), \qquad \dot y = v \sin(\psi + \beta), \qquad \dot v = \frac{F_x}{m}$$

### Herleitung
Die Geschwindigkeitsvektoren an Vorder- und Hinterachse zeigen in Richtung der jeweiligen Radebene (kein Schräglauf). Der Momentanpol liegt im Schnittpunkt der Achsnormalen. Aus den Dreiecken zum Momentanpol folgen Schwimmwinkel $\beta$ im Schwerpunkt und Kurvenradius $R = l/(\cos\beta\,(\tan\delta_v - \tan\delta_h))$; mit $\dot\psi = v/R$ ergibt sich die Gierrate.

### Annahmen
- Kein Schräglauf, starre Räder, ebene Fahrbahn.
- Längskraft aus den Radmomenten, auf $\mu\, \mu_{Fahrbahn}\, m g$ begrenzt, abzüglich Fahrwiderständen.
- Statische Radlasten (nur als Ausgangsgröße).

### Randbedingungen
$\vert\delta\vert < \pi/2$; Zustände $(x, y, \psi, v)$.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\beta$ | Schwimmwinkel im Schwerpunkt | rad | `beta` |
| $\delta_v, \delta_h$ | Lenkwinkel vorn, hinten | rad | `u.steer_front`, `u.steer_rear` |
| $v$ | Bahngeschwindigkeit | m/s | `v` |
| $l_v, l_h, l$ | Schwerpunktabstände, Radstand | m | `cg_to_front`, `cg_to_rear`, `wheelbase` |
| $F_x$ | Längskraft | N | `_longitudinal_force()` |

### Anwendungsgrenzen
Bis etwa $a_y \approx 4\ \mathrm{m/s^2}$ (darüber dominiert der Schräglauf); kein Eigenlenkverhalten.

### Vor- und Nachteile
- Vorteil: robust bei jeder Geschwindigkeit (auch $v \to 0$), keine Reifenparameter nötig.
- Nachteil: kein Unter-/Übersteuern, keine Grenzbereichseffekte.

### Numerische Aspekte
Nicht steif; große Schritte möglich. Bei $v = 0$ bleibt das Modell wohldefiniert.

### Praktische Auswirkungen
Erste Wahl für Trajektorienplanung und die Spurwechsel-Latenzstudie; für ESP-, ABS- oder Grenzbereichsversuche ungeeignet.

### In einfachen Worten
Das Auto fährt wie auf Schienen genau dorthin, wohin die Räder zeigen.

### Quellen
[[Rajamani (2012, Kap. 2)](../references.md#rajamani2012)], [[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)]

## Lineares Einspurmodell {#linear_bicycle}

### Ziel und Zweck
Lineares Modell der Quer- und Gierdynamik für Reglerentwurf, Frequenzgang und Stabilitätsanalyse.

### Theorie
Schräglaufwinkel und Achskräfte:

$$\alpha_v = \delta_v - \frac{v_y + l_v r}{v_x}, \qquad \alpha_h = \delta_h - \frac{v_y - l_h r}{v_x}, \qquad F_{y,i} = C_i\, \alpha_i$$

$$\dot v_y = \frac{F_{yv} + F_{yh}}{m} - v_x r, \qquad \dot r = \frac{l_v F_{yv} - l_h F_{yh}}{I_z}$$

Zustandsraum $\dot{\mathbf{x}} = A \mathbf{x} + B \mathbf{u}$ mit $\mathbf{x} = (v_y, r)$, $\mathbf{u} = (\delta_v, \delta_h)$ und den Elementen (im Code `state_space(vx)`):

$$a_{11} = -\frac{C_v + C_h}{m v_x}, \qquad a_{12} = -v_x - \frac{C_v l_v - C_h l_h}{m v_x}$$

$$a_{21} = -\frac{C_v l_v - C_h l_h}{I_z v_x}, \qquad a_{22} = -\frac{C_v l_v^2 + C_h l_h^2}{I_z v_x}, \qquad B = \frac{1}{m}\left(C_v, C_h\right),\ \frac{1}{I_z}\left(C_v l_v, -C_h l_h\right)$$

### Herleitung
Impuls- und Drallsatz in der Ebene im mitbewegten System, Linearisierung für kleine Winkel ($\sin x \approx x$, $\cos x \approx 1$), Seitenkräfte linear in $\alpha$ und Längskräfte ohne Einfluss auf die Querdynamik. Die Achssteifigkeit $C_i$ wird numerisch aus dem eingestellten Reifenmodell bei statischer Radlast bestimmt: $C_i = 2 F_y(\Delta\alpha)/\Delta\alpha$ mit $\Delta\alpha = 10^{-4}$ (`axle_cornering_stiffness`).

### Annahmen
- Konstante Längsgeschwindigkeit für die Analyse, kleine Winkel, keine Wank- und Nickbewegung.
- Lineare Reifen, statische Achslasten.

### Randbedingungen
$v_x$ wird im Nenner auf mindestens 1 m/s begrenzt.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $C_v, C_h$ | Achs-Schräglaufsteifigkeit | N/rad | `c_front`, `c_rear` |
| $\alpha_v, \alpha_h$ | Schräglaufwinkel | rad | `alpha_f`, `alpha_r` |
| $I_z$ | Gierträgheitsmoment | kg m² | `inertia_z` |
| $A, B$ | Systemmatrizen | – | `state_space()` |

### Anwendungsgrenzen
Lineare Reifen: gültig bis $a_y \approx 4\ \mathrm{m/s^2}$; keine Sättigung, daher keine Instabilität durch Haftungsverlust.

### Vor- und Nachteile
- Vorteil: analytisch lösbar (Eigenwerte, Verstärkungen, Bode), exakte Referenz für Tests.
- Nachteil: keine Lastverlagerung, keine Kopplung mit der Längsdynamik.

### Numerische Aspekte
Eigenwerte skalieren mit $1/v_x$; bei kleiner Geschwindigkeit wird das System steif. Die Begrenzung von $v_x$ verhindert Division durch null.

### Praktische Auswirkungen
Grundlage von MPC, ESP-Referenzgierrate, Stanley-Vorsteuerung und der linearen Analyse (Eigenlenkgradient, charakteristische Geschwindigkeit).

### In einfachen Worten
Ein vereinfachtes Auto mit je einem Rad vorn und hinten, dessen Reifen wie Federn wirken. Damit lässt sich ausrechnen, wie schnell und wie stark das Auto auf Lenken reagiert.

### Quellen
[[Rajamani (2012, Kap. 2)](../references.md#rajamani2012)], [[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)]

## Nichtlineares Einspurmodell {#nonlinear_bicycle}

### Ziel und Zweck
Einspurmodell für den Grenzbereich ohne Wanken: nichtlineare Reifen je Achse, Längslastverlagerung und Kopplung von Längs- und Seitenkraft.

### Theorie
Längslastverlagerung aus der geschätzten Längsbeschleunigung:

$$\Delta F_z = \frac{m\, a_{x,est}\, h}{l}, \qquad F_{zv} = F_{zv,0} - \Delta F_z, \qquad F_{zh} = F_{zh,0} + \Delta F_z$$

Schräglauf $\alpha_v = \delta_v - \mathrm{atan2}(v_y + l_v r, v_x)$, Seitenkraft je Achse aus dem Reifenmodell mit halber Achslast mal zwei, reduziert durch die Reibellipse:

$$F_{y,i} = 2 F_{y0,i} \sqrt{\max\left(1 - \left(\frac{F_{x,i}}{\mu_i F_{z,i}}\right)^2, 0\right)}$$

Die Achskräfte werden mit dem Lenkwinkel ins Fahrzeugsystem gedreht; das Giermoment enthält die Rückstellmomente.

### Herleitung
Momentengleichgewicht um den Nickpol bei starrem Aufbau liefert $\Delta F_z = m a_x h / l$. Die Reibellipse priorisiert die Längskraft (zuerst begrenzt auf $\mu F_z$) und gibt der Seitenkraft das verbleibende Potenzial.

### Annahmen
- $a_{x,est}$ aus Momentenanforderung minus Fahrwiderständen, begrenzt auf $\pm 1.5 g$ (keine algebraische Schleife).
- Reibwert je Achse am Aufstandspunkt der Achsmitte.
- Stillstand: Bremsen halten, kein Rückwärtsrollen.

### Randbedingungen
$F_z \ge 0$; $v_x$ im Nenner mindestens 1 m/s.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $h$ | Schwerpunkthöhe | m | `cg_height` |
| $a_{x,est}$ | geschätzte Längsbeschleunigung | m/s² | `ax_est` |
| $F_{y0}$ | Seitenkraft bei reinem Schräglauf (ein Reifen) | N | `fy0_f`, `fy0_r` |
| $\mu_i$ | Reibwert an der Achse | – | `mu_f`, `mu_r` |

### Anwendungsgrenzen
Ohne Wankdynamik fehlt der Einfluss der Querlastverteilung auf das Eigenlenkverhalten; für Split-µ und radindividuelle Eingriffe ist das Zweispurmodell nötig.

### Vor- und Nachteile
- Vorteil: schnell, Grenzbereich qualitativ richtig.
- Nachteil: keine radindividuellen Größen, Reibellipse nicht glatt an der Grenze.

### Numerische Aspekte
Die Wurzel in der Reibellipse wird mit $\max(\cdot, 0)$ geschützt; Nenner erhalten $10^{-9}$.

### Praktische Auswirkungen
Schnelle Variantenrechnungen und Reglerstudien im Grenzbereich ohne Fahrwerksdetails.

### In einfachen Worten
Wie das lineare Einspurmodell, aber die Reifen haben eine Haftgrenze und beim Bremsen wird vorne mehr Last aufgebracht.

### Quellen
[[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)], [[Pacejka (2012, Kap. 1)](../references.md#pacejka2012)]

## Zweispurmodell mit Wanken und Raddrehung {#double_track}

### Ziel und Zweck
Radindividuelles Modell für Grenzbereich und Fahrdynamikregelsysteme (ABS, ASR, ESP, Torque Vectoring, Split-µ) mit Wankdynamik, Raddrehzahlen, Sturz und Rolllenken.

### Theorie
Radpositionen $x_i \in \{l_v, l_v, -l_h, -l_h\}$, $y_i \in \{t_v/2, -t_v/2, t_h/2, -t_h/2\}$. Radgeschwindigkeiten im Radsystem und Schlupf:

$$v_{wx,i} = v_x - r y_i, \qquad v_{wy,i} = v_y + r x_i, \qquad \alpha_i = -\mathrm{atan2}\left(v_{lat,i}, \max(\vert v_{long,i}\vert, 1)\right), \qquad \kappa_i = \frac{\omega_i R - v_{long,i}}{\max(\vert v_{long,i}\vert, v_{min})}$$

Radlasten aus statischem Anteil, Längs- und Querlastverlagerung (elastisch über die Wanksteifigkeit, geometrisch über die Rollzentren):

$$\Delta F_{z,lat} = \frac{-M_{susp} + k_{geo}\, a_{y,est}}{t}, \qquad M_{susp} = -c_\varphi \varphi + \frac{t}{2}\left(F_{D,l} - F_{D,r}\right) + M_{akt}$$

$$k_{geo,v} = \frac{m_s \frac{l_h}{l} h_{RZ,v} + 2 m_{u,v} R}{t_v}$$

Bewegungsgleichungen:

$$\dot v_x = \frac{\sum F_{x,i} - F_L}{m} + v_y r, \qquad \dot v_y = \frac{\sum F_{y,i}}{m} - v_x r, \qquad I_z \dot r = \sum \left(x_i F_{y,i} - y_i F_{x,i}\right) + \sum M_{z,i}$$

$$I_x \ddot\varphi = m_s h' \left(a_y + g \sin\varphi\right) + M_{susp,v} + M_{susp,h}, \qquad J \dot\omega_i = T_{A,i} - T_{B,i} \tanh(\omega_i/\omega_s) - F_{x,i} R - T_{R,i}$$

### Herleitung
Impuls- und Drallsatz für den Gesamtaufbau in der Ebene, Drallsatz um die Rollachse für die gefederte Masse $m_s$ mit Hebelarm $h'$ (Schwerpunkthöhe minus Rollachshöhe) und Drallsatz je Rad um die Drehachse. Die Wankfedermomente bestehen aus Federn ($k\, t^2/2$) und Stabilisatoren. Das aktive Wankmoment wird nach dem Verhältnis der Wanksteifigkeiten auf die Achsen verteilt. Sturz relativ zur Fahrbahn: $\gamma_i = -s_i\, k_\gamma\, y_i \varphi - \varphi$, Rolllenken $\Delta\delta_i = k_{RL} \varphi$.

### Annahmen
- Rollachse fest, gerade Verbindung der Rollzentren; kein Nicken, keine Hubbewegung.
- Längslastverlagerung quasistatisch aus der Momentenanforderung, Querlastverlagerung geometrisch aus $a_{y,est} = v_x r$.
- Dämpferkennlinien als stückweise lineare Tabellen; Rollwiderstand als Moment $f_R F_z R \tanh(\omega)$.

### Randbedingungen
$F_z \ge 0$; $v_{min}$ = `slip_speed_floor` = 3 m/s; Bremsmoment-Glättung $\omega_s$ = `brake_smoothing` = 2 rad/s.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\varphi$ | Wankwinkel | rad | `roll`, `phi` |
| $c_{\varphi v}, c_{\varphi h}$ | Wanksteifigkeit vorn/hinten | N m/rad | `k_roll_f`, `k_roll_r` |
| $h'$ | Hebelarm Schwerpunkt – Rollachse | m | `h_arm` |
| $m_s$ | gefederte Masse | kg | `m_s` |
| $k_{geo}$ | geometrische Querlastverlagerung je Achse | N/(m/s²) | `geo_f`, `geo_r` |
| $J$ | Radträgheit | kg m² | `wheel_inertia` |
| $\omega_i$ | Raddrehzahlen | rad/s | `omega` |
| $T_{A}, T_{B}$ | Antriebs-, Bremsmoment | N m | `u.drive_torque`, `u.brake_torque` |
| $M_{akt}$ | aktives Wankmoment | N m | `u.roll_moment` |

### Anwendungsgrenzen
Grenzbereich, Regelsysteme und Split-µ; nicht für Komfortbewertung (keine Vertikaldynamik), nicht für Rückwärtsfahrt.

### Vor- und Nachteile
- Vorteil: radindividuelle Kräfte und Raddrehzahlen bei moderatem Rechenaufwand.
- Nachteil: Lastverlagerung ohne Aufbau-Nickdynamik; Raddrehdynamik ist bei kleiner Geschwindigkeit steif.

### Numerische Aspekte
Die Raddrehdynamik bestimmt die stabile Schrittweite des expliziten RK4; `stable_dt()` liefert sie (siehe [Teilschritte](../simulation/theory.md#stable_substeps) im Paket simulation).

### Praktische Auswirkungen
Standardmodell der Szenario-Bibliothek für ISO-Manöver, ABS-Bremsungen und ESP-Tests.

### In einfachen Worten
Ein Auto mit vier einzelnen Rädern, das sich in Kurven zur Seite neigt. Jedes Rad hat seine eigene Last, seinen eigenen Schlupf und seine eigene Drehzahl.

### Quellen
[[Schramm et al. (2018)](../references.md#schramm2018)], [[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)], [[Pacejka (2012, Kap. 1)](../references.md#pacejka2012)]

## Mehrkörpermodell mit Vertikaldynamik {#multibody}

### Ziel und Zweck
Gesamtfahrzeugmodell für Komfort (ISO 2631), Radlastschwankungen, aktives Fahrwerk und Fahrbahnanregung.

### Theorie
Federweg je Ecke aus Aufbau-Hub $z$, Wanken $\varphi$, Nicken $\theta$ und Radhub $z_{w,i}$:

$$z_{b,i} = z - x_i \theta + y_i \varphi, \qquad s_i = z_{w,i} - z_{b,i}, \qquad F_{s,i} = k_i s_i + F_D(\dot s_i) + F_{ARB,i} + F_{akt,i}$$

Reifen als radiale Feder-Dämpfer über dem Fahrbahnprofil, Radlast inklusive Anlenkungskräften (Rollzentren, Anti-Dive/-Squat):

$$F_{t,i} = k_t (z_{road,i} - z_{w,i}) + c_t (\dot z_{road,i} - \dot z_{w,i}), \qquad F_{z,i} = \max\left(F_{z0,i} + F_{t,i} + \Delta F_{link,i}, 0\right)$$

$$m_s \ddot z = \sum F_{s,i}, \qquad I_x \ddot\varphi = \sum y_i F_{s,i} + m_s h' (a_y + g \sin\varphi), \qquad I_y \ddot\theta = -\sum x_i F_{s,i} - m_s a_x h (1 - a_{anti})$$

$$m_{u,i} \ddot z_{w,i} = F_{t,i} - F_{s,i}$$

Die Ebenenbewegung und die Raddrehung entsprechen dem Zweispurmodell.

### Herleitung
Lagrange- bzw. Newton-Euler-Gleichungen für einen starren Aufbau mit drei Freiheitsgraden (Hub, Wanken, Nicken) und vier vertikal geführten Radmassen, linearisiert für kleine Aufbauwinkel. Der Stabilisator koppelt die Federwege einer Achse: $F_{ARB} = \pm k_{ARB} (s_r - s_l)/t^2$. Anti-Dive/-Squat überträgt einen Anteil $a_{anti}$ der Längslastverlagerung direkt über die Lenker.

### Annahmen
- Kleine Aufbauwinkel, lineare Federn und Reifen, Dämpfer als Kennlinien.
- Gleiches Fahrbahnprofil links und rechts; Ableitung des Profils über Differenzenquotient (1 cm).
- Zustände $z$, $z_w$ sind Abweichungen vom statischen Gleichgewicht.

### Randbedingungen
Radlast $\ge 0$ (Abheben möglich); Reifendämpfung $c_t$ = 150 N s/m.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $z, \theta$ | Aufbauhub, Nickwinkel | m, rad | `z`, `theta` / `pitch` |
| $s_i$ | Federweg (Einfedern > 0) | m | `travel` |
| $k_i$ | Radfederrate | N/m | `k_s` |
| $k_t, c_t$ | Reifen-Vertikalsteifigkeit, -dämpfung | N/m, N s/m | `k_t`, `tire_damping` |
| $m_{u,i}$ | ungefederte Masse | kg | `m_u` |
| $a_{anti}$ | wirksamer Anti-Dive/-Squat-Anteil | – | `anti_eff` |
| $z_{road}$ | Fahrbahnhöhe | m | `env.road_height()` |

### Anwendungsgrenzen
Komfort und Radlastschwankung bis etwa 20 Hz; Reifen als Punktkontakt ohne Latschfilterung (kurze Hindernisse werden überschätzt).

### Vor- und Nachteile
- Vorteil: physikalische Radlasten inklusive Fahrbahnanregung; Grundlage für Skyhook und Komfort-KPIs.
- Nachteil: 24 Zustände und hohe Eigenfrequenz der Radmassen erfordern kleine Schrittweiten.

### Numerische Aspekte
`stable_dt()` berücksichtigt zusätzlich Dämpfersteigung über Radmasse und Radeigenfrequenz $\sqrt{(k + k_t)/m_u}$.

### Praktische Auswirkungen
Erforderlich für die ISO-2631-Bewertung, Fahrbahnklassen nach ISO 8608 und die Wirkung aktiver Dämpfung.

### In einfachen Worten
Zusätzlich zum Zweispurmodell federt der Aufbau auf und ab, nickt beim Bremsen und jedes Rad hüpft auf seiner Reifenfeder über die Unebenheiten.

### Quellen
[[Schramm et al. (2018)](../references.md#schramm2018)], [[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)]

## Fahrwiderstände {#driving_resistances}

### Ziel und Zweck
Luft- und Rollwiderstand für alle Modelle und für die Vorsteuerung der Längsregelung.

### Theorie
$$F_L = \frac{1}{2} \rho\, c_w A\, (v - v_W) \vert v - v_W \vert, \qquad F_R = f_R\, m g \tanh\left(\frac{v}{0.5\ \mathrm{m/s}}\right)$$

### Herleitung
Quadratischer Strömungswiderstand mit Relativgeschwindigkeit gegenüber dem Wind; Rollwiderstand proportional zur Normalkraft. Der $\tanh$ ersetzt die Vorzeichenfunktion und macht die Kraft im Stillstand stetig.

### Annahmen
Gegenwind $v_W > 0$; konstanter Rollwiderstandsbeiwert; Luftdichte 1,204 kg/m³ (20 °C).

### Randbedingungen
Keine Steigung, keine Seitenwindkräfte.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $c_w$ | Luftwiderstandsbeiwert | – | `drag_coefficient` |
| $A$ | Stirnfläche | m² | `frontal_area` |
| $f_R$ | Rollwiderstandsbeiwert | – | `rolling_resistance` |
| $v_W$ | Windgeschwindigkeit (Gegenwind > 0) | m/s | `env.wind_speed` |
| $\rho$ | Luftdichte | kg/m³ | `AIR_DENSITY` |

### Anwendungsgrenzen
Ebene Straße; kein Abtrieb, kein geschwindigkeitsabhängiger Rollwiderstand.

### Vor- und Nachteile
- Vorteil: einfach, stetig.
- Nachteil: Rollwiderstand im Zweispur- und Mehrkörpermodell zusätzlich als Radmoment modelliert (konsistent, aber zwei Formulierungen).

### Numerische Aspekte
Die tanh-Glättung vermeidet eine unstetige rechte Seite bei $v = 0$ (wichtig für explizite Integratoren).

### Praktische Auswirkungen
Bestimmt Ausrollen, Energiebedarf und Höchstgeschwindigkeit.

### In einfachen Worten
Fahrtwind und walkende Reifen bremsen das Auto ständig ein wenig; der Fahrtwind umso mehr, je schneller man fährt.

### Quellen
[[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)]

## Konzepte ohne Theorieabschnitt {#konzepte-ohne-theorie}

Folgende Konzepte werden im Code oder in der Paketdoku genannt, haben aber noch keinen Abschnitt `## … {#concept-id}`:

- `desm`

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Desm](../README.md#konzepte-ohne-dokumentation) | [`werling_models.desm_forces`](../../../vdsim/vehicle_models/werling_models.py#L120), [`werling_models.slip_angles`](../../../vdsim/vehicle_models/werling_models.py#L108), [`werling_models.werling_model4`](../../../vdsim/vehicle_models/werling_models.py#L141) | – | [Werling (2011)](../references.md#werling2011) |
| [Zweispurmodell mit Wanken und Raddrehung](theory.md#double_track) | [`double_track_model.DoubleTrackModel.derivatives`](../../../vdsim/vehicle_models/double_track_model.py#L77) | [`vehicle_model/double_track`](components/vehicle_model__double_track.md) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Pacejka (2012)](../references.md#pacejka2012), [Schramm et al. (2018)](../references.md#schramm2018) |
| [Fahrwiderstände](theory.md#driving_resistances) | [`common.aero_drag`](../../../vdsim/vehicle_models/common.py#L8), [`common.rolling_resistance`](../../../vdsim/vehicle_models/common.py#L13) | [`vehicle_model/bicycle_kinematic`](components/vehicle_model__bicycle_kinematic.md), [`vehicle_model/bicycle_linear`](components/vehicle_model__bicycle_linear.md), [`vehicle_model/bicycle_nonlinear`](components/vehicle_model__bicycle_nonlinear.md), [`vehicle_model/double_track`](components/vehicle_model__double_track.md), [`vehicle_model/multibody`](components/vehicle_model__multibody.md) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Pacejka (2012)](../references.md#pacejka2012), [Rajamani (2012)](../references.md#rajamani2012), [Schramm et al. (2018)](../references.md#schramm2018) |
| [Erweitertes kinematisches Einspurmodell](../stabilization/theory.md#kesm) | [`werling_kinematic.force_from_acceleration`](../../../vdsim/stabilization/werling_kinematic.py#L85), [`werling_models.werling_model1`](../../../vdsim/vehicle_models/werling_models.py#L156) | [`tracking_controller/werling_kinematic_orientation`](../stabilization/components/tracking_controller__werling_kinematic_orientation.md) | [Khalil (2002)](../references.md#khalil2002), [Rajamani (2012)](../references.md#rajamani2012), [Werling et al. (2010)](../references.md#werling2010tro), [Werling (2011)](../references.md#werling2011) |
| [Kinematisches Einspurmodell](theory.md#kinematic_bicycle) | [`vehicle_step`](../../../lane_change/vehicle_model.py#L6), [`bicycle_model.KinematicBicycleModel.derivatives`](../../../vdsim/vehicle_models/bicycle_model.py#L42) | [`lateral_controller/curvature_feedforward`](../controllers/components/lateral_controller__curvature_feedforward.md), [`vehicle_model/bicycle_kinematic`](components/vehicle_model__bicycle_kinematic.md) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Rajamani (2012)](../references.md#rajamani2012) |
| [Lineares Einspurmodell](theory.md#linear_bicycle) | [`bicycle_model.LinearBicycleModel.state_space`](../../../vdsim/vehicle_models/bicycle_model.py#L77), [`common.axle_cornering_stiffness`](../../../vdsim/vehicle_models/common.py#L23) | [`lateral_controller/mpc`](../controllers/components/lateral_controller__mpc.md), [`vehicle_model/bicycle_linear`](components/vehicle_model__bicycle_linear.md) | [Borrelli et al. (2017)](../references.md#borrelli2017), [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Rajamani (2012)](../references.md#rajamani2012), [Stark und Parker (1995)](../references.md#stark1995) |
| [Mehrkörpermodell mit Vertikaldynamik](theory.md#multibody) | [`multibody_model.MultibodyModel.derivatives`](../../../vdsim/vehicle_models/multibody_model.py#L89) | [`vehicle_model/multibody`](components/vehicle_model__multibody.md) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Schramm et al. (2018)](../references.md#schramm2018) |
| [Nichtlineares Einspurmodell](theory.md#nonlinear_bicycle) | [`bicycle_model.NonlinearBicycleModel.derivatives`](../../../vdsim/vehicle_models/bicycle_model.py#L127) | [`vehicle_model/bicycle_nonlinear`](components/vehicle_model__bicycle_nonlinear.md) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Pacejka (2012)](../references.md#pacejka2012) |
| [Stabilitätsbegrenzte Teilschritte (stable_dt)](../simulation/theory.md#stable_substeps) | [`simulator.Simulator._substeps`](../../../vdsim/simulation/simulator.py#L70), [`double_track_model.DoubleTrackModel.stable_dt`](../../../vdsim/vehicle_models/double_track_model.py#L65), [`multibody_model.MultibodyModel.stable_dt`](../../../vdsim/vehicle_models/multibody_model.py#L78) | – | [Hairer et al. (1993)](../references.md#hairer1993), [Hairer und Wanner (1996)](../references.md#hairer1996) |
| [Eigenlenkgradient und charakteristische Geschwindigkeit](../analysis/theory.md#understeer_gradient) | [`linear_analysis.LinearSingleTrackAnalysis.characteristic_speed`](../../../vdsim/analysis/linear_analysis.py#L20), [`linear_analysis.LinearSingleTrackAnalysis.critical_speed`](../../../vdsim/analysis/linear_analysis.py#L26), [`esp_controller.understeer_gradient`](../../../vdsim/controllers/esp_controller.py#L12), [`bicycle_model.LinearBicycleModel.understeer_gradient`](../../../vdsim/vehicle_models/bicycle_model.py#L87) | [`chassis_system/esp`](../controllers/components/chassis_system__esp.md) | [ISO 4138:2021 (2021)](../references.md#iso4138), [Milliken und Milliken (1995)](../references.md#milliken1995), [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Rajamani (2012)](../references.md#rajamani2012), [Reif (2010)](../references.md#reif2010), [van Zanten et al. (1995)](../references.md#vanzanten1995) |
