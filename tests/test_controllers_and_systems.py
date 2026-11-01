import numpy as np
import pytest

from vdsim.reporting import evaluate


def _kpis(result):
    return {k.key: k.value for k in evaluate(result)}


@pytest.mark.parametrize("controller,limit", [("stanley", 0.12), ("mpc", 0.05), ("pure_pursuit", 0.8)])
def test_dlc_path_tracking(run, controller, limit):
    result, sim = run(model="double_track", maneuver="iso_double_lane_change", lateral_controller=controller)
    assert sim.stop_reason == "Ende der Trajektorie"
    assert np.max(np.abs(result["lateral_error"])) < limit


def test_stanley_has_no_steady_state_offset_in_tight_turns(run):
    result, _ = run(model="double_track", maneuver="figure_eight")
    assert np.max(np.abs(result["lateral_error"])) < 0.3


def test_acc_keeps_time_gap(run):
    lead = {"initial_gap": 60.0, "time": [0, 8, 14, 300], "speed": [27.8, 27.8, 16.7, 16.7]}
    result, _ = run(model="bicycle_nonlinear", maneuver="straight", maneuver_params={"length": 1200, "speed_kmh": 120},
                    longitudinal_controller="acc", environment={"lead_vehicle": lead}, duration=30)
    k = _kpis(result)
    assert k["collision"] == "nein"
    assert k["min_time_gap"] == pytest.approx(1.8, abs=0.1)
    assert result["speed"][-1] * 3.6 == pytest.approx(60.0, abs=1.5)


@pytest.mark.parametrize("speed", [40, 70])
def test_aeb_avoids_stationary_obstacle(run, speed):
    lead = {"initial_gap": 120.0, "time": [0, 100], "speed": [0.0, 0.0]}
    result, sim = run(model="double_track", maneuver="straight", maneuver_params={"length": 400, "speed_kmh": speed},
                      longitudinal_controller="aeb", longitudinal_params={"base": "speed_pi"},
                      environment={"lead_vehicle": lead}, duration=15)
    assert "Kollision" not in sim.stop_reason
    assert _kpis(result)["min_gap"] > 0.5


def test_lane_keeping_assist_prevents_departure(run):
    off, _ = run(model="double_track", maneuver="highway", lateral_controller="lane_keeping",
                 lateral_params={"enabled": False}, duration=25)
    on, _ = run(model="double_track", maneuver="highway", lateral_controller="lane_keeping", duration=25)
    assert _kpis(off)["lane_departure"] == "ja"
    assert _kpis(on)["lane_departure"] == "nein"


CIRCLE = dict(model="double_track", vehicle="ev_sedan", maneuver="circle",
              maneuver_params={"radius": 30, "laps": 1, "speed_start_kmh": 40, "speed_end_kmh": 60})


def test_torque_vectoring_reduces_understeer(run):
    passive, _ = run(**CIRCLE)
    tv, _ = run(vehicle_overrides={"systems.torque_vectoring_enabled": True}, **CIRCLE)
    assert _kpis(tv)["understeer_gradient"] < 0.85 * _kpis(passive)["understeer_gradient"]


def test_active_roll_reduces_roll_and_rear_steering_acts(run):
    passive, _ = run(**CIRCLE)
    roll, _ = run(vehicle_overrides={"systems.active_roll_enabled": True}, **CIRCLE)
    rws, _ = run(vehicle_overrides={"systems.rear_steering_enabled": True}, **CIRCLE)
    assert _kpis(roll)["max_roll"] < 0.4 * _kpis(passive)["max_roll"]
    assert np.max(np.abs(rws["delta_r"])) > 0.005
    assert _kpis(rws)["understeer_gradient"] < _kpis(passive)["understeer_gradient"]


def test_esp_reduces_side_slip_in_sine_with_dwell(run):
    base = dict(model="double_track", vehicle="sports_car", maneuver="sine_with_dwell",
                maneuver_params={"amplitude_deg": 220, "speed_kmh": 100})
    off, _ = run(**base)
    on, _ = run(vehicle_overrides={"systems.esp_enabled": True}, **base)
    assert _kpis(on)["max_beta"] < _kpis(off)["max_beta"]


def test_latency_chain_scenario_estimates_actuator_error(run):
    steering = {"dead_time": 0.045, "sensor_delay": 0.045, "characteristic_error": True, "feedback_correction": True}
    result, _ = run(model="bicycle_kinematic", maneuver="lane_change", lateral_controller="curvature_feedforward",
                    steering_actuator=steering, dt_control=0.005)
    assert result["error_factor_est"][-1] == pytest.approx(1.10, abs=0.01)
