# mcp_media — 미디어 설치 — Whisper(STT)·TTS·FFmpeg

> **Prefix**: `mcp_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 10 | **Token estimate**: ~1600

## 📖 개요

미디어 MCP — Whisper·TTS·FFmpeg.

## 📋 커맨드

- `/install` ⭐ 기본
- `/mcp_media`
- `/status`

## 🧠 스킬

- `skill-22-remotion` ⭐ 핵심
- `skill-25-media-enhance` ⭐ 핵심

## 🤖 에이전트

- `agent-02-implementer`
- `agent-05-monitor`

## 🪝 훅

- `hook-02-post-impl` (spec)
- `hook-06-notify` (spec)

## 🔗 의존성

- **플러그인**: `exec_orch`

## 💡 사용 예시

### 예시 1: 일괄 설치
```bash
/plug_media
```

### 예시 2: 상태 확인
```bash
/mcp_media-status
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
