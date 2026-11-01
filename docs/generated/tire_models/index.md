# Reifenmodelle

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.tire_models` · Quellcode: [vdsim/tire_models/](../../../vdsim/tire_models) · Paketdoku: [vdsim/tire_models/docs/](../../../vdsim/tire_models/docs)

## Übersicht

**Stationäre Reifenkraftmodelle – linear mit Reibkreis, Pacejka Magic Formula mit kombiniertem Schlupf und Bürstenmodell.**

Die Reifenkräfte bestimmen das Fahrverhalten im Grenzbereich. Das Paket stellt drei austauschbare
Modelle mit identischer Schnittstelle `forces(alpha, kappa, fz, mu, camber) -> (fx, fy, mz)` bereit:
ein lineares Modell für Reglerauslegung und Analyse, die Magic Formula als empirisches Standardmodell
und das physikalisch begründete Bürstenmodell. Alle Modelle sind vektorisiert (numpy) und werden von allen
Fahrzeugmodellen genutzt.

Paket-Docstring:

```text
Tire models: linear, Pacejka Magic Formula, brush model.
```

| Kennzahl | Anzahl |
|---|---|
| Module | 5 |
| Komponenten | 4 |
| Verfahren/Konzepte | 5 |
| @trace-Einträge | 7 |
| Tests | 3 |
| Beispiele | 1 |

## Architektur

- `linear_tire.LinearTire`: Kräfte proportional zu Schlupf und Last, optional am Reibkreis begrenzt.
- `pacejka.PacejkaTire` mit der Funktion `magic_formula(slip, B, C, D, E)`; lastdegressive
  Schräglaufsteifigkeit, lastabhängiger Reibwert, Sturz als äquivalenter Schräglaufwinkel,
  kombinierter Schlupf über cos(atan)-Gewichtungsfunktionen, Rückstellmoment über Reifennachlauf.
- `brush_model.BrushTire`: theoretischer Schlupf, isotroper kombinierter Schlupf, parabolische Druckverteilung.
- `__init__.create_tires(TireParameters)` erzeugt (vorn, hinten), `create_tire_set` eine Instanz für vier Räder.
Parameter stammen aus `vdsim.core.parameters.TireParameters`.

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.tire_models`](../../../vdsim/tire_models/__init__.py) | 32 | – | Tire models: linear, Pacejka Magic Formula, brush model. |
| [`vdsim.tire_models.brush_model`](../../../vdsim/tire_models/brush_model.py) | 51 | BrushTire | Brush tire model with parabolic pressure distribution (Pacejka, Tyre and Vehicle Dynamics, ch. |
| [`vdsim.tire_models.isotropic`](../../../vdsim/tire_models/isotropic.py) | 177 | IsotropicPacejkaTire | Isotropic Pacejka tire (Werling 2011, 4.3.2) and its combined-slip inversion. |
| [`vdsim.tire_models.linear_tire`](../../../vdsim/tire_models/linear_tire.py) | 29 | LinearTire | Linear tire: forces proportional to slip and load, limited by the friction circle. |
| [`vdsim.tire_models.pacejka`](../../../vdsim/tire_models/pacejka.py) | 68 | PacejkaTire | Pacejka Magic Formula tire model (reduced parameter set). |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [framework](../framework/index.md)
- genutzt von: [controllers](../controllers/index.md), [core](../core/index.md), [stabilization](../stabilization/index.md), [vehicle_models](../vehicle_models/index.md), [visualization](../visualization/index.md)
- externe Bibliotheken: `dataclasses`, `math`, `numpy`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Reduzierter Magic-Formula-Parametersatz aus physikalischen Kenngrößen (Schräglaufsteifigkeit, Längssteifigkeit, Nennlast, mu) | Parameter sind aus Datenblättern und Messungen leicht zu schätzen; B folgt aus K/(C D), damit stimmt die Anfangssteigung exakt | vollständiger MF-6.2-Datensatz mit TIR-Import (Ausbaustufe) |
| Kombinierter Schlupf über Gewichtungsfunktionen G = cos(atan(B kappa)) | einfache, glatte und monotone Reduktion; entspricht dem Aufbau der Magic Formula | Reibellipse (nicht glatt), Similarity-Ansatz |
| Gemeinsame Schnittstelle für alle Modelle, vektorisiert | Zweispur- und Mehrkörpermodell berechnen alle vier Räder in einem Aufruf | – |

## Implementierung

- Alle Modelle setzen negative Radlasten auf 0 und addieren 1e-9 in Nennern (abgehobenes Rad ohne Division durch null).
- PacejkaTire normiert die degressive Steifigkeit so, dass sie bei Nennlast genau `cornering_stiffness` ergibt.
- Der Reibwert `mu` ist das Produkt aus Reifen-mu (TireParameters.mu) und Fahrbahn-mu der Reibwertkarte.

### Komponenten

| Komponente | Bezeichnung | Version | Kurzbeschreibung |
|---|---|---|---|
| [`tire_model/brush`](components/tire_model__brush.md) | – | legacy | Bürstenmodell mit parabolischer Druckverteilung und isotropem kombiniertem Schlupf. |
| [`tire_model/isotropic`](components/tire_model__isotropic.md) | – | legacy | Isotropic Magic Formula tire for the generic vehicle models (per wheel, vectorized). |
| [`tire_model/linear`](components/tire_model__linear.md) | – | legacy | Lineares Reifenmodell mit Lastproportionalität und optionaler Begrenzung am Reibkreis. |
| [`tire_model/pacejka`](components/tire_model__pacejka.md) | – | legacy | Magic Formula (reduzierter Parametersatz) mit lastabhängiger Steifigkeit und Reibung, Sturz, kombiniertem Schlupf und Rückstellmoment. |

### Verfahren und Konzepte

- [Bürstenmodell](theory.md#brush_model)
- [Kombinierter Schlupf (Gewichtungsfunktionen)](theory.md#combined_slip)
- [Dynamisches Einspurmodell mit isotropem Reifen](../stabilization/theory.md#isotropic_tire)
- [Lineares Reifenmodell mit Reibkreis](theory.md#linear_tire)
- [Pacejka Magic Formula](theory.md#magic_formula)

## Erweiterungspunkte

- Neues Reifenmodell als Unterklasse von vdsim.core.interfaces.TireModel mit "@register('tire_model', name)"; danach tires.model = name
- MF 6.2 mit TIR-Import, Einlaufverhalten erster Ordnung (Relaxationslänge)

## Verwandte Module

[vehicle_models](../vehicle_models/index.md), [core](../core/index.md), [visualization](../visualization/index.md)

## Hauptquellen

[Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Pacejka (2012)](../references.md#pacejka2012), [Schramm et al. (2018)](../references.md#schramm2018)
