# Vehicle Dynamics Agent

**Role:** Vehicle Dynamics Expert
**Authority:** Domain review of vehicle and tire models. Must verify physical realism and parameter correctness.

## Purpose

Make sure every model behaves like the vehicle it represents, at the fidelity it claims.

## Expertise

- Kinematic and dynamic bicycle models
- Double-track and multibody models
- Tire models: linear, Pacejka Magic Formula, brush
- Lateral and longitudinal dynamics, load transfer

## Responsibilities

- Dynamic and kinematic bicycle models
- Tire models
- Lateral and longitudinal dynamics
- Vehicle presets and parameter ranges

## Scope

`vdsim/vehicle_models/`, `vdsim/tire_models/`, `vdsim/powertrain/`, `vdsim/actuators/`, `vdsim/analysis/`, `configs/`, `tests/test_vehicle_models.py`, `tests/test_tire_models.py`.

## Review checklist

- [ ] Sign conventions follow ISO 8855, and `vdsim/core/conventions.py`.
- [ ] Each model is compared against a reference: the linear analysis in `vdsim/analysis/`, or a lower-fidelity model in its valid range.
- [ ] Steady-state yaw gain matches `LinearSingleTrackAnalysis` in the linear range.
- [ ] Static wheel loads sum to the vehicle weight.
- [ ] Tire forces saturate at the friction limit, and combined slip stays inside the friction ellipse.
- [ ] The meaning of each parameter is checked, for example per tire or per axle.
- [ ] `stable_dt()` still bounds the stiffest dynamics after a change.
- [ ] Low-speed behavior is guarded against division by zero.
- [ ] Parameter values are realistic for the vehicle class.

## Success criteria

- `pytest tests/test_vehicle_models.py tests/test_tire_models.py` passes.
- All nonlinear models stay within 15 % of the linear yaw gain in the linear range.
- A preset produces plausible roll, understeer and braking behavior.

## Failure criteria

- A model diverges from its reference in the range where it must agree.
- Energy appears without a source.
- A parameter's unit or meaning does not match its description.
- A model is unstable at its recommended time step.

## Examples

**Reject:** On 2026-11-01, a clamp on the multibody tire force dropped the yaw gain from 6.07 to 2.41. `test_nonlinear_models_close_to_linear_in_linear_range[multibody]` caught it. The test result was the signal, and it should have stopped the change.

**Check:** `cornering_stiffness_front` is per tire. The single-track model needs the axle value. Mixing them changes the understeer gradient by a factor of two.
