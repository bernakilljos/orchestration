# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-10-13

### Added
- **pyproject.toml** — Python project configuration with ruff, mypy, pytest setup
- **requirements.txt** — Pinned dependencies for reproducible builds
- **Dockerfile** — Python 3.14 container with volume mounts for `.claude/` and `plugins/`
- **pytest.ini** — Test configuration with 80% coverage threshold
- **.gitignore** — Enhanced patterns for Python, logs, state files, backups
- **CHANGELOG.md** — Versioning and release notes (this file)
- **Git tag v1.0.0** — Major release marker

### Changed
- Performance optimization: UserPromptSubmit hook consolidated from 13 to 1 Python process
- MCP integration cleanup: Headroom + claude-mem fully removed; codex-auto conditional

### Fixed
- Hook frontmatter validation across 50+ plugins
- Deploy history auto-append mechanism (4 audit findings resolved)
- Auto-stats recalculation (2026-10-12 session)

### Deprecated
- Headroom proxy integration (user directive: local-only stack)
- claude-mem auto-observation (replaced by conversation-history DB)

## [0.9.5] — 2026-10-05

### Added
- Codex auto-delegation matrix (500 LOC+ → Codex ×4 parallel)
- Subagent fork mode (depth 3 nesting default)
- Subagent explore agent parallelization (5+ file reads)

### Fixed
- Git rebase edge case in multi-session worktree isolation
- Sidebar hook polish (deploy-history integration)

## [0.9.0] — 2026-09-02

### Added
- **Conversation history DB** (`orca.db.conversations` + `session_summary`)
- **Artifact freshness check** — auto-detection of stale docx/pptx/md catalogs
- **Semantic caching** — Chroma vector DB for prompt reuse (0 API cost)
- **Production file management** — audit trail, retention policies, rollback support
- **Multi-session isolation** — worktree support + ASCII path enforcement
- **Solution reuse catalog** — problem → approach → solution auto-capture

### Changed
- Routing policy: Qwen 3.8-27B added as local-first RAG candidate
- MCP health check automated (SessionStart + periodic watchdog)

### Deprecated
- Standalone Headroom proxy (in favor of built-in prompt cache)

## [0.8.0] — 2026-08-12

### Added
- User emotion auto-response mapping (15+ triggers)
- Auto-planner 5-stage mandatory workflow
- Sub-agent automatic delegation (v2.1.232 fork + nesting depth 3)
- Teaching doc 8-section standard + page fit verification

### Fixed
- Codex hallucination detection (empty git commits flagged)
- File locking race condition (Writer=1 enforcement)
- Duplicate function detection (function/hook/rule grep)

## [0.7.0] — 2026-07-01

### Added
- Hook scope separation (project vs. global guards)
- Language standards matrix (20+ languages, linter/formatter per type)
- Terminal tools integration (fzf, ripgrep-all, bat, eza, delta, lazygit, btop)
- Skill design 12-section template (Anthropic compliance)

### Changed
- API routing updated for Opus 5.5 default (40% cost reduction)
- Fable 5 / Mythos 5 tier pricing (cache reads 75% discount)
- Claude Sonnet 5 tokenizer impact (30% token inflation · cost re-estimated)

## [0.6.0] — 2026-06-15

### Added
- Approval gate (HITL) for 5 critical categories (data loss, security, cost, system, irreversible)
- Compliance API integration (Enterprise beta)
- On-demand conversation compaction (Messages API)

### Deprecated
- Legacy Workbench (sunset 2026-08-17)

## [0.5.0] — 2026-05-28

### Added
- Opus 4.8 Fast mode (2.5× speed, $10/$50)
- Extended Thinking depth control (xhigh/max effort)
- Supervised fine-tuning support (Files API batch)

### Fixed
- Prompt cache TTL handling (1-hour ephemeral blocks)
- MCP tool 100k+ auto-spill (sandbox file storage)

## [0.4.0] — 2026-05-11

### Added
- **Teaching doc standards** — 8 mandatory sections (context, flow, strengths, weaknesses, recommend, mapping, check)
- **Page fit verification** — automatic PIL ratio validation (docx/pptx/pdf)
- **First-run guide** — SessionStart auto-trigger for fresh installations

### Changed
- 36 stable plugins (up from 26)
- 46 rules (comprehensive failure-mode coverage)

## [0.3.0] — 2026-04-19

### Added
- **Multi-AI orchestration core** — Claude (design), Codex (implementation), Gemini (verification)
- **26 plugins** (16 stable + 10 spec-only)
- **Rule catalog** — 42 rules covering plugin structure, sync workflow, approval gates
- **Installation framework** — Template kit pattern with setup modules

### Changed
- Source of Truth (SoT): `plugins/` ← `→ .claude/` sync workflow
- Hook consolidation: 30 hooks under `.claude/settings.json` management

## [0.2.0] — 2026-03-15

### Added
- Anthropic Batch API integration (50% discount nightly processing)
- Prompt caching strategy (90% reduction on repeated context)
- SQLite state DB (workers, tasks, metrics, quota, budget)

## [0.1.0] — 2026-02-01

### Added
- Initial scaffold
- Git-based versioning
- Basic plugin structure template

---

**Links:**
- [GitHub Releases](https://github.com/anthropics/orchestration-kit-v1/releases)
- [Documentation](https://github.com/anthropics/orchestration-kit-v1/blob/main/guide.txt)
- [Architecture Patterns](https://github.com/anthropics/orchestration-kit-v1/blob/main/docs/architecture-patterns.md)
