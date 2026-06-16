---
description: Anthropic 공식 skills marketplace 자동 install — /anthropic-skill <name>
allowed-tools: Bash(claude:*), Bash(plugin:*), Read
---

# /anthropic-skill — Anthropic 공식 skill 1-shot install

> **근거**: Anthropic 공식 marketplace (`@anthropic-agent-skills`) — 151k stars, 16 검증 skills.
> **참조**: `docs/2026-06-16/tooling-comparison.md` § 적용 후보 ⭐⭐⭐.

## 사용

```bash
/anthropic-skill <name>
# 예:
/anthropic-skill mcp-builder
/anthropic-skill claude-api
/anthropic-skill webapp-testing
```

## 공식 카탈로그 (2026-06 기준 16개)

| 카테고리 | skill 이름 |
|---|---|
| **Design** | algorithmic-art · canvas-design · frontend-design · theme-factory |
| **Document** | doc-coauthoring · docx · pdf · pptx · xlsx |
| **Development** | claude-api · mcp-builder · web-artifacts-builder · webapp-testing |
| **Comms** | internal-comms · slack-gif-creator |
| **Meta** | brand-guidelines · skill-creator |

## 우리 kit 중복 분석

| Anthropic skill | 우리 kit 중복 | 권장 |
|---|---|---|
| docx | `design_word` | 둘 다 사용 (공식 = 검증, 우리 = HTML→Playwright pipeline) |
| pptx | `design_ppt` / `make-ppt` | 우리 더 통합 (OCR 검증 포함) — 공식은 단순 generate 용 |
| xlsx | `design_excel` / `excel-make` | 둘 다 사용 |
| pdf | `pdf-generate` / `pdf-sign` 등 | 우리 더 다양 (sign·secure·fill) |
| claude-api | `claude-thinking` / `claude-status` | 공식 우선 (claude-api 4.7→4.8 migration 가이드 포함) |
| mcp-builder | `install-mcp` / `plug_*` | 공식 우선 (MCP 빌드 표준) |
| webapp-testing | `screen-verify.md` rules | 보완 (우리는 smoke-test, 공식은 e2e) |

## 동작

```bash
# Claude Code 의 native marketplace install 호출
claude /plugin install <name>@anthropic-agent-skills

# 설치 후 자동으로:
# - .claude/skills/ 에 ${name} 디렉토리 생성
# - /<name> 또는 description 매칭 시 자동 활성화
# - 우리 sync-plugins.sh 가 next sync 에서 detect (drift 점검)
```

## 자동 통합 권장 (Anthropic 공식 → 우리 kit 보완)

```bash
# 새 환경 setup 시 자동 install (선택)
/anthropic-skill mcp-builder    # MCP 빌드 표준
/anthropic-skill skill-creator  # 새 skill 만들 때 가이드
/anthropic-skill claude-api     # Claude API migration 도움
```

## 참조

- [anthropics/skills (151k stars)](https://github.com/anthropics/skills)
- `docs/2026-06-16/tooling-comparison.md`
- `plugins/exec_orch/references/external-subagents.md`
- CLAUDE.md § 3.6 MCP 설치 규칙 (npm view 검증 의무)
