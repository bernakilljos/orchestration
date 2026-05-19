# Hook: doc_auto

> **트리거 2종**:
> 1. sec_scan PASS 후 (체인)
> 2. Stop hook (세션 종료 시 마지막 diff 일괄 정리)

## 동작 1 — post-sec-doc.sh

```text
sec_scan PASS → doc_auto 호출 → diff append 후 사용자 review 대기
```

`ai-native-chain.sh doc_auto <file>` 가 진행.

## 동작 2 — stop-doc-summary.sh

```text
세션 종료 시 → .claude/state/doc-auto-*.md 모아서 통합 보고서
```

`.claude/state/session-summary-<date>.md` 에 doc 변경사항 요약.

## 설정 (`.claude/settings.json`)

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "bash ${CLAUDE_PROJECT_DIR}/plugins/doc_auto/hooks/stop-doc-summary.sh",
        "timeout": 30
      }]
    }]
  }
}
```

## 자동 commit 금지

doc_auto 는 **diff 만 append**. 사용자가 review 후 직접 commit.
근거: CLAUDE.md § 7-11 ("사용자 결정 빈발 X" 와 정합 — 단, 문서 commit 은 사용자 review 필요)
