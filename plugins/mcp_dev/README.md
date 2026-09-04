# mcp_dev — 개발 MCP 설치 — GitHub·GitLab·Docker·K8s·AWS·Firebase·Supabase·Vercel·Netlify

> **Prefix**: `mcp_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 10 | **Token estimate**: ~1600

## 📖 개요

개발용 MCP 허브 — GitHub·Docker·AWS·Firebase·Vercel.

## 📋 커맨드

- `/install`  기본
- `/mcp_dev`
- `/status`

## 🧠 스킬

- `skill-30-docker`  핵심
- `skill-33-github-actions`  핵심

## 🤖 에이전트

- `agent-02-implementer`
- `agent-04-architect`

## 🪝 훅

- `hook-01-pre-task` (spec)

## 🔗 의존성

- **플러그인**: `exec_orch`

## 💡 사용 예시

### 예시 1: 일괄 설치
```bash
/plug_dev
```

### 예시 2: 설치 상태
```bash
/mcp_dev-status
```

### 예시 3: 개별 설치
```bash
/mcp_dev-install
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
