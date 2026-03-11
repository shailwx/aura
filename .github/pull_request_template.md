## Summary

<!-- Describe what this PR does and why. Link the related issue. -->

Closes #

---

## Type of Change

- [ ] `feat` — New feature or capability
- [ ] `fix` — Bug fix
- [ ] `infra` — Kubernetes / Docker / pipeline change
- [ ] `test` — Test coverage additions or fixes
- [ ] `docs` — Documentation only
- [ ] `chore` — Tooling, config, or dependency update

---

## Checklist

- [ ] Tests written or updated for all changed logic
- [ ] `pytest tests/ -v` passes locally
- [ ] Documentation updated if behaviour changed (docs/, README)
- [ ] **Compliance impact assessed** — Sentinel/KYC/AML flow is unchanged or intentionally modified
- [ ] Agent orchestration flow is unchanged or changes are reflected in `docs/AGENT_FLOW.md`
- [ ] No secrets or credentials committed (use `.env` / GitHub Secrets)
- [ ] Dockerfile still builds: `docker build -t aura:local .`
