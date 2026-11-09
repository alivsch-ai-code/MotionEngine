# Parking planner

`vdsim.planning.parking` plans and drives parking maneuvers into parallel, perpendicular and angled spots,
entered forward or in reverse, on either side. It covers four steering configurations (front, rear only,
four-wheel counter-phase, four-wheel in-phase) and three drive layouts (front, rear, all-wheel drive).
It is available as a Python API (`park()`), as the REST endpoint `POST /park`, on the web app's **Parking**
page and as the assistant tool `plan_parking`. In the automated-driving stack it drives the parking
maneuver of the mission (planner `trajectory_planner/werling_parking`).

## 1. Research summary

| Topic | Approach used | Source |
|---|---|---|
| Shortest paths with reversing | Reeds-Shepp curves: 48 words of at most 5 arcs/lines in the families CSC, CCC, CCCC, CCSC, CCSCC | Reeds and Shepp 1990; formulation of OMPL (Sucan, Moll, Kavraki 2012) |
| Search among obstacles | Hybrid A*: continuous states, closed per cell of a 3D grid; heuristic = max(Reeds-Shepp length without obstacles, grid distance around obstacles); analytic Reeds-Shepp expansion | Dolgov, Thrun, Montemerlo, Diebel 2010; Kurzer 2016 |
| Tight spots | Multi-maneuver parking: the way out is driven with moves to the limit (constant steering until the margin is reached), the search joins it | Vorobieva, Glaser, Minoiu-Enache, Mammar 2015 ("Automatic parallel parking in tiny spots") |
| Path quality | Greedy shortcutting within each move | LaValle 2006, 7.1 |
| Steering configurations | Instantaneous center of rotation (Ackermann condition); four-wheel steering with a fixed ratio of the tangents | Rajamani 2012, 2.2; Mitschke and Wallentowitz 2014, ch. 23 |
| Path tracking | Rear-axle feedback law, valid for both directions of travel | Samson 1995; De Luca, Oriolo, Samson 1998 |
| Traction | Load on the driven axle(s) times friction, with load transfer from slope and acceleration | Mitschke and Wallentowitz 2014, ch. 4 |
| Spot dimensions | Parallel spots 2.0-2.5 m deep, perpendicular 2.5 m x 5.0 m with a 6.0 m aisle, angled 45-60 deg | EAR 2005 (FGSV), ADAC |

Not used: geometric two-arc parallel parking (one maneuver only) and clothoid-based continuous-curvature
paths (Fraichard and Scheuer 2004). The planner's curvature jumps are handled by the closed loop
instead: it slows down to the speed at which the steering rate can follow and steers at standstill
between moves, as production parking assistants do.

## 2. One planner for every steering configuration

At parking speed the tires roll without side slip, so the vehicle turns about the instantaneous center
of rotation (ICR) where the normals of the wheels meet. With the front angle δf at x_f and the rear angle
δr at x_r (body frame, CoG at 0), the point P = (x_c, 0) below the ICR moves exactly along the vehicle
axis:

```
x_c   = (x_f tan δr - x_r tan δf) / (tan δr - tan δf)
kappa = (tan δf - tan δr) / L
```

If the rear angle is coupled by a fixed ratio of the tangents, tan δr = k tan δf, then x_c does not
depend on the steering angle. P is a fixed point of the body that moves like the rear axle of an ordinary
car, so one Reeds-Shepp / Hybrid A* planner plans P with the configuration's minimum radius:

| Mode | k | Reference point P | Turning radius (mid-size sedan) |
|---|---|---|---|
| front | 0 | rear axle | 4.09 m |
| rear (rear wheels only) | front fixed | front axle | 4.09 m (same angle limit, mirrored) |
| counter (four-wheel, counter-phase) | -0.3 | 0.65 m ahead of the rear axle | 3.76 m (rear limit 10 deg) |
| in_phase (four-wheel, in-phase) | +0.3 | 1.2 m behind the rear axle | 6.99 m |

`tests/planning/test_parking.py` checks P and the curvature against the explicit ICR construction for
all four modes.

## 3. Planning pipeline

1. **Way out** (`ParkingPlanner._escape`): from the goal, moves with constant steering (full or half
   lock either way, or straight) are driven until the clearance margin is reached; then the gear changes.
   This is a best-first search over move sequences. It returns up to four geometrically different ways
   out, each ending where the vehicle keeps 0.6 m clearance and is half a vehicle length from the spot.
2. **Hybrid A*** (`ParkingPlanner._search`): from the start, with arc primitives (5 curvatures x 2
   directions, 0.6 m) and costs for length, reverse driving, gear changes and steering. A lazy heuristic
   computes the Reeds-Shepp part only for nodes that reach the top of the queue. Analytic shots may end
   at the goal (with the required final direction) or at any gear-change pose of a way out, which is then
   driven backwards into the spot. After the first solution the search continues for 400 nodes and
   keeps the cheapest.
