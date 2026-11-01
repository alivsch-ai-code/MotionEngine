# Reifenmodelle – Rückverfolgbarkeit

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · **Rückverfolgbarkeit**


Kette: **Implementierung → Gleichung/Abschnitt → Verfahren/Konzept → Quelle → Test**. „Code (@trace)“ stammt aus `@trace` im Quelltext, „module.yaml“ aus dem Abschnitt `traceability` der Paketdoku.

| Implementierung | Gleichung | Konzept | Quelle | Tests | Herkunft |
|---|---|---|---|---|---|
| [`BrushTire.forces`](../../../vdsim/tire_models/brush_model.py#L28) | Abschn. 3 | [Bürstenmodell](theory.md#brush_model) | [Pacejka (2012)](../references.md#pacejka2012) | [test_tire_models.py](../../../tests/test_tire_models.py) | module.yaml |
| [`force_magnitude`](../../../vdsim/tire_models/isotropic.py#L71) | Abschn. 4.3.2 (4.42) | [Dynamisches Einspurmodell mit isotropem Reifen](../stabilization/theory.md#isotropic_tire) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py) | Code (@trace) |
| [`lateral_force`](../../../vdsim/tire_models/isotropic.py#L95) | Abschn. 4.3.2 (4.43) | [Dynamisches Einspurmodell mit isotropem Reifen](../stabilization/theory.md#isotropic_tire) | [Werling (2011)](../references.md#werling2011) | [test_stabilization_models.py](../../../tests/stabilization/test_stabilization_models.py) | Code (@trace) |
| [`LinearTire.forces`](../../../vdsim/tire_models/linear_tire.py#L20) | – | [Lineares Reifenmodell mit Reibkreis](theory.md#linear_tire) | [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | [test_tire_models.py](../../../tests/test_tire_models.py) | module.yaml |
| [`PacejkaTire.cornering_stiffness`](../../../vdsim/tire_models/pacejka.py#L43) | Abschn. 4 | [Pacejka Magic Formula](theory.md#magic_formula) | [Pacejka (2012)](../references.md#pacejka2012) | [test_tire_models.py](../../../tests/test_tire_models.py) | module.yaml |
| [`PacejkaTire.forces`](../../../vdsim/tire_models/pacejka.py#L52) | Abschn. 4 | [Kombinierter Schlupf (Gewichtungsfunktionen)](theory.md#combined_slip) | [Pacejka (2012)](../references.md#pacejka2012) | [test_tire_models.py](../../../tests/test_tire_models.py) | module.yaml |
| [`magic_formula`](../../../vdsim/tire_models/pacejka.py#L18) | Abschn. 4 | [Pacejka Magic Formula](theory.md#magic_formula) | [Pacejka (2012)](../references.md#pacejka2012) | [test_tire_models.py](../../../tests/test_tire_models.py) | module.yaml |

## Warum es diese Implementierungen gibt

### `BrushTire.forces`

- **Warum:** Physikalisches Modell der Kraftübertragung im Latsch: elastische Borsten haften im vorderen Bereich und gleiten im hinteren.
- **Theorie:** [Bürstenmodell](theory.md#brush_model)
- **Annahmen:** - Parabolische Druckverteilung, starre Karkasse.
- **Quelle:** [Pacejka (2012)](../references.md#pacejka2012)

### `force_magnitude`

- **Warum:** Entwurfs- und Streckenmodell für schnelle Fahrt mit Quer-Längs-Kopplung der Reifenkräfte.
- **Theorie:** [Dynamisches Einspurmodell mit isotropem Reifen](../stabilization/theory.md#isotropic_tire)
- **Annahmen:** Schwerpunkt in Fahrbahnhöhe (keine dynamischen Radlasten), stationäre Reifenkräfte, $A=\mu F_{z,Achse}$, $c=ABC$ gleich der Achs-Schräglaufsteifigkeit der Fahrzeugkonfiguration.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** mode='modified': Faktor [1+tan(pi/2 (|s|/s_max)^n)] nach Fußnote 17

### `lateral_force`

- **Warum:** Entwurfs- und Streckenmodell für schnelle Fahrt mit Quer-Längs-Kopplung der Reifenkräfte.
- **Theorie:** [Dynamisches Einspurmodell mit isotropem Reifen](../stabilization/theory.md#isotropic_tire)
- **Annahmen:** Schwerpunkt in Fahrbahnhöhe (keine dynamischen Radlasten), stationäre Reifenkräfte, $A=\mu F_{z,Achse}$, $c=ABC$ gleich der Achs-Schräglaufsteifigkeit der Fahrzeugkonfiguration.
- **Quelle:** [Werling (2011)](../references.md#werling2011)
- **Hinweis:** äquivalente Nullstellensuche über den Längsschlupfbetrag statt über F_q

### `LinearTire.forces`

- **Warum:** Einfachstes Modell für den linearen Fahrbereich (kleine Schräglaufwinkel).
- **Theorie:** [Lineares Reifenmodell mit Reibkreis](theory.md#linear_tire)
- **Annahmen:** - Kleine Schlupfwerte, lineare Lastabhängigkeit der Steifigkeiten.
- **Quelle:** [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014)

### `PacejkaTire.cornering_stiffness`

- **Warum:** Empirisches Standardmodell für Reifenkräfte bei reinem Schlupf, das die typische Form der Kennlinie (linearer Anstieg, Maximum, Abfall) mit wenigen Parametern wiedergibt.
- **Theorie:** [Pacejka Magic Formula](theory.md#magic_formula)
- **Annahmen:** - Stationärer Reifen, keine horizontalen/vertikalen Verschiebungen $S_H$, $S_V$ außer durch Sturz.
- **Quelle:** [Pacejka (2012)](../references.md#pacejka2012)
- **Hinweis:** degressive Lastabhängigkeit sin(2 atan(Fz/(p_Ky2 Fz0)))

### `PacejkaTire.forces`

- **Warum:** Gleichzeitiges Bremsen bzw.
- **Theorie:** [Kombinierter Schlupf (Gewichtungsfunktionen)](theory.md#combined_slip)
- **Annahmen:** Die Reduktionsfaktoren $B_{x\alpha}$, $B_{y\kappa}$ sind konstant (nicht lastabhängig).
- **Quelle:** [Pacejka (2012)](../references.md#pacejka2012)

### `magic_formula`

- **Warum:** Empirisches Standardmodell für Reifenkräfte bei reinem Schlupf, das die typische Form der Kennlinie (linearer Anstieg, Maximum, Abfall) mit wenigen Parametern wiedergibt.
- **Theorie:** [Pacejka Magic Formula](theory.md#magic_formula)
- **Annahmen:** - Stationärer Reifen, keine horizontalen/vertikalen Verschiebungen $S_H$, $S_V$ außer durch Sturz.
- **Quelle:** [Pacejka (2012)](../references.md#pacejka2012)
