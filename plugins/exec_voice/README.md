# exec_voice — 음성 처리 — STT·TTS·회의록·음성 명령·오디오 편집

> **Prefix**: `exec_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0

## 📖 개요

음성 STT·TTS·회의록·음성 명령.

- **Why**: 회의 녹음 → 회의록 자동. 음성으로 Claude 명령.
- **When**: 회의 직후, 긴 텍스트 듣기, 이동 중 명령.

## 📋 커맨드

- `/convert`
- `/exec_voice`
- `/meeting`
- `/speak`
- `/status`
- `/transcribe` ⭐ 기본
- `/voice-task`

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

### 예시 1: 음성→텍스트
```
/transcribe meeting.m4a
```

### 예시 2: 텍스트→음성
```
/speak "배포 완료"
```

### 예시 3: 회의록 자동
```
/meeting record.wav --summary
```

## 📝 변경 이력

- 1.0 (2026-04-19) — 현재 버전
