#!/usr/bin/env python3
"""music_studio 플러그인 생성 (녹음-작곡-믹싱-편곡)"""
import json, sys
from pathlib import Path

try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

PLUGIN = {
    "name": "music_studio",
    "display": "음악 스튜디오 — 녹음-작곡-믹싱-편곡-가사-MIDI-커버",
    "prefix": "music_",
    "phase": 2,
    "deps": ["exec_orch", "mcp_media", "exec_voice"],
    "default_command": "music_studio-compose",
    "category": "음악/Studio",
    "triggers": ["작곡", "녹음", "믹싱", "편곡", "MIDI", "커버곡", "가사", "Suno", "Udio", "Logic", "Ableton"],
    "commands": {
        "music_studio-record":     "실시간 녹음-멀티트랙 (마이크-라인 입력-24bit/48kHz)",
        "music_studio-compose":    "AI 작곡 (Suno-Udio-MusicGen) — 장르-BPM-키-길이 지정",
        "music_studio-arrange":    "편곡-코드 진행-섹션 구조 (verse-chorus-bridge)",
        "music_studio-lyrics":     "가사 작성 (주제-톤-운율-후크 라인)",
        "music_studio-mix":        "믹싱 — EQ-컴프-리버브-패닝 자동 적용",
        "music_studio-master":     "마스터링 — LUFS 정규화-라우드니스-스트리밍 대응",
        "music_studio-cover":      "커버곡 변형 — 보컬 변환-장르 스와프-reharm",
        "music_studio-midi":       "MIDI 파일 조작 — 코드 추출-퀀타이즈-벨로시티 편집",
        "music_studio-stem":       "스템 분리 — 보컬/드럼/베이스/기타 (Spleeter-Demucs)",
        "music_studio-export":     "최종 출력 — WAV-MP3-FLAC-stem 패키지",
    },
    "skills": {
        "skill-music-production":  "작곡-편곡 원칙 (코드 진행-장르 컨벤션-arrangement 원칙)",
        "skill-music-mixing":      "믹싱-마스터링 가이드 (EQ-컴프-리버브-스트리밍 LUFS)",
        "skill-music-copyright":   "저작권-샘플링-AI 생성물 법적 이슈 (공정 이용-라이선스)",
    },
}

COMMON = '''#!/bin/bash
# common.sh - music_studio 공통 헬퍼
set -uo pipefail
PLUGIN_NAME="music_studio"
REPO_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
LOG_DIR="$REPO_ROOT/.claude/state/$PLUGIN_NAME"
DATA_DIR="$REPO_ROOT/data/$PLUGIN_NAME/$(date +%Y-%m-%d)"
mkdir -p "$LOG_DIR" "$DATA_DIR"

log_info()  { echo "[INFO] $1" >&2; printf '{"ts":"%s","level":"INFO","msg":"%s"}\\n' "$(date -u +%FT%TZ)" "$1" >> "$LOG_DIR/log.jsonl"; }
log_error() { echo "[ERROR] $1" >&2; printf '{"ts":"%s","level":"ERROR","msg":"%s"}\\n' "$(date -u +%FT%TZ)" "$1" >> "$LOG_DIR/log.jsonl"; }
is_dry_run() { [ "${DRY_RUN:-false}" = "true" ] && return 0; for a in "$@"; do [ "$a" = "--dry-run" ] && return 0; done; return 1; }
load_env() { [ -f "$REPO_ROOT/.env" ] && { set -a; source "$REPO_ROOT/.env"; set +a; }; }

# 음악 전용 유틸
check_ffmpeg() {
  command -v ffmpeg >/dev/null 2>&1 || { log_error "ffmpeg 필요 — /mcp_media-install 먼저"; return 1; }
}
check_lufs() {
  # 스트리밍 LUFS 기준 (Spotify/Apple Music: -14 LUFS)
  echo "-14 LUFS (스트리밍 표준)"
}
'''

CMD_TEMPLATE = '''---
description: "DESC"
allowed-tools: Bash(bash:*), Bash(ffmpeg:*), Write, Read
---

## Context
- 플러그인: `music_studio` (spec-only)
- 출력: `data/music_studio/$(date +%Y-%m-%d)/`
- 의존: FFmpeg, (선택) Suno-Udio-MusicGen API

## Your task

```bash
source plugins/music_studio/scripts/common.sh
load_env
check_ffmpeg || exit 1
is_dry_run "$@" && log_info "dry-run"
```

**목적**: DESC

**권장 파라미터**:
- 샘플레이트: 48kHz (표준)
- 비트뎁스: 24bit (작업용) / 16bit (배포)
- 포맷: WAV (무손실) / MP3 320kbps (배포) / FLAC (아카이브)

**실구현은 플랫폼에서**. 상세: `../SPEC.md`
'''

p = Path("plugins/music_studio")

