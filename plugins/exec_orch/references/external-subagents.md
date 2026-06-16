# 외부 subagent / agent 카탈로그 참조

> **목적**: 외부 검증된 subagent·agent 카탈로그 link + 우리 kit 와 매핑.
> **정책**: vendoring 대신 reference link (저장소 비대 방지). 필요 시 선별 vendoring (라이선스·범위 확인 후).

## 1. VoltAgent awesome-claude-code-subagents (MIT, 154+)

[GitHub](https://github.com/VoltAgent/awesome-claude-code-subagents) — 10 카테고리.

| 카테고리 | 예시 subagent | 우리 kit 대응 |
|---|---|---|
| **01-core-development** | backend-developer · frontend-developer · fullstack-developer · mobile-developer | (없음 — 보강 후보) |
| **02-language-specialists** | python-pro · typescript-pro · go-pro · rust-pro · java-pro · php-pro | (없음 — 보강 후보) |
| **03-infrastructure** | devops-engineer · kubernetes-specialist · docker-specialist · terraform-specialist | `exec_remote` 부분 대응 |
| **04-quality-security** | security-auditor · penetration-tester · code-reviewer · compliance-engineer | `review_qa` + `sec-scan` + `security` + agent `code-reviewer` 대응 |
| **05-data-ai** | data-scientist · ml-engineer · llm-architect · nlp-specialist | (없음 — 보강 후보) |
| **06-developer-experience** | build-tools-specialist · cli-specialist · documentation-specialist · refactoring-specialist | `doc-update` · `test-gen` 부분 대응 |
| **07-specialized-domains** | blockchain-developer · fintech-specialist · iot-specialist · gamedev · healthcare | (없음 — 보강 후보, 필요 시) |
| **08-business-product** | product-manager · marketing-specialist · legal-specialist · sales-specialist | (도메인 외 — vendoring X) |
| **09-meta-orchestration** | agent-coordinator · workflow-automator | `exec_orch` + `route_dispatch` + `auto-planner` 강력 대응 |
| **10-research-analysis** | market-researcher · competitive-analyst · trend-forecaster | `scout` 부분 대응 |

### 우리 kit 보강 후보 (라이선스 MIT — vendoring OK)
- `python-pro`, `typescript-pro`, `go-pro` (language specialist) → `plugins/lang_python` / `lang_typescript` 신설 가능
- `data-scientist`, `ml-engineer`, `llm-architect` → `plugins/data_ai` 신설
- `security-auditor`, `penetration-tester` (이미 우리 `review_qa` 있음) — 비교 후 결정

## 2. Anthropic 공식 skills (151k stars, 16개)

[GitHub](https://github.com/anthropics/skills) — 16 skills.

상세 + install wrapper: `plugins/exec_orch/commands/anthropic-skill.md`.

## 3. wshobson/agents multi-harness

[GitHub](https://github.com/wshobson/agents) — Claude Code / Codex CLI / Cursor / OpenCode / Copilot / Gemini CLI 동시 지원.

우리 = Claude+Codex+Gemini 만 → Cursor·Copilot 통합 시 참조.

## 4. hyperskill/claude-code-marketplace

[GitHub](https://github.com/hyperskill/claude-code-marketplace) — Hyperskill Team 큐레이션.

## 5. xiaolai/claude-plugin-marketplace

[GitHub](https://github.com/xiaolai/claude-plugin-marketplace) — documentation/governance/workflow 중심.

## 정책

1. **link 우선** — 저장소 비대 방지
2. **vendoring** 은 (1) 라이선스 MIT/Apache 확인 (2) 우리 kit 부족 카테고리 (3) 사용자 명시 요청 시
3. **자동 install wrapper** (`/anthropic-skill <name>`) — Anthropic 공식만 (검증됨)
4. **우리 룰 (CLAUDE.md § 7, .claude/rules/)** 와 충돌 시 우리 룰 우선

## 참조

- `docs/2026-06-16/tooling-comparison.md` (전체 비교 매트릭스)
- `plugins/exec_orch/commands/anthropic-skill.md` (공식 install wrapper)
- CLAUDE.md § 3.6 MCP 설치 규칙
