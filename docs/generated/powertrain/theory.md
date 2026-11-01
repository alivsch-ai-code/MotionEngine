# Antriebsstrang, Bremse und Längsaktuierung – Theorie und Verfahren

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · **Theorie und Verfahren** · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


Übernommen aus [vdsim/powertrain/docs/theory.md](../../../vdsim/powertrain/docs/theory.md).

## Ideale Bremskraftverteilung (EBV) {#ideal_brake_distribution}

### Ziel und Zweck
Die Bremskraft so auf die Achsen verteilen, dass die Hinterachse nicht vor der Vorderachse blockiert (Stabilität).

### Theorie
Bei der Abbremsung $z = F_B/(m g)$ ist die dynamische Vorderachslast $F_{zv} = m g (l_h + z h)/l$. Ideal ist ein Vorderachsanteil gleich dem Lastanteil:

$$\phi_{ideal} = \frac{l_h + z\, h}{l}, \qquad \phi = \mathrm{clip}\left(\phi_{ideal} + 0.03,\ \phi_{BKV},\ 0.85\right)$$

### Herleitung
Beide Achsen nutzen denselben Kraftschluss, wenn $F_{Bv}/F_{zv} = F_{Bh}/F_{zh}$; mit der Längslastverlagerung $m z g h/l$ folgt $\phi_{ideal}$. Der Zuschlag von 3 % lässt die Vorderachse zuerst an die Grenze gehen.

### Annahmen
Starrer Aufbau (kein Nicken in der Lastverlagerung), gleicher Reibwert an allen Rädern.

### Randbedingungen
Ohne EBV gilt die feste Verteilung `brake_balance`; Momente je Rad auf das Maximum begrenzt.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $z$ | Abbremsung | – | `decel` |
| $\phi$ | Bremskraftanteil vorn | – | `front_share()` |
| $\phi_{BKV}$ | feste Grundverteilung | – | `brake_balance` |
| $h$ | Schwerpunkthöhe | m | `cg_height` |

### Anwendungsgrenzen
Keine radindividuelle Verteilung (Kurvenbremsung); das übernehmen ABS/ESP.

### Vor- und Nachteile
- Vorteil: nutzt die Hinterachsbremse bei leichter Bremsung besser aus.
- Nachteil: idealisiert, ohne Toleranzen.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
Stabile Geradeausbremsung; Grundlage der Rekuperationsaufteilung.

### In einfachen Worten
Beim Bremsen drückt das Gewicht nach vorn, also bremst vorn mehr – aber hinten genug, damit Bremsweg kurz bleibt und das Heck nicht ausbricht.