# plugin.json
pj = {
    "$schema": "../../.claude-plugin/plugin-schema.json",
    "name": PLUGIN["name"],
    "display": PLUGIN["display"],
    "prefix": PLUGIN["prefix"],
    "version": "0.1",
    "status": "spec-only",
    "phase": PLUGIN["phase"],
    "commands": "commands/",
    "skills": "skills/",
    "dependencies": {"plugins": PLUGIN["deps"], "mcp": [], "env": []},
    "entry_points": {
        "default_command": PLUGIN["default_command"],
        "core_skills": list(PLUGIN["skills"].keys()),
    },
    "metadata": {
        "category": PLUGIN["category"],
        "tags": ["music"],
        "author": "bernakilljos",
        "created": "2026-04-19",
        "updated": "2026-04-19",
        "precedence": 10,
        "token_estimate": len(PLUGIN["commands"]) * 200 + len(PLUGIN["skills"]) * 500,
        "triggers": PLUGIN["triggers"],
    },
}
(p / "plugin.json").write_text(json.dumps(pj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# common.sh
(p / "scripts" / "common.sh").write_text(COMMON, encoding="utf-8")

# 커맨드들
for cmd, desc in PLUGIN["commands"].items():
    (p / "commands" / f"{cmd}.md").write_text(
        CMD_TEMPLATE.replace("DESC", desc), encoding="utf-8"
    )

# 스킬들
for skill, sdesc in PLUGIN["skills"].items():
    (p / "skills" / f"{skill}.md").write_text(
        f"# {skill}\n\n> Status: spec-only\n\n## Purpose\n\n{sdesc}\n\n상세: `../SPEC.md`\n",
        encoding="utf-8"
    )

# README
readme = [
    f"# music_studio — {PLUGIN['display']}",
    "",
    f"> **Prefix**: `music_` | **버전**: 0.1 | **Status**: spec-only | **Phase**: 2",
    "",
    "## [WARN] 현재 상태",
    "",
    "**spec-only** — 스펙 + 공통 헬퍼. 실구현은 플랫폼에서.",
    "",
    "## [LIST] 커맨드 (10개)",
    "",
]
for cmd, desc in PLUGIN["commands"].items():
    mark = "  기본" if cmd == PLUGIN["default_command"] else ""
    readme.append(f"- `/{cmd}`{mark} — {desc}")
readme += ["", "##  스킬", ""]
for s, sd in PLUGIN["skills"].items():
    readme.append(f"- `{s}` — {sd}")
readme += [
    "",
    "##  의존성",
    "",
    f"- **플러그인**: {', '.join(f'`{d}`' for d in PLUGIN['deps'])}",
    "- **MCP 권장**: FFmpeg-Whisper (mcp_media)",
    "- **선택 API**: Suno-Udio-MusicGen (env: SUNO_API_KEY 등)",
    "",
    "## [NOTE] 참조",
    "",
    "- 스펙: `SPEC.md`",
    "- 아키텍처: `docs/architecture-patterns.md`",
]
(p / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

# SPEC
spec = [
    f"# music_studio — 상세 스펙 (Phase {PLUGIN['phase']})",
    "",
    "## 목표",
    "",
    f"- {PLUGIN['display']}",
    "",
    "## 커맨드 스펙",
    "",
]
for cmd, desc in PLUGIN["commands"].items():
    spec += [f"### `/{cmd}`", "", desc, "", "- `--dry-run` 지원", "- 48kHz/24bit 기본", ""]

spec += ["## 스킬 스펙", ""]
for s, sd in PLUGIN["skills"].items():
    spec += [f"### `{s}`", "", sd, ""]

spec += [
    "## 기술 스택 (플랫폼 구현 시)",
    "",
    "| 영역 | 도구 |",
    "|---|---|",
    "| 오디오 처리 | FFmpeg - sox - librosa |",
    "| AI 작곡 | Suno API - Udio - MusicGen - Stable Audio |",
    "| 스템 분리 | Demucs - Spleeter |",
    "| MIDI | mido - pretty_midi - music21 |",
    "| 믹싱 | pedalboard (Spotify) - pyo |",
    "| 마스터링 | LUFS 측정 (pyloudnorm) |",
    "",
    "## 구현 체크리스트 (플랫폼)",
    "",
    "- [ ] 멱등성 (같은 시드-입력 = 같은 출력)",
    "- [ ] `--dry-run` 실동작",
    "- [ ] 저작권 경고 자동 출력 (AI 생성물)",
    "- [ ] LUFS 자동 정규화 (-14 LUFS 기본)",
    "- [ ] WAV/MP3/FLAC 다중 출력",
    "- [ ] 시크릿 `.env` (Suno-Udio API)",
    "- [ ] JSON 로그",
    "",
    "## 트러블슈팅",
    "",
    "| 증상 | 원인 | 해결 |",
    "|---|---|---|",
    "| ffmpeg 없음 | 미설치 | `/mcp_media-install` |",
    "| Suno API 실패 | 쿼터-인증 | `.env` SUNO_API_KEY 확인 |",
    "| LUFS 과다 | 마스터 과압 | `-14 LUFS` 목표 재조정 |",
    "| 스템 분리 실패 | Demucs 모델 미다운 | 초회 실행 시 자동 다운로드 대기 |",
    "",
    "## 참조",
    "",
    "- `.claude/rules/skill-design.md`",
    "- `plugins/exec_voice/` (STT-TTS 연계)",
    "- `plugins/mcp_media/` (FFmpeg 설치)",
]
(p / "SPEC.md").write_text("\n".join(spec) + "\n", encoding="utf-8")

print(f"✓ music_studio 생성: {len(PLUGIN['commands'])} 커맨드 + {len(PLUGIN['skills'])} 스킬")
