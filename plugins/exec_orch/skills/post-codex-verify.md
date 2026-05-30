# Codex 보고 후 사후 검증 룰

> **출처**: 2026-05-30 사용자 발견 — codex 가 "DB 반영 완료, 더 채웠다" 보고했으나 실측 0건. 보고만 그럴듯한 hallucination.

## 절대 룰

**Codex / Gemini / 외부 AI worker 보고는 신뢰 X. 사후 측정으로 검증 후만 수용.**

## 검증 매트릭스

| 보고 종류 | 자동 검증 명령 | PASS 조건 |
|---|---|---|
| DB 시드 (INSERT N건) | `SELECT COUNT(*) FROM <table>` before/after | after >= before + N |
| 테이블 신규 | `SELECT name FROM sqlite_master WHERE type='table' AND name='<t>'` | 1건 |
| 파일 생성 | `Test-Path <file>` + `wc -l <file>` | 존재 + 보고 라인 수 ±10% |
| 라우트 추가 | `grep -c '@api_bp.route' web/app.py` before/after | after >= before + N |
| 인덱스 추가 | `SELECT name FROM sqlite_master WHERE type='index' AND name='<i>'` | 1건 |
| 마이그레이션 | schema diff (PRAGMA table_info) before/after | 컬럼 변경 확인 |

## 검증 흐름 (PostToolUse 자동)

1. **Pre-snapshot**: codex 호출 직전 검증 metric 측정 (`pre.json` 저장)
2. **Codex 실행**: `codex exec "..."` 또는 task-instruction.md dispatch
3. **Post-snapshot**: codex 완료 직후 동일 metric 측정 (`post.json`)
4. **Diff**: pre vs post 비교
5. **PASS/FAIL**: 보고된 변경량과 실측 일치 여부

## Git commit 자동화 (핵심)

**매 codex/gemini 작업 완료 → 자동 git commit. empty commit (변경 0) = hallucination 즉시 검출.**

### 흐름
1. codex 호출 직전: `git rev-parse HEAD` → `pre_sha` 저장
2. codex 실행
3. codex 완료 직후: `git add -A && git diff --cached --stat`
4. 변경 0 라인 → **hallucination 확정** + 보고에 표시
5. 변경 있음 → `git commit -m "codex: <task-slug> [auto-verify] <changes_summary>"`
6. `git log --stat pre_sha..HEAD` 로 diff 출력 → 사용자 보고

### Commit message 표준
```text
codex: <task-slug> [auto-verify]

Summary (codex 보고):
<codex가 한 보고 원문>

Actual changes (실측):
- files: N
- lines: +X -Y
- DB rows: <table> +M / <table2> +K
```

### Empty commit 정책
- 변경 0 → `git commit --allow-empty -m "codex: <task-slug> [HALLUCINATION] no changes"`
- 사용자 git log 보면 즉시 "거짓 보고" 보임
- 같은 task 3회 hallucination → codex 잠시 disable

### 적용 task-instruction.md template
```markdown
## 완료 검증 (필수)
작업 끝나면 다음 명령 자동 실행:
1. `git status` 확인
2. `git add -A`
3. `git diff --cached --stat` 출력
4. 변경 0 라인이면 보고에 "[HALLUCINATION SUSPECTED]" 표시
5. report.md 에 git diff 첨부
```

## FAIL 시 조치

- 보고를 사용자에게 인용하면서 실측 0건임을 명시
- 다음 행동 후보:
  - codex 재시도 (1회)
  - 다른 AI (gemini / claude) 로 fallback
  - Claude 직접 수동 작업

## 금지

- codex 보고만 보고 "완료" 사용자 보고 — 검증 누락 = pending 06·09·19 위반
- pre-snapshot 없이 post 만 확인 — 변화량 측정 불가
- 검증 FAIL 후 그냥 넘어감 — 사용자가 한 달 발견한 결함 재발

## 참조
- skill: `plugins/exec_orch/skills/post-codex-verify.md`
- hook: `.claude/hooks/post-codex-verify.sh`
- memory: `feedback_codex_report_unreliable.md`
