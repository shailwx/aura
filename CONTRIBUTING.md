# Contributing to Aura

This document defines the end-to-end engineering workflow for the Aura project — from picking up an issue to merging to `main`.

---

## Workflow at a Glance

```
Issue → Branch → Develop → Test → PR → Review → Merge → CHANGELOG
```

---

## 1. Pick an Issue

1. Go to the [Issues board](https://github.com/shailwx/aura/issues)
2. Choose an open issue — prefer ones in the **Demo Day — Mar 11 2026** milestone first
3. Assign yourself to signal ownership
4. Check the issue for its designated **branch name** (listed in every issue body)

| Milestone | Issues |
|---|---|
| Demo Day — Mar 11 2026 | #1 kagent.yaml, #2 E2E test, #6 CI pipeline, #8 PR template |
| v0.1 Post-Hackathon | #3 Scout tests, #4 Sentinel tests, #5 Closer tests, #7 CD pipeline |

---

## 2. Cut a Branch

Always branch from an up-to-date `main`:

```bash
git checkout main
git pull origin main
git checkout <branch-name-from-issue>
```

### Branch naming convention

| Prefix | Use for |
|---|---|
| `feat/` | New capabilities (kagent.yaml, CI/CD pipeline) |
| `test/` | Test coverage additions |
| `chore/` | Config, tooling, non-functional changes |
| `fix/` | Bug fixes |
| `docs/` | Documentation-only changes |

**Include the issue reference in the branch or first commit**, e.g.:
```
feat/kagent-manifest   →  closes #1
test/sentinel-unit     →  closes #4
```

All 8 branches are already created and pushed. Check out your branch:
```bash
git checkout feat/kagent-manifest   # example
```

---

## 3. Set Up Locally

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your GCP project details if needed
```

---

## 4. Develop

- Follow the existing code style — functions have docstrings and type hints
- Tools live in `tools/`, agents live in `agents/`
- Do **not** commit credentials or secrets — use `.env` / GitHub Secrets
- If touching compliance logic (`tools/compliance_tools.py`, `agents/sentinel.py`), document the impact in your PR

---

## 5. Test

Run the full test suite before pushing:

```bash
# Run all tests
.venv/bin/python -m pytest

# Run a specific file
.venv/bin/python -m pytest tests/test_compliance_tools.py -v

# Lint check
.venv/bin/python -m ruff check .
```

All 91 existing tests must stay green. Add tests for any new logic.

---

## 6. Commit

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format:

```
<type>: <short description>

[optional body]
[optional footer — closes #N]
```

| Type | When to use |
|---|---|
| `feat` | New agent capability, tool, or endpoint |
| `fix` | Bug fix |
| `test` | Adding or fixing tests |
| `infra` | Dockerfile, kagent.yaml, K8s changes |
| `ci` | GitHub Actions pipeline changes |
| `docs` | Documentation only |
| `chore` | Config, tooling, dependencies |

**Examples:**
```bash
git commit -m "feat: add kagent.yaml Agent CRDs for all 4 agents

- Architect, Scout, Sentinel, Closer as kagent.dev/v1alpha2 resources
- Shared ModelConfig for Vertex AI Gemini 2.0 Flash
- Resource limits per DEPLOYMENT.md spec

Closes #1"
```

---

## 7. Open a Pull Request

Push your branch and open a PR against `main`:

```bash
git push origin <your-branch>
gh pr create --base main --fill
```

When opening the PR:
- The **PR template** ([.github/pull_request_template.md](.github/pull_request_template.md)) auto-fills — complete every section
- Reference the issue with `Closes #N` in the summary so it auto-closes on merge
- Ensure the branch name matches the one listed in the issue

---

## 8. CI Must Pass

Every PR triggers the CI pipeline ([.github/workflows/ci.yml](.github/workflows/ci.yml)):

| Job | What it checks |
|---|---|
| `lint` | `ruff check .` — zero warnings |
| `test` | `pytest tests/ --tb=short -v` — 0 failures |
| `docker-build` | `docker build --target runtime` — builds cleanly |

**The PR cannot be merged until all 3 jobs are green.**

Fix failures locally before requesting review:
```bash
.venv/bin/python -m ruff check . --fix   # auto-fix lint issues
.venv/bin/python -m pytest               # confirm tests pass
```

---

## 9. Review & Merge

- At least **1 approval** is required before merging
- Reviewer focuses on: correctness, compliance impact, test coverage, no secrets
- Use **Squash and merge** to keep `main` history clean
- Delete the feature branch after merge (GitHub does this automatically if enabled)

---

## 10. Post-Merge

After your PR lands on `main`:

1. **Update [CHANGELOG.md](CHANGELOG.md)** — move your changes from `[Unreleased]` into the next version block, or add them to `[Unreleased]` if a release isn't imminent
2. **Verify CI/CD on `main`** — the CD pipeline ([.github/workflows/cd.yml](.github/workflows/cd.yml)) triggers automatically on push to `main`
3. **Close the issue** — it auto-closes if your PR contained `Closes #N`

---

## Branch Protection (main)

| Rule | Setting |
|---|---|
| Require PR before merging | ✅ |
| Required approvals | 1 |
| Required status checks | `lint`, `test`, `docker-build` (CI pipeline) |
| No direct pushes | ✅ |

Configure in: **GitHub → Settings → Branches → Branch protection rules → main**

---

## Quick Reference

```bash
# Full local workflow
git checkout main && git pull origin main
git checkout feat/your-branch
# ... make changes ...
.venv/bin/python -m ruff check . --fix
.venv/bin/python -m pytest
git add -A && git commit -m "feat: your change (closes #N)"
git push origin feat/your-branch
gh pr create --base main --fill
```
