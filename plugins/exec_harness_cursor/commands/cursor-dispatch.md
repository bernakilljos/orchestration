---
description: Cursor IDE 에 task 위임 — file-based bridge (Cursor MCP 미존재 시 fallback)
allowed-tools: Bash(cursor:*), Read, Write
---

# /cursor-dispatch — Cursor IDE multi-harness 위임

> **근거**: `docs/2026-06-16/tooling-comparison.md` § ⭐⭐ wshobson/agents 패턴.
> **사용**: 시각적 step-by-step refactor · 복잡 frontend 작업 · Cursor Composer 의 iterative 강점 필요 시.
> **요구**: Cursor IDE 설치 + (선택) `CURSOR_API_KEY`.

## 사용

```bash
/cursor-dispatch <task-instruction-path>
/cursor-dispatch --inline "<prompt>" <file1> <file2>
```

## 동작 (file-based bridge — MCP 미존재 시 fallback)

```bash
# 1. task-instruction 검증 (codex-rules.md 와 동일)
[ -f "$1" ] || { echo "[FAIL] task file 필요"; exit 1; }

# 2. Cursor handoff 폴더에 task 복사
HANDOFF_DIR="${HOME}/.cursor/handoff"
mkdir -p "$HANDOFF_DIR"
SLUG=$(basename "$1" .md)
cp "$1" "$HANDOFF_DIR/${SLUG}.md"

# 3. Cursor 열기 (file:// URL 또는 cursor: deeplink)
if command -v cursor >/dev/null 2>&1; then
  cursor "$HANDOFF_DIR/${SLUG}.md"
else
  echo "[INFO] cursor CLI 없음 — manual: 이 파일을 Cursor 에서 열어주세요: $HANDOFF_DIR/${SLUG}.md"
fi

# 4. 결과 폴링 (60초)
# Cursor 작업 완료 후 사용자가 결과를 $HANDOFF_DIR/${SLUG}-result.md 로 저장
# 또는 git diff 로 변경 감지

# 5. post-verify (codex-rules.md § 사후 검증 패턴 동일)
bash plugins/exec_orch/hooks/post-codex-verify.sh post "$SLUG"
```

## fallback 시나리오

| 상황 | 동작 |
|---|---|
| Cursor 설치 안 됨 | [FAIL] — 사용자 안내 |
| Cursor CLI 없음 | handoff 파일 경로 안내 — 수동 open |
| Cursor MCP 가 향후 추가됨 | MCP 통합으로 자동 (현재 미존재) |
| 결과 60초 미반환 | 사용자 명시 종료 또는 cancel |

## 정책

- 이번 task 의 라이선스·접근 수준 = Claude Code 워크플로우와 동일 (사용자 책임)
- task-instruction 의 § 3 files allow-list 동일 적용
- Cursor 변경은 git diff 로 자동 감지 + post-codex-verify hallucination 검출

## 참조

- `plugins/exec_harness_cursor/SPEC.md`
- `docs/2026-06-16/tooling-comparison.md` § wshobson multi-harness
- `.claude/rules/codex-rules.md` § task-instruction 의무
- `.env.example` § multi-harness
