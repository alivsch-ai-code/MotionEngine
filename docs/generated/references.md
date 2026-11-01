# Literaturverzeichnis

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

Alle Einträge aus `docs/references/*.yaml` (inkl. `user.yaml`). Zitierschlüssel in Klammern.

## Dissertation / Abschlussarbeit

### Fielding (2000) {#fielding2000}

Fielding, R. T. (2000): Architectural Styles and the Design of Network-based Software Architectures. Dissertation. University of California, Irvine. https://ics.uci.edu/~fielding/pubs/dissertation/top.htm. `[fielding2000]`

Verwendet in: – (noch nicht verknüpft)

### Werling (2011) {#werling2011}

Werling, M. (2011): Ein neues Konzept für die Trajektoriengenerierung und -stabilisierung in zeitkritischen Verkehrsszenarien. Dissertation. KIT Scientific Publishing (Schriftenreihe des Instituts für Angewandte Informatik / Automatisierungstechnik, Band 34). ISBN 978-3-86644-631-1. https://publikationen.bibliothek.kit.edu/1000021738. `[werling2011]`

_Dissertation KIT 2010. Grundlage für Trajektorienplanung (Kap. 3), Bi-level-Stabilisierung (Kap. 2) und Trackingregelung (Kap. 4)._

Verwendet in: `@trace:vdsim.behavior.rule_based.RuleBasedBehavior._update_merge`, `@trace:vdsim.geometry.reference_line.ReferenceLine.project`, `@trace:vdsim.geometry.reference_line.ReferenceLine.to_cartesian`, `@trace:vdsim.geometry.reference_line.ReferenceLine.to_frenet`, `@trace:vdsim.matlab.analysis._Analyzer._control`, `@trace:vdsim.planning.analysis.continuous_solution`, `@trace:vdsim.planning.analysis.estimate_sampling_horizon`, `@trace:vdsim.planning.analysis.lock_in_distance`, `@trace:vdsim.planning.analysis.transversality_residual`, `@trace:vdsim.planning.collision.CircleCollisionChecker.geometry_info`, `@trace:vdsim.planning.combination.CandidateEvaluator.batch`, `@trace:vdsim.planning.combination.time_to_arc`, `@trace:vdsim.planning.constraints.MaxLateralAcceleration.violation`, `@trace:vdsim.planning.constraints.TireForceConstraint.violation`, `@trace:vdsim.planning.constraints.VehicleEnvelope.violation`, `@trace:vdsim.planning.cost.CostModel`, `@trace:vdsim.planning.cost.TerminalDeviationCost.lateral`, `@trace:vdsim.planning.kinematics.convert_reference`, `@trace:vdsim.planning.kinematics.taylor_prediction`, `@trace:vdsim.planning.lateral.build_lateral_set`, `@trace:vdsim.planning.longitudinal.FollowingTarget.state`, `@trace:vdsim.planning.longitudinal.MergingTarget.state`, `@trace:vdsim.planning.longitudinal.ObjectMotion.state`, `@trace:vdsim.planning.longitudinal.build_longitudinal_set`, `@trace:vdsim.planning.planner.WerlingPlanner._compose_output`, `@trace:vdsim.planning.planner.WerlingPlanner._start_state`, `@trace:vdsim.planning.polynomials.jerk_integral`, `@trace:vdsim.planning.polynomials.quartic_coefficients`, `@trace:vdsim.planning.polynomials.quintic_coefficients`, `@trace:vdsim.planning.sampling.end_grid`, `@trace:vdsim.planning.selection.fallback_candidate`, `@trace:vdsim.planning.selection.initial_jerk`, `@trace:vdsim.planning.selection.select_mode`, `@trace:vdsim.prediction.predictors.ca_motion`, `@trace:vdsim.prediction.predictors.lateral_convergence`, `@trace:vdsim.research.metrics.consistency_deviation`, `@trace:vdsim.stabilization.errors.center_errors`, `@trace:vdsim.stabilization.errors.flat_reference_transform`, `@trace:vdsim.stabilization.errors.frenet_errors`, `@trace:vdsim.stabilization.errors.rear_axle_error_rates`, `@trace:vdsim.stabilization.errors.rear_axle_errors`, `@trace:vdsim.stabilization.errors.taylor_terms`, `@trace:vdsim.stabilization.reinit.elliptic_measure`, `@trace:vdsim.stabilization.reinit.predict_motion`, `@trace:vdsim.stabilization.switching.select_controller`, `@trace:vdsim.stabilization.vehicle_layers.SplitRangeDynamics.step`, `@trace:vdsim.stabilization.werling_dynamic.ZeroDynamicsReference.derivatives`, `@trace:vdsim.stabilization.werling_dynamic.ZeroDynamicsReference.reference`, `@trace:vdsim.stabilization.werling_dynamic.lookahead_for_damping`, `@trace:vdsim.stabilization.werling_dynamic.point_kinematics`, `@trace:vdsim.stabilization.werling_dynamic.solve_linearizing_input`, `@trace:vdsim.stabilization.werling_dynamic.zero_dynamics_coefficients`, `@trace:vdsim.stabilization.werling_kinematic.center_law`, `@trace:vdsim.stabilization.werling_kinematic.force_from_acceleration`, `@trace:vdsim.stabilization.werling_kinematic.kin_tracking_with_orientation_stab`, `@trace:vdsim.stabilization.werling_kinematic.orientation_law`, `@trace:vdsim.tire_models.isotropic.force_magnitude`, `@trace:vdsim.tire_models.isotropic.lateral_force`, `@trace:vdsim.vehicle_models.werling_models.desm_forces`, `@trace:vdsim.vehicle_models.werling_models.slip_angles`, `@trace:vdsim.vehicle_models.werling_models.werling_model1`, `@trace:vdsim.vehicle_models.werling_models.werling_model4`, `@trace:vdsim.world.road.RoadNetwork.corridor`, `@trace:vdsim.world.road.RoadNetwork.route_line`, `@trace:vdsim.world.road.connect_poses`, `component:actuator/steering_powertrain`, `component:behavior_planner/rule_based`, `component:collision_checker/circles`, `component:constraint/max_curvature`, `component:constraint/max_jerk`, `component:constraint/max_lateral_acceleration`, `component:constraint/max_longitudinal_acceleration`, `component:constraint/max_steering_angle`, `component:constraint/max_steering_velocity`, `component:constraint/max_yaw_rate`, `component:constraint/speed_range`, `component:constraint/tire_force`, `component:constraint/vehicle_envelope`, `component:constraint/vehicle_stability`, `component:cost_term/jerk`, `component:cost_term/terminal_deviation`, `component:cost_term/terminal_time`, `component:predictor/constant_acceleration`, `component:predictor/lane_following`, `component:tracking_controller/ff_fb`, `component:tracking_controller/mpc`, `component:tracking_controller/werling_bilevel`, `component:tracking_controller/werling_dynamic`, `component:tracking_controller/werling_kinematic_center`, `component:tracking_controller/werling_kinematic_orientation`, `component:trajectory_planner/frenet_naive`, `component:trajectory_planner/sequential`, `component:trajectory_planner/werling`, `component:vehicle_dynamics/split_range`, `component:vehicle_plant/vehicle_model`, `component:world/scenario_engine`, `links.yaml`, `module.yaml:framework`, `module.yaml:geometry`, `module.yaml:gui`, `module.yaml:matlab`, `module.yaml:planning`, `module.yaml:research`, `module.yaml:stabilization`, `module.yaml:vdsim.geometry.reference_line.ReferenceLine.from_points`, `module.yaml:vdsim.geometry.reference_line.curvature_profile`, `vdsim/framework/docs/theory.md`, `vdsim/geometry/docs/theory.md`, `vdsim/planning/docs/theory.md`, `vdsim/research/docs/theory.md`, `vdsim/runtime/docs/theory.md`, `vdsim/stabilization/docs/theory.md`

