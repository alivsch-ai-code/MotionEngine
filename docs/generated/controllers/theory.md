# Regler, Fahrerassistenz und Fahrwerksregelsysteme – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


Übernommen aus [vdsim/controllers/docs/theory.md](../../../vdsim/controllers/docs/theory.md).

Gemeinsame Größen: Querablage $e$ (positiv, wenn das Fahrzeug links der Bahn liegt), Bahnkurswinkel $\psi_p$, Bahnkrümmung $\kappa$, Radstand $l$, Eigenlenkgradient $EG$ (siehe Paket analysis). Alle Lenkwinkel werden auf $\pm\delta_{max}$ (`max_steer_angle`) begrenzt.

## Stanley-Bahnregler {#stanley_controller}

### Ziel und Zweck
Robuste Bahnfolge über einen weiten Geschwindigkeitsbereich mit nichtlinearer Rückführung der Querablage an der Vorderachse.

### Theorie
$$\delta = \left(\psi_p - (\psi + \beta)\right) + \arctan\left(\frac{-k\, e_v}{k_s + v}\right) + \delta_{ff} - k_d\left(r - v \kappa\right)$$

$$\delta_{ff} = \arctan(l \kappa) + EG\, v^2 \kappa$$

### Herleitung
Für das kinematische Modell mit Referenz an der Vorderachse gilt $\dot e_v = -v \sin(\delta - \Delta\psi)$. Mit dem Stanley-Gesetz folgt für kleine Fehler $\dot e_v \approx -\frac{k v}{k_s + v} e_v$, also exponentielle Konvergenz unabhängig von der Geschwindigkeit (für $v \gg k_s$). Die Vorsteuerung liefert den stationären Lenkwinkel der Kreisfahrt ($l/R$ plus Untersteueranteil $EG\, a_y$); deshalb ist keine Querablage für die stationäre Kurvenfahrt nötig. Der Kurswinkel enthält den Schwimmwinkel, weil sich bei Kreisfahrt nicht die Fahrzeuglängsachse, sondern die Geschwindigkeit tangential zur Bahn ausrichtet.

### Annahmen
Vorwärtsfahrt; die Bahn ist glatt und ihre Krümmung bekannt.

### Randbedingungen
Querablage an der Vorderachse, Kurswinkel und Krümmung am Schwerpunkt (zwei Projektionen mit eigenen Suchhinweisen).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $k$ | Verstärkung der Querablage | – | `gain` |
| $k_s$ | Softening-Geschwindigkeit | m/s | `softening` |
| $k_d$ | Gierdämpfung | s | `yaw_damping` |
| $e_v$ | Querablage der Vorderachse | m | `front.lateral_error` |
| $EG$ | Eigenlenkgradient | rad/(m/s²) | `eg` |

### Anwendungsgrenzen
Bis in den Grenzbereich robust; bei Rückwärtsfahrt nicht definiert.

### Vor- und Nachteile
- Vorteil: wenige Parameter, keine Modellprädiktion, gutmütig bei großen Fehlern (arctan begrenzt).
- Nachteil: reagiert erst auf Fehler; keine Vorausschau außer über die Vorsteuerung.

### Numerische Aspekte
Winkel werden auf $(-\pi, \pi]$ gewickelt; keine Iteration.

### Praktische Auswirkungen
Standardregler der Szenario-Bibliothek; bleibt im Elchtest stabil.

### In einfachen Worten
Lenke so, dass das Auto in Richtung der Straße fährt, und zusätzlich zur Straße hin, wenn es danebenliegt – umso sanfter, je schneller es fährt.