### Quellen
[[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)], [[Reif (2010)](../references.md#reif2010)]

## Antriebsgrenzen von Motor und Getriebe {#drive_torque_limits}

### Ziel und Zweck
Maximale Antriebskraft am Rad in Abhängigkeit von der Geschwindigkeit.

### Theorie
E-Motor (konstantes Moment bis zur Eckdrehzahl, dann konstante Leistung):

$$T_{max}(\omega_M) = \min\left(T_{M,max}, \frac{P_{max}}{\omega_M}\right), \qquad \omega_M = i_M \frac{v}{R}, \qquad F_{max} = \frac{T_{max}\, i_M\, \eta}{R}$$

Verbrennungsmotor: Volllastkennlinie $T(n)$ (linear interpoliert), $n = \omega_R\, i_G i_A / (2\pi/60)$, Hochschalten über $n_{hoch}$, Rückschalten unter $n_{runter}$; oberhalb der Höchstdrehzahl kein Moment.

### Herleitung
Leistung $P = T \omega$; Übersetzung $i$ multipliziert das Moment und dividiert die Drehzahl, der Wirkungsgrad mindert das Moment.

### Annahmen
Stationäre Kennlinien, keine Motordynamik.

### Randbedingungen
E-Motor: kein Moment über `motor_max_rpm`; Leerlaufdrehzahl als Mindestdrehzahl des Verbrenners.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $T_{M,max}$ | maximales Motormoment | N m | `motor_max_torque` |
| $P_{max}$ | maximale Leistung | W | `motor_max_power` |
| $i_M, i_G, i_A$ | Übersetzungen | – | `motor_gear_ratio`, `gear_ratios`, `final_drive` |
| $\eta$ | Triebstrangwirkungsgrad | – | `driveline_efficiency` |

### Anwendungsgrenzen
Keine Zugkraftunterbrechung beim Schalten.

### Vor- und Nachteile
- Vorteil: realistische Beschleunigungskurven mit wenigen Parametern.
- Nachteil: keine Wirkungsgradkennfelder.

### Numerische Aspekte
Division durch die Drehzahl mit $10^{-6}$ geschützt.

### Praktische Auswirkungen
KPI „Beschleunigung 0–100 km/h“.

### In einfachen Worten
Ein E-Motor zieht bis zu einer bestimmten Geschwindigkeit mit voller Kraft, danach ist seine Leistung der Engpass.

### Quellen
[[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)]

## Rekuperation und Bremsmischung {#regenerative_braking}

### Ziel und Zweck
Energie beim Bremsen zurückgewinnen, ohne die Bremsstabilität zu gefährden.

### Theorie
Benötigte Bremskraft je Achse nach EBV $\mathbf{F}_{B} = (\phi, 1 - \phi)\, F_B$; Rekuperation je Achse begrenzt durch die Motorgrenze und den Antriebsanteil der Achse:

$$F_{rek,i} = \min\left(F_{B,i}, F_{rek,max}(v)\, a_i\right), \qquad F_{Reib,i} = F_{B,i} - F_{rek,i}$$

Gesamtkraftanforderung: $F = m a_{req} + F_L + F_R$, begrenzt auf $\ge -1.3\, m g$.

### Herleitung
Die EBV-Verteilung bleibt erhalten, weil Rekuperation und Reibbremse achsweise zusammen den Sollwert ergeben.

### Annahmen
Rekuperation nur oberhalb 1 m/s; ideale Momentenstellung.

### Randbedingungen
Nur E-Antrieb; Verbrenner ohne Rekuperation.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $F_{rek,max}$ | maximale Rekuperationskraft | N | `max_regen_force()` |
| $a_i$ | Antriebsanteil der Achse | – | `pt_share` |
| $F_{Reib,i}$ | Reibbremskraft je Achse | N | `friction_axle` |

### Anwendungsgrenzen
Keine Koordination mit ABS (ABS moduliert nur das Reibbremsmoment).

### Vor- und Nachteile
- Vorteil: maximale Rückgewinnung bei stabiler Verteilung.
- Nachteil: ideale Überblendung ohne Totzeiten.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
KPIs „Rekuperierte Energie“ und „Verbrauch“.

### In einfachen Worten
Der Elektromotor bremst als Generator zuerst; was er nicht schafft, übernehmen die normalen Bremsen.

### Quellen
[[Reif (2010)](../references.md#reif2010)]

## Energiebilanz {#energy_balance}

### Ziel und Zweck
Energiebedarf, Rückgewinnung und Verbrauch eines Laufs.

### Theorie
$$P_{Batt} = \frac{F_A v}{\eta_M \eta_T} - F_{rek} v\, \eta_M \eta_T + P_{Neben} \ \ (\mathrm{E}), \qquad P = \frac{F_A v}{0.30} + P_{Neben} \ \ (\mathrm{Verbrenner})$$

$$E_{Antrieb} = \int \max(P, 0)\, \mathrm{d}t, \qquad E_{rek} = \int \max(-P, 0)\, \mathrm{d}t$$

### Herleitung
Mechanische Leistung $F v$ über die Wirkungsgradkette auf die Batterie bzw. den Kraftstoff zurückgerechnet.

### Annahmen
Konstante Wirkungsgrade; Verbrenner mit 30 % effektivem Wirkungsgrad.

### Randbedingungen
Rechteckintegration im Reglertakt.

### Variablen
| Symbol | Bedeutung | Einheit | Code-Name |
|---|---|---|---|
| $P_{Batt}$ | Batterieleistung | W | `power_battery` |
| $\eta_M, \eta_T$ | Motor-, Triebstrangwirkungsgrad | – | `motor_efficiency`, `driveline_efficiency` |
| $P_{Neben}$ | Nebenverbraucher | W | `auxiliary_power` |

### Anwendungsgrenzen
Kein Batteriemodell, keine Temperatur.

### Vor- und Nachteile
- Vorteil: einfache Vergleichsgröße.
- Nachteil: absolute Verbräuche nur grob.

### Numerische Aspekte
Keine.

### Praktische Auswirkungen
KPIs in kWh und kWh/100 km.

### In einfachen Worten
Zählt, wie viel Energie aus der Batterie geflossen und wie viel zurückgekommen ist.

### Quellen
[[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)]

## Verknüpfung der Verfahren {#verknuepfung}

| Verfahren | Implementierung | Komponenten | Quellen |
|---|---|---|---|
| [Antriebsgrenzen von Motor und Getriebe](theory.md#drive_torque_limits) | [`engine.ElectricMotor.max_torque`](../../../vdsim/powertrain/engine.py#L63), [`powertrain.Powertrain.max_drive_force`](../../../vdsim/powertrain/powertrain.py#L34) | – | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) |
| [Energiebilanz](theory.md#energy_balance) | [`powertrain.Powertrain.account_energy`](../../../vdsim/powertrain/powertrain.py#L53) | – | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) |
| [Ideale Bremskraftverteilung (EBV)](theory.md#ideal_brake_distribution) | [`powertrain.BrakeSystem.front_share`](../../../vdsim/powertrain/powertrain.py#L74) | – | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Reif (2010)](../references.md#reif2010) |
| [Rekuperation und Bremsmischung](theory.md#regenerative_braking) | [`powertrain.LongitudinalActuation.actuate`](../../../vdsim/powertrain/powertrain.py#L109) | – | [Reif (2010)](../references.md#reif2010) |
