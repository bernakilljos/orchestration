---
description: "코드 보안 스캔 (semgrep + gitleaks + bandit) — HIGH 발견 시 작업 차단"
allowed-tools: Bash, Read
---

# /sec-scan

코드 + 시크릿 + Python 보안 issue 통합 스캔.

## 사용

```text
/sec-scan                  # 전체 변경 파일 스캔
/sec-scan <file>           # 특정 파일
/sec-scan --severity HIGH  # HIGH/CRITICAL 만 보고
/sec-scan --staged         # git staged 파일만
/sec-scan --tool semgrep   # 단일 도구
```

## 실행 순서

1. **gitleaks** (가장 빠름) — 시크릿 검출 (PAT·API key·private key)
2. **semgrep** — OWASP Top 10 패턴 (SQLi·XSS·SSRF·path traversal)
3. **bandit** — Python 한정 (eval·pickle·subprocess·assert in prod)

## 출력

```text
┌─────────────────────────────────────┐
│ sec_scan: 3 issues found            │
├─────────────────────────────────────┤
│ CRITICAL × 1                        │
│   gitleaks: AWS_SECRET_KEY exposed  │
│   → src/config.py:42                │
│ HIGH × 1                            │
│   semgrep: SQL injection            │
│   → src/db.py:128                   │
│ MEDIUM × 1                          │
│   bandit: pickle.loads on untrusted │
│   → src/cache.py:55                 │
└─────────────────────────────────────┘
```

## 차단 정책

| severity | 정책 |
|---|---|
| CRITICAL/HIGH | git commit 차단 (PreToolUse hook), approval-gate 등록 |
| MEDIUM | 로그 + 사용자 알림 (.claude/logs/sec-scan.log) |
| LOW | 로그만 |

## 다음 단계

PASS (HIGH 0개) → `doc_auto` 자동 호출.
FAIL → `approval-gate.py request` 등록 후 `/approve <task_id>` 대기.

세부: `skills/skill-security-scanning.md`