## Fachartikel

### Allen et al. (1978) {#allen1978}

Allen, B. L.; Shin, B. T.; Cooper, P. J. (1978): Analysis of traffic conflicts and collisions. In: Transportation Research Record 667, 67-74. `[allen1978]`

Verwendet in: `module.yaml:research`, `vdsim/research/docs/theory.md`

### Braghin et al. (2008) {#braghin2008}

Braghin, F.; Cheli, F.; Melzi, S.; Sabbioni, E. (2008): Race driver model. In: Computers & Structures 86(13-14). `[braghin2008]`

_Ideallinie als Kompromiss aus minimaler Krümmung und kürzestem Weg._

Verwendet in: `component:maneuver/race_track`, `module.yaml:trajectory`, `module.yaml:vdsim.trajectory.trajectory_generator.racing_line`, `vdsim/trajectory/docs/theory.md`

### Edwards und Lee (2003) {#edwards_lee2003}

Edwards, S. A.; Lee, E. A. (2003): The semantics and execution of a synchronous block-diagram language. In: Science of Computer Programming 48(1). DOI 10.1016/S0167-6423(02)00096-5. `[edwards_lee2003]`

_Semantik von Blockdiagrammen mit Rückkopplung, Grundlage der Schleifenprüfung_

Verwendet in: `module.yaml:runtime`, `vdsim/runtime/docs/theory.md`

### Fruchterman und Reingold (1991) {#fruchterman1991}

Fruchterman, T. M. J.; Reingold, E. M. (1991): Graph Drawing by Force-directed Placement. In: Software: Practice and Experience 21(11). DOI 10.1002/spe.4380211102. `[fruchterman1991]`

_Kräftebasiertes Layout des Wissensgraphen._

Verwendet in: `@trace:vdsim.knowledge.graph.force_layout`, `module.yaml:knowledge`, `vdsim/knowledge/docs/theory.md`

### Gotel und Finkelstein (1994) {#gotel1994}

Gotel, O. C. Z.; Finkelstein, A. C. W. (1994): An Analysis of the Requirements Traceability Problem. In: Proceedings of the IEEE International Conference on Requirements Engineering. `[gotel1994]`

_Begriffe Vorwärts-/Rückwärts-Rückverfolgbarkeit._

Verwendet in: `@trace:vdsim.knowledge.generator.trace_rows`, `@trace:vdsim.knowledge.graph.KnowledgeGraph.path`, `@trace:vdsim.knowledge.graph.build_graph`, `module.yaml:knowledge`, `module.yaml:vdsim.framework.knowledge.trace`, `vdsim/knowledge/docs/theory.md`

### Hayward (1972) {#hayward1972}

Hayward, J. C. (1972): Near-miss determination through use of a scale of danger. In: Highway Research Record 384, 24-34. `[hayward1972]`

Verwendet in: `module.yaml:research`, `vdsim/research/docs/theory.md`

### Hoffmann et al. (2007) {#hoffmann2007}

Hoffmann, G. M.; Tomlin, C. J.; Montemerlo, M.; Thrun, S. (2007): Autonomous Automobile Trajectory Tracking for Off-Road Driving - Controller Design, Experimental Validation and Racing. In: American Control Conference (ACC). DOI 10.1109/ACC.2007.4282788. `[hoffmann2007]`

_Stanley-Regler_

Verwendet in: `@trace:vdsim.stabilization.classic_lateral.Stanley.control`, `component:lateral_controller/stanley`, `component:tracking_controller/stanley`, `module.yaml:controllers`, `module.yaml:stabilization`, `module.yaml:vdsim.controllers.stanley_controller.StanleyController.steer`, `vdsim/controllers/docs/theory.md`, `vdsim/stabilization/docs/theory.md`

### Kapania et al. (2016) {#kapania2016}

Kapania, N. R.; Subosits, J.; Gerdes, J. C. (2016): A Sequential Two-Step Algorithm for Fast Generation of Vehicle Racing Trajectories. In: Journal of Dynamic Systems, Measurement, and Control 138(9). `[kapania2016]`

_Vorwärts-Rückwärts-Integration des Geschwindigkeitsprofils unter Reibungsgrenzen._

Verwendet in: `component:maneuver/race_track`, `module.yaml:trajectory`, `module.yaml:vdsim.trajectory.speed_profile.speed_profile`, `vdsim/trajectory/docs/theory.md`

### Karnopp et al. (1974) {#karnopp1974}

Karnopp, D.; Crosby, M. J.; Harwood, R. A. (1974): Vibration Control Using Semi-Active Force Generators. In: Journal of Engineering for Industry 96(2). `[karnopp1974]`

_Skyhook-Dämpfung._

Verwendet in: `component:chassis_system/active_damping`, `module.yaml:controllers`, `module.yaml:vdsim.controllers.active_suspension.SkyhookDamping.apply`, `vdsim/controllers/docs/theory.md`

### Smith (1957) {#smith1957}

Smith, O. J. M. (1957): Closer Control of Loops with Dead Time. In: Chemical Engineering Progress 53(5). `[smith1957]`

_Smith-Prädiktor; Idee eines internen Totzeitmodells zur zeitlichen Ausrichtung._

