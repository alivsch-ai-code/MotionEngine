import subprocess

from scripts.review_agents import run_reviews, select_agents


def test_selects_ci_reviewers_for_workflow_changes():
    assert select_agents([".github/workflows/test.yml"]) == [
        "testing-agent",
        "github-agent",
    ]


def test_selects_domain_reviewers_for_vehicle_controllers():
    assert select_agents(["vdsim/controllers/lateral.py"]) == [
        "planning-agent",
        "dynamics-agent",
        "mathematics-agent",
        "physics-agent",
        "testing-agent",
    ]


def test_selects_domain_reviewers_for_planning_tests():
    assert select_agents(["tests/planning/test_planner.py"]) == [
        "planning-agent",
        "mathematics-agent",
        "testing-agent",
    ]


def test_selects_vehicle_domain_reviewers_for_actuator_tests():
    assert select_agents(["tests/actuators/test_brake.py"]) == [
        "dynamics-agent",
        "mathematics-agent",
        "physics-agent",
        "testing-agent",
    ]


def test_selects_architect_for_framework_tests():
    assert select_agents(["tests/framework/test_plugins.py"]) == [
        "architect-agent",
        "testing-agent",
    ]


def test_selects_architect_for_new_python_modules_and_dependencies():
    assert "architect-agent" in select_agents(["vdsim/planning/new_planner.py"], ["vdsim/planning/new_planner.py"])
    assert select_agents(["pyproject.toml"]) == [
        "architect-agent",
        "testing-agent",
        "github-agent",
    ]


def test_selects_documentation_and_research_reviewers_for_references():
    assert select_agents(["docs/references/catalog.yml"]) == [
        "documentation-agent",
        "research-agent",
    ]


def test_selects_documentation_reviewer_for_contributor_instructions():
    assert select_agents(["CONTRIBUTING.md"]) == ["documentation-agent"]


def test_uses_safe_defaults_for_unmapped_files():
    assert select_agents(["configs/custom.toml"]) == [
        "architect-agent",
        "testing-agent",
    ]


def test_empty_change_set_has_no_reviewers():
    assert select_agents([]) == []


def test_review_command_is_read_only_and_does_not_block_on_cli_error(monkeypatch, tmp_path, capsys):
    (tmp_path / "AGENTS.md").write_text("Project review rules", encoding="utf-8")
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "testing-agent.md").write_text("Testing role", encoding="utf-8")
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 1, "", "not signed in")

    monkeypatch.setattr("scripts.review_agents.shutil.which", lambda _: "copilot")
    monkeypatch.setattr("scripts.review_agents.subprocess.run", fake_run)

    run_reviews(tmp_path, ["testing-agent"], "diff --git a/tests/example.py")

    output = capsys.readouterr()
    command, options = next(call for call in calls if call[0][0] == "copilot")
    assert "--available-tools=read" in command
    assert "--allow-tool=read" in command
    assert "--allow-all-tools" not in command
    assert "--deny-tool=write" in command
    assert "--deny-tool=shell" in command
    assert "--allow-all-paths" not in command
    assert "Project review rules" in options["input"]
    assert "Testing role" in options["input"]
    assert "diff --git a/tests/example.py" in options["input"]
    assert "commit will continue" in output.err
