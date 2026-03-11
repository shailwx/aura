# Copilot Instructions for Aura

> Always follow [CONTRIBUTING.md](../CONTRIBUTING.md) for the full engineering workflow.
> The rules below are the machine-readable summary Copilot uses at code-generation time.

## Branch naming

| Prefix   | Use for                                             |
|----------|-----------------------------------------------------|
| `feat/`  | New agent capability, tool, or endpoint             |
| `fix/`   | Bug fixes                                           |
| `test/`  | Test coverage additions                             |
| `docs/`  | Documentation-only changes                         |
| `chore/` | Config, tooling, non-functional changes             |
| `infra/` | Dockerfile, kagent.yaml, Kubernetes changes         |
| `ci/`    | GitHub Actions pipeline changes                     |

Always include the issue reference in the branch name or first commit, e.g.
`feat/bulk-discount  →  closes #N`.

For the bulk purchase / volume discount feature use branch **`feat/bulk-discount`**.

## Code style

- Every function must have a **docstring** and **type hints** on all parameters and return values.
- Follow the existing patterns in `tools/` and `agents/` — dataclasses for structured data, `dict[str, Any]` returns for tool functions.
- Tools live in `tools/`, agents live in `agents/`, tests live in `tests/`.
- Use `from __future__ import annotations` for forward references.

## No secrets

Never commit credentials, API keys, or secrets.
Use `.env` for local config and GitHub Secrets for CI/CD.
See `.env.example` for the expected variables.

## Compliance guard

If you touch `tools/compliance_tools.py` or `agents/sentinel.py`, document the
compliance impact in your PR description.  The Sentinel is the AML/KYC gate —
changes here require extra scrutiny.

## Test rule

- All existing tests must stay green after every change.
- Add tests in `tests/` for any new logic.
- Run locally before pushing: `.venv/bin/python -m pytest`

## Commit format — Conventional Commits

```
<type>: <short description>

[optional body]
[optional footer — closes #N]
```

Types: `feat` · `fix` · `test` · `docs` · `chore` · `infra` · `ci`

Example:
```
feat: add volume discount engine and pricing tiers

- PricingTier dataclass added to ucp_tools.py
- calculate_bulk_price() stacks vendor tier + platform rebate
- Scout and Closer updated to use discounted totals

Closes #12
```

## Pre-push checklist

```bash
.venv/bin/python -m ruff check . --fix   # zero warnings required
.venv/bin/python -m pytest               # zero failures required
```

## Pull requests

- Reference the issue: `Closes #N`
- Complete **every section** of [.github/pull_request_template.md](pull_request_template.md)
- The CI pipeline (`lint` + `test` + `docker-build`) must be green before merge
- At least **1 approval** is required; use **Squash and merge**