Verwendet in: `lane_change/docs/theory.md`, `module.yaml:actuators`, `module.yaml:lane_change`, `vdsim/actuators/docs/theory.md`, `vdsim/controllers/docs/theory.md`

### Stark und Parker (1995) {#stark1995}

Stark, P. B.; Parker, R. L. (1995): Bounded-Variable Least-Squares: an Algorithm and Applications. In: Computational Statistics 10. `[stark1995]`

_BVLS-Verfahren, das scipy.optimize.lsq_linear(method="bvls") umsetzt._

Verwendet in: `component:lateral_controller/mpc`, `module.yaml:controllers`, `vdsim/controllers/docs/theory.md`

### Stellato et al. (2020) {#stellato2020}

Stellato, B.; Banjac, G.; Goulart, P.; Bemporad, A.; Boyd, S. (2020): OSQP: An Operator Splitting Solver for Quadratic Programs. In: Mathematical Programming Computation 12. DOI 10.1007/s12532-020-00179-2. `[stellato2020]`

_ADMM-Iteration des MPC-QP-Lösers (dichte Eigenimplementierung)_

Verwendet in: `module.yaml:stabilization`, `vdsim/stabilization/docs/theory.md`

### Thrun et al. (2006) {#thrun2006}

Thrun, S.; Montemerlo, M.; Dahlkamp, H.; al., e. (2006): Stanley: The Robot that Won the DARPA Grand Challenge. In: Journal of Field Robotics 23(9). DOI 10.1002/rob.20147. `[thrun2006]`

_Ursprung des Stanley-Lenkgesetzes._

Verwendet in: `component:lateral_controller/stanley`, `module.yaml:controllers`, `vdsim/controllers/docs/theory.md`

### van Zanten et al. (1995) {#vanzanten1995}

van Zanten, A. T.; Erhardt, R.; Pfaff, G. (1995): VDC, The Vehicle Dynamics Control System of Bosch. In: SAE Technical Paper 950759. `[vanzanten1995]`

_Gierratenregelung durch radindividuelle Bremseingriffe (ESP)._

Verwendet in: `component:chassis_system/esp`, `module.yaml:controllers`, `module.yaml:vdsim.controllers.esp_controller.ElectronicStabilityProgram.apply`, `vdsim/controllers/docs/theory.md`

### Virtanen et al. (2020) {#virtanen2020}

Virtanen, P.; Gommers, R.; Oliphant, T. E.; al., e. (2020): SciPy 1.0: fundamental algorithms for scientific computing in Python. In: Nature Methods 17. DOI 10.1038/s41592-019-0686-2. `[virtanen2020]`

_solve_ivp (adaptiver Löser), lsq_linear (MPC, Ideallinie), Signalverarbeitung (ISO-2631-Filter, Welch)._

Verwendet in: `module.yaml:simulation`, `module.yaml:vdsim.simulation.solver.AdaptiveSolver`, `vdsim/simulation/docs/theory.md`

### Vogel (2003) {#vogel2003}

Vogel, K. (2003): A comparison of headway and time to collision as safety indicators. In: Accident Analysis & Prevention 35(3), 427-433. DOI 10.1016/S0001-4575(02)00022-2. `[vogel2003]`

Verwendet in: `@trace:vdsim.research.metrics.safety_metrics`, `module.yaml:research`, `vdsim/research/docs/theory.md`

### Welch (1967) {#welch1967}

Welch, P. D. (1967): The use of fast Fourier transform for the estimation of power spectra: A method based on time averaging over short, modified periodograms. In: IEEE Transactions on Audio and Electroacoustics 15(2). `[welch1967]`

_Welch-Schätzer für Leistungs- und Kreuzspektren (Frequenzgang aus dem Sinus-Sweep)._

Verwendet in: `module.yaml:reporting`, `module.yaml:vdsim.reporting.kpi_evaluator.KPIEvaluator._frequency_response`, `vdsim/reporting/docs/theory.md`

### Werling et al. (2010) {#werling2010icra}

Werling, M.; Ziegler, J.; Kammel, S.; Thrun, S. (2010): Optimal Trajectory Generation for Dynamic Street Scenarios in a Frenét Frame. In: IEEE International Conference on Robotics and Automation (ICRA). DOI 10.1109/ROBOT.2010.5509799. `[werling2010icra]`

Verwendet in: `component:trajectory_planner/frenet_naive`, `component:trajectory_planner/werling`, `module.yaml:geometry`, `module.yaml:planning`, `vdsim/geometry/docs/theory.md`, `vdsim/planning/docs/theory.md`

### Werling et al. (2010) {#werling2010tro}

Werling, M.; Gröll, L.; Bretthauer, G. (2010): Invariant Trajectory Tracking With a Full-Size Autonomous Road Vehicle. In: IEEE Transactions on Robotics 26(4). DOI 10.1109/TRO.2010.2052325. `[werling2010tro]`

Verwendet in: `component:tracking_controller/werling_bilevel`, `component:tracking_controller/werling_kinematic_orientation`, `module.yaml:stabilization`

### Werling et al. (2012) {#werling2012ijrr}

Werling, M.; Kammel, S.; Ziegler, J.; Gröll, L. (2012): Optimal trajectories for time-critical street scenarios using discretized terminal manifolds. In: The International Journal of Robotics Research 31(3). DOI 10.1177/0278364911423042. `[werling2012ijrr]`

Verwendet in: `component:trajectory_planner/werling`, `module.yaml:planning`

### Ziegler und Stiller (2010) {#ziegler2010iv}

Ziegler, J.; Stiller, C. (2010): Fast collision checking for intelligent vehicle motion planning. In: IEEE Intelligent Vehicles Symposium (IV), San Diego, 518-522. DOI 10.1109/IVS.2010.5547976. `[ziegler2010iv]`

_Kreisapproximation der Fahrzeugumrisse; Grundlage von collision_checker/circles (Werling 3.5.4, Ref. [93])_

Verwendet in: `@trace:vdsim.planning.collision.CircleCollisionChecker.check`, `component:collision_checker/circles`, `component:trajectory_planner/werling`, `module.yaml:planning`, `vdsim/planning/docs/theory.md`

## Fachbuch

### Aho et al. (2006) {#aho2006}

Aho, A. V.; Lam, M. S.; Sethi, R.; Ullman, J. D. (2006): Compilers: Principles, Techniques, and Tools. 2. Addison-Wesley. ISBN 978-0-321-48681-3. `[aho2006]`

