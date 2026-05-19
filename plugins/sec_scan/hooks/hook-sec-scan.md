# Hook: sec_scan

> **트리거 2종**:
> 1. test_gen PASS 후 (PostToolUse Edit/Write 체인)
> 2. PreToolUse Bash matcher = `git commit` (시크릿 차단)

## 동작 1 — post-test-sec-scan.sh

```text
test_gen → tests 실행 PASS → sec_scan 호출
```

`.claude/scripts/ai-native-chain.sh sec_scan <file>` 가 진행.

## 동작 2 — pre-commit-secrets.sh

```text
사용자 git commit 시도 → gitleaks 즉시 실행 → 검출 시 차단
```

차단 패턴 = HIGH/CRITICAL 시크릿 (PAT·API key·private key).

## 설정 (`.claude/settings.json`)

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "bash ${CLAUDE_PROJECT_DIR}/plugins/sec_scan/hooks/pre-commit-secrets.sh",
        "timeout": 30
      }]
    }]
  }
}
```

## CLAUDE.md § 7-23 정합

HITL Approval Gate 와 동일 패턴:
- CRITICAL/HIGH 발견 = `approval-gate.py request`
- `/approve <task_id>` 받기 전에 진행 X
