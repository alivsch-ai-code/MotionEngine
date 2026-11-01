# Visualisierung – Schnittstellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · **Schnittstellen** · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## Komponenten

_Dieses Paket registriert keine Komponenten._

## Öffentliche API

### `vdsim.visualization.animation`

| Name | Art | Beschreibung |
|---|---|---|
| [`animate(result, fps, follow, window)`](../../../vdsim/visualization/animation.py#L10) | Funktion | – |
| [`save_animation(result, path, fps, **kwargs)`](../../../vdsim/visualization/animation.py#L50) | Funktion | – |

### `vdsim.visualization.dashboard`

| Name | Art | Beschreibung |
|---|---|---|
| [`VehicleTopView`](../../../vdsim/visualization/dashboard.py#L16) | Klasse | Bird's-eye view: reference path, cones, lane lines, driven trace and the vehicle with its wheels |
| [`SignalScope`](../../../vdsim/visualization/dashboard.py#L89) | Klasse | Grid of time plots that update from a SimulationResult while it is being recorded |
| [`KPITile`](../../../vdsim/visualization/dashboard.py#L126) | Klasse | – |
| [`GaugeRow`](../../../vdsim/visualization/dashboard.py#L143) | Klasse | live numeric readouts of the most important vehicle states |
| [`Vehicle3DView`](../../../vdsim/visualization/dashboard.py#L182) | Klasse | Body box, wheels and tire force arrows (vertical: Fz, horizontal: Fx/Fy), camera follows |
| [`make_3d_view(parent)`](../../../vdsim/visualization/dashboard.py#L169) | Funktion | 3D view if OpenGL is available, otherwise a placeholder label |

### `vdsim.visualization.plotter`

| Name | Art | Beschreibung |
|---|---|---|
| [`plot_path(ax, result, color, label, reference, outlines)`](../../../vdsim/visualization/plotter.py#L26) | Funktion | – |
| [`overview_figure(result, title)`](../../../vdsim/visualization/plotter.py#L55) | Funktion | – |
| [`tire_figure(result)`](../../../vdsim/visualization/plotter.py#L90) | Funktion | – |
| [`plot_tire_curves(tire_params, loads, axes)`](../../../vdsim/visualization/plotter.py#L112) | Funktion | – |
| [`plot_ggv(ax, result, mu)`](../../../vdsim/visualization/plotter.py#L133) | Funktion | – |
| [`plot_bode(config, speeds, axes)`](../../../vdsim/visualization/plotter.py#L143) | Funktion | – |
| [`heatmap_figure(result)`](../../../vdsim/visualization/plotter.py#L166) | Funktion | wheel loads and friction utilization over time, plus beta / beta-rate phase plane |
| [`suspension_figure(result)`](../../../vdsim/visualization/plotter.py#L197) | Funktion | suspension travel per wheel and body motion (multibody model) |
| [`energy_figure(result)`](../../../vdsim/visualization/plotter.py#L216) | Funktion | – |
| [`compare_figure(results, signals)`](../../../vdsim/visualization/plotter.py#L232) | Funktion | – |
| [`quasi_static_figure(config)`](../../../vdsim/visualization/plotter.py#L249) | Funktion | – |
