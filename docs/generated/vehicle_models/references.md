# Fahrzeugmodelle – Quellen

> Automatisch erzeugt von `tools/build_docs.py` aus Code und Paketdoku. Nicht von Hand bearbeiten.

[Übersicht](index.md) · [Schnittstellen](interfaces.md) · [Konfiguration](configuration.md) · [Theorie und Verfahren](theory.md) · [Beispiele](examples.md) · [Einschränkungen](limitations.md) · [Validierung](validation.md) · **Quellen** · [Rückverfolgbarkeit](traceability.md)


| Zitat | Quelle | Typ | Verwendet in |
|---|---|---|---|
| [Hairer und Wanner (1996)](../references.md#hairer1996) | Hairer, E.; Wanner, G. (1996): Solving Ordinary Differential Equations II: Stiff and Differential-Algebraic Problems. 2nd revised edition. Springer (Springer Series in Computational Mathematics 14). | Fachbuch | DoubleTrackModel.stable_dt (module.yaml), MultibodyModel.stable_dt (module.yaml) |
| [Mitschke und Wallentowitz (2014)](../references.md#mitschke2014) | Mitschke, M.; Wallentowitz, H. (2014): Dynamik der Kraftfahrzeuge. 5. Auflage. Springer Vieweg. | Fachbuch | LinearBicycleModel.understeer_gradient (module.yaml), NonlinearBicycleModel.derivatives (module.yaml), aero_drag (module.yaml), module.yaml, rolling_resistance (module.yaml), theory.md, vehicle_model/bicycle_linear, vehicle_model/bicycle_nonlinear, vehicle_model/double_track, vehicle_model/multibody |
| [Pacejka (2012)](../references.md#pacejka2012) | Pacejka, H. B. (2012): Tire and Vehicle Dynamics. Butterworth-Heinemann, 3. Auflage. ISBN 978-0-08-097016-5. | Fachbuch | module.yaml, theory.md, vehicle_model/bicycle_nonlinear |
| [Rajamani (2012)](../references.md#rajamani2012) | Rajamani, R. (2012): Vehicle Dynamics and Control. Springer, 2. Auflage. DOI 10.1007/978-1-4614-1433-9. | Fachbuch | KinematicBicycleModel.derivatives (module.yaml), LinearBicycleModel.state_space (module.yaml), links.yaml → package:vehicle_models, module.yaml, theory.md, vehicle_model/bicycle_kinematic, vehicle_model/bicycle_linear |
| [Schramm et al. (2018)](../references.md#schramm2018) | Schramm, D.; Hiller, M.; Bardini, R. (2018): Modellbildung und Simulation der Dynamik von Kraftfahrzeugen. Springer Vieweg. | Fachbuch | DoubleTrackModel.derivatives (module.yaml), MultibodyModel.derivatives (module.yaml), module.yaml, theory.md, vehicle_model/double_track, vehicle_model/multibody |
| [Werling (2011)](../references.md#werling2011) | Werling, M. (2011): Ein neues Konzept für die Trajektoriengenerierung und -stabilisierung in zeitkritischen Verkehrsszenarien. Dissertation. KIT Scientific Publishing (Schriftenreihe des Instituts für Angewandte Informatik / Automatisierungstechnik, Band 34). ISBN 978-3-86644-631-1. https://publikationen.bibliothek.kit.edu/1000021738. | Dissertation / Abschlussarbeit | desm_forces (@trace), slip_angles (@trace), werling_model1 (@trace), werling_model4 (@trace) |
