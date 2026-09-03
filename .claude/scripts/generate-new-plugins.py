#!/usr/bin/env python3
"""4개 신규 플러그인 (design_web-design_pdf-design_video-mcp_queue) 기본 공통 골자 생성"""
import json, sys
from pathlib import Path

try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

PLUGINS = {
    "design_web": {
        "display": "웹사이트-랜딩-블로그 템플릿 자동 생성 (HTML-Tailwind-SEO)",
        "prefix": "design_",
        "phase": 1,
        "deps": ["exec_orch"],
        "default_command": "landing",
        "category": "디자인/Web",
        "commands": {
            "landing":      "랜딩페이지 자동 생성 (헤드라인-CTA-증명)",
            "blog-template":"블로그 템플릿 (Tistory-Ghost-Jekyll)",
            "portfolio":    "포트폴리오 사이트 생성",
            "seo-meta":     "메타태그-OG-JSON-LD 자동 삽입",
        },
        "skills": {
            "skill-web-seo": "웹 SEO 최적화 (메타-구조화 데이터-Core Web Vitals)",
            "skill-web-conversion": "전환율 높이는 랜딩 패턴",
        },
    },
    "design_pdf": {
        "display": "PDF 생성-양식-서명-암호화 (mcp_docs 는 파싱만)",
        "prefix": "design_",
        "phase": 2,
        "deps": ["exec_orch"],
        "default_command": "pdf-generate",
        "category": "디자인/PDF",
        "commands": {
            "pdf-generate": "HTML-Markdown -> PDF 변환",
            "pdf-fill":     "양식(form) 자동 채우기",
            "pdf-sign":     "전자서명-직인 삽입",
            "pdf-secure":   "암호화-워터마크",
        },
        "skills": {
            "skill-pdf-form": "PDF 양식 필드 매핑-검증",
            "skill-pdf-compliance": "전자서명 법적 요건 (전자서명법)",
        },
    },
    "design_video": {
        "display": "영상 편집 — 자막-쇼츠-썸네일 (유튜브 수익화 직결)",
        "prefix": "design_",
        "phase": 2,
        "deps": ["exec_orch", "mcp_media"],
        "default_command": "video-edit",
        "category": "디자인/Video",
        "commands": {
            "video-edit":      "영상 편집 (자르기-합치기-자막)",
            "video-subtitle":  "자막 자동 생성 (Whisper + 번역)",
            "video-template":  "유튜브 인트로-아웃트로 템플릿",
            "video-shorts":    "롱폼 -> 쇼츠 자동 추출",
            "video-thumbnail": "썸네일 A/B 3안 자동 생성",
        },
        "skills": {
            "skill-video-remotion": "Remotion 프로그래매틱 영상 (design_ppt 에서 이관)",
            "skill-video-retention": "시청지속률 높이는 편집 패턴",
        },
    },
    "mcp_queue": {
        "display": "메시지 브로커 MCP — Kafka-RabbitMQ-Redis Pub/Sub-AWS SQS",
        "prefix": "mcp_",
        "phase": 2,
        "deps": ["exec_orch"],
        "default_command": "install",
        "category": "MCP/Queue",
        "commands": {
            "install":  "큐 시스템 MCP 설치 (Kafka-RabbitMQ-Redis-SQS)",
            "topic":    "토픽-큐 관리 (생성-삭제-파티션)",
            "consumer": "컨슈머 그룹 lag-오프셋 모니터링",
            "dlq":      "DLQ 재처리",
        },
        "skills": {
            "skill-queue-patterns": "큐 패턴 (fan-out-pub-sub-work-queue-DLQ)",
        },
    },
}

COMMON_HELPER_TEMPLATE = '''#!/bin/bash
# common.sh - PLUGIN_NAME 공통 헬퍼 (dry-run-검증-로깅)

set -uo pipefail

PLUGIN_NAME="PLUGIN_NAME"
REPO_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
LOG_DIR="$REPO_ROOT/.claude/state/$PLUGIN_NAME"
DATA_DIR="$REPO_ROOT/data/$PLUGIN_NAME/$(date +%Y-%m-%d)"
mkdir -p "$LOG_DIR" "$DATA_DIR"

log_info() {
  local msg="$1"
  local ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  printf '{"ts":"%s","level":"INFO","plugin":"%s","msg":"%s"}\\n' "$ts" "$PLUGIN_NAME" "$msg" >> "$LOG_DIR/log.jsonl"
  echo "[INFO] $msg"
}

log_error() {
  local msg="$1"
  local ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  printf '{"ts":"%s","level":"ERROR","plugin":"%s","msg":"%s"}\\n' "$ts" "$PLUGIN_NAME" "$msg" >> "$LOG_DIR/log.jsonl"
  echo "[ERROR] $msg" >&2
}

is_dry_run() {
  [ "${DRY_RUN:-false}" = "true" ] && return 0
  for arg in "$@"; do
    [ "$arg" = "--dry-run" ] && return 0
  done
  return 1
}

load_env() {
  if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    source "$REPO_ROOT/.env"
    set +a
  fi
}

require_env() {
  local var_name="$1"
  eval "local val=\\"\\${$var_name:-}\\""
  if [ -z "$val" ]; then
    log_error "Required env var not set: $var_name"
    return 1
  fi
}
'''

