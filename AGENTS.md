# AGENTS.md

MotionEngine is reviewed by specialized agents. This file tells any AI coding assistant, and any human contributor, how the repository is governed. Read it before you change anything.

The Python package is called `vdsim`. The project is called MotionEngine.

## Setup and checks

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,gui]"

ruff check .                                    # lint
mypy vdsim/core vdsim/vehicle_models vdsim/tire_models vdsim/simulation --ignore-missing-imports
pytest tests/ -m "not gui and not slow and not integration and not benchmark"   # unit tests
pytest tests/ -m integration                    # integration tests
pytest tests/numerical/                         # numerical validation and performance limits
python scripts/generate_readme_figures.py       # regenerate README figures
```

CI installs only `.[dev]`, without PySide6. Code and tests must work in that environment.

## Rules for every agent

1. **Evidence over assertion.** A claim needs a command output, a test, a measurement, or a derivation. "Should work" is not a review result.
2. **Run it before you report it.** Do not call a task done, a test passing, or a failure "pre-existing" unless you ran it and checked.
3. **A failing test is information.** Find the cause before you change the test. Never weaken an assertion to get a green run.
4. **Never invent numbers.** Benchmarks, candidate counts and scores in documentation must be measured, and the source must be reproducible.
5. **Use the conventions.** ISO 8855 (x forward, y left, z up), SI units, the names in `vdsim/core/conventions.py`.
6. **Understand a quantity before you bound it.** Check what a variable represents, for example absolute force or deviation from equilibrium, before you clamp, filter or sign-correct it.
7. **Keep changes in scope.** Do not refactor unrelated code. Do not add a dependency without saying why.
8. **The maintainer decides.** Agents review and recommend. Only the maintainer merges, releases, or overrides a verdict.

## Agents

| Agent | Role | Authority | Definition |
|---|---|---|---|
| Architect | Principal Software Architect | Highest on structure and public APIs | [architect-agent.md](agents/architect-agent.md) |
| Planning | Motion Planning Expert | Domain review of planning | [planning-agent.md](agents/planning-agent.md) |
| Vehicle Dynamics | Vehicle Dynamics Expert | Domain review of models and parameters | [dynamics-agent.md](agents/dynamics-agent.md) |
| Mathematics | Applied Mathematics Reviewer | Reviews every mathematical implementation | [mathematics-agent.md](agents/mathematics-agent.md) |
| Physics | Physics Validation Expert | May reject anything violating physics | [physics-agent.md](agents/physics-agent.md) |
| Performance | Performance Engineering Lead | Blocks regressions beyond agreed limits | [performance-agent.md](agents/performance-agent.md) |
| Testing | Quality Assurance Lead | May block releases for missing critical tests | [testing-agent.md](agents/testing-agent.md) |
| Documentation | Technical Writer | Reviews all user-facing text | [documentation-agent.md](agents/documentation-agent.md) |
| Research | Scientific Reviewer | Maintains `docs/references/` | [research-agent.md](agents/research-agent.md) |
| GitHub | Open Source Maintainer | Maintains CI/CD and repository health | [github-agent.md](agents/github-agent.md) |
| Release | Release Manager | Final gate before a release | [release-agent.md](agents/release-agent.md) |

## Which agents apply

| Change touches | Domain agent | Also required |
|---|---|---|
| `vdsim/planning/`, `vdsim/behavior/`, `vdsim/prediction/`, `vdsim/geometry/` | Planning | Mathematics, Testing |
| `vdsim/vehicle_models/`, `vdsim/tire_models/`, `vdsim/powertrain/`, `vdsim/actuators/` | Vehicle Dynamics | Mathematics, Physics, Testing |
| `vdsim/stabilization/`, `vdsim/controllers/` | Vehicle Dynamics, Planning | Mathematics, Physics, Testing |
| `vdsim/simulation/` | Vehicle Dynamics | Mathematics, Performance, Testing |
| `vdsim/core/`, `vdsim/framework/`, `vdsim/runtime/`, public interfaces, folder structure | Architect | Testing |
| `tests/` | Testing | The domain agent of the code under test |
| `.github/`, `pyproject.toml`, `scripts/` | GitHub | Testing |
| `README.md`, `docs/`, `CHANGELOG.md` | Documentation | Research for citations |

The Architect also reviews any change that adds a module, a dependency or a public interface. Performance also reviews anything on the per-cycle or per-substep path.

## Review flow

A change is **major** if it changes behavior, numerics, a public interface, the folder structure, CI, or a dependency. Typo fixes and comment edits are not major.

For every major change:

1. **Architect review.** Does it fit the structure?
2. **Domain review.** Is it correct for the domain?
3. **Mathematics and Physics review.** Are the equations and the physics right?
4. **Testing approval.** Are the tests sufficient, and do they pass?
5. **Documentation update.** Is every affected document still true?
6. **GitHub validation.** Are all workflows green on the actual commit?
7. **Release approval.** Only when the change ships in a release.

Skip a step only when no applicable agent exists for it, and say that you skipped it. **No feature is complete until all applicable agents approve.**

## Review format

Record the result in the pull request, one block per agent:

```text
Agent: Physics
Verdict: APPROVED | CHANGES REQUESTED | BLOCKED
Evidence: commands run, results, derivations
Findings: file:line, what is wrong, why it matters
```

An approval without evidence does not count.

## Authority and conflicts

- Architect decides structure. Physics and Mathematics decide correctness. Testing decides whether evidence is sufficient. A domain agent cannot overrule them in their area.
- Correctness wins over performance, and performance wins over style.
- Disagreements go to the maintainer, with both positions stated.
- An agent reviewing its own change must re-derive the result independently, not re-read its reasoning.

## Using an agent

Agent definitions are plain Markdown and work with any tool. Ask your assistant to adopt a role, for example:

> Act as the Physics Agent from `agents/physics-agent.md`. Review the diff of this branch and report in the format from `AGENTS.md`.

For local, advisory reviews on every commit, install the pre-commit hook and
configure Copilot CLI as described in [docs/AGENT_REVIEWS.md](docs/AGENT_REVIEWS.md).
The hook reviews staged changes only, selects applicable roles from the table
above, and never blocks a commit when an AI review cannot run.

| Tool | Entry point in this repository |
|---|---|
| Claude Code | `CLAUDE.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Cursor | `.cursor/rules/motionengine.mdc` |
| Cline | `.clinerules` |
| Roo Code | `.roo/rules/motionengine.md` |
| Other agents | `AGENTS.md` |

All entry points only link here, so this file stays the single source of truth.

## Repository map

| Path | Content |
|---|---|
| `vdsim/core/` | Interfaces, registry, parameters, conventions |
| `vdsim/framework/` | Component model, versioned plugins, tracing |
| `vdsim/planning/` | Werling planner and baselines |
| `vdsim/stabilization/`, `vdsim/controllers/` | Tracking controllers, chassis systems |
| `vdsim/vehicle_models/`, `vdsim/tire_models/` | Plant models |
| `vdsim/simulation/`, `vdsim/world/` | Solver, environment, scenarios, traffic |
| `tests/numerical/` | Numerical validation and performance limits |
| `docs/references/` | Bibliography in YAML |
| `docs/images/` | Generated figures. Do not edit by hand |
| `agents/` | Agent definitions |
