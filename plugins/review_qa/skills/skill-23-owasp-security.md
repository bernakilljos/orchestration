# Skill 23: OWASP Security Audit

## 목적
OWASP Top 10 기반으로 프로젝트의 보안 취약점을 체계적으로 감사한다.
코드 레벨 + 설정 레벨 + 인프라 레벨 전방위 보안 점검.

## 트리거
- "보안 감사", "security audit", "owasp", "취약점 점검"
- 배포 전 자동 제안 (HOOK-04 pre-deploy에서 호출)
- PR 코드리뷰 시 보안 관련 파일 변경 감지

## 실행 흐름

### 1. OWASP Top 10 (2021) 체크리스트

#### A01: Broken Access Control
```
- [ ] 인증 없이 접근 가능한 API 엔드포인트
- [ ] IDOR (Insecure Direct Object Reference)
- [ ] 수평적/수직적 권한 상승
- [ ] CORS 설정 (*는 금지)
- [ ] JWT 토큰 검증 누락
- [ ] 관리자 페이지 접근 제어
```

#### A02: Cryptographic Failures
```
- [ ] 평문 비밀번호 저장
- [ ] 약한 해시 알고리즘 (MD5, SHA1)
- [ ] 하드코딩된 API 키/토큰/비밀번호
- [ ] HTTP (non-HTTPS) 통신
- [ ] 민감 데이터 로그 출력
```

#### A03: Injection
```
- [ ] SQL Injection (문자열 연결 쿼리)
- [ ] NoSQL Injection
- [ ] OS Command Injection
- [ ] LDAP Injection
- [ ] XSS (Cross-Site Scripting)
  - Reflected XSS
  - Stored XSS
  - DOM-based XSS
- [ ] Template Injection (SSTI)
```

#### A04: Insecure Design
```
- [ ] 비즈니스 로직 결함
- [ ] Rate limiting 미적용
- [ ] 브루트포스 방어 없음
- [ ] 에러 메시지에 내부 정보 노출
```

#### A05: Security Misconfiguration
```
- [ ] 디버그 모드 프로덕션 활성화
- [ ] 기본 계정/비밀번호 미변경
- [ ] 불필요한 포트/서비스 노출
- [ ] 디렉토리 리스팅 활성화
- [ ] 보안 헤더 미설정 (CSP, X-Frame-Options 등)
```

#### A06: Vulnerable Components
```
- [ ] npm audit / pip audit 취약점
- [ ] 오래된 라이브러리 버전
- [ ] 알려진 CVE가 있는 의존성
```

#### A07: Authentication Failures
```
- [ ] 세션 고정 공격
- [ ] 세션 타임아웃 미설정
- [ ] 비밀번호 복잡도 미검증
- [ ] 2FA 미적용 (관리자)
```

#### A08: Data Integrity Failures
```
- [ ] 서명 없는 데이터 역직렬화
- [ ] CI/CD 파이프라인 무결성
- [ ] 자동 업데이트 검증
```

#### A09: Logging & Monitoring Failures
```
- [ ] 로그인 실패 로깅 누락
- [ ] 에러 로그에 스택트레이스 전체 노출
- [ ] 감사 로그(audit log) 미구현
```

#### A10: SSRF (Server-Side Request Forgery)
```
- [ ] 사용자 입력 URL로 서버 요청
- [ ] 내부 네트워크 접근 가능
- [ ] 리다이렉트 검증 누락
```

### 2. 자동 스캔
```bash
# 의존성 취약점
npm audit --json > docs/YYYY-MM-DD/npm-audit.json
pip audit --format json > docs/YYYY-MM-DD/pip-audit.json

# 시크릿 스캔
grep -rn "password\|secret\|api_key\|token" --include="*.js" --include="*.py" --include="*.java" --include="*.env"

# 하드코딩 체크
grep -rn "ghp_\|sk-ant-\|sk-\|AIza\|AKIA" --include="*"
```

### 3. 점수 리포트
```
OWASP Security Score: 72/100

[CRITICAL] ❌ A03 SQL Injection: src/api/users.js:42 — 문자열 연결 쿼리
[HIGH]     ❌ A02 Hardcoded secret: .env.example:3 — API 키 노출
[MEDIUM]   ⚠️ A05 Debug mode: vue.config.js — devtool: 'source-map'
[LOW]      ⚠️ A09 Missing audit log: 로그인 실패 로깅 없음
[PASS]     ✅ A01 CORS properly configured
[PASS]     ✅ A07 Session timeout: 30min
```

### 4. 자동 수정
```
- 하드코딩된 시크릿 → process.env 참조로 변경
- SQL 문자열 연결 → PreparedStatement/파라미터 바인딩
- XSS 취약 출력 → 이스케이프/새니타이즈 적용
- 보안 헤더 자동 추가 (helmet.js 등)
- .gitignore에 민감 파일 추가
```

### 5. CI/CD 연동
```
- pre-commit hook으로 시크릿 스캔 자동 실행
- PR 리뷰 시 보안 점수 자동 코멘트
- 배포 전 최소 점수 (80점) 미달 시 차단
```

## 출력
- `docs/YYYY-MM-DD/owasp-audit.md` — 전체 보안 리포트
- `docs/YYYY-MM-DD/npm-audit.json` — 의존성 취약점
- 코드 수정 (자동 패치 가능한 항목)

## MCP 연동
- **WebSearch**: CVE 데이터베이스 조회
- **WebSearch / WebFetch**: 보안 라이브러리 문서 참조 (내장, MCP 불필요) / context7 MCP 설치 시 추가 활용
- skill-03 (review)의 Security-Only Scan과 연동
