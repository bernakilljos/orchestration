#!/usr/bin/env python3
"""exec_offline + bundles_cowork 플러그인 스펙 + 공통 헬퍼 생성
출처:
  - exec_offline: docs/upgrade/KakaoTalk_20260419_133731661_02.jpg ($0 AI Stack — Brij)
  - bundles_cowork: https://www.instagram.com/p/DW9GwvhFCu5/ (@aifornontechies Cowork Essentials)
"""
import json, sys
from pathlib import Path

try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

PLUGINS = {
    "exec_offline": {
        "display": "로컬/오프라인 AI 스택 — Ollama·ChromaDB·Phoenix ($0 운영)",
        "prefix": "exec_",
        "phase": 2,
        "deps": ["exec_orch"],
        "default_command": "exec_offline-setup",
        "category": "실행/로컬",
        "source": "docs/upgrade § 이미지 3 ($0 AI Stack 2026, Brij Kishore Pandey)",
        "commands": {
            "exec_offline-setup":    "로컬 스택 설치 (Ollama + ChromaDB + Phoenix)",
            "exec_offline-model":    "로컬 모델 다운로드·실행 (Llama·Gemma·Mistral)",
            "exec_offline-vector":   "ChromaDB 로컬 벡터DB 관리",
            "exec_offline-observe":  "Phoenix self-hosted 관측 대시보드",
            "exec_offline-route":    "API vs 로컬 라우팅 결정 (비용·품질)",
        },
        "skills": {
            "skill-local-llm":       "Ollama 모델 선택 가이드 (VRAM·품질 매트릭스)",
            "skill-cost-zero":       "완전 오프라인 파이프라인 설계 (no external API)",
        },
    },
    "bundles_cowork": {
        "display": "업무 자동화 번들 — 이메일·영수증·슬라이드·제안서·계약·브리핑",
        "prefix": "bundles_",
        "phase": 2,
        "deps": ["exec_orch", "design_ppt", "design_word", "design_pdf", "mcp_collab", "exec_scheduler"],
        "default_command": "bundles_cowork-briefing",
        "category": "번들/Cowork",
        "source": "https://www.instagram.com/p/DW9GwvhFCu5/ (@aifornontechies 'Claude Cowork Essentials')",
        "commands": {
            "bundles_cowork-email":      "이메일 자동 분류·초안·답장 (mcp_collab·Gmail 연계)",
            "bundles_cowork-receipt":    "영수증 스캔·회계 JSON·세금 분류 (mcp_docs·OCR)",
            "bundles_cowork-deck":       "슬라이드 빌드 (design_ppt 연계)",
            "bundles_cowork-proposal":   "제안서 작성 (design_word 연계)",
            "bundles_cowork-plan":       "주간 계획·할 일 (exec_scheduler 연계)",
            "bundles_cowork-contract":   "계약 검토·리스크 (design_pdf·legal 체크)",
            "bundles_cowork-briefing":   "아침 브리핑 드래프트 (Slack·이메일 요약)",
        },
        "skills": {
            "skill-cowork-flow":         "여러 플러그인 조합 워크플로우 (체인 패턴)",
            "skill-cowork-personal":     "개인 비서 수준 컨텍스트 유지 (name·prefs·history)",
        },
    },
}

COMMON = '''#!/bin/bash
# common.sh - PLUGIN_NAME 공통 헬퍼
set -uo pipefail
PLUGIN_NAME="PLUGIN_NAME"
REPO_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
LOG_DIR="$REPO_ROOT/.claude/state/$PLUGIN_NAME"
DATA_DIR="$REPO_ROOT/data/$PLUGIN_NAME/$(date +%Y-%m-%d)"
mkdir -p "$LOG_DIR" "$DATA_DIR"
log_info()  { echo "[INFO] $1" >&2; printf '{"ts":"%s","level":"INFO","msg":"%s"}\\n' "$(date -u +%FT%TZ)" "$1" >> "$LOG_DIR/log.jsonl"; }
log_error() { echo "[ERROR] $1" >&2; printf '{"ts":"%s","level":"ERROR","msg":"%s"}\\n' "$(date -u +%FT%TZ)" "$1" >> "$LOG_DIR/log.jsonl"; }
is_dry_run() { [ "${DRY_RUN:-false}" = "true" ] && return 0; for a in "$@"; do [ "$a" = "--dry-run" ] && return 0; done; return 1; }
load_env() { [ -f "$REPO_ROOT/.env" ] && { set -a; source "$REPO_ROOT/.env"; set +a; }; }
'''

