"""Vehicle layers: split range (Werling 5.1.2.2), actuator, plant wrapper, component registration and docs."""

import math
from types import SimpleNamespace

import numpy as np
import pytest

from vdsim.framework.context import RunContext
from vdsim.framework.plugins import available_components, create_component, get_component
from vdsim.framework.types import ActuatorCommand, ControlCommand, EgoState
from vdsim.simulation.environment import Environment
from vdsim.simulation.vehicle_state import ControlInput
from vdsim.stabilization import DEFAULT_CONTROLLER
from vdsim.stabilization.simulate import run_closed_loop
from vdsim.stabilization.trajectories import SpeedProfile, build_trajectory, path_from_curvature


def _straight(v, duration=20.0):
    return build_trajectory(path_from_curvature(lambda s: 0.0, v * duration + 50), SpeedProfile([(0, v), (duration, v)]),
                            reference_point="cog")


@pytest.mark.parametrize("disturbance", ["head_wind", "grade"])
def test_split_range_integrator_compensates_disturbance(sedan, disturbance):
    # Environment.wind_speed > 0 is head wind (air speed = vx + wind_speed)
    env = Environment(wind_speed=20.0) if disturbance == "head_wind" else Environment()
    if disturbance == "grade":
        env.grade = 0.04                                 # 4 % uphill (werling models read env.grade)
    traj = _straight(20.0)
    res = {}
    for k_i in (0.0, 0.5):
        log, comps = run_closed_loop("werling_bilevel", traj, sedan, duration=20.0, environment=env,
                                     dynamics_params={"k_i": k_i}, ego_initial=dict(x=0, y=0, psi=0, v=20.0))
        res[k_i] = (log["e_t"][-1], log["e_v"][-1], log["integrator"][-1])
    # without integrator: the Werling feedback alone leaves a steady longitudinal error
    assert abs(res[0.0][0]) > 0.3
    # with integrator: the disturbance force is taken over by the integrator, the error vanishes
    assert abs(res[0.5][0]) < 0.1 * abs(res[0.0][0]) and abs(res[0.5][1]) < 0.02
    expected = 1600 * 9.81 * math.sin(0.04) if disturbance == "grade" else None
    if expected:
        assert res[0.5][2] == pytest.approx(expected, rel=0.1)


def test_split_range_anti_windup(sedan):
    dyn = create_component("vehicle_dynamics/split_range", {"k_i": 1.0})
    dyn.reset(RunContext(vehicle=sedan))
    ego = EgoState(vx=10.0, ax=2.0)
    # demand far beyond the drive limit: actuator saturated, integrator must not wind up
    for k in range(200):
        out = dyn.step(k * 0.01, {"command": ControlCommand(force=30000.0, info={"a_expected": 18.0}), "ego": ego})
    assert out["demand"].info["saturated"] == 1 and abs(dyn.integrator) < 1e-9
    # unsaturated with the same acceleration deficit: integrator grows
    for k in range(200, 300):
        out = dyn.step(k * 0.01, {"command": ControlCommand(force=1000.0, info={"a_expected": 2.5}), "ego": ego})
    assert out["demand"].info["saturated"] == 0 and dyn.integrator > 300.0
    # braking: gamma = 0.75 distribution, reverse gear for varsigma = -1
    out = dyn.step(3.01, {"command": ControlCommand(force=-6000.0, info={"a_expected": -3.75}), "ego": ego})
    bt = out["demand"].brake_torque
    assert bt[0] / (bt[0] + bt[2]) == pytest.approx(0.75, abs=0.01) and np.all(out["demand"].drive_torque == 0)
    dyn.integrator = 0.0
    out = dyn.step(3.02, {"command": ControlCommand(force=-1500.0, direction=-1, info={"a_expected": -0.9}),
                          "ego": EgoState(vx=-1.0)})
    assert np.sum(out["demand"].drive_torque) < 0 and np.all(out["demand"].brake_torque == 0)


