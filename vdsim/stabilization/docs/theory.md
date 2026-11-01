# Trajektorienstabilisierung – Verfahren

Grundlage ist Werling (2011), Kap. 2, 4 und 5.1.2. Gleichungsnummern in Klammern beziehen sich auf die Dissertation.

## Erweitertes kinematisches Einspurmodell {#kesm}

### Ziel und Zweck
Entwurfsmodell für langsame Fahrt (vorwärts, rückwärts, Stand), das neben der Lenkwinkelrate die Reifenlängskräfte als Eingang enthält, damit keine unterlagerte Geschwindigkeitsregelung nötig ist.

### Theorie
Zustand der Hinterachsmitte $[x_1,x_2,\psi,\delta,v]$, Eingänge $u_1=\dot\delta$, $u_2=F_l=F_{vl}+F_{hl}$, Kräfteverhältnis $\gamma=F_{vl}/F_l$:

$$\dot x_1=v\cos\psi,\quad \dot x_2=v\sin\psi,\quad \dot\psi=v\tan\delta/l,\quad \dot\delta=u_1$$

$$\dot v=\frac{[1+\gamma(1/\cos\delta-1)]u_2-2Mv\tan\delta\,u_1/\cos^2\delta}{m+M\tan^2\delta},\quad M=\frac{ml_h^2+J}{l^2}\quad(4.2)$$

### Herleitung
Lagrange mit der Bogenlänge $s$ der Hinterachse als generalisierter Koordinate: $L=\frac{1}{2}\dot s^2[m+M\tan^2\delta]$ (Schwerpunkt- und Drehenergie), generalisierte Kraft aus virtueller Arbeit $Q=F_{hl}+F_{vl}[\cos\delta+\sin\delta\tan\delta]=F_l[1+\gamma(1/\cos\delta-1)]$ (4.4). Euler-Lagrange liefert $\ddot s[m+M\tan^2\delta]+2M\dot s\dot\delta\tan\delta/\cos^2\delta=Q$. Die Lenkung ist eine rheonome Bindung: $\dot E=Qv-Mv^2\tan\delta\,\dot\delta/\cos^2\delta$ (im Test geprüft). Die Eingangssubstitution $w_2=\dot v$ (4.6) ist für $|\delta|<\pi/2$ umkehrbar (4.7).

### Annahmen
Keine Schräglaufwinkel (geringe Querbeschleunigung), ebene Fahrbahn, schnelle unterlagerte Antriebs-/Bremsregelung.

### Randbedingungen
$|\delta|<\pi/2$ (praktisch Lenkanschlag 0.6 rad); in der Strecke zusätzlich Fahrwiderstände, optionale Steigung `env.grade`, Lenkdynamik erster Ordnung (20 ms).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $x_1,x_2$ | Hinterachsmitte | m | `x1`, `x2` |
| $\delta$ | Radlenkwinkel | rad | `delta` |
| $v$ | Geschwindigkeit Hinterachse (vorzeichenbehaftet) | m/s | `v` |
| $M$ | effektive Trägheit | kg | `P.M` |
| $\gamma$ | Kräfteverhältnis | - | `gamma` |

### Anwendungsgrenzen
Bis etwa 3 m/s bzw. kleine Querbeschleunigung; bei schneller Fahrt wird der Schräglauf relevant.

### Vor- und Nachteile
Singularitätsfrei bei $v=0$ und rückwärts, flach; vernachlässigt Reifenkräfte.

### Numerische Aspekte
Nicht steif bis auf die Lenkdynamik; `stable_dt` = Lenkzeitkonstante, RK4 mit 5 ms.

### Praktische Auswirkungen
Erlaubt Anfahren, Anhalten und Wenden ohne Umschalten der Regelstruktur.

### In einfachen Worten
Das Auto wird wie auf Schienen betrachtet, deren Krümmung der Lenkwinkel vorgibt; berechnet wird nur, wie stark Gas und Bremse das Auto entlang dieser Schiene beschleunigen.

### Quellen
[@werling2011, Abschn. 4.2.1, 4.2.2], [@rajamani2012, Kap. 2]

## Dynamisches Einspurmodell mit isotropem Reifen {#isotropic_tire}

