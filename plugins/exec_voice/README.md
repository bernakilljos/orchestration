# exec_voice — 음성 처리 — STT·TTS·회의록·음성 명령·오디오 편집

> **Prefix**: `exec_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 10 | **Token estimate**: ~2400

## 📖 개요

음성 STT·TTS·회의록·음성 명령.

## 📋 커맨드

- `/convert`
- `/exec_voice`
- `/meeting`
- `/speak`
- `/transcribe` ⭐ 기본
- `/voice-status`
- `/voice-task`

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

### 예시 1: 음성 → 텍스트
```bash
/transcribe meeting.m4a
```

### 예시 2: 텍스트 → 음성
```bash
/speak "배포 완료"
```

### 예시 3: 회의록 자동
```bash
/meeting record.wav
```

### 예시 4: 음성 명령
```bash
/voice-task  # 말로 태스크 생성
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