_Lexikalische Analyse, rekursiver Abstieg (Kap. 4), Typprüfung (Kap. 6), syntaxgesteuerte Übersetzung (Kap. 5, 8), Datenflussanalyse (Kap. 9)_

Verwendet in: `@trace:vdsim.matlab.analysis.analyze`, `@trace:vdsim.matlab.codegen.generate`, `@trace:vdsim.matlab.parser.parse`, `@trace:vdsim.matlab.typeinfer.infer_types`, `module.yaml:matlab`

### Åström und Hägglund (2006) {#astrom2006}

Åström, K. J.; Hägglund, T. (2006): Advanced PID Control. ISA. ISBN 978-1-55617-942-6. `[astrom2006]`

_PID, Vorsteuerung, Anti-Windup (Split-Range-Integrator, Geschwindigkeitsregler)_

Verwendet in: `@trace:vdsim.stabilization.classic_longitudinal.PID.accel`, `@trace:vdsim.stabilization.classic_longitudinal.VehicleSpeedController.accel`, `component:tracking_controller/ff_fb`, `component:tracking_controller/pi`, `component:tracking_controller/pid`, `component:tracking_controller/speed_pi`, `component:vehicle_dynamics/split_range`, `module.yaml:stabilization`, `vdsim/stabilization/docs/theory.md`

### Bellman (1957) {#bellman1957}

Bellman, R. (1957): Dynamic Programming. Princeton University Press. `[bellman1957]`

_Optimalitätsprinzip, Grundlage der zeitlichen Konsistenz (Werling 3.2)_

Verwendet in: `module.yaml:planning`, `vdsim/planning/docs/theory.md`

### Borrelli et al. (2017) {#borrelli2017}

Borrelli, F.; Bemporad, A.; Morari, M. (2017): Predictive Control for Linear and Hybrid Systems. Cambridge University Press. DOI 10.1017/9781139061759. `[borrelli2017]`

_Lineare (zeitvariante) MPC, kondensiertes QP_

Verwendet in: `@trace:vdsim.stabilization.classic_lateral.MPC.solve`, `component:lateral_controller/mpc`, `component:tracking_controller/mpc`, `module.yaml:controllers`, `module.yaml:stabilization`, `module.yaml:vdsim.controllers.mpc_controller.MPCController.steer`, `vdsim/controllers/docs/theory.md`, `vdsim/stabilization/docs/theory.md`

### Bryson und Ho (1975) {#bryson1975}

Bryson, A. E.; Ho, Y. C. (1975): Applied Optimal Control. Optimization, Estimation, and Control. Hemisphere Publishing. `[bryson1975]`

_Transversalitätsbedingungen bei freier Endzeit und Zielmannigfaltigkeit ((3.11), (3.13); Werling Ref. [23])_

Verwendet in: `module.yaml:planning`, `vdsim/planning/docs/theory.md`

### Butcher (2016) {#butcher2016}

Butcher, J. C. (2016): Numerical Methods for Ordinary Differential Equations. 3rd edition. Wiley. `[butcher2016]`

_Runge-Kutta-Theorie, Butcher-Tableau, lineare Stabilität._

Verwendet in: `module.yaml:simulation`, `module.yaml:vdsim.simulation.solver.EulerSolver`, `module.yaml:vdsim.simulation.solver.HeunSolver`, `vdsim/simulation/docs/theory.md`

### de Boor (2001) {#deboor2001}

de Boor, C. (2001): A Practical Guide to Splines. revised edition. Springer (Applied Mathematical Sciences 27). `[deboor2001]`

_Hermite-Interpolation und Splines (Referenzkurve in vdsim.geometry)._

Verwendet in: `module.yaml:geometry`, `module.yaml:vdsim.geometry.reference_line.ReferenceLine.evaluate`, `vdsim/geometry/docs/theory.md`, `vdsim/trajectory/docs/theory.md`

### Ericson (2004) {#ericson2004}

Ericson, C. (2004): Real-Time Collision Detection. Morgan Kaufmann. ISBN 978-1-55860-732-3. `[ericson2004]`

Verwendet in: `@trace:vdsim.research.metrics.rectangle_distance`, `module.yaml:research`, `vdsim/research/docs/theory.md`

### Chacon und Straub (2014) {#git_book}

Chacon, S.; Straub, B. (2014): Pro Git. 2. Apress. https://git-scm.com/book. `[git_book]`

_Inhaltsadressierte Speicherung (SHA), Vorbild des Versionsspeichers_

Verwendet in: `vdsim/runtime/docs/theory.md`

### Hairer et al. (1993) {#hairer1993}

Hairer, E.; Nørsett, S. P.; Wanner, G. (1993): Solving Ordinary Differential Equations I: Nonstiff Problems. 2nd revised edition. Springer (Springer Series in Computational Mathematics 8). `[hairer1993]`

_Runge-Kutta-Verfahren, Ordnung, Fehlerabschätzung, Schrittweitensteuerung._

Verwendet in: `module.yaml:simulation`, `module.yaml:vdsim.simulation.solver.RK4Solver`, `vdsim/simulation/docs/theory.md`

### Hairer und Wanner (1996) {#hairer1996}

Hairer, E.; Wanner, G. (1996): Solving Ordinary Differential Equations II: Stiff and Differential-Algebraic Problems. 2nd revised edition. Springer (Springer Series in Computational Mathematics 14). `[hairer1996]`

_Steifheit und Stabilitätsgebiete expliziter Verfahren (Grundlage für stable_dt)._

Verwendet in: `module.yaml:simulation`, `module.yaml:vdsim.simulation.simulator.Simulator._substeps`, `module.yaml:vdsim.vehicle_models.double_track_model.DoubleTrackModel.stable_dt`, `module.yaml:vdsim.vehicle_models.multibody_model.MultibodyModel.stable_dt`, `vdsim/simulation/docs/theory.md`

### Isidori (1995) {#isidori1995}

Isidori, A. (1995): Nonlinear Control Systems. Springer, 3. Auflage. ISBN 978-3-540-19916-8. `[isidori1995]`

_Exakte E/A-Linearisierung, relativer Grad, Nulldynamik, Minimalphasigkeit (Sätze 8 und 9)_

Verwendet in: `component:tracking_controller/werling_dynamic`, `component:tracking_controller/werling_kinematic_center`, `module.yaml:stabilization`, `vdsim/stabilization/docs/theory.md`

### Kamm (1936) {#kamm1936}

Kamm, W. (1936): Das Kraftfahrzeug. Betriebsgrundlagen, Berechnung, Gestaltung und Versuch. Springer. `[kamm1936]`

