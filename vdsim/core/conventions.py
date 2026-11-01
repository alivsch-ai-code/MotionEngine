"""Units and sign conventions used throughout vdsim (ISO 8855).

- SI units everywhere (m, s, kg, N, rad). Degrees and km/h only in GUI and reports.
- Earth frame: x east/forward, y north/left, yaw angle psi counter-clockwise positive.
- Vehicle frame: x forward, y left, z up.
- Positive steering angle steers left. A positive slip angle alpha produces a
  positive (leftward) lateral tire force.
- Longitudinal slip kappa = (omega * R - v_x,wheel) / |v_x,wheel|: positive when driving,
  negative when braking.
- Wheel order in every 4-element array: FL, FR, RL, RR.
"""

FL, FR, RL, RR = 0, 1, 2, 3
WHEEL_NAMES = ("FL", "FR", "RL", "RR")
FRONT = (FL, FR)
REAR = (RL, RR)
LEFT = (FL, RL)
RIGHT = (FR, RR)

G = 9.81            # m/s^2
AIR_DENSITY = 1.204  # kg/m^3 at 20 degC
