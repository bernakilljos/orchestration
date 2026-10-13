# CI/CD Pipeline Documentation

## Overview

The orchestration-kit-v1 uses a comprehensive GitHub Actions CI/CD pipeline with:
- **Test Matrix**: Python 3.11–3.14 with pytest + coverage
- **Security Scans**: bandit (Python) + semgrep (SAST) + hardcoded-secrets detection
- **Release Automation**: GitHub Releases + PyPI publish + Docker build/push
- **Dependency Management**: Dependabot (Python, GitHub Actions, Docker)

---

## Workflows

### 1. test-matrix.yml
**Trigger**: Push to main/develop or PR against main  
**Runs**: For each Python version (3.11, 3.12, 3.13, 3.14)

**Steps**:
1. Checkout + setup Python + cache pip
2. Install dependencies (requirements.txt + dev tools)
3. Lint with ruff (format + import sort)
4. Type-check with mypy (strict mode)
5. Run pytest with coverage (target: 80%)
6. Upload coverage to Codecov
7. Validate plugin schemas
8. Smoke test (install check)

**Matrix Strategy**:
- Jobs run in parallel across Python versions
- Coverage upload only on Python 3.13
- Failures don't block PR (dev phase)

---

### 2. security-scan.yml
**Trigger**: Push to main/develop, PR against main, or weekly (Sunday 00:00 UTC)

**Steps**:
- **Bandit**: Python security issues (JSON + text reports)
- **Semgrep**: Static analysis (p/security-audit + p/python rules)
- **Hardcoded Secrets**: audit-hardcoded.py + audit-mojibake.py
- **Dependency Check**: pip-audit for outdated packages
- **Artifacts**: Uploads bandit + semgrep reports (30-day retention)
- **PR Comment**: Notifies reviewer on security scan completion

**Security Categories**:
- Hardcoded credentials / API keys
- SQL injection / command injection risks
- Path traversal / insecure deserialization
- Mojibake (encoding) issues

---

### 3. release.yml
**Trigger**: Tag push (v* or release-*)