_Kammscher Kreis (Reibungskreis) der Reifenkraft, Restriktion tire_force_

Verwendet in: `module.yaml:planning`, `vdsim/planning/docs/theory.md`

### Khalil (2002) {#khalil2002}

Khalil, H. K. (2002): Nonlinear Systems. Prentice Hall, 3. Auflage. ISBN 978-0-13-067389-3. `[khalil2002]`

_Lyapunov-Stabilität, LaSalle-Invarianzprinzip, Backstepping (Sätze 4 und 6)_

Verwendet in: `component:tracking_controller/werling_dynamic`, `component:tracking_controller/werling_kinematic_center`, `component:tracking_controller/werling_kinematic_orientation`, `module.yaml:stabilization`, `vdsim/stabilization/docs/theory.md`

### Lee und Seshia (2017) {#lee_seshia2017}

Lee, E. A.; Seshia, S. A. (2017): Introduction to Embedded Systems: A Cyber-Physical Systems Approach. 2. MIT Press. ISBN 978-0-262-53381-2. https://ptolemy.berkeley.edu/books/leeseshia/. `[lee_seshia2017]`

_Zeitdiskrete Modelle, synchron-reaktive Komposition, Rückkopplung und Determinismus (Kap. 2, 5, 6)_

Verwendet in: `@trace:vdsim.runtime.blocks.Integrator.update`, `@trace:vdsim.runtime.blocks.LowPass.step`, `module.yaml:runtime`, `vdsim/runtime/docs/theory.md`

### Ljung (1999) {#ljung1999}

Ljung, L. (1999): System Identification: Theory for the User. 2nd edition. Prentice Hall. `[ljung1999]`

_Rekursive Kleinste-Quadrate-Schätzung mit Vergessensfaktor (Rückkanal-Schätzer)._

Verwendet in: `lane_change/docs/theory.md`, `module.yaml:actuators`, `module.yaml:controllers`, `module.yaml:lane_change`, `module.yaml:lane_change.simulation.simulate`, `module.yaml:vdsim.controllers.curvature_feedback.CurvatureCorrection.update`, `vdsim/actuators/docs/theory.md`, `vdsim/controllers/docs/theory.md`

### Martin (2017) {#martin2017}

Martin, R. C. (2017): Clean Architecture: A Craftsman's Guide to Software Structure and Design. Prentice Hall. ISBN 978-0-13-449416-6. `[martin2017]`

Verwendet in: `module.yaml:framework`, `vdsim/core/docs/theory.md`, `vdsim/framework/docs/theory.md`

### Milliken und Milliken (1995) {#milliken1995}

Milliken, W. F.; Milliken, D. L. (1995): Race Car Vehicle Dynamics. SAE International. `[milliken1995]`

_g-g-Diagramm (GGV), Reibkreis, Eigenlenkverhalten, Radlastverlagerung._

Verwendet in: `module.yaml:analysis`, `module.yaml:trajectory`, `module.yaml:vdsim.analysis.quasi_static.QuasiStaticAnalysis.roll_gradient`, `module.yaml:vdsim.analysis.quasi_static.QuasiStaticAnalysis.wheel_loads`, `module.yaml:vdsim.reporting.kpi_evaluator.KPIEvaluator._general`, `module.yaml:visualization`, `vdsim/analysis/docs/theory.md`, `vdsim/reporting/docs/theory.md`, `vdsim/trajectory/docs/theory.md`

### Mitschke und Wallentowitz (2004) {#mitschke2004}

Mitschke, M.; Wallentowitz, H. (2004): Dynamik der Kraftfahrzeuge. Springer (4. Auflage). ISBN 978-3-540-42011-1. `[mitschke2004]`

_lineares Einspurmodell, stationärer Schwimmwinkel; Restriktion vehicle_stability_

Verwendet in: `module.yaml:planning`, `vdsim/planning/docs/theory.md`

### Mitschke und Wallentowitz (2014) {#mitschke2014}

Mitschke, M.; Wallentowitz, H. (2014): Dynamik der Kraftfahrzeuge. 5. Auflage. Springer Vieweg. `[mitschke2014]`

_Standardwerk zu Längs-, Quer- und Vertikaldynamik, Einspurmodell, Eigenlenkverhalten, Bremskraftverteilung, Fahrkomfort._

Verwendet in: `component:chassis_system/rear_steering`, `component:tire_model/linear`, `component:vehicle_model/bicycle_linear`, `component:vehicle_model/bicycle_nonlinear`, `component:vehicle_model/double_track`, `component:vehicle_model/multibody`, `module.yaml:analysis`, `module.yaml:powertrain`, `module.yaml:tire_models`, `module.yaml:vdsim.analysis.linear_analysis.LinearSingleTrackAnalysis.characteristic_speed`, `module.yaml:vdsim.analysis.linear_analysis.LinearSingleTrackAnalysis.critical_speed`, `module.yaml:vdsim.analysis.linear_analysis.LinearSingleTrackAnalysis.steady_state_gains`, `module.yaml:vdsim.analysis.quasi_static.QuasiStaticAnalysis.ackermann_angles`, `module.yaml:vdsim.controllers.esp_controller.understeer_gradient`, `module.yaml:vdsim.controllers.rear_axle_steering.RearAxleSteering.apply`, `module.yaml:vdsim.core.parameters.VehicleParameters.static_axle_loads`, `module.yaml:vdsim.powertrain.powertrain.BrakeSystem.front_share`, `module.yaml:vdsim.tire_models.linear_tire.LinearTire.forces`, `module.yaml:vdsim.vehicle_models.bicycle_model.LinearBicycleModel.understeer_gradient`, `module.yaml:vdsim.vehicle_models.bicycle_model.NonlinearBicycleModel.derivatives`, `module.yaml:vdsim.vehicle_models.common.aero_drag`, `module.yaml:vdsim.vehicle_models.common.rolling_resistance`, `module.yaml:vehicle_models`, `vdsim/analysis/docs/theory.md`, `vdsim/controllers/docs/theory.md`, `vdsim/core/docs/theory.md`, `vdsim/powertrain/docs/theory.md`, `vdsim/tire_models/docs/theory.md`, `vdsim/trajectory/docs/theory.md`, `vdsim/vehicle_models/docs/theory.md`

### Montgomery (2017) {#montgomery2017}

Montgomery, D. C. (2017): Design and Analysis of Experiments. Wiley (9. Auflage). ISBN 978-1-119-11347-8. `[montgomery2017]`

