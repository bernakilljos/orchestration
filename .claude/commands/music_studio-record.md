---
description: "실시간 녹음·멀티트랙 (마이크·라인 입력·24bit/48kHz)"
allowed-tools: Bash(bash:*), Bash(ffmpeg:*), Write, Read
---

## Context
- 플러그인: `music_studio` (spec-only)
- 출력: `data/music_studio/$(date +%Y-%m-%d)/`
- 의존: FFmpeg, (선택) Suno·Udio·MusicGen API

## Your task

```bash
source plugins/music_studio/scripts/common.sh
load_env
check_ffmpeg || exit 1
is_dry_run "$@" && log_info "dry-run"
```

**목적**: 실시간 녹음·멀티트랙 (마이크·라인 입력·24bit/48kHz)

**권장 파라미터**:
- 샘플레이트: 48kHz (표준)
- 비트뎁스: 24bit (작업용) / 16bit (배포)
- 포맷: WAV (무손실) / MP3 320kbps (배포) / FLAC (아카이브)

**실구현은 플랫폼에서**. 상세: `../SPEC.md`