### Ziel und Zweck
Entwurfs- und Streckenmodell für schnelle Fahrt mit Quer-Längs-Kopplung der Reifenkräfte.

### Theorie
Modell 4 (4.39) mit $x=[x_1,x_2,\psi,r,\beta,v]$, $u=[\delta,F_l]$. Isotroper Reifen je Achse:

$$F=A\sin(B\arctan(C\|s\|))\,s/\|s\|\quad(4.40),\qquad c=ABC\quad(4.41)$$

Querschlupf $s_q=\sin\alpha$ (4.44), Schräglaufwinkel (4.45). Bei vorgegebenem $F_l$ folgt $F_q$ aus $g(F_q)=0$ (4.43).

### Herleitung
Kräfte- und Momentenbilanz im Schwerpunkt. Implementiert in $v_x=v\cos\beta$, $v_y=v\sin\beta$; für $v>0$ identisch mit (4.39). Äquivalente Inversion: mit dem Längsschlupfbetrag $u$ und $S=\sqrt{u^2+s_q^2}$ gilt $f(S)u/S=|F_l|$, $F_q=f(S)s_q/S$; die linke Seite ist monoton in $u$ ($\partial_u=f'(S)u^2/S^2+f(S)s_q^2/S^3\geq0$). Sättigungsmodifikation (Fußnote 17): $f(S)[1+\tan(\frac{\pi}{2}(S/s_{max})^n)]$ mit $s_{max}=\tan(\pi/(2B))/C$.

### Annahmen
Schwerpunkt in Fahrbahnhöhe (keine dynamischen Radlasten), stationäre Reifenkräfte, $A=\mu F_{z,Achse}$, $c=ABC$ gleich der Achs-Schräglaufsteifigkeit der Fahrzeugkonfiguration.

### Randbedingungen
Strecke: jenseits des Maximums Kammscher Kreis $F_q=\sqrt{A^2-F_l^2}$; unter 1.5 m/s Überblendung mit dem kinematischen Modell (Relaxation 50 ms), unter 0.5 m/s rein kinematisch.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $A,B,C$ | Maximalkraft, Formfaktor, Steifigkeitsfaktor | N, -, - | `P.Av`, `P.Bv`, `P.Cv` |
| $s_q$ | Querschlupf | - | `s_q` |
| $\alpha_v,\alpha_h$ | Schräglaufwinkel | rad | `alpha_v`, `alpha_h` |
| $F_{vq},F_{hq}$ | Seitenkräfte | N | `F_vq`, `F_hq` |

### Anwendungsgrenzen
Mittlere bis hohe Geschwindigkeit; Rückwärtsfahrt nur langsam (kinematischer Bereich).

### Vor- und Nachteile
Bildet Sättigung und Quer-Längs-Kopplung ab; im Stand singulär in der Originalform (hier umgangen).

### Numerische Aspekte
Eigenwert $\approx(c_v+c_h)/(mv)$: `stable_dt` $=2/\lambda_{max}$; Reifeninversion mit gesichertem Newton-Verfahren.

### Praktische Auswirkungen
Bremsen/Antreiben verringert das Seitenführungspotential (Über-/Untersteuern).

### In einfachen Worten
Jeder Reifen hat ein begrenztes Kraftbudget; was für Bremsen oder Antreiben verbraucht wird, fehlt für die Kurve.

### Quellen
[@werling2011, Abschn. 4.3.1, 4.3.2], [@pacejka2012, Kap. 4]

## Lyapunov-Tracking mit Orientierungsstabilisierung {#lyapunov_orientation}

### Ziel und Zweck
Stabilisierung der Hinterachsmitte samt Orientierung für langsame Vorwärts- und Rückwärtsfahrt (Satz 4).

### Theorie
Invariante Fehler (4.9): $[e_t,e_n]=R(\psi_d)(y-y_d)$, $e_\psi=\psi-\psi_d$, $\kappa_\delta=\tan\delta/l$; Fehlerdynamik (4.10). Fiktives Regelgesetz und virtueller Eingang:

$$\xi_1=\kappa_d-k_1\left[e_t\frac{\cos e_\psi-1}{e_\psi}+e_n\frac{\sin e_\psi}{e_\psi}\right]-\varsigma k_2e_\psi\quad(4.11)$$

$$w_2=\dot v_d-k_1e_t-k_3e_v+\varsigma k_2e_\psi^2-e_\psi\kappa_d\quad(4.12)$$

Backstepping: $e_\delta=\kappa_\delta-\xi_1$ (4.16), $w_1=-e_\psi v+\dot\xi_1-k_4e_\delta$ (4.17), $u_1=lw_1\cos^2\delta$ (4.15), $u_2$ aus (4.7).

### Herleitung
$V=\frac{1}{2}[k_1e_t^2+k_1e_n^2+e_\psi^2+e_v^2]$ liefert mit (4.11), (4.12) $\dot V=-\dot s_dk_2e_\psi^2-k_3e_v^2\leq0$; LaSalle: $e_v\equiv0\Rightarrow e_t=0$, $e_\psi\equiv0\Rightarrow e_n=0$. Erweitert $V_c=V+\frac{1}{2}e_\delta^2$: $\dot V_c=-\dot s_dk_2e_\psi^2-k_3e_v^2-k_4e_\delta^2\leq0$, asymptotische Stabilität für $\dot s_d\ne0$ (Satz 4). Die hebbaren Lücken werden durch (A.10)-(A.13) genähert (Bemerkung 5, Taylor für $|e_\psi|<0.5$), die Punktgrößen in (4.18) aus (4.10a-c) berechnet (Bemerkung 6). Linearisiert: $\ddot e_t=-k_3\dot e_t-k_1e_t$, $e_n''=-k_2e_n'-k_1e_n$ (4.37).

### Annahmen
KESM gültig, Zustände gemessen, Werling-Vorzeichen: $\psi_d=\theta+\pi$ rückwärts, $v_d=\varsigma v$, $\kappa_d=\varsigma\kappa$.

### Randbedingungen
$\dot s_d\ne0$ für asymptotische Konvergenz (im Stand bleiben die Fehler beschränkt, kein Lenkwinkelsprung, keine Drift).

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $k_1..k_4$ | Verstärkungen (0.5, 2, 2, 10) | div. | `k1`..`k4` |
| $\varsigma$ | Fahrtrichtung | - | `varsigma` |
| $\xi_1$ | fiktive Krümmung | 1/m | `xi1` |
| $w_1,w_2$ | virtuelle Eingänge | 1/(ms), m/s² | `w1`, `w2` |

### Anwendungsgrenzen
Langsame Fahrt; die Fahrzeugfront schwenkt bei großen Korrekturen aus.

### Vor- und Nachteile
Einziger Regler für Rückwärtsfahrt; unruhigeres Lenken als Satz 6 (Werling 5.2).

### Numerische Aspekte
Diskretisierungsfehler O(dt) durch Halteglied (4 mm bei 100 Hz im Nominalfall).

### Praktische Auswirkungen
Standardregler für Rückwärtsfahrt im `werling_bilevel`.

### In einfachen Worten
Der Regler hält die Hinterachse auf der Sollbahn und dreht das Auto in die richtige Richtung – vorwärts wie rückwärts, auch beim Anhalten.

### Quellen
[@werling2011, Abschn. 4.2.3, A.3, A.5], [@khalil2002, Kap. 4, 14]

## Lyapunov-Tracking ohne Orientierungsstabilisierung {#lyapunov_center}

### Ziel und Zweck
Direkte Stabilisierung der geometrischen Fahrzeugmitte ($\lambda\approx l/2$ vor der Hinterachse) bei langsamer Vorwärtsfahrt (Satz 6).

### Theorie
Flachheitsbasierte Sollgrößentransformation (Satz 5):

$$\tilde y_d=y_d+\lambda[\cos\psi_d,\sin\psi_d]^T,\quad \tilde v_d=v_d\sqrt{1+(\lambda\kappa_d)^2},\quad \tilde\theta_d=\psi_d+\arctan(\lambda\kappa_d)\quad(4.20)-(4.22)$$

$$\tilde\kappa_d=\frac{\kappa_d}{\sqrt{1+(\lambda\kappa_d)^2}}+\frac{\lambda\kappa_d'}{(1+(\lambda\kappa_d)^2)^{3/2}}\quad(4.24)$$

Fehler (4.25), Modell 3 (4.26)/(4.27), Regelgesetz:

$$\tilde w_1=-\tilde k_1\tilde v_d\left[\tilde e_t\frac{\cos\tilde e_\theta-1}{\tilde e_\theta}+\tilde e_n\frac{\sin\tilde e_\theta}{\tilde e_\theta}\right]-\tilde k_4\tilde e_\theta\quad(4.30)$$

$$\tilde w_2=\dot{\tilde v}_d-\tilde k_3\tilde e_v-\tilde k_1[\tilde e_t\cos\tilde e_\theta+\tilde e_n\sin\tilde e_\theta]\quad(4.31)$$

mit den Inversen (4.28), (4.29) und danach (4.7).

### Herleitung
$\tilde V=\frac{1}{2}[\tilde k_1\tilde e_t^2+\tilde k_1\tilde e_n^2+\tilde e_\theta^2+\tilde e_v^2]$. Die Terme $\tilde k_1\tilde e_v[\tilde e_t\cos\tilde e_\theta+\tilde e_n\sin\tilde e_\theta]$ aus (4.26a,b) werden nur mit dem Pluszeichen in (4.31) gekürzt: $\dot{\tilde V}=-\tilde k_4\tilde e_\theta^2-\tilde k_3\tilde e_v^2\leq0$. **Entscheidung:** Implementiert ist das Vorzeichen des Beweises; das gedruckte Minus ergibt $\dot{\tilde V}=-\tilde k_4\tilde e_\theta^2-\tilde k_3\tilde e_v^2+2\tilde k_1\tilde e_v\tilde e_n\sin\tilde e_\theta$, indefinit für $(\tilde k_1\tilde e_n)^2>\tilde k_3\tilde k_4$ (numerisch nachgewiesen). Nulldynamik (Satz 7): mit $\tilde e_t\equiv\tilde e_n\equiv0$ folgt

$$\dot e^0_\psi=-\frac{v_d}{\lambda}\left[\sin e^0_\psi+\lambda\kappa_d(1-\cos e^0_\psi)\right]\quad(4.36)$$

stabil für $v_d>0$, $|\kappa_d|<1/\lambda$, $|e_\psi(0)|\leq\pi/2$; dann $|\tilde\beta|<3\pi/4$. Für $v_d<0$ instabil (Taschenmessereffekt).

### Annahmen
Vorwärtsfahrt, $|\tilde\beta|<\pi/2$ (durch den Lenkanschlag erfüllt), Planung für den flachen Ausgang $\lambda=0$.

### Randbedingungen
$|\kappa_d|<1/\lambda$ (bei $\lambda=1.4$ m: $R>1.4$ m), nur Vorwärtsfahrt.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\lambda$ | Abstand Referenzpunkt–Hinterachse | m | `lam` |
| $\tilde k_1,\tilde k_3,\tilde k_4$ | Verstärkungen (0.5, 2, 5) | div. | `k1`, `k3`, `k4` |
| $\tilde\beta$ | Schwimmwinkel des Referenzpunkts | rad | `beta` |
| $\tilde e_\theta$ | Kurswinkelfehler | rad | `e_theta` |

### Anwendungsgrenzen
Nur vorwärts; Orientierung nur über die Nulldynamik stabil.

### Vor- und Nachteile
Ruhigere Lenkung und kleinere Korrekturamplituden als Satz 4 (Werling 5.2); keine Rückwärtsfahrt.

### Numerische Aspekte
Linearisiert $\tilde e_n''=-(\tilde k_4/\tilde v)\tilde e_n'-\tilde k_1\tilde e_n$ (4.38); bei $v_s$ entspricht das den Polen $-1.18$, $-3.82$ 1/s des dynamischen Reglers.

### Praktische Auswirkungen
Standardregler langsam vorwärts; geeignet zum Rangieren in Engstellen.

### In einfachen Worten
Statt die Hinterachse wird die Fahrzeugmitte auf der Bahn gehalten; die Fahrzeugausrichtung stellt sich dabei von selbst richtig ein, solange vorwärts gefahren wird.

### Quellen
[@werling2011, Abschn. 4.2.4, A.4], [@isidori1995, Kap. 4]

## Exakte E/A-Linearisierung für schnelle Fahrt {#exact_io_linearization}

### Ziel und Zweck
Invariantes Trajektorientracking auf dem DESM mit isotropem Reifen bei schneller Fahrt (Satz 8) ohne Schleppfehler.

### Theorie
Ausgang $\tilde y=[x_1,x_2]+\lambda[\cos\psi,\sin\psi]$ (4.46), Fehler (4.48), Hilfsgrößen $\tilde\beta=\arctan(\lambda r/(v\cos\beta)+\tan\beta)$, $\tilde v=v\cos\beta/\cos\tilde\beta$ (4.52)-(4.57), relativer Grad $[2,2]$. Lineare Stabilisierung $\tilde w_1=-k_{n1}\tilde e_n-k_{n2}\dot{\tilde e}_n$, $\tilde w_2=-k_{t1}\tilde e_t-k_{t2}\dot{\tilde e}_t$ (4.68)/(4.69), Pole $-1.18,-3.82$ (quer) und $-0.29,-1.71$ (längs), überkritisch gedämpft. Vorausschau für konstanten Dämpfungsgrad $\zeta$ der Nulldynamik:

$$\lambda(\zeta,v_d)=\frac{2\zeta v_d\sqrt{(\zeta l_vmv_d)^2+c_h(l_v+l_h)(J-ml_hl_v)}-c_hl_h^2-c_hl_vl_h+2\zeta^2l_vmv_d^2}{c_h(l_v+l_h)}\quad(4.70)$$

Lenkrate $u_{\dot\delta}=\dot\delta_{vs}-k_\delta(\delta-u_1)$ mit $\dot\delta_{vs}=d\delta_0/dt$ (4.75).

### Herleitung
Die Bedingung (4.60) $L_f^2\tilde e=\tilde w$ wird äquivalent umgeformt: mit $\omega=\tilde v_d\tilde\kappa_d$, $P=[[0,-1],[1,0]]$ gilt im mitbewegten Frenet-Rahmen

$$R(\tilde\theta_d)\ddot{\tilde y}=[\dot{\tilde v}_d,\tilde v_d^2\tilde\kappa_d]^T+\tilde w-\omega^2\tilde e+2\omega P\dot{\tilde e}+\dot\omega P\tilde e$$

und in Fahrzeugkoordinaten $\ddot{\tilde y}=[F_x/m-\lambda r^2,\ F_y/m+\lambda M_z/J]$; das 2D-Newton-Verfahren löst nach $u=[\delta,F_l]$ (vgl. Kap. 5). Satz 9: Linearisierung um die Geradeausfahrt ergibt die Nulldynamik (4.67) mit $p_0=c_h(l_v+l_h)/(J+\lambda l_vm)$, $p_1=c_h(l_v+l_h)(\lambda+l_h)/(v_d(J+\lambda l_vm))$, stabil für $\lambda>\max(-l_h,-J/(l_vm))$; $\zeta=p_1/(2\sqrt{p_0})$, Auflösen nach $\lambda$ ergibt (4.70). Dynamische Sollgrößentransformation (4.71)-(4.74): ein Referenzfahrzeug mit $x^0=y_d$, $\psi^0=\theta_d-\beta^0$, $v^0=v_d$ und den Zuständen $r^0,\beta^0$ aus (4.72), $u^0$ aus (4.73), wird online simuliert (Bemerkung 10); sein Punkt $\tilde y^0$ ist die Sollgröße. Wegen der stabilen Nulldynamik konvergiert das reale gegen das simulierte Fahrzeug, es bleibt kein Schleppfehler.

### Annahmen
$v>0$, Reifenparameter bekannt, $\gamma$ bekannt (Antrieb nach Layout, Bremsen 0.75), Bedingung (4.49) lokal erfüllt.

### Randbedingungen
$\lambda\in[\lambda_{min},\lambda_{max}]=[0,20]$ m, Änderungsrate 4 m/s; unter $v_{min}=1$ m/s Rückfall auf den kinematischen Regler. Sättigung: Modifikationsfaktor $>1.02$ an der Vorderachse $\Rightarrow$ Lenkwinkel zum Querkraftoptimum $s_q=s_{max}\sqrt{1-(F_{vl}/A_v)^2}$.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $\lambda$ | Vorausschau vor dem Schwerpunkt | m | `lam`, `status.lookahead` |
| $\zeta$ | Dämpfungsgrad Nulldynamik | - | `zeta` |
| $r^0,\beta^0,\delta^0$ | Zustände/Eingang des Referenzfahrzeugs | rad/s, rad, rad | `zd.r0`, `zd.beta0`, `delta0` |
| $k_\delta$ | Lenkwinkelrückführung | 1/s | `k_delta` |

### Anwendungsgrenzen
Lokal (Reifensättigung); Nulldynamik nur für Geradeausfahrt linear analysiert.

### Vor- und Nachteile
Große Vorausschau (11 m bei 30 m/s) ohne Schleppfehler; höherer Rechenaufwand (Newton, Online-Simulation, ca. 0.4 ms/Schritt).

### Numerische Aspekte
Newton mit Finite-Differenzen-Jacobi-Matrix und Schrittweitenhalbierung, Warmstart; Nulldynamik explizites Euler-Verfahren mit $h\leq5$ ms (stabil, da $\lambda=0$ minimalphasig); $\dot{\tilde\kappa}_d$ durch Rückwärtsdifferenz.

### Praktische Auswirkungen
Bei 30 m/s Ausweichen: 2–6 cm Querfehler mit dynamischer, 16 cm mit statischer, 46 cm ohne Transformation.

### In einfachen Worten
Der Regler schaut einen geschwindigkeitsabhängigen Abstand nach vorn und rechnet genau aus, wie stark gelenkt und beschleunigt werden muss; ein mitgerechnetes Idealfahrzeug zeigt ihm, wo dieser vorausschauende Punkt sein muss.

### Quellen
[@werling2011, Abschn. 4.3.3], [@isidori1995, Kap. 5], [@khalil2002, Kap. 13]

## Stoßfreie Reglerumschaltung {#controller_switching}

### Ziel und Zweck
Wechsel zwischen den drei Reglern nach Fahrsituation (Abb. 4.13).

### Theorie
`rear_axle` und $\varsigma=-1$: Satz 4; `rear_axle` und $\varsigma=+1$: Satz 6; `cog`: Satz 8. Bei $v_d=0$ entscheidet $\varsigma$; maßgeblich ist der Referenzpunkt der Trajektorie (Planer schaltet bei $v_s=3$ m/s mit Hysterese).

### Herleitung
Keine Überblendung möglich (unterschiedliche Referenzpunkte, Stetigkeitsverlust bei der Umrechnung, Werling 4.4). Stoßarmut entsteht, weil bei $v_s$ beide Modelle gültig sind, die modellinvertierenden Vorsteueranteile dominieren und die Fehlerdynamiken abgestimmt sind ($k_{n1}=\tilde k_1v_s^2$, $k_{n2}=\tilde k_4$, $k_{t1}=\tilde k_1$, $k_{t2}=\tilde k_3$).

### Annahmen
Konsistente Trajektorien beider Referenzpunkte zum Umschaltzeitpunkt.

### Randbedingungen
Beim Wechsel auf Satz 8 wird die Nulldynamik-Simulation mit den aktuellen Zuständen gestartet.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $v_s$ | Umschaltgeschwindigkeit | m/s | `v_switch` |
| $v_{min}$ | Mindestgeschwindigkeit Satz 8 | m/s | `v_min_dynamic` |

### Anwendungsgrenzen
Harte Umschaltung; Sprünge klein, aber nicht null.

### Vor- und Nachteile
Einfach und analysierbar; jeder Teilregler bleibt für sich stabil.

### Numerische Aspekte
Test: Kraftsprung ca. 1 N, Lenkratensprung ca. 0.01 rad/s beim Wechsel.

### Praktische Auswirkungen
Anfahren, Rangieren und Autobahnfahrt mit einem Reglerbaustein.

### In einfachen Worten
Je nach Tempo und Fahrtrichtung übernimmt der passende Spezialist, und die Übergabe merkt man kaum.

### Quellen
[@werling2011, Abschn. 4.4]

## Reinitialisierung und Bewegungsprädiktion {#reinitialization_trigger}

### Ziel und Zweck
High-level-Anteil der Bi-level-Stabilisierung: Impulsstörungen früh erkennen und die Planung vom prädizierten Fahrzustand neu starten lassen.

### Theorie
Auslösung, sobald

$$(\dot e_t/c_t)^2+(\dot e_n/c_n)^2\geq1$$

mit $\dot e$ nach (4.58), (4.59) im Schwerpunkt bzw. geometrischen Mittelpunkt; optional absolute Schwellen $e_{max}$ (Kap. 2). Prädiktion über die Planungslatenz $\Delta t$ mit konstantem $\dot v_0$, $\dot\theta_0$:

$$x_1=v_0\Delta t+\frac{\dot v_0}{2}\Delta t^2-\frac{v_0\dot\theta_0^2}{6}\Delta t^3-\frac{\dot v_0\dot\theta_0^2}{8}\Delta t^4,\quad x_2=\frac{v_0\dot\theta_0}{2}\Delta t^2+\frac{\dot v_0\dot\theta_0}{3}\Delta t^3-\frac{v_0\dot\theta_0^3}{24}\Delta t^4$$

### Herleitung
Impulsstörungen wirken kurz und zeigen sich sofort als Geschwindigkeits-/Kursänderung, also in $\dot e$, bevor sich große $e$ aufintegrieren (Werling 2.3). Die Taylor-Reihen sind die singularitätsfreie Näherung der geschlossenen Lösung (hebbare Lücke bei $\dot\theta_0=0$). Langsam: $\theta_0$, $\dot\theta_0=v\tan\delta/l$ aus dem KESM; schnell: $\dot\theta_0=a_q/v$ (Fußnote 20).

### Annahmen
Planer beantwortet die Anforderung mit `reinitialized=True`; Krümmung und Beschleunigung setzt er aus der aktuellen Trajektorie fort.

### Randbedingungen
Anforderung gehalten bis zur Antwort (max. 0.5 s), danach 0.3 s Sperrzeit.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $c_t,c_n$ | Schwellwerte (1.0, 0.5) | m/s | `c_t`, `c_n` |
| $\Delta t$ | Prädiktionszeit | s | `prediction_dt` |
| - | prädizierter Zustand | - | `status.prediction` |

### Anwendungsgrenzen
Schwellwerte fahrzeug- und reglerspezifisch (hier für die Mittelklasselimousine eingestellt).

### Vor- und Nachteile
Kein Integratoraufbau großer Fehler, kleine Stellamplituden; erfordert Rückkopplung zur Planung.

### Numerische Aspekte
Prädiktionsfehler über 0.3 s unter 2 cm (Test).

### Praktische Auswirkungen
Seitenwindböe bei 30 m/s: Querfehler 16 statt 85 cm.

### In einfachen Worten
Wird das Auto plötzlich weggestoßen, versucht der Regler nicht mit Gewalt zurück, sondern die Planung bekommt Bescheid und plant einen sanften Weg von der neuen Position.

### Quellen
[@werling2011, Abschn. 2.3, 4.5]

## Split-Range-Längskraftumsetzung {#split_range}

### Ziel und Zweck
Umsetzung der Solllängskraft in Antriebs- und Bremsmomente mit Kompensation der in den Entwurfsmodellen vernachlässigten Fahrwiderstände.

### Theorie
$u=F_{ld}+F_W(v)+I$, $\dot I=k_Im(a_{exp}-a)$; $\varsigma u\geq0$: Antrieb (Rückwärtsgang für $\varsigma=-1$, Grenze `max_drive_force`), sonst Bremse mit $\gamma=0.75$. Anti-Windup: Integration angehalten, solange gesättigt und der Fehler in die Sättigung zeigt.

### Herleitung
Längsbewegung $m\dot v=F_l-F_W(v)-F_s$; mit $F_W$-Vorsteuerung bleibt die unbekannte Störung $F_s$ (Gegenwind, Steigung), die der Integrator stationär genau übernimmt ($\dot I=0\Rightarrow a=a_{exp}$).

### Annahmen
Momente wirken unverzögert; $a_{exp}$ vom Regler (Werling: $w_2$), gemessen $a=a_x+rv_y$.

### Randbedingungen
$|I|\leq0.3mg$, Integration nur bei $|v|>0.3$ m/s oder Sollbeschleunigung.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $F_W$ | Luft- und Rollwiderstand | N | `F_W` |
| $k_I$ | Integratorverstärkung | 1/s | `k_i` |
| $\gamma$ | Bremskraftverteilung | - | `gamma_brake` |

### Anwendungsgrenzen
Kein Motorkennfeld/Schleppmoment (Momentenschnittstelle der vdsim-Strecken).

### Vor- und Nachteile
Einfach, stationär genau; Integrator reagiert langsam.

### Numerische Aspekte
Bedingte Integration statt Rückrechnung.

### Praktische Auswirkungen
4 % Steigung: Längsfehler ohne Integrator ca. $F_s/(mk_{t1})\approx0.8$ m, mit Integrator unter 10 % davon (Test).

### In einfachen Worten
Gas oder Bremse – nie beides; ein kleiner Zusatzanteil lernt Gegenwind und Steigung.

### Quellen
[@werling2011, Abschn. 5.1.2.2, Abb. 5.3], [@astrom2006, Kap. 3]

## Klassische Trackingregler {#classic_tracking}

### Ziel und Zweck
Vergleichsregler: Pure Pursuit, Stanley, LQR, MPC (quer); PID, PI, Vorsteuerung+Rückführung, ACC, Geschwindigkeitsregler (längs).

### Theorie
Pure Pursuit $\delta=\arctan(2l\sin\alpha/L_d)$; Stanley $\delta=\theta_e+\arctan(-ke/(k_s+v))+\delta_{ff}$; LQR auf $[e_1,\dot e_1,e_2,\dot e_2]$ mit DARE, Gain-Scheduling und $\delta_{ff}=l\kappa+EGv^2\kappa-k_3e_{2,ss}$; LTV-MPC mit $[e_y,e_\psi,\delta]$, Eingang $\dot\delta$, $|\delta|\leq\delta_{max}$, $|\dot\delta|\leq\dot\delta_{max}$.

### Herleitung
LQR: ZOH-Diskretisierung des Fehlermodells (Rajamani 3.2), Riccati-Gleichung je Stützstelle. MPC: kondensierte Prädiktion $X=X_0+\Gamma u$ entlang der Solltrajektorie (zeitvariante $v_k,\kappa_k$), QP $\min\frac{1}{2}u^THu+g^Tu$ mit Box- und Summenbeschränkungen, gelöst per ADMM (OSQP-Schema).

### Annahmen
Vorwärtsfahrt, entkoppelte Quer-/Längsregelung.

### Randbedingungen
Lenkwinkelgrenze des Fahrzeugs; MPC-Neuberechnung alle 50 ms.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $L_d$ | Vorausschau | m | `lookahead_gain`, `lookahead_min` |
| $K$ | LQR-Verstärkung | div. | `K` |
| $N$ | MPC-Horizont | - | `horizon` |

### Anwendungsgrenzen
Keine Stabilitätsgarantie im Nichtlinearen (außer Stanley kinematisch), keine Rückwärtsfahrt.

### Vor- und Nachteile
Einfach und bekannt; Kopplungen und Schleppfehler nicht berücksichtigt.

### Numerische Aspekte
LQR 0.1–0.3 ms, MPC 0.3–0.8 ms pro Schritt.

### Praktische Auswirkungen
Doppelspurwechsel 15→20 m/s (DESM): Werling 1.5 cm, LQR 4 cm, MPC 5 cm, Stanley 9 cm, Pure Pursuit 37 cm Querfehler.

### In einfachen Worten
Bewährte Standardregler als Messlatte für die Werling-Regelung.

### Quellen
[@snider2009], [@hoffmann2007], [@rajamani2012, Kap. 3, 5], [@borrelli2017], [@stellato2020], [@astrom2006]
