# Branch Protection & GitHub Settings

Recommended configuration for MotionEngine as a single-maintainer project,
designed to scale for community contributions.

## Branch Protection Rules — `main`

### Required Status Checks

Enable **"Require status checks to pass before merging"** with these checks:

| Check | Workflow | Purpose |
|---|---|---|
| `Build Package` | `build.yml` | Package builds and imports correctly |
| `Unit Tests` | `test.yml` | All unit tests pass (matrix: OS × Python) |
| `Numerical Validation` | `test.yml` | Physics and math validation tests pass |
| `Ruff (lint + format)` | `lint.yml` | Code style and lint rules |
| `Type Check (mypy)` | `quality.yml` | Type correctness on core modules |
| `Test Coverage` | `coverage.yml` | Coverage ≥ 80% |

### Recommended Settings

```
☑ Require a pull request before merging
  ☐ Require approvals (0 — single maintainer; increase to 1 when team grows)
  ☑ Dismiss stale pull request approvals when new commits are pushed
  ☑ Require review from Code Owners (add CODEOWNERS file when team grows)

☑ Require status checks to pass before merging
  ☑ Require branches to be up to date before merging

☑ Require conversation resolution before merging

☐ Require signed commits (optional — enable for higher trust)

☑ Require linear history (keeps git log clean)

☐ Include administrators (optional — you may want to bypass for hotfixes)

☑ Restrict who can push to matching branches
  → Only the repository owner
```

### When to Tighten

| Team Size | Changes |
|---|---|
| 1 (current) | No required approvals; owner can merge directly |
| 2–3 | Require 1 approval; add CODEOWNERS |
| 4+ | Require 2 approvals; enable signed commits; restrict force-push |

## Protected Tags

Enable tag protection for `v*` tags to ensure only the maintainer can create releases.

## GitHub Settings Checklist

- [ ] Enable **GitHub Actions** for the repository
- [ ] Add repository topics: `trajectory-planning`, `motion-planning`, `autonomous-driving`, `vehicle-dynamics`, `mpc`, `path-planning`, `adas`, `simulation`, `robotics`
- [ ] Set repository description: *"Open-source framework for motion planning, trajectory optimization, vehicle dynamics simulation, and autonomous driving research"*
- [ ] Enable **Dependabot alerts** and **security advisories**
- [ ] Enable **CodeQL** analysis (auto-configured via `security.yml`)
- [ ] Configure **branch protection** for `main` as described above
- [ ] Set default branch to `main`
- [ ] Enable **Discussions** (for community Q&A, when ready)
- [ ] Add a **social preview image** (use `docs/images/banner.svg` rendered to PNG)

## Secrets Required

| Secret | Purpose | Required For |
|---|---|---|
| `CODECOV_TOKEN` | Coverage upload to Codecov | `coverage.yml` |
| `GITLEAKS_LICENSE` | Gitleaks secret scanning | `security.yml` (optional) |

## Workflow Dependency Graph

```
push/PR → build.yml ──→ Build Package
        → test.yml  ──→ Unit Tests → Integration Tests
                                   → Numerical Validation
                                   → Slow Tests
        → lint.yml  ──→ Ruff
        → quality.yml → mypy + radon + pip-audit
        → coverage.yml → Coverage ≥ 80%
        → security.yml → CodeQL + Gitleaks

tag v* → release.yml → Validate → Build → GitHub Release
```
