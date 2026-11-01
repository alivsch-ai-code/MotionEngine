# Trajektorienstabilisierung nach Werling und Fahrzeugebenen – Beispiele

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · **Beispiele** · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## [examples/stabilization/controller_comparison.py](../../../examples/stabilization/controller_comparison.py)

Comparison of all tracking controllers on the same trajectory (double lane change 15 -> 20 m/s, initial
lateral offset 0.3 m) on the DESM plant and on the double-track model (model error).

Output: examples/stabilization/output/controller_comparison.csv and controller_comparison.png

Verwendet: `vdsim.stabilization.simulate`, `vdsim.stabilization.trajectories`

Ausführen: `python examples/stabilization/controller_comparison.py`

## [examples/stabilization/highway_gust.py](../../../examples/stabilization/highway_gust.py)

Fast driving (30 m/s) with an evasive maneuver and a strong side-wind gust: bi-level stabilization.

Low-level: exact I/O linearization (Satz 8) with speed dependent look-ahead lambda(zeta, v) (4.70) and the
dynamic reference transformation (4.71)-(4.74). High-level: the elliptic error-rate measure (4.5.1)
triggers a re-initialization, the planner (stand-in: replan_from_prediction) restarts the trajectory at the
predicted vehicle state (4.5.2) and merges back into the lane. Compared: with and without re-initialization.

Output: examples/stabilization/output/highway_gust.png

Verwendet: `vdsim.stabilization.simulate`, `vdsim.stabilization.trajectories`

Ausführen: `python examples/stabilization/highway_gust.py`

## [examples/stabilization/plotting.py](../../../examples/stabilization/plotting.py)

Shared helpers of the stabilization examples (plots are saved to examples/stabilization/output/).

Ausführen: `python examples/stabilization/plotting.py`

## [examples/stabilization/reverse_maneuver.py](../../../examples/stabilization/reverse_maneuver.py)

Reverse driving with the bi-level controller: forward arc, stop, reverse into a parking position.

The planner is replaced by two stored rear-axle trajectories; at standstill the direction varsigma of the
active trajectory switches from +1 to -1, and the werling_bilevel controller changes from the controller
without orientation stabilization (Satz 6) to the one with orientation stabilization (Satz 4) - without a
steering angle jump. Plant: werling_kesm (drives backwards).

Output: examples/stabilization/output/reverse_maneuver.png

Verwendet: `vdsim.stabilization.simulate`, `vdsim.stabilization.trajectories`

Ausführen: `python examples/stabilization/reverse_maneuver.py`

## [examples/stabilization/slow_comparison.py](../../../examples/stabilization/slow_comparison.py)

Werling 5.2: comparison of the low-level controllers on a stored slow stop-and-go trajectory.

(a) forward with orientation stabilization (Satz 4), (b) reverse with orientation stabilization,
(c) forward without orientation stabilization (Satz 6, geometric center). The trajectory starts with
v_d = 0 directly at the rear axle of the waiting vehicle (no initial tracking error), stops for one
second every few meters and changes its curvature permanently. Plant: werling_desm (forward) /
werling_kesm (reverse), full chain split range -> actuator -> plant.

Output: examples/stabilization/output/slow_comparison_signals.png, slow_comparison_path.png

Verwendet: `vdsim.stabilization.simulate`, `vdsim.stabilization.trajectories`

Ausführen: `python examples/stabilization/slow_comparison.py`

## Szenarien und Konfigurationen

| Datei | Titel | Beschreibung |
|---|---|---|
| [configs/stabilization/classic_controllers.json](../../../configs/stabilization/classic_controllers.json) | classic_controllers | Parametersätze der klassischen Vergleichsregler (tracking_controller/composite). |
| [configs/stabilization/werling_bilevel_default.json](../../../configs/stabilization/werling_bilevel_default.json) | werling_bilevel_default | Standard-Parametersatz der Bi-level-Stabilisierung (Mittelklasselimousine). Alle Fehlerdynamiken überkritisch gedämpft; Verstärkungen bei v_s so abgestimmt, dass die Umschaltung kaum Sprünge erzeugt (Werling 4.4). |
| [configs/stabilization/werling_dynamic_highway.json](../../../configs/stabilization/werling_dynamic_highway.json) | werling_dynamic_highway | Exakt E/A-linearisierender Regler für Autobahnfahrt, Dämpfungsgrad der Nulldynamik zeta = 1.0 (4.70). |
| [configs/stabilization/werling_slow_orientation.json](../../../configs/stabilization/werling_slow_orientation.json) | werling_slow_orientation | Langsame Vorwärtsfahrt mit Orientierungsstabilisierung (Werling 5.2, Vergleichsfahrt (a)). |
