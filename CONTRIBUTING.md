# Contributing to MotionEngine

Thank you for your interest in contributing to MotionEngine! This document explains how to get involved.

## Getting Started

1. Fork the repository and clone your fork
2. Create a virtual environment and install dev dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -e ".[dev,gui]"
pre-commit install
```

3. Run the tests to verify your setup:

```bash
pytest -x
```

## Development Workflow

1. Create a branch from `main` for your changes
2. Make your changes with clear, focused commits
3. Add or update tests for any changed behavior
4. Run the linter and test suite before submitting:

```bash
ruff check .
ruff format .
pytest -x
```

5. Open a pull request against `main`

The installed pre-commit hook runs Ruff and, when GitHub Copilot CLI is
installed and authenticated, advisory reviews from the applicable project
agents. See [Using the project agents](docs/AGENT_REVIEWS.md) for setup,
privacy details, and ways to run or skip the AI review.

## Code Style

- We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Follow PEP 8 naming conventions
- Public APIs and module docstrings in English
- SI units internally; degrees and km/h only at GUI and report boundaries
- ISO 8855 coordinate conventions (x forward, y left, z up)
- Wheel order in all arrays: FL, FR, RL, RR

## Adding a New Component

vdsim uses a plugin registry. To add a new component:

| Component | Base class | Decorator |
|---|---|---|
| Vehicle model | `VehicleModel` | `@register("vehicle_model", "name")` |
| Tire model | `TireModel` | `@register("tire_model", "name")` |
| Lateral controller | `LateralController` | `@register("lateral_controller", "name")` |
| Longitudinal controller | `LongitudinalController` | `@register("longitudinal_controller", "name")` |
| Chassis system | `ChassisSystem` | `@register("chassis_system", "name")` |
| Maneuver | — | `@maneuver("key", "Label", ...)` |
| Trajectory loader | — | `@register("trajectory_loader", "name")` |

See `examples/custom_nodes/` for complete examples in Python, C++, and Rust.

## Testing

- Tests live in `tests/`, mirroring the `vdsim/` package structure
- Use `pytest` markers: `@pytest.mark.slow` for long-running tests, `@pytest.mark.gui` for display-dependent tests
- Prefer numerical validation against analytical solutions where possible

## Commit Messages

- Use imperative mood: "Add feature" not "Added feature"
- Keep the first line under 72 characters
- Reference issues when applicable: "Fix #123"

## Review Process

Major changes follow the agent review flow in [AGENTS.md](AGENTS.md). The role definitions in [agents/](agents/) contain the checklists. They apply to human contributors and AI coding assistants alike.

## Reporting Bugs

Use the [bug report template](https://github.com/alivsch-ai-code/MotionEngine/issues/new?template=bug_report.yml) and include a minimal reproduction script.

## Questions?

Open a [discussion](https://github.com/alivsch-ai-code/MotionEngine/discussions) for questions about the codebase, design decisions, or feature ideas.