3. **Shortcutting** within each move, and a **curvature reserve**: plans use 90 % of the maximum
   curvature, so the controller keeps steering headroom.

Collision check: obstacles are rasterized (5 cm), and the distance transform gives the clearance. A pose
is free if the outline of the vehicle rectangle keeps the margin (15 cm). A three-circle test and a
circumscribed-circle test accept most poses without sampling the outline.

## 4. Closed loop

`drive()` runs the path move by move on a low-speed model:
- **Lateral:** P moves without side slip; the actual road-wheel angles follow the commands with a rate
  limit of 0.6 rad/s.
- **Longitudinal:** the drive force at the driven axle(s) is limited by μ times their load (slope and load
  transfer included); braking acts on all wheels.
- **Speed:** the profile is limited by steering rate ÷ steering change per meter and stops at the end of
  each move.
- **Steering:** the controller is the Samson rear-axle law with a 0.5 s curvature preview.

KPIs reported: final position and heading error, maximum tracking error, minimum clearance, maneuver
time, moves, maximum front and rear steering angles, standstill steering time, and time spent at the
traction limit.

## 5. Results (mid-size sedan, `PlannerSettings()` defaults, 4 vCPU)

Plan, then drive: 3 spot kinds × 2 entries × 4 steering modes, with the default dimensions (6.2 m
parallel gap in this run, 6.0 m aisles).

| | front | rear | counter | in_phase |
|---|---|---|---|---|
| parallel, reverse | ok, 10 moves | ok, 8 | ok, 24 | ok, 6 |
| parallel, forward | ok, 3 | ok, 3 | ok, 7 | ok, 3 |
| perpendicular, reverse | ok, 2 | ok, 4 | ok, 4 | no path |
| perpendicular, forward | ok, 5 | ok, 1 | ok, 1 | no path |
| angled, reverse | ok, 4 | no path | ok, 4 | no path |
| angled, forward | ok, 3 | ok, 1 | ok, 1 | no path |

For every result that drives: final position error 1-12 cm, final heading error below 3 deg, tracking
error 2-14 cm, and planning time 0.3-12 s.

In-phase four-wheel steering is a high-speed mode. With a 7 m turning radius it does not fit standard
6 m aisles; production systems switch to counter-phase below about 30-60 km/h.

## 6. Drive layout

The drive layout does not change the path. It decides whether the vehicle can move on a slope or on low
friction. The mid-size sedan carries 55 % of its weight on the front axle. On a 10 % uphill slope with
μ = 0.2:
- the front axle can transmit 1.67 kN and the rear axle 1.46 kN;
- slope plus rolling resistance need 1.80 kN;
- so front- and rear-wheel drive get stuck, and all-wheel drive parks.

## 7. Automated-driving stack (review finding F2)

Before, the reverse phase of `laengsparken_rueckwaerts` ran the Werling planner on the reversed lane
center line. Its velocity mode had a standstill local optimum, so the vehicle stayed beside the gap.

Now the behavior layer stops beside the gap as before, then hands a parking task to the planner:
- the goal (the spot center);
- the perceived parked vehicles;
- the curbs;
- the required final direction.

`trajectory_planner/werling_parking` plans the path once and gives the bi-level controller one move at
a time: reference point at the rear axle, re-anchored every cycle, stopping at each cusp. The scenario
now passes all criteria: parked 0.21 m and 0.3 deg from the spot center, no collision, no off-road
steps, final speed 0.

## 8. References

- J. A. Reeds, L. A. Shepp: Optimal paths for a car that goes both forwards and backwards. Pacific J. Math. 145(2), 1990.
- D. Dolgov, S. Thrun, M. Montemerlo, J. Diebel: Path planning for autonomous vehicles in unknown semi-structured environments. IJRR 29(5), 2010.
- K. Kurzer: Path planning in unstructured environments: a real-time hybrid A* implementation for fast and deterministic path generation for the KTH Research Concept Vehicle. Master thesis, KTH, 2016.
- H. Vorobieva, S. Glaser, N. Minoiu-Enache, S. Mammar: Automatic parallel parking in tiny spots: path planning and control. IEEE T-ITS 16(1), 2015.
- S. M. LaValle: Planning Algorithms. Cambridge University Press, 2006.
- C. Samson: Control of chained systems: application to path following and time-varying point-stabilization of mobile robots. IEEE TAC 40(1), 1995.
- A. De Luca, G. Oriolo, C. Samson: Feedback control of a nonholonomic car-like robot. In: Robot Motion Planning and Control, Springer, 1998.
- R. Rajamani: Vehicle Dynamics and Control, 2nd ed. Springer, 2012.
- M. Mitschke, H. Wallentowitz: Dynamik der Kraftfahrzeuge, 5th ed. Springer Vieweg, 2014.
- T. Fraichard, A. Scheuer: From Reeds and Shepp's to continuous-curvature paths. IEEE T-RO 20(6), 2004.
- I. A. Sucan, M. Moll, L. E. Kavraki: The Open Motion Planning Library. IEEE RAM 19(4), 2012.