def test_actuator_integrates_rate_limits_and_latency(sedan):
    act = create_component("actuator/steering_powertrain")
    act.reset(RunContext(vehicle=sedan, dt=0.01))
    ego = EgoState(delta=0.0)
    for k in range(100):
        u = act.step(k * 0.01, {"demand": ActuatorCommand(steer_rate=0.1, info={"steer_mode": "rate"}), "ego": ego})
    assert u["control"].steer_front == pytest.approx(0.1, abs=1e-6)
    for k in range(100, 1100):
        u = act.step(k * 0.01, {"demand": ActuatorCommand(steer_rate=1.0, info={"steer_mode": "rate"}), "ego": ego})
    assert u["control"].steer_front == pytest.approx(sedan.vehicle.max_steer_angle)
    # latency chain of the lane-change study (dead time) and rate limit
    act = create_component("actuator/steering_powertrain", {"steering": {"dead_time": 0.05, "rate_limit": 0.5}})
    act.reset(RunContext(vehicle=sedan, dt=0.01))
    out = [act.step(k * 0.01, {"demand": ActuatorCommand(steer_angle=0.2, info={"steer_mode": "angle"}),
                               "ego": ego})["control"].steer_front for k in range(60)]
    assert out[4] == pytest.approx(0.0, abs=1e-9) and out[5] > 0
    assert max(np.diff(out)) <= 0.5 * 0.01 + 1e-9 and out[-1] == pytest.approx(0.2, abs=1e-6)
    # drive torque dead time
    act = create_component("actuator/steering_powertrain", {"drive_dead_time": 0.1})
    act.reset(RunContext(vehicle=sedan, dt=0.01))
    tq = [act.step(k * 0.01, {"demand": ActuatorCommand(drive_torque=np.full(4, 100.0)), "ego": ego})["control"]
          .drive_torque[0] for k in range(15)]
    assert tq[9] == 0.0 and tq[10] == pytest.approx(100.0)


@pytest.mark.parametrize("model", ["werling_desm", "werling_kesm", "bicycle_kinematic", "double_track"])
def test_plant_wraps_vehicle_models(sedan, model):
    ctx = RunContext(vehicle=sedan, scenario=SimpleNamespace(ego_initial={"x": 5.0, "y": -2.0, "psi": 0.3, "v": 8.0}))
    plant = create_component("vehicle_plant/vehicle_model", {"model": model})
    plant.reset(ctx)
    ego = plant.output(0.0)["ego"]
    assert (ego.x, ego.y, ego.psi) == pytest.approx((5.0, -2.0, 0.3)) and ego.vx == pytest.approx(8.0)
    u = ControlInput(steer_front=0.05)
    for k in range(50):
        plant.update(k * 0.01, {"control": u}, 0.01)
    ego = plant.output(0.5)["ego"]
    assert ego.t == pytest.approx(0.5) and ego.r > 0 and ego.delta > 0.0 and np.isfinite(ego.delta_rate)


@pytest.mark.parametrize("model,reverses", [("werling_kesm", True), ("bicycle_kinematic", True)])
def test_plant_reverse_driving(sedan, model, reverses):
    plant = create_component("vehicle_plant/vehicle_model", {"model": model})
    plant.reset(RunContext(vehicle=sedan))
    u = ControlInput(drive_torque=np.array([0, 0, -400.0, -400.0]))
    for k in range(200):
        plant.update(k * 0.01, {"control": u}, 0.01)
    ego = plant.output(2.0)["ego"]
    assert (ego.vx < -0.5) == reverses and ego.gear == -1


def test_components_registered_with_docs():
    specs = ["tracking_controller/werling_bilevel", "tracking_controller/werling_kinematic_orientation",
             "tracking_controller/werling_kinematic_center", "tracking_controller/werling_dynamic",
             "vehicle_dynamics/split_range", "actuator/steering_powertrain", "vehicle_plant/vehicle_model"]
    assert DEFAULT_CONTROLLER == specs[0]
    for spec in specs:
        cls = get_component(spec)
        assert cls.LABEL and cls.DOC.summary and cls.DOC.purpose and cls.DOC.references and cls.DOC.expert
        assert cls.DOC.assumptions and cls.DOC.limitations
        cls.describe()
    assert get_component("vehicle_plant/vehicle_model").DIRECT_FEEDTHROUGH is False
    names = {c["name"] for c in available_components("tracking_controller")}
    assert {"werling_bilevel", "pure_pursuit", "stanley", "lqr", "mpc", "pid", "pi", "ff_fb", "acc", "speed_pi",
            "composite"} <= names


def test_traceability_of_equations():
    from vdsim.framework.knowledge import traces_for
    eqs = " ".join(t["equation"] for t in traces_for("vdsim.stabilization"))
    for eq in ("(4.9)", "(4.11)", "(4.20)-(4.24)", "(4.25)", "(4.28)-(4.31)", "(4.60)", "(4.67)", "(4.70)",
               "(4.71)", "(A.10)-(A.13)"):
        assert eq in eqs


def test_parameter_configs_instantiate():
    import json
    from pathlib import Path
    folder = Path(__file__).resolve().parents[2] / "configs" / "stabilization"
    files = sorted(folder.glob("*.json"))
    assert len(files) >= 4
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        entries = []
        if "component" in data:
            entries.append((data["component"], data["params"]))
        entries += [(v["component"], v["params"]) for v in data.get("sets", {}).values()]
        entries += [(k.split("#")[0], v) for k, v in data.items() if "/" in k]
        assert entries, f.name
        for spec, params in entries:
            create_component(spec, params).reset(RunContext())
