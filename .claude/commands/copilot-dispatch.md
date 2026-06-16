---
description: GitHub Copilot CLI 에 task 위임 — gh copilot 호출 (저비용 보완)
allowed-tools: Bash(gh:*), Read, Write
---

# /copilot-dispatch — GitHub Copilot CLI multi-harness 위임

> **근거**: `docs/2026-06-16/tooling-comparison.md` § ⭐⭐ wshobson/agents 패턴.
> **사용**: GitHub-native workflow (issue → PR → review) 자동화 · Copilot 구독 시 저비용 보완.
> **요구**: `gh` CLI + `gh extension install github/gh-copilot` + Copilot 권한 포함 `GITHUB_TOKEN`.

## 사용

```bash
/copilot-dispatch suggest "이 함수에 type hint 추가"
/copilot-dispatch explain <file>
/copilot-dispatch pr-review <pr-number>
```

## 동작

```bash
# 1. gh CLI + copilot extension 검증
gh extension list | grep -q "github/gh-copilot" || {
  echo "[FAIL] gh copilot 미설치 — gh extension install github/gh-copilot"
  exit 1
}

# 2. 명령 분기
case "$1" in
  suggest)
    gh copilot suggest "$2"
    ;;
  explain)
    cat "$2" | gh copilot explain -
    ;;
  pr-review)
    # PR diff 추출 → Copilot 에 전달
    gh pr diff "$2" | gh copilot suggest "이 PR diff 의 issue·improvement 식별"
    ;;
esac

# 3. 결과 → .claude/tasks/done/<slug>-copilot.md
# 4. post-codex-verify 패턴 적용
```

## 라우팅 매트릭스

| 적합 | 부적합 |
|---|---|
| GitHub PR review (저비용) | 설계·아키텍처 (Opus 4.8) |
| 단순 코드 suggest | 보안·민감 (security-guidance plugin) |
| issue → PR 자동화 | 멀티 파일 cross-cutting refactor (Codex/Cursor) |

## 비용

- Copilot Pro 구독 ($10/m) 안에서 무제한 — 우리 quota·budget 정책 외부
- 단 token consumption 은 메트릭에 기록 (`.claude/state/orca.db` metrics 테이블)

## 참조

- `plugins/exec_harness_copilot/SPEC.md`
- [gh copilot extension](https://github.com/github/gh-copilot)
- `.env.example` GITHUB_TOKEN
