# Fahrzeuganalyse – linear und quasi-statisch

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.analysis` · Quellcode: [vdsim/analysis/](../../../vdsim/analysis) · Paketdoku: [vdsim/analysis/docs/](../../../vdsim/analysis/docs)

## Übersicht

**Kennwerte eines Fahrzeugs ohne Simulation – Eigenlenkgradient, Verstärkungen, Eigenwerte, Frequenzgang, Radlasten, Wankgradient, Rollachse, Lenkkinematik.**

Viele Fahrzeugeigenschaften folgen direkt aus den Parametern. Die analytischen Werte dienen als
schnelle Auslegungshilfe (z. B. Parameterstudie Schräglaufsteifigkeit gegen Eigenlenkgradient) und als
Referenz, gegen die die Simulationsmodelle getestet werden.

Paket-Docstring:

```text
Analysis: quasi-static (loads, roll, kinematics) and linear (gains, eigenvalues, Bode).
```

| Kennzahl | Anzahl |
|---|---|
| Module | 3 |
| Komponenten | 0 |
| Verfahren/Konzepte | 4 |
| @trace-Einträge | 9 |
| Tests | 3 |
| Beispiele | 1 |

## Architektur

- `linear_analysis.LinearSingleTrackAnalysis`: nutzt `LinearBicycleModel.state_space()`; Eigenlenkgradient,
  charakteristische und kritische Geschwindigkeit, stationäre Verstärkungen, Eigenwerte, Bode-Daten, Zusammenfassung.
- `quasi_static.QuasiStaticAnalysis`: Rollachse, Wankgradient, Wanksteifigkeitsverteilung, Radlasten bei
  konstanter Längs- und Querbeschleunigung, Querlastverteilung (LLTD), Abhebegrenze, Sturz, Ackermann-Winkel, Wendekreis.

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.analysis`](../../../vdsim/analysis/__init__.py) | 7 | – | Analysis: quasi-static (loads, roll, kinematics) and linear (gains, eigenvalues, Bode). |
| [`vdsim.analysis.linear_analysis`](../../../vdsim/analysis/linear_analysis.py) | 73 | LinearSingleTrackAnalysis | Linear single-track analysis: understeer, steady-state gains, eigenvalues, frequency response. |
| [`vdsim.analysis.quasi_static`](../../../vdsim/analysis/quasi_static.py) | 98 | QuasiStaticAnalysis | Quasi-static analysis: wheel loads and load transfer, roll (roll axis, roll gradient), steering kinematics. |

### Abhängigkeiten

- nutzt: [core](../core/index.md), [vehicle_models](../vehicle_models/index.md)
- genutzt von: [gui](../gui/index.md), [visualization](../visualization/index.md)
- externe Bibliotheken: `numpy`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Lineare Analyse auf dem identischen Modell, das auch simuliert wird | Test „lineares Modell gleich Analyse“ ist exakt; Achssteifigkeiten kommen aus dem eingestellten Reifenmodell | – |
| Quasi-statische Lasten mit denselben Formeln wie das Zweispurmodell | Validierung des Zweispurmodells innerhalb 2–3 % | – |

## Implementierung

- Eigenfrequenz aus dem Produkt der Eigenwerte (Determinante von A), Dämpfung aus deren Summe (Spur von A).
- Die Abhebegrenze wird durch Abtasten von a_y bis 30 m/s² bestimmt (600 Stützstellen).

### Verfahren und Konzepte

- [Ackermann-Lenkgeometrie und Wendekreis](theory.md#ackermann_steering)
- [Lineare Stabilitäts- und Frequenzganganalyse](theory.md#linear_stability_analysis)
- [Quasi-statische Radlasten und Wankgradient](theory.md#quasi_static_wheel_loads)
- [Eigenlenkgradient und charakteristische Geschwindigkeit](theory.md#understeer_gradient)

## Erweiterungspunkte

- Weitere Kennwerte als Methoden; die GUI (Tab „Kennwerte“) zeigt summary() automatisch

## Verwandte Module

[vehicle_models](../vehicle_models/index.md), [reporting](../reporting/index.md), [visualization](../visualization/index.md)

## Hauptquellen

[ISO 4138:2021 (2021)](../references.md#iso4138), [Milliken und Milliken (1995)](../references.md#milliken1995), [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014), [Rajamani (2012)](../references.md#rajamani2012)
