---
name: skill-security-scanning
description: |
  코드 보안 스캔 — semgrep (OWASP) + gitleaks (시크릿) + bandit (Python) 통합.
  사용자가 "보안 스캔", "시크릿 검출", "OWASP", "AI-Native 2단계" 같은 말을 할 때 활성.
  test_gen PASS 후 자동 또는 PreToolUse git commit 시 자동.
---

# Skill: Security Scanning

## 트리거
- 수동: `/sec-scan`
- 자동: hooks/post-test-sec-scan.sh (test_gen 완료 후)
- 자동: hooks/pre-commit-secrets.sh (PreToolUse Bash matcher `git commit`)
- 명시적 요청: "보안 검사", "취약점 찾아줘", "시크릿 새는지 봐"

## 스캐너 3종

### 1. gitleaks (시크릿)

```bash
gitleaks detect --source . --report-format json --report-path .claude/state/gitleaks.json
```

대상 패턴:
- AWS_ACCESS_KEY / SECRET_KEY
- GitHub PAT (`ghp_*`, `github_pat_*`)
- API keys (Stripe, OpenAI, Anthropic, Slack)
- Private keys (RSA, SSH, PGP)

### 2. semgrep (OWASP)

```bash
semgrep --config=auto --json --output=.claude/state/semgrep.json
```

룰셋:
- `p/owasp-top-ten` (필수)
- `p/security-audit`
- `p/secrets`
- 커스텀: `.semgrep/custom.yml`

### 3. bandit (Python)

```bash
bandit -r . -f json -o .claude/state/bandit.json -ll
```

검출:
- `eval()` 사용
- `pickle.loads` 신뢰 X 데이터
- `subprocess` shell=True
- `assert` 프로덕션 코드
- 약한 암호 (md5·sha1)

## 결과 통합

```python
# .claude/scripts/lib/sec_scan_aggregate.py
def aggregate():
    issues = []
    issues.extend(parse_gitleaks(".claude/state/gitleaks.json"))
    issues.extend(parse_semgrep(".claude/state/semgrep.json"))
    issues.extend(parse_bandit(".claude/state/bandit.json"))
    return sorted(issues, key=lambda i: SEVERITY_ORDER[i.severity])
```

## 차단 정책

| severity | git commit | 다음 단계 |
|---|---|---|
| CRITICAL | 차단 | approval-gate.py request |
| HIGH | 차단 | approval-gate.py request |
| MEDIUM | 통과 | doc_auto 진행 + 사용자 알림 |
| LOW | 통과 | doc_auto 진행 + 로그만 |

## 자동 설치

도구 없으면 SessionStart hook 이 자동 설치:

```bash
# scripts/install-sec-tools.sh
pip install semgrep bandit 2>/dev/null
command -v gitleaks >/dev/null || {
  curl -sSL https://github.com/gitleaks/gitleaks/releases/download/v8.18/gitleaks_linux_x64.tar.gz | tar -xz -C /usr/local/bin
}
```

## False-Positive 튜닝

`.semgrepignore` + `.bandit` 으로 화이트리스트:
```text
# .semgrepignore
tests/
node_modules/
docs/screens/
```

## 연결 (chain)

sec_scan PASS → `doc_auto` 호출 (`ai-native-chain.sh doc_auto`).
sec_scan FAIL → `approval-gate.py request sec-<sha>` 등록 → `/approve` 대기.

## 참조

- `plugins/exec_orch/skills/skill-approval-gate.md`
- `.claude/scripts/approval-gate.py`
- OWASP Top 10 (2025): https://owasp.org/Top10/
