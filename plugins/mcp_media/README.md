# mcp_media — 미디어 설치 — Whisper(STT)·TTS·FFmpeg

> **Prefix**: `mcp_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0

## 📖 개요

미디어·AI 처리 MCP — Whisper(STT)·TTS·FFmpeg.

- **Why**: 음성·영상 처리 파이프라인 통합.
- **When**: 영상 편집, 자막 생성, 오디오 정제.

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

- `hook-02-post-impl`
- `hook-06-notify`

## 🔗 의존성

- **플러그인**: `exec_orch`
- **MCP**: 해당 없음
- **환경변수**: 해당 없음

## 💡 사용 예시

### 예시 1: 일괄 설치
```
/plug_media
```

### 예시 2: FFmpeg만
```
/install ffmpeg
```

## 📝 변경 이력

- 1.0 (2026-04-19) — 현재 버전