Verwendet in: `@trace:vdsim.research.experiments.parameter_sweep`, `module.yaml:research`, `vdsim/research/docs/theory.md`

### Pacejka (2012) {#pacejka2012}

Pacejka, H. B. (2012): Tire and Vehicle Dynamics. Butterworth-Heinemann, 3. Auflage. ISBN 978-0-08-097016-5. `[pacejka2012]`

_Magic Formula; Grundlage des isotropen Reifenmodells (Werling 4.3.2)_

Verwendet in: `component:tire_model/brush`, `component:tire_model/pacejka`, `component:tracking_controller/werling_dynamic`, `component:vehicle_model/bicycle_nonlinear`, `module.yaml:stabilization`, `module.yaml:tire_models`, `module.yaml:vdsim.tire_models.brush_model.BrushTire.forces`, `module.yaml:vdsim.tire_models.pacejka.PacejkaTire.cornering_stiffness`, `module.yaml:vdsim.tire_models.pacejka.PacejkaTire.forces`, `module.yaml:vdsim.tire_models.pacejka.magic_formula`, `module.yaml:vehicle_models`, `module.yaml:visualization`, `vdsim/stabilization/docs/theory.md`, `vdsim/tire_models/docs/theory.md`, `vdsim/vehicle_models/docs/theory.md`

### Rajamani (2012) {#rajamani2012}

Rajamani, R. (2012): Vehicle Dynamics and Control. Springer, 2. Auflage. DOI 10.1007/978-1-4614-1433-9. `[rajamani2012]`

_Querfehlermodell des Einspurmodells, LQR mit Vorsteuerung (Kap. 3), ACC (Kap. 5)_

Verwendet in: `@trace:vdsim.stabilization.classic_lateral.LQR.control`, `@trace:vdsim.stabilization.classic_lateral.lateral_error_model`, `@trace:vdsim.stabilization.classic_longitudinal.ACC.accel`, `component:chassis_system/esp`, `component:chassis_system/torque_vectoring`, `component:lateral_controller/mpc`, `component:longitudinal_controller/acc`, `component:tracking_controller/acc`, `component:tracking_controller/composite`, `component:tracking_controller/lqr`, `component:tracking_controller/mpc`, `component:tracking_controller/pure_pursuit`, `component:vehicle_model/bicycle_kinematic`, `component:vehicle_model/bicycle_linear`, `lane_change/docs/theory.md`, `links.yaml`, `module.yaml:analysis`, `module.yaml:controllers`, `module.yaml:lane_change.vehicle_model.vehicle_step`, `module.yaml:stabilization`, `module.yaml:vdsim.analysis.linear_analysis.LinearSingleTrackAnalysis.eigen`, `module.yaml:vdsim.controllers.esp_controller.reference_yaw_rate`, `module.yaml:vdsim.controllers.mpc_controller.MPCController._matrices`, `module.yaml:vdsim.controllers.speed_controller.AdaptiveCruiseControl.acceleration`, `module.yaml:vdsim.vehicle_models.bicycle_model.KinematicBicycleModel.derivatives`, `module.yaml:vdsim.vehicle_models.bicycle_model.LinearBicycleModel.state_space`, `module.yaml:vehicle_models`, `vdsim/analysis/docs/theory.md`, `vdsim/controllers/docs/theory.md`, `vdsim/stabilization/docs/theory.md`, `vdsim/vehicle_models/docs/theory.md`

### Reif (2010) {#reif2010}

Reif, K. (2010): Bremsen und Bremsregelsysteme. Vieweg+Teubner (Bosch Fachinformation Automobil). `[reif2010]`

_Herausgeberwerk. Bremsanlage, Bremskraftverteilung, ABS, ASR, ESP._

Verwendet in: `component:chassis_system/abs`, `component:chassis_system/esp`, `component:chassis_system/tcs`, `module.yaml:controllers`, `module.yaml:powertrain`, `module.yaml:vdsim.controllers.slip_control.AntiLockBraking.apply`, `module.yaml:vdsim.controllers.slip_control.TractionControl.apply`, `module.yaml:vdsim.powertrain.powertrain.LongitudinalActuation.actuate`, `vdsim/controllers/docs/theory.md`, `vdsim/powertrain/docs/theory.md`

### Saltelli et al. (2008) {#saltelli2008}

Saltelli, A.; Ratto, M.; Andres, T.; Campolongo, F.; Cariboni, J.; Gatelli, D.; Saisana, M.; Tarantola, S. (2008): Global Sensitivity Analysis. The Primer. Wiley. ISBN 978-0-470-05997-5. `[saltelli2008]`

Verwendet in: `@trace:vdsim.research.experiments.monte_carlo`, `module.yaml:research`, `vdsim/research/docs/theory.md`

### Schramm et al. (2018) {#schramm2018}

Schramm, D.; Hiller, M.; Bardini, R. (2018): Modellbildung und Simulation der Dynamik von Kraftfahrzeugen. Springer Vieweg. `[schramm2018]`

_Mehrkörpermodellierung, Zweispur- und Gesamtfahrzeugmodelle, Reifen- und Fahrbahnmodelle._

Verwendet in: `component:vehicle_model/double_track`, `component:vehicle_model/multibody`, `module.yaml:tire_models`, `module.yaml:vdsim.vehicle_models.double_track_model.DoubleTrackModel.derivatives`, `module.yaml:vdsim.vehicle_models.multibody_model.MultibodyModel.derivatives`, `module.yaml:vehicle_models`, `vdsim/tire_models/docs/theory.md`, `vdsim/vehicle_models/docs/theory.md`

## Industriestandard

### ASAM OpenDRIVE {#asam_opendrive}

ASAM e.V.: ASAM OpenDRIVE – Format zur Beschreibung von Straßennetzen. https://www.asam.net/standards/detail/opendrive/. `[asam_opendrive]`

_Referenzlinie aus line, arc, spiral, poly3, paramPoly3; Fahrstreifen mit Breitenpolynomen._

Verwendet in: `component:trajectory_loader/opendrive`, `module.yaml:trajectory`, `module.yaml:vdsim.trajectory.opendrive.load_opendrive`, `vdsim/trajectory/docs/theory.md`

### FMVSS No. 126 (49 CFR 571.126) (2007) {#fmvss126}

National Highway Traffic Safety Administration (NHTSA) (2007): FMVSS No. 126 (49 CFR 571.126): Electronic Stability Control Systems for Light Vehicles. `[fmvss126]`

_Sinus mit Haltezeit, Gierraten- und Querversatzkriterien._

