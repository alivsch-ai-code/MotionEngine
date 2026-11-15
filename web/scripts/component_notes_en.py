"""English texts of the component notes (theory, expert notes, assumptions, limitations).

The German texts are read from the library (ComponentDoc of each component). `generate_domain_locales.py`
fails if a component has a German note without an English text here, or a list of a different length.
"""

NOTES_EN = {
    "world/scenario_engine": {
        "theory": "Synchronous update of all actors (accelerations from the state at time t, then integration with substeps $h \\le h_{max}$). Collisions between oriented rectangles with the separating axis theorem (SAT).",
        "assumptions": [
            "Ego outline as a rectangle; its centre lies midway between the axles (equal overhangs)",
            "Actors react to the ego vehicle through IDM as soon as it occupies their lane",
        ],
        "limitations": [
            "no vehicle dynamics of the actors (kinematic motion along the lane)",
            "disturbances such as the crosswind gust are only reported as an event, not applied by the engine",
        ],
    },
    "perception/object_sensor": {
        "theory": "Polar measurement model: $r_m = r + n_r$, $\\varphi_m = \\varphi + n_\\varphi$ with $n \\sim \\mathcal{N}(0, \\sigma^2)$, plus additive noise on position, speed, orientation and acceleration. An object is visible if one corner lies within range, it intersects the field of view and it is not mostly hidden by closer objects.",
        "assumptions": [
            "Objects as rectangles, occlusion only in the plane (no height information)",
            "Noise is white and normally distributed, objects are independent",
        ],
        "limitations": [
            "no tracking, no false alarms (ghost objects)",
            "no fusion of several sensors",
        ],
    },
    "predictor/constant_acceleration": {
        "theory": "$s_v(t) = s_v(0) + \\dot s_v(0) t + \\tfrac12 \\ddot s_v(0) t^2$, $d(t) = d(0)$; for $\\dot s_v(t) \\le 0$ the standstill is held. Objects without a lane are predicted in Cartesian coordinates along their orientation.",
        "assumptions": [
            "Acceleration constant over the horizon",
            "no lateral motion relative to the lane",
            "at a branch the object follows the default continuation of the lane",
        ],
        "limitations": [
            "Lane changes and turns of other road users are not predicted",
        ],
    },
    "predictor/constant_velocity": {
        "theory": "$x(t) = x_0 + v \\cos\\psi\\, t$, $y(t) = y_0 + v \\sin\\psi\\, t$; with CTRV $\\psi(t) = \\psi_0 + \\dot\\psi t$.",
    },
    "predictor/lane_following": {
        "theory": "Longitudinal: $s(t) = s_0 + \\dot s_0 t$ (optionally with $\\ddot s_0$). Lateral: critically damped $d(t) = d_z + (e_0 + (\\dot d_0 + e_0/\\tau) t) e^{-t/\\tau}$ with $e_0 = d_0 - d_z$. The target offset $d_z$ is the centre of the neighbouring lane if $|\\dot d_0|$ exceeds the intention threshold and the object moves towards it, otherwise the centre of its own lane.",
        "assumptions": [
            "Objects follow the default continuation of the lane",
        ],
        "limitations": [
            "Turning intentions at intersections are not estimated",
        ],
    },
    "behavior_planner/rule_based": {
        "theory": "Lane change in the manner of MOBIL: $\\tilde a_c - a_c + p(\\tilde a_n - a_n) \\pm a_{bias} > \\Delta a_{th}$ with IDM accelerations and a safety check on the prediction. Merging: gap centre $s_{ref} = \\tfrac12 (s_a + s_b)$ (3.15), gap selection by the required acceleration. Right of way: gap acceptance with the predicted occupancy of the conflict zones.",
        "assumptions": [
            "Map knowledge (lanes, markings, stop lines) is known exactly",
            "Objects carry lane_id/s/d from the scenario engine or the perception",
        ],
        "limitations": [
            "no replanning of the route after a missed exit",
            "Left turn on green: simple gap check against oncoming traffic",
        ],
    },
    "trajectory_planner/frenet_naive": {
        "limitations": [
            "no temporal consistency: the result depends on the replanning frequency",
            "Control errors are set to zero in every cycle (no low-level robustness)",
        ],
    },
    "trajectory_planner/learned": {
        "theory": "Imitation learning of the selection of the Werling planner; features: start state, task, curvature ahead, nearest objects, previous choice (Bellman principle).",
        "expert": "docs/learning/trajectory_model.md",
        "assumptions": [
            "Fast driving with d(t), velocity mode",
        ],
        "limitations": [
            "Following, merging, stopping, slow driving and reversing are planned by the Werling planner",
            "The cost distance to the teacher is measured, not bounded",
        ],
    },
    "trajectory_planner/sequential": {
        "limitations": [
            "Longitudinal candidates are sorted lexicographically before lateral candidates",
        ],
    },
    "trajectory_planner/werling": {
        "theory": "Lateral and longitudinal motion are the output of an integrator chain; the jerk-optimal solutions are quintic polynomials (fixed end state) or quartic polynomials (free end position). End times and end offsets are discretized on the target manifold; the best combination that satisfies the constraints is searched lazily in ascending order of cost.",
        "assumptions": [
            "Side slip angle at the reference point = 0 for the collision check",
            "Leading vehicles with constant acceleration (clamped at standstill)",
            "Reference curve with continuous change of curvature (remark 4)",
        ],
        "limitations": [
            "temporal consistency only with inactive constraints and purely consistent cost terms",
            "Class of functions limited to a double change of course (no maze manoeuvres)",
            "Change of direction (ς) only at standstill through the behavior layer",
        ],
    },
    "trajectory_planner/werling_parking": {
        "theory": "Reeds-Shepp curves, Hybrid A*, multi-move exit; time parametrization with a steering rate limit.",
        "expert": "docs/planning/parking.md",
        "assumptions": [
            "Front-axle steering, low speed in parking mode",
        ],
        "limitations": [
            "In the stack only reverse parallel parking",
        ],
    },
    "tracking_controller/acc": {
        "theory": "$a=\\min(a_{cruise},k_g(d-d_0-\\tau v)+k_v(v_l-v))$",
        "expert": "String stability for $\\tau>0$ and suitable gains (Rajamani ch. 5).",
        "assumptions": [
            "Leading vehicle inside the driving corridor of the trajectory",
        ],
        "limitations": [
            "Freedom from collision is not guaranteed",
        ],
    },
    "tracking_controller/composite": {
        "expert": "Stability follows from the partial controllers only for weak coupling.",
        "assumptions": [
            "Lateral and longitudinal dynamics decoupled",
        ],
        "limitations": [
            "Coupling (friction circle) not considered",
        ],
    },
    "tracking_controller/ff_fb": {
        "theory": "$a=a_d+k_v(v_d-v)-k_se_t$",
        "expert": "Error dynamics $\\ddot e_t+k_v\\dot e_t+k_se_t=0$, stable for $k_v,k_s>0$.",
        "assumptions": [
            "Forward driving",
        ],
        "limitations": [
            "Actuator limits only clamped",
        ],
    },
    "tracking_controller/lqr": {
        "theory": "$x=[e_1,\\dot e_1,e_2,\\dot e_2]$, $u=-Kx+\\delta_{ff}$, $K$ from the DARE of the model discretized with ZOH, $\\delta_{ff}=l\\kappa+K_V v^2\\kappa-k_3e_{2,ss}$.",
        "expert": "For every fixed $v$ the closed discrete loop $A_d-B_dK$ is asymptotically stable (stabilizable pair, $Q\\geq0$ observable); slow gain scheduling preserves stability.",
        "assumptions": [
            "Linear tires, small angles, forward driving",
        ],
        "limitations": [
            "Linearization, model singular for v -> 0 (v_min)",
        ],
    },
    "tracking_controller/mpc": {
        "theory": "States $[e_y,e_\\psi,\\delta]$, input $\\dot\\delta$; $\\dot e_y=v_ke_\\psi$, $\\dot e_\\psi=v_k(\\delta/(l+EG\\,v_k^2)-\\kappa_k)$ with $v_k,\\kappa_k$ of the reference trajectory at the times of the horizon; condensed QP, solved with ADMM.",
        "expert": "Recursive feasibility is not guaranteed by the box constraints alone; stable in practice with a sufficiently long horizon (Rawlings/Mayne).",
        "assumptions": [
            "Kinematics with understeer gradient (quasi-stationary yaw dynamics)",
            "Forward driving",
        ],
        "limitations": [
            "No stability proof without terminal cost or terminal constraint",
            "Higher computing effort",
        ],
    },
    "tracking_controller/pi": {
        "theory": "$a=K_Pe_v+K_I\\int e_v$",
        "expert": "Closed loop similar to a second-order lag, stable for $K_P,K_I>0$.",
        "assumptions": [
            "Forward driving",
        ],
        "limitations": [
            "No feedforward",
        ],
    },
    "tracking_controller/pid": {
        "theory": "$a=K_Pe_v+K_I\\int e_v+K_D\\dot e_v$",
        "expert": "Stable for positive gains on the integrator $\\dot v=a$.",
        "assumptions": [
            "Forward driving",
        ],
        "limitations": [
            "No feedforward, following error in e_t",
        ],
    },
    "tracking_controller/pure_pursuit": {
        "theory": "$\\delta=\\arctan(2l\\sin\\alpha/L_d)$, $L_d=\\max(L_{min},kv)$, $\\alpha$ angle to the target point.",
        "expert": "For small errors Pure Pursuit corresponds to a proportional controller on the lateral error with gain $2/L_d^2$; stability follows from the positive look-ahead (Snider 2009).",
        "assumptions": [
            "Kinematic vehicle, forward driving",
        ],
        "limitations": [
            "Cuts corners, stationary lateral error with a long look-ahead",
            "No reversing",
        ],
    },
    "tracking_controller/speed_pi": {
        "theory": "$a=a_d+K_Pe_v+K_II$, $\\dot I=e_v+k_{aw}(a_{sat}-a)/K_I$",
        "expert": "The back-calculation limits the integrator in saturation (Åström/Hägglund).",
        "assumptions": [
            "Forward driving",
        ],
        "limitations": [
            "No position error",
        ],
    },
    "tracking_controller/stanley": {
        "theory": "$\\delta=\\theta_e+\\arctan(-k e_{fa}/(k_{soft}+v))+\\delta_{ff}-k_r(r-v\\kappa)$.",
        "expert": "For the kinematic model the error at the front axle converges exponentially, $\\dot e=-v\\sin(\\arctan(ke/v))$ (Hoffmann et al. 2007).",
        "assumptions": [
            "Forward driving",
        ],
        "limitations": [
            "No reversing, kinematic derivation",
        ],
    },
    "tracking_controller/werling_bilevel": {
        "theory": "Switching according to fig. 4.13; elliptic measure $(\\dot e_t/c_t)^2+(\\dot e_n/c_n)^2\\geq1$ (4.5.1) at the centre of gravity or the geometric centre; Taylor prediction of the reference point over the planning latency (4.5.2).",
        "expert": "Each partial controller is asymptotically stable on its own (theorems 4, 6, 8). Because both models are valid at the moment of switching and the feedforward parts dominate, the jumps stay small; the reinitialization sets the low-level errors to zero (Werling 2.3).",
        "assumptions": [
            "The planner switches reference_point with hysteresis around v_s (contracts.md section 7)",
            "The planner answers reinit_request with a trajectory with reinitialized=True",
        ],
        "limitations": [
            "Hard switching: small jumps of the control input are possible, gains are matched",
            "Thresholds c_t, c_n found by experiment (defaults for the mid-size sedan)",
        ],
    },
    "tracking_controller/werling_dynamic": {
        "theory": "Output (4.46), invariant errors (4.48), relative degree [2,2], linearizing feedback as the solution of (4.60) (2D Newton), linear stabilization (4.68)/(4.69), zero dynamics (4.67), lambda(zeta, v_d) (4.70), online simulation of the zero dynamics (4.71)-(4.74), steering rate control (4.75).",
        "expert": "After the linearization $\\ddot{\\tilde e}_t=\\tilde w_2$, $\\ddot{\\tilde e}_n=\\tilde w_1$ holds; with (4.68)/(4.69) and $k>0$ the errors converge exponentially. The zero dynamics (4.67) are stable for $\\lambda>\\max(-l_h,-J/[l_vm])$ (theorem 9), their damping $\\zeta$ is kept constant through (4.70).",
        "assumptions": [
            "Flat road, no dynamic wheel loads (single-track model)",
            "Tire parameters A, B, C per axle known (certainty equivalence)",
            "Drive and brake forces controlled quickly, force ratio gamma known",
            "v > 0 (forward driving, singular at v = 0)",
        ],
        "limitations": [
            "Only local (tire saturation, condition (4.49))",
            "Actuator limits are not part of the control law",
            "Zero dynamics analysed linearly only for straight driving (theorem 9)",
        ],
    },
    "tracking_controller/werling_kinematic_center": {
        "theory": "Flatness-based transformation of the reference (4.20)-(4.24), invariant errors of the vehicle centre (4.25), error dynamics of model 3 (4.26)/(4.27), control law (4.30)/(4.31) with the inverses (4.28)/(4.29) and back-substitution (4.7).",
        "expert": "With $\\tilde V=\\frac{1}{2}[\\tilde k_1\\tilde e_t^2+\\tilde k_1\\tilde e_n^2+\\tilde e_\\theta^2+\\tilde e_v^2]$ and $\\tilde w_2=\\dot{\\tilde v}_d-\\tilde k_3\\tilde e_v-\\tilde k_1[\\tilde e_t\\cos\\tilde e_\\theta+\\tilde e_n\\sin\\tilde e_\\theta]$ it follows that $\\dot{\\tilde V}=-\\tilde k_4\\tilde e_\\theta^2-\\tilde k_3\\tilde e_v^2\\leq0$ (theorem 6). Zero dynamics (4.36) stable for $v_d>0$, $|\\kappa_d|<1/\\lambda$ (theorem 7).",
        "assumptions": [
            "Kinematic single-track model, |beta~| < pi/2 (met by the steering angle limit)",
            "Forward driving only, |kappa_d| < 1/lambda (theorem 7)",
        ],
        "limitations": [
            "Zero dynamics unstable in reverse (jackknife effect)",
            "Orientation stable only through the zero dynamics (|psi - psi_d| <= pi/2 at the start)",
        ],
    },
    "tracking_controller/werling_kinematic_orientation": {
        "theory": "Invariant errors in the Frenet frame of the reference trajectory (4.9), fictitious control law for $\\kappa_\\delta$ (4.11), virtual input $w_2=\\dot v$ (4.12), backstepping to $u_1=\\dot\\delta$ (4.16)-(4.18), back-substitution (4.15), (4.7).",
        "expert": "With $V_c=\\frac{1}{2}[k_1e_t^2+k_1e_n^2+e_\\psi^2+e_v^2+e_\\delta^2]$, $\\dot V_c=-\\dot s_dk_2e_\\psi^2-k_3e_v^2-k_4e_\\delta^2\\leq0$ holds; LaSalle gives asymptotic stability of $[e_t,e_n,e_\\psi,e_v,e_\\delta]=0$ for $\\dot s_d\\ne0$ (theorem 4). Forward and reverse through $\\varsigma$, no jump of the steering angle at standstill because there is no division by $v$.",
        "assumptions": [
            "No tire slip angles (slow driving, kinematic single-track model)",
            "All states measured, steering angle |delta| < pi/2",
            "Drive and brake forces are set quickly by subordinate control loops",
        ],
        "limitations": [
            "The front swings out during large corrections (reference point at the rear axle)",
            "No actuator limit in the control law (reserve through the planning)",
            "Unsuitable for fast driving (slip neglected)",
        ],
    },
    "vehicle_dynamics/split_range": {
        "theory": "$u=F_{ld}+F_W(v)+k_I\\int m(a_{exp}-a)\\,dt$; $u\\varsigma\\geq0$: drive (reverse gear for $\\varsigma=-1$), otherwise brake. Anti-windup: the integration is halted when the actuator is saturated and the error drives further into saturation (Werling fig. 5.3).",
        "expert": "In steady state (constant disturbance F_s) and with the integrator active, $a\\to a_{exp}$ holds because the integrator takes over the disturbance completely; in saturation its state stays bounded, so that there is no overshoot after leaving saturation.",
        "assumptions": [
            "Powertrain dynamics neglected (torques act without delay, Werling 5.1.2.2)",
            "Brake force distribution fixed at gamma (default 0.75)",
        ],
        "limitations": [
            "No engine map F_M^-1 and no transmission drag torque (torque interface)",
        ],
    },
    "actuator/steering_powertrain": {
        "expert": "The integration of $\\dot\\delta$ is limited (anti-windup), so that the integrator does not run away at the steering stop.",
        "assumptions": [
            "Constant step dt (component period or executor step)",
        ],
        "limitations": [
            "The characteristic error acts on the curvature tan(delta)/l (as in vdsim.actuators)",
        ],
    },
    "vehicle_plant/vehicle_model": {
        "expert": "Explicit integration (Euler/Heun/RK4) with substeps; the substep size is limited by the recommendation or stable_dt of the model (for example DESM: $h<2/\\max(\\lambda_i)$ with $\\lambda\\approx(c_v+c_h)/(mv)$), so that RK4 stays numerically stable.",
        "assumptions": [
            "Control inputs constant over one executor step (zero-order hold)",
        ],
        "limitations": [
            "Reversing only with werling_kesm, bicycle_kinematic (werling_desm only slowly)",
            "Disturbance forces only for models with the states vy and r",
        ],
    },
}
