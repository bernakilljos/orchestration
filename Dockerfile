FROM python:3.14-slim

# Metadata
LABEL maintainer="Claude <noreply@anthropic.com>"
LABEL description="Multi-AI Orchestration Kit v1 container"
LABEL version="1.0.0"

# Set working directory
WORKDIR /kit

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy project files (excluding .gitignore'd items)
COPY pyproject.toml requirements.txt ./
COPY plugins/ ./plugins/
COPY .claude/ ./.claude/
COPY setup/ ./setup/
COPY docs/ ./docs/
COPY CLAUDE.md README.md CHANGELOG.md guide.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Create non-root user (optional, for security)
RUN useradd -m -u 1000 orchestration && chown -R orchestration:orchestration /kit
USER orchestration

# Health check (basic)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Environment defaults
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV CLAUDE_PROJECT_DIR=/kit
ENV PATH="/kit/.claude/scripts:${PATH}"

# Volume mounts (user can bind at runtime)
VOLUME ["/kit/.claude", "/kit/plugins", "/kit/setup"]

# Default entrypoint (user can override)
ENTRYPOINT ["/bin/bash"]
CMD ["bash", ".claude/scripts/init-state-db.py"]

# Optional: For orchestration server mode
# EXPOSE 8787 9080 37777
# CMD ["python", "-m", "uvicorn", "plugins.exec_orch.api:app", "--host", "0.0.0.0", "--port", "8787"]