Verwendet in: `component:lateral_controller/open_loop`, `component:maneuver/sine_with_dwell`, `module.yaml:reporting`, `module.yaml:trajectory`, `module.yaml:vdsim.reporting.kpi_evaluator.KPIEvaluator._sine_dwell`, `vdsim/reporting/docs/theory.md`

### IEEE (2019) {#ieee754_2019}

IEEE (2019): IEEE Standard for Floating-Point Arithmetic (IEEE 754-2019). DOI 10.1109/IEEESTD.2019.8766229. `[ieee754_2019]`

_Grundlage der Bitgleichheits-Aussagen zwischen Interpreter und generiertem Code_

Verwendet in: `module.yaml:matlab`

### JTC1/SC22/WG21 (2017) {#iso_cpp17}

JTC1/SC22/WG21, I. (2017): ISO/IEC 14882:2017 Programming languages — C++. `[iso_cpp17]`

_Zielsprache des C++-Generators (std::optional, Aggregat-Initialisierung)_

Verwendet in: `module.yaml:matlab`

### UN-ECE-Regelung Nr. 13-H {#unece_r13h}

United Nations Economic Commission for Europe (UNECE): UN-ECE-Regelung Nr. 13-H: Einheitliche Bedingungen für die Genehmigung von Personenkraftwagen hinsichtlich der Bremsen. `[unece_r13h]`

_Definition der mittleren Vollverzögerung (MFDD) zwischen 0,8 v0 und 0,1 v0._

Verwendet in: `module.yaml:reporting`, `module.yaml:vdsim.reporting.kpi_evaluator.KPIEvaluator._braking`, `vdsim/reporting/docs/theory.md`

## Norm

### ISO 26262:2018 (2018) {#iso26262}

International Organization for Standardization (2018): ISO 26262:2018: Road vehicles — Functional safety. `[iso26262]`

_Fordert u. a. Rückverfolgbarkeit zwischen Anforderungen, Entwurf, Implementierung und Verifikation._

Verwendet in: `module.yaml:knowledge`, `module.yaml:vdsim.knowledge.collector.Collector._doc_traces`, `vdsim/knowledge/docs/theory.md`

### ISO 2631-1:1997 (1997) {#iso2631_1}

International Organization for Standardization (1997): ISO 2631-1:1997: Mechanical vibration and shock — Evaluation of human exposure to whole-body vibration — Part 1 General requirements. `[iso2631_1]`

_Frequenzbewertung Wk, bewerteter Effektivwert a_w, Komfortskala (Anhang C)._

Verwendet in: `module.yaml:reporting`, `module.yaml:vdsim.reporting.kpi_evaluator.iso2631_rating`, `module.yaml:vdsim.reporting.kpi_evaluator.iso2631_weighted_rms`, `vdsim/reporting/docs/theory.md`

### ISO 3888-1:2018 (2018) {#iso3888_1}

International Organization for Standardization (2018): ISO 3888-1:2018: Passenger cars — Test track for a severe lane-change manoeuvre — Part 1 Double lane-change. `[iso3888_1]`

Verwendet in: `component:maneuver/iso_double_lane_change`, `module.yaml:reporting`, `module.yaml:trajectory`, `module.yaml:vdsim.reporting.kpi_evaluator.KPIEvaluator._cone_test`, `vdsim/reporting/docs/theory.md`

### ISO 3888-2:2011 (2011) {#iso3888_2}

International Organization for Standardization (2011): ISO 3888-2:2011: Passenger cars — Test track for a severe lane-change manoeuvre — Part 2 Obstacle avoidance. `[iso3888_2]`

Verwendet in: `component:maneuver/iso_obstacle_avoidance`, `module.yaml:reporting`, `module.yaml:trajectory`, `vdsim/reporting/docs/theory.md`

### ISO 4138:2021 (2021) {#iso4138}

International Organization for Standardization (2021): ISO 4138:2021: Passenger cars — Steady-state circular driving behaviour — Open-loop test methods. `[iso4138]`

Verwendet in: `component:lateral_controller/open_loop`, `component:maneuver/circle`, `component:maneuver/ramp_steer`, `module.yaml:analysis`, `module.yaml:reporting`, `module.yaml:trajectory`, `module.yaml:vdsim.reporting.kpi_evaluator.KPIEvaluator._understeer`, `vdsim/analysis/docs/theory.md`, `vdsim/reporting/docs/theory.md`

### ISO 7401:2011 (2011) {#iso7401}

International Organization for Standardization (2011): ISO 7401:2011: Road vehicles — Lateral transient response test methods — Open-loop test methods. `[iso7401]`

Verwendet in: `component:lateral_controller/open_loop`, `component:maneuver/frequency_sweep`, `component:maneuver/step_steer`, `module.yaml:reporting`, `module.yaml:trajectory`, `module.yaml:vdsim.reporting.kpi_evaluator.KPIEvaluator._step_steer`, `vdsim/reporting/docs/theory.md`

### ISO 7975:2019 (2019) {#iso7975}

International Organization for Standardization (2019): ISO 7975:2019: Passenger cars — Braking in a turn — Open-loop test method. `[iso7975]`

Verwendet in: `component:maneuver/brake_in_turn`, `module.yaml:reporting`, `module.yaml:trajectory`, `vdsim/reporting/docs/theory.md`

### ISO 8608:2016 (2016) {#iso8608}

International Organization for Standardization (2016): ISO 8608:2016: Mechanical vibration — Road surface profiles — Reporting of measured data. `[iso8608]`

_Fahrbahnklassen A–H über die Unebenheitsdichte G_d(n0) bei n0 = 0,1 1/m._

Verwendet in: `module.yaml:simulation`, `module.yaml:vdsim.simulation.environment.iso8608_profile`, `vdsim/simulation/docs/theory.md`

### ISO 8855:2011 (2011) {#iso8855}

International Organization for Standardization (2011): ISO 8855:2011: Road vehicles — Vehicle dynamics and road-holding ability — Vocabulary. `[iso8855]`

_Koordinatensysteme und Vorzeichenkonventionen._

Verwendet in: `module.yaml:core`, `vdsim/core/docs/theory.md`

## Offizielle Dokumentation

### Project (2024) {#cargo_book}

Project, T. R. (2024): The Cargo Book. https://doc.rust-lang.org/cargo/. `[cargo_book]`

_cargo build --release, --target-dir, crate-type cdylib_

Verwendet in: `module.yaml:runtime`, `vdsim/runtime/docs/theory.md`

### Fowler (2004) {#fowler2004}

