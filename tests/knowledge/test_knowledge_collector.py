from vdsim.knowledge.collector import collect

OWN_PACKAGES = ["core", "tire_models", "vehicle_models", "powertrain", "actuators", "controllers", "trajectory",
                "simulation", "analysis", "reporting", "visualization", "gui", "framework", "geometry", "lane_change",
                "knowledge"]
WITH_THEORY = ["core", "tire_models", "vehicle_models", "powertrain", "actuators", "controllers", "trajectory",
               "simulation", "analysis", "reporting", "framework", "geometry", "lane_change", "knowledge"]
SUBSECTIONS = ["Ziel und Zweck", "Theorie", "Herleitung", "Annahmen", "Randbedingungen", "Variablen",
               "Anwendungsgrenzen", "Vor- und Nachteile", "Numerische Aspekte", "Praktische Auswirkungen",
               "In einfachen Worten", "Quellen"]


def test_collects_whole_repository(kb):
    assert set(OWN_PACKAGES) <= set(kb.packages)
    assert "vdsim.geometry.reference_line" in kb.modules
    mod = kb.modules["vdsim.tire_models.pacejka"]
    assert mod.doc.startswith("Pacejka") and "magic_formula" in [f.name for f in mod.functions]
    assert "vdsim.tire_models.pacejka" in kb.modules["vdsim.tire_models"].imports


def test_legacy_and_framework_components(kb):
    for cid in ("vehicle_model/double_track", "tire_model/pacejka", "lateral_controller/stanley",
                "longitudinal_controller/acc", "chassis_system/esp", "maneuver/iso_double_lane_change",
                "trajectory_loader/opendrive"):
        assert cid in kb.components, cid
    stanley = kb.components["lateral_controller/stanley"]
    assert stanley.legacy and stanley.inputs["state"]["type"] == "VehicleState"
    gain = next(p for p in stanley.params if p["name"] == "gain")
    assert gain["default"] == 1.2 and gain["unit"] == "-"
    assert "stanley_controller" in stanley.doc["concepts"]
    esp = kb.components["chassis_system/esp"]
    assert any(f["name"] == "systems.esp_gain" and f["unit"] == "N m s/rad" for f in esp.config_fields)
    tire = next(p for p in kb.components["tire_model/linear"].params if p["name"] == "nominal_load")
    assert tire["unit"] == "N"


def test_traces_from_code_and_module_yaml(kb):
    impls = {(t["implementation"], t["concept"], t["origin"]) for t in kb.traces}
    assert ("vdsim.geometry.reference_line.ReferenceLine.to_frenet", "frenet_transformation", "@trace") in impls
    assert ("vdsim.tire_models.pacejka.magic_formula", "magic_formula", "module.yaml") in impls
    assert ("vdsim.knowledge.graph.force_layout", "force_directed_layout", "@trace") in impls


def test_handwritten_docs_complete(kb):
    for name in OWN_PACKAGES:
        pkg = kb.packages[name]
        assert pkg.has_meta, name
        for key in ("title", "summary", "purpose", "architecture", "limitations", "references"):
            assert key in pkg.meta, (name, key)
    for name in WITH_THEORY:
        theory = kb.packages[name].theory
        assert theory is not None and theory.sections, name
        for sec in theory.sections:
            assert [t for t, _ in sec.subsections] == SUBSECTIONS, (name, sec.id)
            assert "Code-Name" in sec.subsection("Variablen"), (name, sec.id)
    for cid in ("frenet_transformation", "magic_formula", "runge_kutta", "stable_substeps", "stanley_controller",
                "pure_pursuit", "path_mpc", "wheel_slip_control", "esp_yaw_control", "torque_vectoring",
                "rear_axle_steering", "active_suspension", "latency_chain", "steering_characteristic_error",
                "curvature_feedback_correction", "understeer_gradient", "quasi_static_wheel_loads",
                "iso2631_comfort", "iso_test_kpis", "racing_line", "ggv_speed_profile", "curve_projection",
                "component_model", "plugin_registry", "dependency_injection", "kinematic_bicycle", "linear_bicycle",
                "nonlinear_bicycle", "double_track", "multibody", "brush_model", "combined_slip"):
        assert kb.concepts[cid].documented, cid


def test_tests_examples_and_configs_linked(kb):
    assert "tests/test_tire_models.py" in kb.packages["tire_models"].tests
    cfg = kb.configs["configs/scenarios/iso_doppelspurwechsel_80.json"]
    assert {"vehicle_model/double_track", "lateral_controller/stanley", "maneuver/iso_double_lane_change"} <= set(cfg.components)
    assert "run_lane_change.py" in kb.packages["lane_change"].examples


def test_tolerant_against_broken_files(tmp_path):
    pkg = tmp_path / "vdsim" / "broken"
    (pkg / "docs").mkdir(parents=True)
    (tmp_path / "vdsim" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "__init__.py").write_text('"""Broken package."""\nfrom . import bad\n', encoding="utf-8")
    (pkg / "bad.py").write_text("def f(:\n", encoding="utf-8")
    (pkg / "docs" / "module.yaml").write_text("title: [unclosed\n", encoding="utf-8")
    (pkg / "docs" / "theory.md").write_text("# T\n\n## Verfahren {#x}\n\n### Ziel und Zweck\n\nnur halb\n",
                                            encoding="utf-8")
    half = tmp_path / "vdsim" / "half"
    half.mkdir()
    (half / "m.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "docs" / "references").mkdir(parents=True)
    (tmp_path / "docs" / "references" / "r.yaml").write_text(": : :", encoding="utf-8")
    kb = collect(tmp_path, import_modules=False)
    assert {"broken", "half"} <= set(kb.packages)
    text = " ".join(kb.warnings)
    assert "Syntaxfehler" in text and "nicht lesbar" in text and "Namespace" in text
    assert kb.concepts["x"].documented