CMD_TEMPLATE = '''---
description: "DESC"
allowed-tools: Bash(bash:*), Write, Read
---

## Context
- 플러그인: `PLUGIN` (spec-only)
- 출처: SOURCE

## Your task
```bash
source plugins/PLUGIN/scripts/common.sh
load_env
is_dry_run "$@" && log_info "dry-run"
```

**목적**: DESC

실구현은 플랫폼에서. 상세: `../SPEC.md`
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
            "precedence": 6,
            "token_estimate": len(info["commands"]) * 200 + len(info.get("skills", {})) * 500,
            "source": info["source"],
        },
    }
    (p / "plugin.json").write_text(json.dumps(pj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # common.sh
    (p / "scripts" / "common.sh").write_text(COMMON.replace("PLUGIN_NAME", name), encoding="utf-8")

    # 커맨드들
    for cmd, desc in info["commands"].items():
        content = CMD_TEMPLATE.replace("PLUGIN", name).replace("DESC", desc).replace("SOURCE", info["source"])
        (p / "commands" / f"{cmd}.md").write_text(content, encoding="utf-8")

    # 스킬들
    for skill, sdesc in info.get("skills", {}).items():
        (p / "skills" / f"{skill}.md").write_text(f"# {skill}\n\n> Status: spec-only\n\n## Purpose\n\n{sdesc}\n\n## 출처\n\n{info['source']}\n\n상세: `../SPEC.md`\n", encoding="utf-8")

    # README
    deps_str = ", ".join(f"`{d}`" for d in info["deps"])
    readme = [
        f"# {name} — {info['display']}",
        "",
        f"> **Prefix**: `{info['prefix']}` | **버전**: 0.1 | **Status**: spec-only | **Phase**: {info['phase']}",
        f"> **출처**: {info['source']}",
        "",
        "## ⚠️ 현재 상태",
        "",
        "**spec-only** — 스펙 + 공통 헬퍼만. 실구현은 install 후 플랫폼에서.",
        "",
        "## 📋 커맨드",
        "",
    ]
    for cmd, desc in info["commands"].items():
        mark = " ⭐ 기본" if cmd == info["default_command"] else ""
        readme.append(f"- `/{cmd}`{mark} — {desc}")
    readme += ["", "## 🧠 스킬", ""]
    for s, sd in info.get("skills", {}).items():
        readme.append(f"- `{s}` — {sd}")
    readme += [
        "",
        "## 🔗 의존성",
        "",
        f"- **플러그인**: {deps_str}",
        "- **공통 헬퍼**: `scripts/common.sh`",
        "",
        "## 📝 참조",
        "",
        "- 스펙: `SPEC.md`",
        "- 분석: `docs/upgrade-analysis-2026-04-19.md`",
    ]
    (p / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    # SPEC
    spec = [
        f"# {name} — 상세 스펙 (Phase {info['phase']})",
        "",
        f"**출처**: {info['source']}",
        "",
        "## 목표",
        "",
        f"- {info['display']}",
        "",
        "## 커맨드 스펙",
        "",
    ]
    for cmd, desc in info["commands"].items():
        spec += [f"### `/{cmd}`", "", desc, "", "- `--dry-run` 지원", "- 구조화 로그", ""]
    if info.get("skills"):
        spec += ["## 스킬 스펙", ""]
        for s, sd in info["skills"].items():
            spec += [f"### `{s}`", "", sd, ""]
    spec += [
        "## 구현 체크리스트 (플랫폼)",
        "",
        "- [ ] 멱등성",
        "- [ ] `--dry-run` 실동작",
        "- [ ] 에러 복구",
        "- [ ] 시크릿 `.env`",
        "- [ ] JSON 로그",
        "",
        "## 참조",
        "",
        f"- 출처: {info['source']}",
        "- 아키텍처: `docs/architecture-patterns.md`",
    ]
    (p / "SPEC.md").write_text("\n".join(spec) + "\n", encoding="utf-8")

    print(f"OK: {name}")

print("\nDone.")
