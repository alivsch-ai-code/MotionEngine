# Visualisierung

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

**Übersicht** · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


`vdsim.visualization` · Quellcode: [vdsim/visualization/](../../../vdsim/visualization) · Paketdoku: [vdsim/visualization/docs/](../../../vdsim/visualization/docs)

## Übersicht

**matplotlib-Diagramme (Pfad, Zustandsgrößen, Reifen, Pacejka-Kurven, GGV, Bode, Heatmaps, Energie, Vergleich), Echtzeit-Widgets (Draufsicht, Signal-Scope, Kacheln, 3D) und Draufsicht-Animation.**

Ergebnisse und Modelleigenschaften müssen schnell erfassbar sein. Das Paket bündelt alle Diagramme für
GUI, PDF-Bericht und Skripte und die Echtzeit-Widgets der Live-Ansicht.

Paket-Docstring:

```text
Visualization: matplotlib plots, 2D animation, real-time dashboard widgets (PySide6/pyqtgraph).
```

| Kennzahl | Anzahl |
|---|---|
| Module | 4 |
| Komponenten | 0 |
| Verfahren/Konzepte | 0 |
| @trace-Einträge | 0 |
| Tests | 1 |
| Beispiele | 1 |

## Architektur

- `plotter.py`: Diagrammfunktionen auf matplotlib-Achsen bzw. -Figuren; feste kategoriale Farbpalette
  (Fahrzeug, Referenz, Räder FL/FR/RL/RR); `plot_tire_curves` wertet das eingestellte Reifenmodell aus,
  `plot_bode` die lineare Analyse, `plot_ggv` das g-g-Diagramm.
- `dashboard.py`: pyqtgraph/PySide6-Widgets `VehicleTopView`, `SignalScope`, `KPITile`, `GaugeRow`, `Vehicle3DView`.
- `animation.py`: Draufsicht-Animation als GIF/MP4 (matplotlib.animation).

### Module

| Modul | Zeilen | Klassen | Inhalt |
|---|---|---|---|
| [`vdsim.visualization`](../../../vdsim/visualization/__init__.py) | 2 | – | Visualization: matplotlib plots, 2D animation, real-time dashboard widgets (PySide6/pyqtgraph). |
| [`vdsim.visualization.animation`](../../../vdsim/visualization/animation.py) | 58 | – | 2D top-view animation of a simulation result (matplotlib), exportable as GIF or MP4. |
| [`vdsim.visualization.dashboard`](../../../vdsim/visualization/dashboard.py) | 264 | VehicleTopView, SignalScope, KPITile, GaugeRow, Vehicle3DView | Real-time dashboard widgets (PySide6 + pyqtgraph): top view, signal scope, KPI tiles, 3D view. |
| [`vdsim.visualization.plotter`](../../../vdsim/visualization/plotter.py) | 267 | – | matplotlib figures: path, state overview, tire curves, GGV, Bode, heatmaps, energy, run comparison. |

### Abhängigkeiten

- nutzt: [analysis](../analysis/index.md), [core](../core/index.md), [tire_models](../tire_models/index.md)
- genutzt von: [gui](../gui/index.md), [reporting](../reporting/index.md)
- externe Bibliotheken: `PySide6`, `matplotlib`, `numpy`, `pyqtgraph`

## Designentscheidungen

| Entscheidung | Begründung | Alternativen |
|---|---|---|
| Feste Farbzuordnung je Entität (Fahrzeug, Referenz, Rad) | dieselbe Größe hat in allen Diagrammen dieselbe Farbe | – |
| Diagrammfunktionen nehmen Achsen entgegen | wiederverwendbar in GUI, Bericht und eigenen Skripten | – |

## Implementierung

- Plots lesen ausschließlich SimulationResult und Metadaten; keine Abhängigkeit vom Simulator-Zustand.

## Erweiterungspunkte

- Neues Diagramm als Funktion in plotter.py und Eintrag in PLOTS des Analyse-Panels

## Verwandte Module

[reporting](../reporting/index.md), [analysis](../analysis/index.md), [tire_models](../tire_models/index.md), [gui](../gui/index.md)

## Hauptquellen

[Milliken und Milliken (1995)](../references.md#milliken1995), [Pacejka (2012)](../references.md#pacejka2012)