**Steps**:
1. **Extract version** from git tag (e.g., v1.0.0 → 1.0.0)
2. **Generate changelog** from git log
3. **Build distribution** (python -m build → dist/*.whl)
4. **Create GitHub Release** (with changelog + artifacts)
5. **Publish to PyPI** (only for stable releases, skip alpha/beta)
6. **Build + Push Docker image** to ghcr.io
7. **Generate SBOM** (Software Bill of Materials) with Syft
8. **Slack notification** (optional)

**Docker Release**:
- Multi-stage build (builder + runtime)
- Metadata tags: semver + SHA + latest
- Caching enabled (gha type)
- SBOM uploaded as artifact

---

### 4. dependabot.yml
**Trigger**: Weekly on Monday (04:00 UTC)

**Targets**:
1. **pip** (Python deps): All production + dev packages
   - Ignore semver-major for 'anthropic' (stability)
   - PR branch: `dependabot/pip/<package>`
   - Labels: dependencies, python

2. **GitHub Actions**: All action versions
   - PR branch: `dependabot/github-actions/<action>`
   - Labels: ci/cd, github-actions

3. **Docker**: Base image updates
   - Labels: docker, dependencies

**Review Rules**:
- Reviewers: bernakilljos
- Allow both direct + dev dependencies
- Weekly PRs auto-created, need manual merge

---

## Docker Build Pipeline

### Dockerfile (Multi-stage)

**Stage 1: Builder**
- Base: python:3.14-slim
- Install build tools (git, gcc)
- Create wheels for all dependencies
- Output: `/build/wheels/`

**Stage 2: Runtime**
- Base: python:3.14-slim
- Non-root user: orchestration (uid 1000)
- Copy wheels from builder (no source)
- Minimal runtime deps only (git, curl, libgomp1)
- Final size: ~400MB (vs 1.2GB without multi-stage)

**Security Hardening**:
- Non-root user (`orchestration:orchestration`)
- Read-only volumes for code (`plugins:ro`)
- Dropped Linux capabilities (implicit with slim base)
- `PYTHONDONTWRITEBYTECODE=1` (no .pyc files)

**Health Check**:
- Tests SQLite DB connectivity
- 30s startup grace period
- Interval: 30s, timeout: 10s, retries: 3

**Volumes**:
- `/kit/.claude/state` — SQLite DB, logs (persistent)
- `/kit/plugins` — Plugin code (read-only)
- `/kit/setup` — Setup templates (read-only)
- `/kit/docs` — Documentation (read-only)

**Exposed Ports**:
- 8787 — Headroom proxy (optional)
- 9080 — Ask-Web relay (optional)
- 37777 — claude-mem worker (optional)

---

## docker-compose.yml

### Services

1. **kit** (main)
   - Builds from local Dockerfile
   - Environment: `ANTHROPIC_API_KEY` required
   - Volumes: state, logs, plugins (ro), setup (ro)
   - Health check enabled
   - Restart: unless-stopped
   - Network: orch-network (172.30.0.0/16)

2. **headroom** (optional, profile: with-headroom)
   - Image: headroom-ai:latest
   - Purpose: Prompt compression proxy (60-95% savings)
   - Port: 8787
   - Depends on: kit (healthy)

3. **mem-worker** (optional, profile: with-memory)
   - Image: node:20-alpine
   - Purpose: claude-mem auto-memory worker
   - Port: 37777
   - Volume: ~/.claude-mem (persistent)

4. **postgres** (optional, profile: with-db)
   - Image: postgres:16-alpine
   - Purpose: Distributed state storage
   - Init script: setup/sql/init-schema.sql
   - Password: `POSTGRES_PASSWORD` env var

5. **redis** (optional, profile: with-cache)
   - Image: redis:7-alpine
   - Purpose: Caching / pub-sub
   - Password: `REDIS_PASSWORD` env var

6. **prometheus** (optional, profile: with-monitoring)
   - Image: prom/prometheus:latest
   - Purpose: Metrics collection
   - Config: setup/prometheus/prometheus.yml

### Usage

```bash
# Basic: kit only
docker-compose up -d kit

# Full stack: kit + headroom + memory + DB + cache + monitoring
ANTHROPIC_API_KEY=sk-... \
POSTGRES_PASSWORD=secret \
REDIS_PASSWORD=secret \
docker-compose --profile with-headroom --profile with-memory --profile with-db --profile with-cache --profile with-monitoring up -d

# Check health
docker-compose ps
docker-compose logs kit -f
```

---

## Local Development

### Quick Start

```bash
# 1. Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov ruff mypy bandit

# 2. Run linter
ruff check .claude/scripts plugins --fix

# 3. Run type checker
mypy .claude/scripts/lib/ --ignore-missing-imports

# 4. Run tests
pytest .claude/scripts/tests -v --cov=.claude/scripts

# 5. Run security scan
bandit -r .claude/scripts plugins
semgrep --config=p/security-audit .claude/scripts plugins

# 6. Build Docker locally
docker build -t orchestration-kit:dev .
docker run -it orchestration-kit:dev bash
```

### Pre-commit Checks

Before pushing, ensure:
```bash
# Linting passes
ruff check .claude/scripts plugins

# Type checking passes
mypy .claude/scripts/lib/ --ignore-missing-imports

# Tests pass
pytest .claude/scripts/tests -v

# Security passes
bandit -r .claude/scripts plugins
python .claude/scripts/audit-hardcoded.py
```

---

## Environment Variables

### Docker Compose

```env
ANTHROPIC_API_KEY=sk-...           # Required for kit
POSTGRES_PASSWORD=secret           # Required for postgres service
REDIS_PASSWORD=secret              # Required for redis service
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')  # Release.yml
VCS_REF=main                       # Release.yml
```

### GitHub Actions Secrets

```bash
ANTHROPIC_API_KEY       # For testing
PYPI_API_TOKEN          # For PyPI publish
SLACK_WEBHOOK           # Optional: Slack notifications
GITHUB_TOKEN            # Built-in (auto)
```

---

## Troubleshooting

### Test Matrix Failure
- Check Python version support in pyproject.toml
- Run locally: `python -m pytest .claude/scripts/tests -v`

### Security Scan False Positives
- Semgrep: Add `# nosemgrep` comment (last resort)
- Bandit: Add `# nosec` comment (Python only)
- Update scan rules in security-scan.yml if needed

### Docker Build Fails
- Check `.dockerignore` exclusions
- Verify `requirements.txt` is complete
- Run `docker build --no-cache .` to debug layer-by-layer

### Dependabot Not Working
- Verify `.github/dependabot.yml` syntax (YAML strict)
- Check repository settings: Dependabot enabled
- Wait 24h for first run after enabling

---

## References

- `.github/workflows/test-matrix.yml` — Test matrix configuration
- `.github/workflows/security-scan.yml` — Security scanning
- `.github/workflows/release.yml` — Release automation
- `.github/dependabot.yml` — Dependency updates
- `Dockerfile` — Multi-stage container build
- `docker-compose.yml` — Local development stack
- `pyproject.toml` — Project metadata + tool configs
- `CLAUDE.md § 3.2` — AI model routing + API limits
