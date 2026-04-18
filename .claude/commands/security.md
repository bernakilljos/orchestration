---
description: "보안 검사 — OWASP 기준 취약점 스캔 + 의존성 감사 + 시크릿 노출 체크"
allowed-tools: Bash(npm:*), Bash(python:*), Bash(powershell:*), Bash(where:*)
---

## Context
- 프로젝트 타입: !`if exist package.json (echo nodejs) else if exist requirements.txt (echo python) else (echo unknown)`
- node_modules: !`if exist node_modules (echo 있음) else (echo 없음)`
- git 상태: !`git status --short 2>/dev/null | wc -l`
- 오늘 날짜: !`date /t 2>nul`

## Your task

### Step 1 — 의존성 보안 감사 (직접 실행)

**Node.js:**
```
npm audit --json 2>&1
```
결과에서 critical/high 취약점만 추출.

**Python:**
```
pip-audit --format json 2>&1
```
pip-audit 없으면: `pip install pip-audit` 후 재실행.

### Step 2 — 시크릿 노출 체크 (코드베이스 검색)

```powershell
# API 키, 패스워드, 토큰 패턴 검색
$patterns = @(
  'api[_-]?key\s*=\s*["\x27][^"\x27]{10,}',
  'password\s*=\s*["\x27][^"\x27]+',
  'secret\s*=\s*["\x27][^"\x27]{8,}',
  'token\s*=\s*["\x27][^"\x27]{10,}',
  'ghp_[a-zA-Z0-9]{36}',        # GitHub PAT
  'sk-[a-zA-Z0-9]{48}',          # OpenAI
  'AIza[0-9A-Za-z-_]{35}'        # Google API
)
Get-ChildItem -Recurse -Include *.js,*.ts,*.py,*.env,*.config.* |
  Where-Object { $_.FullName -notmatch 'node_modules|\.git|dist' } |
  ForEach-Object {
    $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
    foreach ($p in $patterns) {
      if ($content -match $p) {
        Write-Host "[WARN] $($_.FullName): 시크릿 의심 패턴"
      }
    }
  }
```

### Step 3 — .env 파일 체크

```
.env 파일이 .gitignore에 있는지 확인
.env가 git에 커밋됐는지 확인: git log --all -- .env
```

### Step 4 — OWASP Top 10 체크 (skill-23 연동)

`plugins/review_qa/skills/skill-23-owasp-security.md` 기준으로 코드 리뷰:
- A01: 접근 제어 취약점
- A02: 암호화 실패
- A03: 인젝션 (SQL, Command, XSS)
- A05: 보안 설정 오류
- A07: 인증/세션 관리

### Step 5 — 보고서

`docs/YYYY-MM-DD/validation/security-report.md` 저장:

```markdown
# 보안 검사 보고서 — YYYY-MM-DD

## 의존성 취약점
| 심각도 | 패키지 | 문제 | 해결방법 |
|--------|--------|------|---------|
| CRITICAL | ... | ... | npm update ... |

## 시크릿 노출
- [x] .env gitignore 확인
- [ ] [파일명] 시크릿 의심 패턴 발견 ← 즉시 수정 필요

## OWASP 체크
- A01 접근제어: PASS/FAIL
- A03 인젝션: PASS/FAIL
- A07 인증: PASS/FAIL

## 결론
PASS / FAIL — [즉시 수정 필요 항목]
```
