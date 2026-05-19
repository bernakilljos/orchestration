# sec_scan — 보안 스캔 (semgrep + gitleaks + bandit)

> **AI-Native 파이프라인 2단계**: 코드 변경 + 테스트 통과 후 보안 스캔

## 동작

1. **트리거**: test_gen PASS 또는 PreToolUse (commit·push)
2. **스캐너 3종**:
   - **semgrep** — OWASP Top 10·SQLi·XSS·SSRF (코드 패턴)
   - **gitleaks** — PAT·API key·private key (시크릿 누출)
   - **bandit** — Python 보안 issue (eval·pickle·subprocess)
3. **결과**: `.claude/state/sec-scan-<sha>.json` 저장
4. **정책**:
   - HIGH/CRITICAL → 작업 차단 (PreCommit hook)
   - MEDIUM → 로그 + 사용자 알림
   - LOW → 로그만
5. **다음 단계**: PASS → `doc_auto` 트리거

## 명령

```bash
/sec-scan              # 전체 변경 파일
/sec-scan <file>       # 특정 파일
/sec-scan --severity HIGH   # HIGH 이상만
/sec-scan --staged     # git staged 만
```

## 자동 트리거

- `hooks/post-test-sec-scan.sh` — test_gen 완료 후
- `hooks/pre-commit-secrets.sh` — PreToolUse Bash `git commit`

## 의존성

- `semgrep` (pip install semgrep)
- `gitleaks` (https://github.com/gitleaks/gitleaks)
- `bandit` (pip install bandit) — Python 만

자동 설치: `scripts/install-sec-tools.sh` (SessionStart hook 통합)

## CLAUDE.md § 7-23 정합

HITL Approval Gate (`approval-gate.py`) 와 정합:
- HIGH 보안 issue 발견 → `approval-gate` waiting_approval
- `/approve <task_id>` 받아야 진행

## 정책

- false-positive 5% 한계 — 초과 시 rule 튜닝
- 새 PR = sec_scan 자동 발동
- 결과 = Slack outbox 또는 Notion outbox 자동 push
