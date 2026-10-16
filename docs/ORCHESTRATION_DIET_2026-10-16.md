# Orchestration Diet — 2026-10-16

**원칙** (사용자 명시 2026-10-16):
- 자동 수정 X · CHANGE CANDIDATE 보고만 · 사용자 승인 후만 축약
- 핵심 뼈대 (Request Ledger·Standing Req·Stop Gate·Codex·전파·FREEZE) 건드리지 X
- 축약 후 반드시 회귀: golden test → request → Codex → Stop Gate → 전파 → statusline → PASS면 FREEZE

## 요약

| 자산 | 전체 | KEEP | MERGE 후보 | REMOVE 후보 |
|---|---|---|---|---|
| Hooks  | 84  | 30  | 1 그룹 | 51 |
| Rules  | 54  | 27  | 0 그룹 | 27 |
| Agents | 19 | 17 | 1 그룹 | - |
| Skills | 99 | - | - | 0 중복 |

## 1. Hooks

### REMOVE 후보 (orphan 또는 등록 X)

- `aggregate-rule-adherence.sh`
- `approval-gate-detect.sh`
- `auto-compact-check.sh`
- `auto-install-deps.sh`
- `block-file-deletion.sh`
- `block-korean-removal.sh`
- `block-tricks.sh`
- `block-version-suffix.sh`
- `block-visible-windows.sh`
- `check-claude-md-size.sh`
- `check-hardcoded-paths.sh`
- `check-html-balance.sh`
- `check-indentation.sh`
- `check-js-syntax.sh`
- `check-korean-only.sh`
- `check-mojibake.sh`
- `cleanup-orphans.sh`
- `deploy-vscode-settings.sh`
- `detect-asset-creation.sh`
- `detect-deflection.sh`
- ... + 31 more

### MERGE 후보 (같은 prefix 3+)

- `session-start-*` (3개): session-start-git-fetch.sh, session-start-recap.sh, session-start-replay-standing.sh

## 2. Rules

### REMOVE 후보 (0 참조)

- `anthropic-api-features.md` (refs: 0)
- `approval-gate-rules.md` (refs: 0)
- `artifact-freshness-check.md` (refs: 0)
- `batch-api-nightly.md` (refs: 0)
- `best-practices.md` (refs: 0)
- `codex-rules.md` (refs: 0)
- `conversation-history.md` (refs: 0)
- `direction-first.md` (refs: 0)
- `environment-dependent-bug.md` (refs: 0)
- `gemini-review-policy.md` (refs: 0)
- `industry-transfer-format.md` (refs: 0)
- `investigation-discipline.md` (refs: 0)
- `mcp-install-rules.md` (refs: 0)
- `measurement-two-deaths.md` (refs: 0)
- `multi-session-isolation.md` (refs: 0)

## 3. Agents

### MERGE 후보 (역할 중복)

- role `code` (2개): python-pro.md, typescript-pro.md

## 4. Skills (중복)

## 다음 단계

1. 사용자가 CHANGE CANDIDATE 리스트 승인
2. 영향 범위 분석 (각 후보 참조 그래프)
3. 축약 (REMOVE → MERGE → MOVE 순)
4. **회귀 테스트**:
   - `python .claude/scripts/golden-test.py` → 13/13 PASS
   - `python .claude/scripts/request-ledger.py gate` → exit 0
   - `python .claude/scripts/standing-requirements.py gate` → exit 0
   - Codex 라우팅 명시 테스트
   - 전파: `bash .claude/scripts/sync-to-team.sh`
5. PASS 시 **FREEZE**

