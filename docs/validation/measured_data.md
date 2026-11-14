# Validation against measured data

Does the vehicle model behave like a real car? This document compares the lateral dynamics of
MotionEngine's single-track model with 46 hours of measurements from four production cars. Nothing in the
model is fitted to the measurements.

Reproduce it with `python scripts/validate_measured.py` (downloads about 165 MB). The numbers below are in
`docs/validation/results.json`.

## 1. Data

| | |
|---|---|
| Measurements | [commaSteeringControl](https://huggingface.co/datasets/commaai/commaSteeringControl) (comma.ai, MIT license): drives of production cars with driver assistance engaged, 60 s segments at 10 Hz |
| Signals used | speed, steering wheel angle, lateral acceleration from the device's localizer |
| Vehicle parameters | public specifications in [opendbc](https://github.com/commaai/opendbc) (MIT license): wheelbase, steering ratio, position of the center of gravity; axle cornering stiffness and yaw inertia scaled from a reference car |

The mass does not matter here: stiffness and inertia are specified per mass, so it cancels in the lateral
model (tested).

## 2. Method

The model is replayed open loop (`vdsim.validation`). The measured steering angle and speed are the
inputs; the lateral acceleration is the output and is compared with the measured one.

- **Model:** the linear single-track model of the library, as a state-space model with the measured speed
  in every step: [v_y, r]' = A(v) [v_y, r] + B(v) δ, a_y = v r + v_y'.
- **Samples:** all samples above 10 m/s.
- **Two results per car:**
  1. **No fit.** Parameters from the public specifications only.
  2. **Steering offset calibrated.** The zero of a steering angle sensor is off by a fraction of a degree
     in every car. The data source estimates this offset while driving and does not publish it. Here one
     offset per 60 s drive is estimated from the data (least squares). This is the only quantity taken
     from the measurements.
- **Yardstick:** the data set contains the lateral acceleration computed by the source's own model, whose
  steering ratio, stiffness and offset are tuned continuously while driving.

Not used: the road roll. With fixed parameters the roll compensation of the reference model did not reduce
the error on this data.

## 3. Results

RMSE in m/s²; R² is the share of the variance of the measurement that the model explains.

| Car | Hours | Measured RMS (max) | No fit | Offset calibrated | Source's tuned model |
|---|---|---|---|---|---|
| Genesis G70 2018 | 8.2 | 0.44 (4.7) | RMSE 0.157, R² 0.870 | RMSE 0.111, R² 0.935 | RMSE 0.071, R² 0.973 |
| Kia Seltos 2021 | 7.8 | 0.74 (9.9) | RMSE 0.161, R² 0.952 | RMSE 0.128, R² 0.970 | RMSE 0.079, R² 0.988 |
| Kia Stinger 2022 | 7.2 | 0.43 (4.1) | RMSE 0.198, R² 0.792 | RMSE 0.094, R² 0.953 | RMSE 0.053, R² 0.985 |
| Toyota C-HR 2018 | 23.2 | 0.49 (5.3) | RMSE 0.382, R² 0.401 | RMSE 0.170, R² 0.881 | RMSE 0.069, R² 0.980 |

Estimated steering offsets (mean ± standard deviation over the drives): G70 −0.33° ± 0.26°, Seltos
0.27° ± 0.43°, Stinger 0.69° ± 0.63°, C-HR 1.31° ± 0.95°.

Gain of the model, offset calibrated (measured = slope × predicted), by lateral acceleration:

| Car | 0.5–1 m/s² | 1–2 m/s² | 2–6 m/s² |
|---|---|---|---|
| Genesis G70 | 0.99 | 1.00 | 0.95 |
| Kia Seltos | 0.92 | 0.93 | 0.93 |
| Kia Stinger | 1.14 | 1.14 | 1.14 |
| Toyota C-HR | 0.82 | 0.80 | 0.78 |

## 4. What the numbers say

- **The structure of the model is right.** With published parameters and no fit, the single-track model
  explains 79 to 95 % of the measured lateral acceleration of three cars.
- **The steering angle zero dominates the error.** An offset of 0.3° to 1.3° at the steering wheel explains
  most of the remaining error: with it calibrated the model explains 88 to 97 %. The C-HR shows this most
  clearly (R² 0.40 without, 0.88 with the offset).
- **The gain depends on the parameters.** For the G70 the gain is within 5 %. The measured lateral
  acceleration is 8 % below the prediction for the Seltos, 14 % above it for the Stinger and about 20 %
  below it for the C-HR. These factors are constant over the lateral acceleration, which points at the
  steering ratio or the stiffness of the specification, not at the model equations.
- **The tuned model of the data source is better** (R² 0.97 to 0.99). It adapts steering ratio, stiffness
  and offset while driving. MotionEngine uses fixed parameters here on purpose.
- **Dynamics add nothing on this data.** The steady-state gain alone is as good as the dynamic model
  (G70: RMSE 0.107 against 0.111). The drives are gentle and sampled at 10 Hz; yaw dynamics above 1 Hz are
  not excited.

## 5. Limits of this validation

- Normal driving on public roads: 86 to 96 % of the samples are below 1 m/s². The nonlinear range of the tires,
  where the double-track and multibody models differ from the single-track model, is not covered.
- Lateral acceleration only. Longitudinal dynamics, roll, load transfer and the actuators are not
  validated against measurements.
- The measured lateral acceleration comes from a sensor fusion and is noisy at small values.
- Four cars of two manufacturers.

## 6. Use it for another car

```python
from vdsim.validation import PublicSpecs, compare, load_segments, vehicle_config

cfg = vehicle_config(PublicSpecs(wheelbase=2.84, steer_ratio=13.56))
result = compare(cfg, load_segments("GENESIS_G70_2018.zip"))
```

The data set has 120 platforms. Add the specifications of a platform to `PLATFORMS` in
`scripts/validate_measured.py`. A log of your own works too: `read_csv` expects the columns `t`, `vEgo`,
`steeringAngleDeg`, `roll`, `latAccelLocalizer` and `latAccelSteeringAngle`.
