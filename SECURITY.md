# Security Policy — orchestration_v1

> **Effective**: 2026-10-13  
> **Updated**: F8 (Functional/Immutable + Security 2026)

## Overview

This document defines security practices, incident reporting, and responsible disclosure for **orchestration_v1 kit**—a multi-AI orchestration framework with infrastructure automation, secrets management, and production-grade hardening.

**Scope**: Kit repository (`C:\pjt\orchestration_v1\`), plugins, hooks, scripts, and configuration deployed to multiple targets.

---

## 1. Secrets Management

### Policy

- **Never commit secrets** (API keys, PATs, passwords, database credentials, certificates)
- Use `.env.vault` (encrypted, 0o600 permissions) for local development
- Use OS keyring (via `python-keyring`) for production
- Environment variables for CI/CD (GitHub Actions Secrets, etc.)

### Implementation

**Vault Class** (`secrets_vault.py`):
```python
from .claude.scripts.lib.secrets_vault import SecretVault
vault = SecretVault()
anthropic_key = vault.get("ANTHROPIC_API_KEY")
vault.set("github_pat", "ghp_...")
```

**Priority** (fallback chain):
1. OS keyring (production)
2. `.env.vault` (local)
3. Environment variables (CI/CD)
4. Default (if public)

### Files

| File | Purpose | Permissions | Git |
|------|---------|-------------|-----|
| `.env.vault` | Encrypted local secrets | `0o600` (owner only) | `.gitignore` |
| `.env.example` | Template (no values) | Public | Committed |
| `pyproject.toml` | Config, no secrets | Public | Committed |

### Rotation

- Anthropic API keys: quarterly or on compromise
- GitHub PATs: 90-day expiration (GitHub organization setting)
- Database credentials: on personnel change or compromise
- Log files: 14-day retention, then deletion

---

## 2. Code Security

### Pre-Commit Hooks

Run before every commit:

```bash
pre-commit install
```

Hooks enforce:
- **Bandit**: Python security (hardcoded secrets, unsafe patterns)
- **Gitleaks**: Credential detection
- **Ruff**: Linting + formatting
- **Mypy**: Type checking (strict on `.claude/scripts/lib/`)
- **YAML/JSON validation**: Config correctness

### Type Safety

Python scripts in `.claude/scripts/lib/` use:
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    """Immutable config (no mutation accidents)."""
    api_key: str
    timeout: int = 30
```

- **Frozen dataclasses** prevent mutation
- **Type hints** enforce contracts
- **Mypy strict** catches bugs at check time, not runtime

### Static Analysis

Run manually:
```bash
python .claude/scripts/lib/bandit -r .claude/scripts/lib/ plugins/
ruff check --strict .claude/scripts/lib/
mypy --strict .claude/scripts/lib/
```

---

## 3. Hardcoded Paths & Credentials

### Absolute Prohibition

| Pattern | Example | Solution |
|---------|---------|----------|
| User paths | `C:\Users\ja205\...` | `Path.home()` · `%USERPROFILE%` |
| Python version | `C:\...\Python314\python.exe` | `shutil.which('python')` |
| Hostname | `DESKTOP-AR8DB38` | `socket.gethostname()` |
| API keys | `export OPENAI_API_KEY=sk-...` | `.env.vault` · SecretVault · keyring |
| Database URLs | `postgres://user:pass@localhost:5432/db` | SecretVault · env var |

### Validation

```bash
# Audit for hardcoded secrets
grep -rn 'C:\\Users\\[a-z0-9_]*' .
grep -rn '/home/[a-z0-9_]*' .
grep -rn 'Python3[0-9][0-9]' .
grep -rn 'sk-' plugins/ .claude/scripts/
```

**CI Gate**: Pre-push gitleaks scan blocks any commit with:
- API key patterns (Anthropic, OpenAI, GitHub, AWS)
- Certificate/key files
- Database credentials
- OAuth tokens

---

## 4. Data Protection

### Sensitive Data Classification

| Level | Examples | Storage | Retention |
|-------|----------|---------|-----------|
| **Public** | Architecture docs, public code | Git | Permanent |
| **Internal** | Runbooks, deployment guides | Git (`.claudeai/rules/`) | Permanent |
| **Confidential** | Credentials, API keys, PII | `.env.vault` / keyring / CI secrets | 90 days |
| **Restricted** | Database contents, business data | Encrypted DB / target system | Per policy |

### Audit Trail

All file access / modification logged in `orca.db.file_audit`:
- Session ID, timestamp, actor (claude/codex/gemini/user)
- File path, action (create/write/rename/archive/delete)
- Size, hash (for tamper detection)

Query:
```bash
sqlite3 .claude/state/orca.db "SELECT * FROM file_audit WHERE ts > datetime('now', '-7 days') ORDER BY ts DESC"
```

### .env.vault Handling

```bash
# Create with secure permissions
touch .env.vault
chmod 0o600 .env.vault

# Never commit
echo ".env.vault" >> .gitignore
echo ".env" >> .gitignore

# Example content
ANTHROPIC_API_KEY="sk-ant-v0-..."
GITHUB_PAT="ghp_..."
DB_PASSWORD="encrypted_via_keyring"
```

---

## 5. Infrastructure Security

### Deployment Checklist

Before `install.bat` / `sync-to-team.sh`:

- [ ] `.env.vault` not in git
- [ ] All credentials in SecretVault / keyring
- [ ] Pre-commit hooks pass (bandit, gitleaks)
- [ ] Mypy strict on `.claude/scripts/lib/`
- [ ] CODEOWNERS review (kit-level changes)
- [ ] No hardcoded paths (grep audit)
- [ ] .pre-commit-config.yaml installed on target
- [ ] Approval gate active (approval-gate-rules.md)

### Network & Access

| Layer | Control |
|-------|---------|
| **VCS** | GitHub organization MFA required |
| **Secrets** | GitHub Actions Secrets (encrypted at rest) |
| **CI/CD** | `.github/workflows/` restricted to CODEOWNERS |
| **Deployment** | SSH keys in CI only, never in code |
| **Logs** | `.claude/logs/*.log` contain no secrets (masked) |

---

## 6. Incident Response

### Suspected Breach

1. **Immediate**: Rotate affected secrets (API keys, PATs, DB passwords)
2. **Contain**: Revoke any exposed tokens in provider dashboards
3. **Investigation**: Check git log for commit timestamp and content
4. **Notification**: Report to team leads and affected platforms (GitHub, Anthropic, etc.)
5. **Prevention**: Update pre-commit hooks, audit pipeline

### Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email: **sjseo@itcen.com**

- Subject: `[SECURITY] orchestration_v1 — <vulnerability type>`
- Include: Affected component, reproduction steps, impact, suggested fix
- Response time: 48 hours (weekday), 72 hours (weekend)

### Public Disclosure

Once fixed and deployed:
1. Create GitHub Release notes with CVE ID (if applicable)
2. Update SECURITY.md with lesson learned
3. Add regression test to prevent recurrence

---

## 7. Compliance & Audit

### Automated Checks

| Tool | Trigger | Scope |
|------|---------|-------|
| **Bandit** | Pre-commit, PR CI | `.claude/scripts/lib/`, plugins/ |
| **Gitleaks** | Pre-commit, PR CI, push | Full repo |
| **Ruff** | Pre-commit, CI | Python code |
| **Mypy** | Pre-commit, CI | Type safety (lib only) |
| **OWASP Dependency Check** | Weekly CI | Python packages |

### Audit Trail

```bash
# Session activity
sqlite3 .claude/state/orca.db "SELECT ts, actor, action, path FROM file_audit ORDER BY ts DESC LIMIT 20"

# Approval gate decisions
sqlite3 .claude/state/orca.db "SELECT * FROM approval_requests WHERE status IN ('approved', 'rejected')"

# Worker heartbeats (health)
tail -f .claude/logs/watchdog-heartbeat.log
```

### Manual Review Frequency

- **Kit code** (CLAUDE.md, plugins/, .claude/rules/): Before merge to main
- **Secrets usage**: Monthly (grep `.env*`, SecretVault calls)
- **Dependencies**: Quarterly (pip audit, npm audit)
- **Logs**: Weekly (rotate & compress)

---

## 8. Best Practices for Contributors

### Before Committing

```bash
# Install pre-commit hooks
pre-commit install

# Run checks locally
pre-commit run --all-files

# Audit for secrets
gitleaks detect --verbose

# Type check (lib only)
mypy --strict .claude/scripts/lib/
```

### Writing Secure Code

1. **Dataclasses** for configuration (immutable, type-safe)
   ```python
   @dataclass(frozen=True)
   class DbConfig:
       host: str
       port: int = 5432
       user: str = "app"
   ```

2. **SecretVault** for all credentials
   ```python
   vault = SecretVault()
   db_pass = vault.get("DB_PASSWORD")
   ```

3. **Never hardcode paths**
   ```python
   # WRONG
   db_path = "C:/Users/ja205/data/app.db"
   
   # RIGHT
   db_path = Path.home() / "data" / "app.db"
   ```

4. **Mask secrets in logs**
   ```python
   vault = SecretVault()
   token = vault.get("API_TOKEN")
   print(f"Token: {vault.mask(token)}")  # Token: ghp_...1234
   ```

5. **Handle errors gracefully**
   ```python
   try:
       result = call_external_api(key)
   except KeyError as e:
       logger.error("Missing credential: %s", e)
       return None  # Don't expose key name
   ```

---

## 9. Future Enhancements

| Item | Status | ETA |
|------|--------|-----|
| **Hardware security module (HSM) integration** | Planned | 2026 Q4 |
| **Audit log encryption** | In progress | 2026 Q3 |
| **Secrets rotation automation** | Spec | 2026 Q4 |
| **FIPS 140-2 compliance** | Planned | 2027 Q1 |
| **Zero-knowledge proof for deployments** | Research | TBD |

---

## 10. References

- `.claude/rules/best-practices.md` — Hardcoding prevention
- `.claude/rules/approval-gate-rules.md` — Sensitive operation approval
- `.claude/rules/failure-mode.md` — Error handling
- `.secrets.baseline` — Detect-secrets baseline
- `.bandit.yaml` — Bandit configuration
- `.pre-commit-config.yaml` — Hook pipeline

---

**Security Officer**: @bernakilljos  
**Last Updated**: 2026-10-13  
**Next Review**: 2026-12-13 (quarterly)