### Quellen
[[Hoffmann et al. (2007)](../references.md#hoffmann2007)], [[Thrun et al. (2006)](../references.md#thrun2006)], [[Snider (2009)](../references.md#snider2009)]

## Pure Pursuit {#pure_pursuit}

### Ziel und Zweck
Geometrischer Bahnregler: Ein Kreisbogen durch die Hinterachse trifft einen Zielpunkt im Abstand $l_d$ auf der Bahn.

### Theorie
$$\delta = \arctan\left(\frac{2 l \sin\alpha}{l_d}\right), \qquad l_d = \max(l_{d,min}, k_{la} v)$$

mit $\alpha$ als Winkel zwischen Fahrzeuglängsachse und der Verbindung Hinterachse–Zielpunkt.

### Herleitung
Für einen Kreis durch Hinterachse und Zielpunkt gilt $\kappa = 2 \sin\alpha / l_d$ (Sehnensatz). Das kinematische Einspurmodell mit Referenz an der Hinterachse fährt diesen Kreis mit $\tan\delta = l \kappa$.

### Annahmen
Kinematisches Fahrzeug, Zielpunkt auf der Bahn bei $s_{proj} + l_d$.

### Randbedingungen
Mindestvorausschau `lookahead_min` = 4 m.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $l_d$ | Vorausschaudistanz | m | `lookahead` |
| $k_{la}$ | Vorausschauzeit | s | `lookahead_gain` |
| $\alpha$ | Winkel zum Zielpunkt | rad | `alpha` |

### Anwendungsgrenzen
Kurvenschneiden bei großer Vorausschau; ohne Schwimmwinkel- und Dynamikmodell.

### Vor- und Nachteile
- Vorteil: sehr einfach und robust gegen Rauschen.
- Nachteil: Zielkonflikt Stabilität (große $l_d$) gegen Genauigkeit (kleine $l_d$).

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Dient auch als Fahrermodell im Spurhalteassistenten.

### In einfachen Worten
Schau auf einen Punkt ein Stück voraus auf der Straße und lenke so, dass du ihn auf einem Kreisbogen erreichst.

### Quellen
[[Coulter (1992)](../references.md#coulter1992)], [[Snider (2009)](../references.md#snider2009)]

## Modellprädiktive Bahnregelung (lineare MPC) {#path_mpc}

### Ziel und Zweck
Optimale Lenkfolge über einen Horizont unter Lenkwinkelgrenzen, mit Vorausschau auf die Bahnkrümmung.

### Theorie
Fehlerzustand $\mathbf{e} = (e, \dot e, e_\psi, \dot e_\psi)$, Stellgröße $\delta$, gemessene Störung $w = v \kappa$ (Soll-Gierrate):

$$\dot{\mathbf{e}} = A(v)\, \mathbf{e} + B\, \delta + E(v)\, w$$

Exakte ZOH-Diskretisierung über die Matrixexponentialfunktion des erweiterten Systems und kondensierte Prädiktion $\mathbf{E} = \Phi \mathbf{e}_0 + \Gamma \mathbf{\delta} + \Psi \mathbf{w}$. Gütemaß:

$$J = \sum_{k=1}^{N} \mathbf{e}_k^T Q\, \mathbf{e}_k + r \sum_{k=0}^{N-1} \delta_k^2 + s \sum_{k=0}^{N-1} (\delta_k - \delta_{k-1})^2, \qquad \vert\delta_k\vert \le \delta_{max}$$

### Herleitung
Die Fehlerdynamik folgt aus dem linearen Einspurmodell, ausgedrückt relativ zur Bahn (Rajamani, Abschn. 2.5). Für die exakte Diskretisierung wird die erweiterte Matrix $\mathbf{M}$ mit den Blöcken $A$, $B$, $E$ und Nullzeilen gebildet; der obere Block von $e^{\mathbf{M}\Delta t}$ enthält $A_d$, $B_d$ und $E_d$. Die quadratische Kostenfunktion lässt sich als $\Vert \mathcal{A} \mathbf{\delta} - \mathbf{b}\Vert^2$ schreiben (Wurzeln der Gewichte als Zeilen) und mit Box-Restriktionen per BVLS lösen. Nur der erste Wert wird angewendet (Receding Horizon).

### Annahmen
Konstante Geschwindigkeit über den Horizont, lineare Reifen (Achssteifigkeit aus dem Reifenmodell), Vorschau der Krümmung entlang $s + v\, k\, \Delta t$.

### Randbedingungen
$N$ = 25, $\Delta t$ = 0,05 s (Horizont 1,25 s); $v \ge 2$ m/s; Neuberechnung alle 10 ms.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $N$ | Horizontlänge | – | `horizon`, `N` |
| $Q$ | Zustandsgewichte diag(q_e, 0, q_psi, 0) | – | `Q`, `q_lateral`, `q_heading` |
| $r$ | Lenkwinkelgewicht | – | `r_steer` |
| $s$ | Gewicht der Lenkänderung | – | `r_rate`, `s_rate` |
| $\Phi, \Gamma, \Psi$ | Prädiktionsmatrizen | – | `Phi`, `Gam`, `Psi` |
| $w$ | Soll-Gierrate aus Krümmung | rad/s | `w` |

### Anwendungsgrenzen
Am Haftlimit falsch (lineare Reifen); Geschwindigkeitsänderungen innerhalb des Horizonts werden ignoriert.

### Vor- und Nachteile
- Vorteil: Vorausschau, explizite Restriktionen, gut abstimmbar.
- Nachteil: höherer Rechenaufwand, Modellabhängigkeit.

### Numerische Aspekte
Prädiktionsmatrizen werden gespeichert, solange sich $v$ um weniger als 0,5 m/s ändert. BVLS ist für die kleine, dichte Aufgabe (75 × 25) exakt und schnell.

### Praktische Auswirkungen
Glattere Lenkung als Stanley im Doppelspurwechsel; im Grenzbereich ist Stanley robuster (siehe Grenzen).

### In einfachen Worten
Der Regler rechnet für die nächste gute Sekunde durch, wie das Auto auf verschiedene Lenkfolgen reagiert, und wählt die beste – lenkt aber nur den ersten Schritt davon und rechnet dann neu.

### Quellen
[[Rajamani (2012, Abschn. 2.5)](../references.md#rajamani2012)], [[Borrelli et al. (2017)](../references.md#borrelli2017)], [[Stark und Parker (1995)](../references.md#stark1995)]

## Geschwindigkeitsregelung (PI mit Vorsteuerung) {#speed_control}

### Ziel und Zweck
Folgen des Geschwindigkeitsprofils der Trajektorie.

### Theorie
$$a = a_{ff} + k_p (v_{ref} - v) + k_i \int (v_{ref} - v)\, \mathrm{d}t, \qquad a_{ff} = \frac{v_{ahead}^2 - v_{ref}^2}{2 \max(v, 1)\, T_p}$$

mit $v_{ahead}$ als Sollgeschwindigkeit im Abstand $\max(v, 1) T_p$ voraus. Integriert wird nur, solange $a$ nicht begrenzt ist (Anti-Windup).

### Herleitung
Die Vorsteuerung ist die konstante Beschleunigung, die $v_{ref}$ auf der Strecke $v T_p$ in $v_{ahead}$ überführt ($v_2^2 = v_1^2 + 2 a s$).

### Annahmen
Profil entlang der Bahn bekannt; Fahrwiderstände kompensiert die Längsaktuierung.

### Randbedingungen
$a \in [a_{min}, a_{max}]$ = [−9, 4] m/s²; Beschleunigungstabellen offener Manöver haben Vorrang.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $k_p, k_i$ | Verstärkungen | 1/s, 1/s² | `kp`, `ki` |
| $T_p$ | Vorausschauzeit | s | `preview` |
| $a_{ff}$ | Vorsteuerung | m/s² | `a_ff` |

### Anwendungsgrenzen
Keine Ruckbegrenzung.

### Vor- und Nachteile
- Vorteil: einfach, stationär genau.
- Nachteil: kein Abstandsverhalten (dafür ACC).

### Numerische Aspekte
Rechteckintegration mit dem Reglertakt.

### Praktische Auswirkungen
Geschwindigkeitsführung aller geschlossenen Manöver.

### In einfachen Worten
Gas geben oder bremsen, je nachdem wie weit man von der Sollgeschwindigkeit entfernt ist, und schon vorher reagieren, wenn eine Kurve kommt.

### Quellen
[[Rajamani (2012)](../references.md#rajamani2012)]

## Abstandsregeltempomat und Notbremsassistent {#acc_aeb}

### Ziel und Zweck
ACC hält eine Zeitlücke zum vorausfahrenden Fahrzeug, AEB vermeidet Auffahrunfälle durch gestufte Bremsung.

### Theorie
ACC mit konstanter Zeitlücke:

$$d^* = d_0 + T_{gap} v, \qquad a_{follow} = k_d (d - d^*) + k_v (v_{lead} - v), \qquad a = \mathrm{clip}\left(\min(a_{cruise}, a_{follow}), a_{min}, a_{max}\right)$$

AEB über die Zeit bis zur Kollision:

$$TTC = rac{d}{v - v_{lead}} \quad (v - v_{lead} > 0.1)$$

Stufe 1 (Warnung) bei $TTC < 2.6$ s, Stufe 2 (Teilbremsung) bei $TTC < 2.0$ s, Stufe 3 (Vollbremsung) bei $TTC < 1.3$ s.

Stufe 2 bremst mit mindestens 5 m/s², Stufe 3 mit 9,5 m/s²; nach dem Stillstand hält das System mit −3 m/s².

### Herleitung
Die Zeitlückenregel ist ein linearer Abstands- und Relativgeschwindigkeitsregler; die Fehlerdynamik ist ein Feder-Dämpfer-System mit $k_d$, $k_v$. Die Stufen sind monoton (eine höhere Stufe wird bis zum Stillstand gehalten).

### Annahmen
Ideale Objekterkennung (Abstand und Geschwindigkeit des Vorderfahrzeugs bekannt), gleiche Fahrspur.

### Randbedingungen
ACC: $a \in [-3.5, 2]$ m/s²; Abstand Stoßfänger–Stoßfänger über die halbe Fahrzeuglänge.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $T_{gap}$ | Zeitlücke | s | `time_gap` |
| $d_0$ | Stillstandsabstand | m | `standstill_gap` |
| $k_d, k_v$ | Verstärkungen | 1/s², 1/s | `k_gap`, `k_speed` |
| $TTC$ | Zeit bis zur Kollision | s | `ttc` |

### Anwendungsgrenzen
Ein Vorderfahrzeug, keine Einscherer, keine Sensorlatenz.

### Vor- und Nachteile
- Vorteil: transparent und normnah.
- Nachteil: keine Kolonnenstabilität nachgewiesen.

### Numerische Aspekte
TTC wird bei nicht annäherndem Verkehr auf unendlich gesetzt.

### Praktische Auswirkungen
Szenarien „Autobahn mit ACC“ und „Notbremsassistent“.

### In einfachen Worten
Der Tempomat hält Abstand in Sekunden. Wird der Abstand bedrohlich kurz, bremst der Notbremsassistent erst leicht, dann voll.

### Quellen
[[Rajamani (2012)](../references.md#rajamani2012)]

## Spurhalteassistent mit Fahrermodell {#lane_keeping_assist}

### Ziel und Zweck
Verhindert das ungewollte Verlassen der Spur bei einem abgelenkten Fahrer.

### Theorie
Fahrer: Pure Pursuit plus Lenkdrift $\delta_{drift}$ ab $t_{drift}$. Abstand der Fahrzeugkante zur Markierung (an der Vorderachse):

$$d_{line} = \frac{w}{2} - \vert e\vert - \frac{b}{2}$$

Eingriff mit Hysterese (aktiv bei $d_{line} < m$, aus bei $d_{line} > 2m$) und begrenztem Zusatzlenkwinkel:

$$\delta_{LKA} = \mathrm{clip}\left(-k\, \frac{10\, e}{\max(v, 5)} + k_\psi e_\psi,\ \pm \delta_{LKA,max}\right)$$

### Herleitung
Proportionale Rückführung von Ablage und Kurswinkelfehler; die Hysterese verhindert Flattern an der Aktivierungsschwelle.

### Annahmen
Spurmitte gleich Referenzbahn, konstante Spurbreite.

### Randbedingungen
Zusatzlenkwinkel höchstens 3°.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $w$ | Spurbreite | m | `lane_width` |
| $b$ | Fahrzeugbreite | m | `vehicle.width` |
| $m$ | Aktivierungsabstand | m | `activation_margin` |
| $d_{line}$ | Abstand zur Markierung | m | `distance_to_line` |

### Anwendungsgrenzen
Keine Fahrerübersteuerung, keine Markierungserkennung.

### Vor- und Nachteile
- Vorteil: zeigt Wirkung und Grenzen eines Eingriffs mit begrenzter Autorität.
- Nachteil: stark vereinfachtes Fahrermodell.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
KPIs „Spurverlassen“ und „LKA-Eingriffsdauer“.

### In einfachen Worten
Driftet der Fahrer zur Linie, lenkt das System sanft zurück.

### Quellen
[[Rajamani (2012)](../references.md#rajamani2012)]

## Schlupfregelung ABS und ASR {#wheel_slip_control}

### Ziel und Zweck
ABS verhindert blockierende Räder beim Bremsen, ASR durchdrehende Räder beim Antreiben, damit Seitenführung und Kraftschluss erhalten bleiben.

### Theorie
Radindividueller Modulationsfaktor $m_i \in [0, 1]$ auf das Brems- bzw. Antriebsmoment:

$$m_i \leftarrow m_i - \frac{\Delta t}{T_{ab}} \ \ (\mathrm{Schlupf\ zu\ groß}), \qquad m_i \leftarrow m_i + \frac{\Delta t}{T_{auf}} \ \ (\mathrm{Schlupf\ klein})$$

ABS: zu groß bei $\kappa_i < -\kappa^*$ und $v > 2$ m/s, klein bei $\kappa_i > -\kappa^*/2$. ASR: zu groß bei $\kappa_i > \kappa^*$, klein bei $\kappa_i < \kappa^*/2$. Dazwischen wird gehalten.

### Herleitung
Dreiphasige Logik (Druck abbauen, halten, aufbauen) realer ABS-Hydraulik als Zweipunktregler mit Hysterese; die Rampen bilden die begrenzte Druckänderungsgeschwindigkeit nach. Die Kennlinie $\mu(\kappa)$ hat ihr Maximum bei etwa 10–15 % Schlupf, deshalb liegt der Zielschlupf dort.

### Annahmen
Schlupf je Rad messbar (Modell mit Raddynamik).

### Randbedingungen
ABS: $T_{ab}$ = 0,04 s, $T_{auf}$ = 0,25 s; ASR: 0,08 s und 0,4 s.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $m_i$ | Modulationsfaktor | – | `factor` |
| $\kappa^*$ | Zielschlupf | – | `abs_target_slip`, `tcs_target_slip` |
| $T_{ab}, T_{auf}$ | Abbau-, Aufbauzeit | s | `release_time`, `apply_time` |

### Anwendungsgrenzen
Keine Fahrzeugreferenzgeschwindigkeits-Schätzung, keine Select-Low-Logik an der Hinterachse.

### Vor- und Nachteile
- Vorteil: robust, typisches Regelzyklen-Verhalten.
- Nachteil: Grenzzyklus; Parameter qualitativ gewählt.

### Numerische Aspekte
Diskrete Aktualisierung im Reglertakt; Faktoren werden auf [0, 1] begrenzt.

### Praktische Auswirkungen
Bremsweg aus 100 km/h 38–50 m mit Lenkfähigkeit (Test), Split-µ-Bremsung.

### In einfachen Worten
Fängt ein Rad an zu blockieren, lässt das System kurz die Bremse los und baut dann wieder Druck auf – viele Male pro Sekunde.

### Quellen
[[Reif (2010)](../references.md#reif2010)], [[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)]

## ESP – Gierratenregelung durch Einzelradbremsung {#esp_yaw_control}

### Ziel und Zweck
Stabilisiert das Fahrzeug beim Über- und Untersteuern durch ein Giermoment aus gezielten Bremseingriffen.

### Theorie
Referenzgierrate aus dem stationären linearen Einspurmodell, begrenzt durch den Kraftschluss:

$$r_{ref} = \frac{v\, \delta}{l + EG\, v^2}, \qquad \vert r_{ref}\vert \le \frac{0.85\, \mu g}{v}$$

Giermoment mit Totband und Umrechnung in ein Bremsmoment am gewählten Rad:

$$M = K\left(e_r - \mathrm{sign}(e_r)\, \Delta\right), \quad e_r = r_{ref} - r, \qquad \Delta T_B = \frac{\vert M\vert R}{t/2}$$

Übersteuern ($\vert r\vert > \vert r_{ref}\vert$): kurvenäußeres Vorderrad; Untersteuern: kurveninneres Hinterrad. Während des Eingriffs wird das Antriebsmoment um 30 % reduziert.

### Herleitung
Eine Bremskraft $F_B$ an einem Rad mit Abstand $t/2$ zur Mittelebene erzeugt das Giermoment $F_B t/2$; mit $F_B = \Delta T_B / R$ folgt die Umrechnung. Die Begrenzung von $r_{ref}$ folgt aus $a_y = v r \le \mu g$ mit 15 % Reserve.

### Annahmen
Reibwert als Mittel der Radreibwerte bekannt; ein Rad pro Eingriff.

### Randbedingungen
Aktiv ab 5 m/s; Bremsmoment je Rad auf die maximale Bremsleistung begrenzt.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $r_{ref}$ | Referenzgierrate | rad/s | `esp_r_ref` |
| $K$ | Reglerverstärkung | N m s/rad | `esp_gain` |
| $\Delta$ | Totband | rad/s | `esp_deadband` |
| $M$ | Soll-Giermoment | N m | `esp_moment` |

### Anwendungsgrenzen
Keine Schwimmwinkelregelung, keine Schätzung des Reibwerts.

### Vor- und Nachteile
- Vorteil: physikalisch nachvollziehbar, wirkt im Sinus-mit-Haltezeit-Test.
- Nachteil: einfache Radauswahl, kein Zusammenspiel mit ABS-Modulation über eine Koordination.

### Numerische Aspekte
Keine; Totband verhindert Dauereingriffe im Rauschen.

### Praktische Auswirkungen
FMVSS-126-Kriterien werden mit ESP eingehalten (Test „ESP reduziert Schwimmwinkel“).

### In einfachen Worten
Dreht sich das Auto zu stark oder zu wenig, bremst das System ein einzelnes Rad, das das Auto wieder in die richtige Richtung zieht.

### Quellen
[[van Zanten et al. (1995)](../references.md#vanzanten1995)], [[Rajamani (2012)](../references.md#rajamani2012)], [[Reif (2010)](../references.md#reif2010)]

## Torque Vectoring {#torque_vectoring}

### Ziel und Zweck
Erzeugt ein Giermoment durch Umverteilung des Antriebsmoments zwischen linkem und rechtem Rad, um das Eigenlenkverhalten agiler zu machen.

### Theorie
$$r_{ref} = \frac{v\, \delta}{l + c_{TV} EG\, v^2}, \qquad M = K_{TV}(r_{ref} - r), \qquad \Delta T_{Achse} = \mathrm{clip}\left(a_{Achse} \frac{M R}{t/2},\ \pm \Delta T_{max}\right)$$

Links $-\Delta T/2$, rechts $+\Delta T/2$ auf den angetriebenen Achsen (Anteil $a_{Achse}$ nach Antriebslayout).

### Herleitung
Eine Momentendifferenz $\Delta T$ ergibt eine Kraftdifferenz $\Delta T/R$ und das Giermoment $(\Delta T/R)(t/2)$. Mit $c_{TV} = 0$ ist das Ziel neutrales Lenkverhalten, mit $c_{TV} = 1$ das passive Fahrzeug.

### Annahmen
Ideales Differenzial mit begrenztem Differenzmoment.

### Randbedingungen
Nur angetriebene Achsen; Summenmoment bleibt erhalten.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $c_{TV}$ | Ziel-Eigenlenkfaktor | – | `torque_vectoring_target` |
| $K_{TV}$ | Verstärkung | N m s/rad | `torque_vectoring_gain` |
| $\Delta T_{max}$ | maximales Differenzmoment | N m | `torque_vectoring_max_torque` |

### Anwendungsgrenzen
Wirkt nur bei Antriebsmoment; im Schub keine Momentenverteilung.

### Vor- und Nachteile
- Vorteil: Giermoment ohne Bremsverluste.
- Nachteil: begrenzt durch Kraftschluss der Antriebsräder.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Reduziert Untersteuern in der Kreisfahrt (Test).

### In einfachen Worten
Das kurvenäußere Rad bekommt mehr Antrieb als das innere und schiebt das Auto in die Kurve.

### Quellen
[[Rajamani (2012)](../references.md#rajamani2012)], [[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)]

## Hinterachslenkung {#rear_axle_steering}

### Ziel und Zweck
Verbessert Wendigkeit bei niedriger und Stabilität bei hoher Geschwindigkeit.

### Theorie
$$\delta_h = \mathrm{clip}\left(i(v)\, \delta_v,\ \pm 0.1\ \mathrm{rad}\right)$$

mit linear interpoliertem Verhältnis $i(v)$ zwischen $i_{low}$ (gegensinnig, $< 0$) bei $v_{low}$ und $i_{high}$ (gleichsinnig, $> 0$) bei $v_{high}$.

### Herleitung
Gegensinniges Lenken verkürzt den effektiven Radstand (kleinerer Wendekreis); gleichsinniges Lenken reduziert den Schwimmwinkel und die Phasenverzögerung der Querbeschleunigung, wirkt also stabilisierend.

### Annahmen
Statische Kennlinie ohne Aktordynamik.

### Randbedingungen
Hinterachslenkwinkel höchstens 0,1 rad.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $i(v)$ | Lenkverhältnis hinten/vorn | – | `rws_ratio` |
| $v_{low}, v_{high}$ | Übergangsgeschwindigkeiten | m/s | `rear_steering_speed_low`, `..._high` |

### Anwendungsgrenzen
Keine dynamische (zustandsabhängige) Ansteuerung.

### Vor- und Nachteile
- Vorteil: einfach, deutlicher Effekt.
- Nachteil: bei Fahrfehlern keine Regelung.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Test „Hinterachslenkung wirkt“.

### In einfachen Worten
Langsam lenken die Hinterräder entgegen (enger wenden), schnell in dieselbe Richtung (ruhiger Spurwechsel).

### Quellen
[[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)]

## Aktives Fahrwerk: Wankstabilisierung und Skyhook {#active_suspension}

### Ziel und Zweck
Reduziert Wankwinkel in Kurven und Aufbaubewegungen auf unebener Straße.

### Theorie
Aktive Wankstabilisierung (Kompensationsgrad $g$, Wankdämpfung 3000 N m s/rad):

$$M_{akt} = -g\, m_s a_y h' - 3000\, \dot\varphi$$

Skyhook-Dämpfung je Ecke mit absoluter Aufbaugeschwindigkeit:

$$F_{akt,i} = -c_{sky}\, \dot z_{b,i}, \qquad \dot z_{b,i} = \dot z + y_i \dot\varphi - x_i \dot\theta$$

### Herleitung
Das Wankmoment der Fliehkraft um die Rollachse ist $m_s a_y h'$; $g = 1$ kompensiert es vollständig. Skyhook: ein gedachter Dämpfer zwischen Aufbau und einem ruhenden „Himmel“ dämpft die Aufbaubewegung, ohne die Radbewegung an den Aufbau zu koppeln.

### Annahmen
Ideale Aktoren ohne Dynamik und Leistungsgrenze.

### Randbedingungen
Wankstabilisierung wirkt im Zweispur- und Mehrkörpermodell, Skyhook nur im Mehrkörpermodell (Hub- und Nickgeschwindigkeit).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $g$ | Wankkompensationsgrad | – | `active_roll_gain` |
| $c_{sky}$ | Skyhook-Dämpfung | N s/m | `skyhook_gain` |
| $M_{akt}$ | aktives Wankmoment | N m | `u.roll_moment` |

### Anwendungsgrenzen
Unbegrenzte Aktorkraft; keine Energiebetrachtung.

### Vor- und Nachteile
- Vorteil: zeigt das Potenzial aktiver Systeme.
- Nachteil: unrealistisch ideale Aktorik.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Test „aktive Wankstabilisierung reduziert Wankwinkel“; Komfort-KPIs mit Skyhook.

### In einfachen Worten
Ein Motor hält das Auto in Kurven gerade, und die Dämpfer bremsen die Bewegung des Aufbaus so, als hinge er an einem Seil am Himmel.

### Quellen
[[Karnopp et al. (1974)](../references.md#karnopp1974)], [[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)]

## Rückkanal-Korrektur des Krümmungsfehlers {#curvature_feedback_correction}

### Ziel und Zweck
Schätzt laufend den multiplikativen Fehler der Aktuator-Kennlinie aus gesendeter und gemessener Krümmung und korrigiert die Sollkrümmung.

### Theorie
Mit der über ein Modell der Latenzkette verzögerten erwarteten Krümmung $\kappa_e$ und der gemessenen Krümmung $\kappa_m$:

$$N_k = N_{k-1} + \alpha\left(\kappa_e \kappa_m - N_{k-1}\right), \qquad D_k = D_{k-1} + \alpha\left(\kappa_e^2 - D_{k-1}\right), \qquad \alpha = \frac{\Delta t}{T}$$

$$\hat g = \mathrm{clip}\left(\frac{N_k}{D_k}, 0.5, 2\right) \ \ (D_k > \kappa_{min}^2), \qquad \kappa_{sent} = \frac{\kappa_{des}}{\hat g}$$

### Herleitung
Kleinste-Quadrate-Schätzung des Faktors $g$ im Modell $\kappa_m = g\, \kappa_e$ mit exponentieller Gewichtung: $\hat g = \sum \lambda^{k-i} \kappa_e \kappa_m / \sum \lambda^{k-i} \kappa_e^2$. Die rekursive Mittelung von Zähler und Nenner entspricht einem Vergessensfaktor $\lambda = 1 - \alpha$. Die zeitliche Ausrichtung über ein internes Latenzmodell entspricht der Idee des Smith-Prädiktors.

### Annahmen
Latenz der Wirkkette bekannt; Fehler näherungsweise multiplikativ und langsam veränderlich.

### Randbedingungen
Schätzung eingefroren, solange zu wenig Krümmung anliegt ($D_k \le \kappa_{min}^2$).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\alpha$ | Mittelungsfaktor | – | `alpha` |
| $T$ | Zeitkonstante | s | `time_constant` |
| $N_k, D_k$ | gemittelter Zähler, Nenner | 1/m² | `num`, `den` |
| $\hat g$ | geschätzter Fehlerfaktor | – | `gain` |
| $\kappa_{min}$ | Mindestkrümmung | 1/m | `min_curvature` |

### Anwendungsgrenzen
Nichtlineare Kennlinien werden nur lokal korrigiert; unbekannte oder veränderliche Latenz verfälscht die Schätzung.

### Vor- und Nachteile
- Vorteil: einfach, robust gegen Rauschen.
- Nachteil: Schätzung braucht Anregung und Zeit (Zeitkonstante 0,5 s).

### Numerische Aspekte
Begrenzung auf [0,5; 2] verhindert Division durch kleine Schätzwerte.

### Praktische Auswirkungen
Reduziert den y-Versatz der Spurwechsel-Studie deutlich (siehe Paket lane_change).

### In einfachen Worten
Der Planer vergleicht, wie stark er lenken wollte, mit dem, was tatsächlich passiert ist, und lenkt beim nächsten Mal entsprechend mehr oder weniger.

### Quellen
[[Ljung (1999)](../references.md#ljung1999)], [[Smith (1957)](../references.md#smith1957)]

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Abstandsregeltempomat und Notbremsassistent](theory.md#acc_aeb) | [`speed_controller.AdaptiveCruiseControl.acceleration`](../../../vdsim/controllers/speed_controller.py#L69), [`speed_controller.EmergencyBrakeAssist.acceleration`](../../../vdsim/controllers/speed_controller.py#L104) | [`longitudinal_controller/acc`](components/longitudinal_controller__acc.md), [`longitudinal_controller/aeb`](components/longitudinal_controller__aeb.md) | [Rajamani (2012)](../references.md#rajamani2012) |
| [Aktives Fahrwerk: Wankstabilisierung und Skyhook](theory.md#active_suspension) | [`active_suspension.ActiveRollStabilization.apply`](../../../vdsim/controllers/active_suspension.py#L23), [`active_suspension.SkyhookDamping.apply`](../../../vdsim/controllers/active_suspension.py#L42) | [`chassis_system/active_damping`](components/chassis_system__active_damping.md), [`chassis_system/active_roll`](components/chassis_system__active_roll.md) | [Karnopp et al. (1974)](../references.md#karnopp1974), [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) |
| [Rückkanal-Korrektur des Krümmungsfehlers](theory.md#curvature_feedback_correction) | [`curvature_feedback.CurvatureCorrection.update`](../../../vdsim/controllers/curvature_feedback.py#L18) | – | [Ljung (1999)](../references.md#ljung1999), [Smith (1957)](../references.md#smith1957) |
| [ESP – Gierratenregelung durch Einzelradbremsung](theory.md#esp_yaw_control) | [`esp_controller.ElectronicStabilityProgram.apply`](../../../vdsim/controllers/esp_controller.py#L42), [`esp_controller.reference_yaw_rate`](../../../vdsim/controllers/esp_controller.py#L22) | [`chassis_system/esp`](components/chassis_system__esp.md) | [Rajamani (2012)](../references.md#rajamani2012), [Reif (2010)](../references.md#reif2010), [van Zanten et al. (1995)](../references.md#vanzanten1995) |
| [Kinematisches Einspurmodell](../vehicle_models/theory.md#kinematic_bicycle) | [`vehicle_step`](../../../lane_change/vehicle_model.py#L6), [`bicycle_model.KinematicBicycleModel.derivatives`](../../../vdsim/vehicle_models/bicycle_model.py#L42) | [`lateral_controller/curvature_feedforward`](components/lateral_controller__curvature_feedforward.md), [`vehicle_model/bicycle_kinematic`](../vehicle_models/components/vehicle_model__bicycle_kinematic.md) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Rajamani (2012)](../references.md#rajamani2012) |
| [Spurhalteassistent mit Fahrermodell](theory.md#lane_keeping_assist) | [`lane_keeping.LaneKeepingAssist.steer`](../../../vdsim/controllers/lane_keeping.py#L38) | [`lateral_controller/lane_keeping`](components/lateral_controller__lane_keeping.md) | [Rajamani (2012)](../references.md#rajamani2012) |
| [Lineares Einspurmodell](../vehicle_models/theory.md#linear_bicycle) | [`bicycle_model.LinearBicycleModel.state_space`](../../../vdsim/vehicle_models/bicycle_model.py#L77), [`common.axle_cornering_stiffness`](../../../vdsim/vehicle_models/common.py#L23) | [`lateral_controller/mpc`](components/lateral_controller__mpc.md), [`vehicle_model/bicycle_linear`](../vehicle_models/components/vehicle_model__bicycle_linear.md) | [Borrelli et al. (2017)](../references.md#borrelli2017), [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Rajamani (2012)](../references.md#rajamani2012), [Stark und Parker (1995)](../references.md#stark1995) |
| [Modellprädiktive Bahnregelung (lineare MPC)](theory.md#path_mpc) | [`mpc_controller.MPCController._matrices`](../../../vdsim/controllers/mpc_controller.py#L45), [`mpc_controller.MPCController.steer`](../../../vdsim/controllers/mpc_controller.py#L82) | [`lateral_controller/mpc`](components/lateral_controller__mpc.md) | [Borrelli et al. (2017)](../references.md#borrelli2017), [Rajamani (2012)](../references.md#rajamani2012), [Stark und Parker (1995)](../references.md#stark1995) |
| [Pure Pursuit](theory.md#pure_pursuit) | [`pure_pursuit.PurePursuitController.steer`](../../../vdsim/controllers/pure_pursuit.py#L20), [`classic_lateral.PurePursuit.control`](../../../vdsim/stabilization/classic_lateral.py#L180) | [`lateral_controller/lane_keeping`](components/lateral_controller__lane_keeping.md), [`lateral_controller/pure_pursuit`](components/lateral_controller__pure_pursuit.md), [`tracking_controller/pure_pursuit`](../stabilization/components/tracking_controller__pure_pursuit.md) | [Coulter (1992)](../references.md#coulter1992), [Rajamani (2012)](../references.md#rajamani2012), [Snider (2009)](../references.md#snider2009) |
| [Hinterachslenkung](theory.md#rear_axle_steering) | [`rear_axle_steering.RearAxleSteering.apply`](../../../vdsim/controllers/rear_axle_steering.py#L18) | [`chassis_system/rear_steering`](components/chassis_system__rear_steering.md) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) |
| [Geschwindigkeitsregelung (PI mit Vorsteuerung)](theory.md#speed_control) | [`speed_controller.SpeedController.acceleration`](../../../vdsim/controllers/speed_controller.py#L24) | [`longitudinal_controller/speed_pi`](components/longitudinal_controller__speed_pi.md) | [Rajamani (2012)](../references.md#rajamani2012) |
| [Stanley-Bahnregler](theory.md#stanley_controller) | [`stanley_controller.StanleyController.steer`](../../../vdsim/controllers/stanley_controller.py#L31) | [`lateral_controller/stanley`](components/lateral_controller__stanley.md) | [Hoffmann et al. (2007)](../references.md#hoffmann2007), [Snider (2009)](../references.md#snider2009), [Thrun et al. (2006)](../references.md#thrun2006) |
| [Torque Vectoring](theory.md#torque_vectoring) | [`torque_vectoring.TorqueVectoring.apply`](../../../vdsim/controllers/torque_vectoring.py#L20) | [`chassis_system/torque_vectoring`](components/chassis_system__torque_vectoring.md) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Rajamani (2012)](../references.md#rajamani2012) |
| [Eigenlenkgradient und charakteristische Geschwindigkeit](../analysis/theory.md#understeer_gradient) | [`linear_analysis.LinearSingleTrackAnalysis.characteristic_speed`](../../../vdsim/analysis/linear_analysis.py#L20), [`linear_analysis.LinearSingleTrackAnalysis.critical_speed`](../../../vdsim/analysis/linear_analysis.py#L26), [`esp_controller.understeer_gradient`](../../../vdsim/controllers/esp_controller.py#L12), [`bicycle_model.LinearBicycleModel.understeer_gradient`](../../../vdsim/vehicle_models/bicycle_model.py#L87) | [`chassis_system/esp`](components/chassis_system__esp.md) | [ISO 4138:2021 (2021)](../references.md#iso4138), [Milliken und Milliken (1995)](../references.md#milliken1995), [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Rajamani (2012)](../references.md#rajamani2012), [Reif (2010)](../references.md#reif2010), [van Zanten et al. (1995)](../references.md#vanzanten1995) |
| [Schlupfregelung ABS und ASR](theory.md#wheel_slip_control) | [`slip_control.AntiLockBraking.apply`](../../../vdsim/controllers/slip_control.py#L32), [`slip_control.TractionControl.apply`](../../../vdsim/controllers/slip_control.py#L50) | [`chassis_system/abs`](components/chassis_system__abs.md), [`chassis_system/tcs`](components/chassis_system__tcs.md) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Reif (2010)](../references.md#reif2010) |
