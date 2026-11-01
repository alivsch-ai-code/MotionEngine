# Using the project agents

MotionEngine's specialist roles live in [`agents/`](../agents/). The local
pre-commit hook can ask GitHub Copilot CLI to review staged changes with the
roles that match the changed files.

## One-time setup

1. Install the project development tools:

   ```powershell
   python -m pip install -e ".[dev]"
   pre-commit install
   ```

2. Install GitHub Copilot CLI and sign in:

   ```powershell
   npm install --global @github/copilot
   copilot login
   ```

   Copilot CLI requires an account with access to Copilot CLI. This is separate
   from GitHub Actions billing or GitHub Pro. Check your account's Copilot plan
   and usage limits before enabling AI reviews.

3. From the repository root, stage a change and commit as usual:

   ```powershell
   git add path/to/changed-file.py
   git diff --cached
   git commit -m "Describe the change"
   ```

The hook reviews only staged changes. It chooses the applicable roles using
the routing rules in [`AGENTS.md`](../AGENTS.md), then runs each role separately.
For example, changes to `.github/workflows/` use the GitHub and Testing agents;
vehicle-model changes use the domain, Mathematics, Physics, and Testing agents.
Every selected reviewer receives the complete staged diff, so inspect it before
committing and do not stage unrelated files.

## Important behavior

- Reviews are advisory: missing Copilot CLI, missing authentication, timeouts,
  or review errors print a warning but do not prevent a commit.
- The hook never edits files. Copilot is limited to the read tool; shell and
  write tools are denied.
- Staged diffs are sent to GitHub Copilot for review. Do not stage secrets or
  sensitive data you are not permitted to share with that service.
- The regular Ruff pre-commit hooks still run independently.

## Run or skip a review manually

To run the hook again on the current index:

```powershell
pre-commit run motionengine-agent-review
```

To run the staged-change reviewer directly:

```powershell
python scripts/review_agents.py
```

To skip AI review for one commit while keeping other pre-commit hooks:

```powershell
$env:MOTIONENGINE_AGENT_REVIEW = "off"
git commit -m "Describe the change"
Remove-Item Env:MOTIONENGINE_AGENT_REVIEW
```

On Bash, use `MOTIONENGINE_AGENT_REVIEW=off git commit -m "Describe the change"`.
Set `MOTIONENGINE_AGENT_REVIEW_TIMEOUT` to change the total time limit in
seconds (default: 300).

## What the roles review

The hook uses the domain routing table in `AGENTS.md`. Unknown file areas
receive an Architect and Testing review rather than silently receiving no
review. Release approval is intentionally not run on every commit; it remains
a release-time gate.