CMD_TEMPLATE = '''---
description: "DESC"
allowed-tools: Bash(bash:*), Write, Read
---

## Context

- 플러그인: `PLUGIN` (status=spec-only)
- 출력: `data/PLUGIN/$(date +%Y-%m-%d)/`
- DRY_RUN 환경변수: `${DRY_RUN:-false}`

## Your task

### 기본 공통 (모든 커맨드 공유)

```bash
source plugins/PLUGIN/scripts/common.sh
load_env

if is_dry_run "$@"; then
  log_info "dry-run 모드"
fi
```

### 커맨드별 로직

**목적**: DESC

**단계**:
1. 입력 검증 (필수 인자-환경변수)
2. 드라이런 분기 (미리보기)
3. 실제 작업 (플랫폼 구현)
4. 결과 JSON 로깅

**실구현은 플랫폼에서** — 상세: `../SPEC.md`
'''

plugins_dir = Path("plugins")

for name, info in PLUGINS.items():
    p = plugins_dir / name

    # plugin.json
    pj = {
        "$schema": "../../.claude-plugin/plugin-schema.json",
        "name": name,
        "display": info["display"],
        "prefix": info["prefix"],
        "version": "0.1",
        "status": "spec-only",
        "phase": info["phase"],
        "commands": "commands/",
        "skills": "skills/",
        "dependencies": {
            "plugins": info["deps"],
            "mcp": [],
            "env": [],
        },
        "entry_points": {
            "default_command": info["default_command"],
            "core_skills": list(info.get("skills", {}).keys()),
        },
        "metadata": {
            "category": info["category"],
            "tags": [info["prefix"].rstrip("_")],
            "author": "bernakilljos",
            "created": "2026-04-19",
            "updated": "2026-04-19",
            "precedence": 10,
            "token_estimate": len(info["commands"]) * 200 + len(info.get("skills", {})) * 500,
        },
    }
    if (p / "hooks").exists():
        pj["hooks"] = "hooks/"
    (p / "plugin.json").write_text(json.dumps(pj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # common.sh
    (p / "scripts" / "common.sh").write_text(
        COMMON_HELPER_TEMPLATE.replace("PLUGIN_NAME", name), encoding="utf-8"
    )

    # 커맨드들
    for cmd, desc in info["commands"].items():
        content = CMD_TEMPLATE.replace("PLUGIN", name).replace("DESC", desc)
        (p / "commands" / f"{cmd}.md").write_text(content, encoding="utf-8")

    # 스킬들
    for skill, sdesc in info.get("skills", {}).items():
        skill_content = f"""# {skill}

> **분류**: `{info['prefix']}` | **Status**: spec-only

## Purpose

{sdesc}

## When to invoke

- 관련 커맨드 호출 시 자동 활성화
- 사용자가 관련 주제 언급 시

## Procedure (개요)

1. 컨텍스트 수집 (`common.sh` 헬퍼)
2. 도메인 로직 (플랫폼 구현)
3. 결과 검증 + 로깅

상세: `../SPEC.md`
"""
        (p / "skills" / f"{skill}.md").write_text(skill_content, encoding="utf-8")

    # README.md
    deps_str = ", ".join(f"`{d}`" for d in info["deps"]) if info["deps"] else "없음"
    readme = [
        f"# {name} — {info['display']}",
        "",
        f"> **Prefix**: `{info['prefix']}` | **버전**: 0.1 | **Status**: spec-only | **Phase**: {info['phase']}",
        "",
        "## [WARN] 현재 상태",
        "",
        "**spec-only** — 스펙 + 기본 공통 헬퍼(`scripts/common.sh`) 만 있음. 도메인 로직은 플랫폼에서 구현.",
        "",
        "## [LIST] 커맨드",
        "",
    ]
    for cmd, desc in info["commands"].items():
        mark = "  기본" if cmd == info["default_command"] else ""
        readme.append(f"- `/{cmd}`{mark} — {desc}")
    readme += ["", "##  스킬", ""]
    for s, sd in info.get("skills", {}).items():
        readme.append(f"- `{s}` — {sd}")
    readme += [
        "",
        "##  의존성",
        "",
        f"- **플러그인**: {deps_str}",
        "- **공통 헬퍼**: `scripts/common.sh` (dry-run-로깅-env)",
        "",
        "## [NOTE] 참조",
        "",
        "- 스펙: `SPEC.md`",
        "- 로드맵: `docs/2026-04-19/로드맵.md`",
    ]
    (p / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    # SPEC.md
    spec = [
        f"# {name} — 상세 스펙 (Phase {info['phase']})",
        "",
        "## 목표",
        "",
        f"- {info['display']}",
        "",
        "## 커맨드 스펙",
        "",
    ]
    for cmd, desc in info["commands"].items():
        spec += [
            f"### `/{cmd}`",
            "",
            desc,
            "",
            "**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장",
            "",
        ]
    if info.get("skills"):
        spec += ["## 스킬 스펙", ""]
        for s, sd in info["skills"].items():
            spec += [f"### `{s}`", "", sd, ""]
    spec += [
        "## 구현 체크리스트 (플랫폼)",
        "",
        "- [ ] 멱등성",
        "- [ ] `--dry-run` 실동작",
        "- [ ] 입력 검증",
        "- [ ] 에러 복구",
        "- [ ] Rate limit (지수백오프)",
        "- [ ] 시크릿 `.env` 로드",
        "- [ ] JSON 구조화 로그",
        "",
        "## 의존성",
        "",
        f"- upstream: {', '.join(info['deps']) if info['deps'] else '없음'}",
        "- 공통 헬퍼: `scripts/common.sh`",
        "",
        "## 참조",
        "",
        "- `docs/architecture-patterns.md`",
        "- `.claude/rules/file-naming.md`",
    ]
    (p / "SPEC.md").write_text("\n".join(spec) + "\n", encoding="utf-8")

    print(f"OK: {name}")

print(f"\nTotal: {len(PLUGINS)} plugins")
