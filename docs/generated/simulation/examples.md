# Simulationskern – Löser, Regelkreis, Szenarien, Ergebnisse – Beispiele

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · **Beispiele** · [Einschränkungen](limitations.md) · [Validierung](validation.md) · [Quellen](references.md) · [Rückverfolgbarkeit](traceability.md)


## [examples/custom_nodes/python/my_vehicle_model.py](../../../examples/custom_nodes/python/my_vehicle_model.py)

Custom node (Python): kinematic single-track vehicle with the ports of VehiclePlantBase.

Graph spec: "python:examples/custom_nodes/python/my_vehicle_model.py:KinematicBicyclePlant"

    input:  control (ControlInput: steer_front, drive/brake torque per wheel)
    output: ego (EgoState at the CoG)
    no direct feedthrough: output(t) from the state, update(t, inputs, dt) integrates

The file also contains CommandToControl, a simplified stand-in for the layers Vehicle
Dynamics + Actuators (ControlCommand -> ControlInput), so the example chain can be closed
with Python custom nodes only.

Verwendet: `vdsim.simulation.vehicle_state`

Ausführen: `python examples/custom_nodes/python/my_vehicle_model.py`

## [run_scenario.py](../../../run_scenario.py)

Command line: run scenarios, print KPIs, export results and reports.

python run_scenario.py --list
python run_scenario.py iso_doppelspurwechsel_80 --plot
python run_scenario.py kreisfahrt_r40 bremsen_100_abs --report bericht.pdf --summary bericht.md
python run_scenario.py configs/scenarios/slalom_60.json --csv slalom.csv
python run_scenario.py --all

Verwendet: `vdsim.simulation.scenario`, `vdsim.simulation.simulator`

Ausführen: `python run_scenario.py`
