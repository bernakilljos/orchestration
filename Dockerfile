# Multi-stage Dockerfile for orchestration-kit-v1
# Optimized for production deployment with security hardening

# ============ Stage 1: Builder ============
FROM python:3.14-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Build wheels for all dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# ============ Stage 2: Runtime ============
FROM python:3.14-slim

LABEL maintainer="Claude <noreply@anthropic.com>"
LABEL org.opencontainers.image.title="Orchestration Kit v1"
LABEL org.opencontainers.image.description="Multi-AI Orchestration Kit — Claude + Codex + Gemini"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.url="https://github.com/anthropics/orchestration-kit-v1"

WORKDIR /kit

# Install runtime dependencies only (minimal attack surface)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (security best practice)
RUN groupadd -r orchestration && \
    useradd -r -u 1000 -g orchestration orchestration && \
    mkdir -p /kit/.claude /kit/plugins /kit/setup && \
    chown -R orchestration:orchestration /kit

# Copy wheels from builder
COPY --from=builder --chown=orchestration:orchestration /build/wheels /tmp/wheels

# Install wheels
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --no-index --find-links=/tmp/wheels -r requirements.txt && \
    rm -rf /tmp/wheels

# Copy application code
COPY --chown=orchestration:orchestration pyproject.toml requirements.txt ./
COPY --chown=orchestration:orchestration .claude/ ./.claude/
COPY --chown=orchestration:orchestration plugins/ ./plugins/
COPY --chown=orchestration:orchestration setup/ ./setup/
COPY --chown=orchestration:orchestration docs/ ./docs/
COPY --chown=orchestration:orchestration CLAUDE.md README.md CHANGELOG.md guide.txt ./

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_INPUT=1 \
    CLAUDE_PROJECT_DIR=/kit \
    PATH="/kit/.claude/scripts:${PATH}" \
    ANTHROPIC_API_KEY=""

# Health check (startup grace period: 30s)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys, sqlite3; \
                   db=sqlite3.connect('/kit/.claude/state/orca.db'); \
                   cursor=db.cursor(); \
                   cursor.execute('SELECT 1 FROM sqlite_master LIMIT 1'); \
                   sys.exit(0 if cursor.fetchone() else 1)" || exit 1

# Switch to non-root user
USER orchestration

# Volume mounts for persistence
VOLUME ["/kit/.claude/state", "/kit/plugins", "/kit/setup", "/kit/docs"]

# Expose ports (optional — used only in server mode)
# 8787: Headroom proxy
# 9080: Ask-Web relay
# 37777: claude-mem worker
EXPOSE 8787 9080 37777

# Default entrypoint: bash shell (developer friendly)
ENTRYPOINT ["/bin/bash"]

# Default command: initialize state DB and show help
CMD ["-c", "python .claude/scripts/init-state-db.py 2>/dev/null || true; \
            echo ''; \
            echo '╔══════════════════════════════════════════════════════════╗'; \
            echo '║  Orchestration Kit v1 — Multi-AI Container Ready        ║'; \
            echo '║  Run: bash .claude/scripts/sync-plugins.sh --dry        ║'; \
            echo '║  Or:  python -m pytest .claude/scripts/tests/          ║'; \
            echo '║  Or:  /bin/bash (interactive shell)                    ║'; \
            echo '╚══════════════════════════════════════════════════════════╝'; \
            echo ''; \
            /bin/bash"]

# Build metadata labels (populated by docker build --label-file)
ARG BUILD_DATE
ARG VCS_REF
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}"