Fowler, M. (2004): Inversion of Control Containers and the Dependency Injection pattern. https://martinfowler.com/articles/injection.html. `[fowler2004]`

_Dependency-Injection-Container (vdsim.framework.container)._

Verwendet in: `module.yaml:framework`, `module.yaml:vdsim.framework.container.Container.resolve`, `vdsim/framework/docs/theory.md`

### MathWorks und Inc. (2024) {#mathworks_matlab}

MathWorks, T.; Inc. (2024): MATLAB Language Fundamentals (Operators and Elementary Operations, Operator Precedence, Matrix Indexing, Functions). The MathWorks, Inc.. https://www.mathworks.com/help/matlab/language-fundamentals.html. `[mathworks_matlab]`

_Referenz für Syntax, Operatorrangfolge, Indizierung (1-basiert, spaltenweise), Colon-Operator und Built-ins von vdsim.matlab_

Verwendet in: `@trace:vdsim.matlab.interpreter.Interpreter.call`, `@trace:vdsim.matlab.verify.verify_file`, `module.yaml:matlab`

### MathWorks und Inc. (2024) {#mathworks_precedence}

MathWorks, T.; Inc. (2024): Operator Precedence. https://www.mathworks.com/help/matlab/matlab_prog/operator-precedence.html. `[mathworks_precedence]`

_Rangfolge der Operatoren, wie sie der Parser umsetzt_

Verwendet in: `module.yaml:matlab`

### Matplotlib Development Team {#matplotlib_mathtext}

Matplotlib Development Team: Matplotlib: Writing mathematical expressions (mathtext). https://matplotlib.org/stable/users/explain/text/mathtext.html. `[matplotlib_mathtext]`

_Unterstützter LaTeX-Umfang der Formeldarstellung im Wissensbrowser._

Verwendet in: `module.yaml:knowledge`

### Microsoft (2024) {#msvc_dll}

Microsoft (2024): DLLs in Visual C++; LoadLibrary/FreeLibrary; vswhere; Use the Microsoft C++ toolset from the command line. https://learn.microsoft.com/en-us/cpp/build/dlls-in-visual-cpp. `[msvc_dll]`

___declspec(dllexport), Sperren geladener DLLs (Schattenkopie), vcvars64.bat, cl /LD_

Verwendet in: `module.yaml:runtime`, `vdsim/runtime/docs/theory.md`

### Initiative (2021) {#openapi31}

Initiative, O. (2021): OpenAPI Specification 3.1.0. https://spec.openapis.org/oas/v3.1.0. `[openapi31]`

Verwendet in: – (noch nicht verknüpft)

### Foundation (2024) {#python_ctypes}

Foundation, P. S. (2024): ctypes – A foreign function library for Python. https://docs.python.org/3/library/ctypes.html. `[python_ctypes]`

_Laden der nativen Nodes, Funktionssignaturen, Zeigerarrays_

Verwendet in: `module.yaml:runtime`, `vdsim/runtime/docs/theory.md`

### Project (2024) {#rust_ffi}

Project, T. R. (2024): The Rustonomicon: FFI; The Rust Reference: External blocks and the C ABI. https://doc.rust-lang.org/nomicon/ffi.html. `[rust_ffi]`

_extern "C", no_mangle, catch_unwind an der FFI-Grenze, cdylib_

Verwendet in: `module.yaml:runtime`, `vdsim/runtime/docs/theory.md`

### Developers (2024) {#rust_reference}

Developers, T. R. P. (2024): The Rust Reference. https://doc.rust-lang.org/reference/. `[rust_reference]`

_Zielsprache des Rust-Generators (f64, Destrukturierende Zuweisung, Edition 2021)_

Verwendet in: `module.yaml:matlab`

### Preston-Werner {#semver2}

Preston-Werner, T.: Semantic Versioning 2.0.0. https://semver.org/spec/v2.0.0.html. `[semver2]`

_Versionsschema der Komponenten (MAJOR.MINOR.PATCH) und Bereichsangaben ^, ~._

Verwendet in: `module.yaml:framework`, `module.yaml:vdsim.framework.plugins.version_matches`, `vdsim/framework/docs/theory.md`

### MathWorks (2024) {#simulink_exec}

MathWorks, T. (2024): Simulink: Simulation Phases in Dynamic Systems, Algebraic Loop Concepts, Time-Based Scheduling. The MathWorks, Inc.. https://www.mathworks.com/help/simulink/ug/simulating-dynamic-systems.html. `[simulink_exec]`

_Ausführungsmodell (output/update, Durchgriff), Multi-Rate mit Halteglied und Behandlung algebraischer Schleifen als Vorbild des Executors_

Verwendet in: `module.yaml:runtime`, `vdsim/runtime/docs/theory.md`

## Open-Source-Referenz

### comma.ai {#openpilot}

comma.ai: openpilot – Open-Source-Fahrerassistenzsystem. https://github.com/commaai/openpilot. `[openpilot]`

_Größenordnung der Lenkaktor-Latenz (steerActuatorDelay) als Plausibilisierung der Latenzfälle._

Verwendet in: `lane_change/docs/theory.md`, `module.yaml:actuators`, `module.yaml:lane_change`, `vdsim/actuators/docs/theory.md`

## Technischer Bericht

### Coulter (1992) {#coulter1992}

Coulter, R. C. (1992): Implementation of the Pure Pursuit Path Tracking Algorithm. Bericht CMU-RI-TR-92-01. Carnegie Mellon University, Robotics Institute. `[coulter1992]`

_Algorithmus des Beispiel-Reglers in examples/custom_nodes_

Verwendet in: `component:lateral_controller/pure_pursuit`, `module.yaml:controllers`, `module.yaml:vdsim.controllers.pure_pursuit.PurePursuitController.steer`, `vdsim/controllers/docs/theory.md`

### Snider (2009) {#snider2009}

Snider, J. M. (2009): Automatic Steering Methods for Autonomous Automobile Path Tracking. Carnegie Mellon University, Robotics Institute, CMU-RI-TR-09-08. `[snider2009]`

_Pure Pursuit, Stanley, Vergleich geometrischer und kinematischer Querregler_

Verwendet in: `@trace:vdsim.stabilization.classic_lateral.PurePursuit.control`, `component:lateral_controller/pure_pursuit`, `component:lateral_controller/stanley`, `component:tracking_controller/pure_pursuit`, `component:tracking_controller/stanley`, `module.yaml:controllers`, `module.yaml:stabilization`, `vdsim/controllers/docs/theory.md`, `vdsim/stabilization/docs/theory.md`
