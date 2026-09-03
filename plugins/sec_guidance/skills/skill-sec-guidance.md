---
name: sec-guidance-integration
description: |
  Anthropic 공식 security-guidance plugin 자동 활용. Write/Edit/MultiEdit 시 25 위험 패턴 검출 → 경고 시 사용자 결정.
  사용자가 "보안", "취약점", "vulnerability", "command injection", "XSS", "pickle", "eval" 언급 시 활성화.
---

# sec_guidance 통합 스킬

## 트리거
- Write/Edit/MultiEdit 도구 사용 시 (자동, 사용자 입력 X)
- 사용자가 "보안 검사", "취약점 검출", "안전한가?" 등 질문
- CI/PR 직전 점검 요청

## 자동 작동 (설치 후)

설치되어 있으면 Claude Code 가 Write/Edit/MultiEdit 호출 직전 plugin 의 pre-hook 가 발동. 25 위험 패턴 정규식 매치 시:

```text
 security-guidance: command injection detected
  File: scripts/deploy.sh:42
  Pattern: $(unsanitized_input)
  Suggestion: use printf '%q' or array form

Proceed? [y/N]
```

사용자가 `y` → 진행. `N` → 차단.

## 우리 워크플로우 통합

### 1. 24/7 자동화 (Orca)
- codex/haiku worker 도 Write/Edit 호출 → sec_guidance 가드
- 위험 패턴 매치 시 worker 작업 중단 + approval gate 등록 (`.claude/rules/approval-gate-rules.md` 와 정합)

### 2. /sec-scan 과 조합
```bash
# 실시간 가드 (자동)
sec_guidance (always on)

# 명시적 깊은 감사 (사용자 호출)
/sec-scan
```

### 3. PR 직전 체크
```bash
/sec-scan                              # semgrep + gitleaks + bandit
# 다음 PR commit 시 sec_guidance 가 추가 가드
```

## 25 패턴 카테고리 요약

| 카테고리 | 언어 | 위험 |
|---|---|---|
| GitHub Actions injection | YAML | RCE |
| `child_process.exec()` | Node | RCE |
| `eval()` / `new Function()` | JS/Py | RCE |
| `dangerouslySetInnerHTML` | React | XSS |
| `innerHTML` 직접 할당 | JS | XSS |
| Python `pickle.loads()` | Py | RCE (deserialize) |
| `os.system()` 문자열 결합 | Py | command injection |
| SQL string concat | 다중 | SQL injection |
| hardcoded API key/secret | 다중 | 키 노출 |
| 외 16개 | — | OWASP Top 10 위주 |

## 설치 확인

```bash
# Claude Code 안에서
/plugin list | grep security-guidance
```

미설치 시:
```text
/plugin install security-guidance@claude-plugins-official
```

## 금지

- sec_guidance 경고 무시하고 진행 — 위험 패턴 commit 가능성
- /sec-scan 만 의존 — pre-hook 가드 누락
- 두 도구를 중복 취급 — 시점·깊이가 다름

## 참조

- 공식: https://code.claude.com/docs/en/security-guidance
- Anthropic blog Week 22 (2026-05-25)
- 우리 깊은 감사: `plugins/dev_security/` 또는 `/sec-scan`
- approval gate: `.claude/rules/approval-gate-rules.md`
- 우리 보완: `plugins/review_qa/` (코드 리뷰)
