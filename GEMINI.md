# GEMINI.md — Multi-AI Orchestration Kit v1 (Gemini용)

> Claude용: `CLAUDE.md` | Codex용: `AGENTS.md` | Gemini용: 이 파일
> MCP 설정: `.gemini/config.toml`
> 버전: v1.0.1 · 2026-04-24

---

## 시작: Standalone vs Full

**이 문서를 읽고 있다면:**
- **Standalone 모드**: `install_gemini` 로 설치함. Claude 없이 Gemini 단독. 자연어 한 줄로 끝.
- **Full 모드**: `install.bat` 로 설치함. Claude 설계 → Codex 구현 → Gemini 검증 자동화.

| 측면 | Standalone | Full Mode |
|------|-----------|-----------|
| 설치 | `install_gemini <폴더>` | `install.bat <폴더>` |
| 설정 | `.gemini/` 만 | `.gemini/` + `.claude/` |
| 사용 | `gemini-go "자연어"` | Codex 작성 후 Gemini가 검증 |
| 역할 | 검증+구현+요약+문서화 모두 | 검증만 전담 (Codex가 구현) |
| 1M 컨텍스트 | 자유롭게 활용 | 대용량 파일 검증에 활용 |
| 비용 | Gemini만 (저가) | Codex+Gemini+Claude (높음) |
| 팀 크기 | 개인·소팀 | 팀/조직 |

**업그레이드 경로:**
```bash
# Standalone → Full 전환 (기존 .gemini/ 유지)
install.bat <현재 폴더>
```

---

## Role
**검증 담당 AI**. 코드 리뷰, 보안 점검, 품질 검증, 문서화를 맡는다.
- 구현은 Codex가 한다 (`AGENTS.md` 참조)
- 설계·판단은 Claude가 한다 (`CLAUDE.md` 참조)
- Gemini Flash 모델은 저단가·1M 컨텍스트 — 검증·요약에 강점

---

## 태스크 읽기 규칙

1. `.claude/tasks/` 폴더에서 `verify-*.md` 또는 `review-*.md` 파일 확인
2. `.claude/tasks/locks/` 에 같은 이름 `.lock` 없는 태스크만 처리
3. 처리 시작 시 `.lock` 파일 생성 (동시 검증 방지)
4. 완료 시 `.claude/tasks/done/` 으로 이동
5. Codex 가 만든 `done/TASK-ID-report.md` 가 입력 후보

## 태스크 파일 구조 (verify-*.md 형식)

```
# 검증 제목
## Target: 검증 대상 (PR / 파일 / 모듈)
## Files: 검증할 파일 목록 (상대경로)
## Checks: 점검 항목
  - Security: OWASP Top 10
  - Quality: 복잡도·중복·네이밍
  - Tests: 커버리지·엣지케이스
  - Docs: README·주석 일관성
## Pass Criteria: 합격 기준
```

---

## 검증 규칙

### Security
- 하드코딩된 시크릿 (API 키, 토큰, 비밀번호) 탐지
- SQL/Command Injection 가능성
- XSS / CSRF 가능성
- 인증·인가 누락
- 의존성 취약점 (npm audit, pip-audit)

### Quality
- 함수 복잡도 (Cyclomatic ≤ 10)
- 중복 코드 (>30줄 동일 패턴 → 경고)
- 네이밍 컨벤션 일관성
- 에러 처리 누락
- 로깅 적절성

### 코드 규칙 (Codex와 동일하게 적용 — 위반 시 불합격)
- 하드코딩 금지 (경로·포트·도메인 → 환경변수)
- 서버 파일 한글 문자열 금지 → 영어
- 주석에 "주인" 사용 금지
- optional chaining(`?.`) 사용 금지
- 기존 파일 전체 재작성 금지

### Docs
- README.md 갱신 여부
- 함수 docstring 일관성
- 변경 사항 → CHANGELOG/PR 설명에 반영

---

## 플러그인 연동

각 플러그인의 `gemini/` 폴더에 Gemini 전용 검증 지시서가 있을 수 있다 (없으면 공통 규칙 적용):

| 플러그인 | Gemini 지시서 (선택) |
|---------|---------------------|
| exec_orch | `plugins/exec_orch/gemini/verify-checklist.md` |
| review_qa | `plugins/review_qa/gemini/qa-runbook.md` |
| design_ppt | `plugins/design_ppt/gemini/visual-review.md` |

폴더가 없으면 `AGENTS.md` 의 코드 규칙을 그대로 적용해 검증.

---

## MCP 설정
`.gemini/config.toml` 참조.
플러그인별 추가 MCP는 해당 `gemini/` 디렉토리에 설명됨.

---

## 결정 권한 (중요)

Gemini 의 검증 결과는 **참고용**. 최종 채택·거부 결정은 **Claude (팀장)** 이 한다.
- Gemini: "이 코드는 이러이러한 이슈가 있다" (사실 보고)
- Claude: "그 이슈는 수용 가능 / 수정 필요" (판단)

→ Gemini 가 직접 코드를 수정하지 않는다. **리뷰 결과 파일만 생성**.

---

## 완료 보고

검증 완료 시 아래 형식으로 `.claude/tasks/done/TASK-ID-review.md` 생성:

```markdown
## 검증 보고
- Target: [검증 대상]
- 검증 파일: [목록]
- 결과: PASS | FAIL | WARN
- 발견 이슈:
  - [심각도] [카테고리] 설명 (파일:줄)
  - 예: [HIGH] [Security] API 키 하드코딩 (src/auth.js:42)
- 권장 조치:
  - 1순위: ...
  - 2순위: ...
- 다음: Claude 판단 필요 (채택/수정/거부)
```

---

## 비용 효율 가이드

Gemini Flash 는 저단가 · 빠른 검증에 강점. 다음에 우선 활용:
- 대량 파일 1차 스캔 (수백 파일)
- 반복 검증 (빌드마다)
- 긴 문서 요약 (1M 컨텍스트)

복잡 추론·아키텍처 결정은 Claude Opus 에게 위임 (orchestration 환경에서).

---

## Standalone 모드 (Claude 없이 Gemini 단독 사용)

`install_gemini` 로 셋업한 환경에서는 Claude orchestration 없이 Gemini 만으로 작업.
역할이 **검증 전용 → 일반 작업 가능**으로 확장됨.
**task 파일 수동 편집 필요 없음 — 자연어 한 줄로 끝.**

### 특징

1. **1M 토큰 컨텍스트** — Gemini의 최대 강점. 100MB 로그도 한 번에 처리
2. **저단가** — 반복 검증·요약에 경제적
3. **다목적** — 검증·구현·요약·문서화 모두 가능
4. **자동 로깅** — 모든 호출이 `.gemini/usage.jsonl` 에 기록 (비용 추적)
5. **모델 선택** — `gemini-2.0-flash` (기본, 빠름) 또는 `gemini-1.5-pro` (1M 컨텍스트)

### 사용법

**A. 검증 (기본)**
```bash
cd C:\myproject
gemini-go "이 코드 보안 검증해줘"
gemini-go "PR 코드 리뷰해줘"
```

**B. 1M 컨텍스트 활용 (Gemini 강점)**
```bash
# 100MB 이상의 대용량 파일도 처리 가능
gemini-go "로그 파일 분석해줘"
gemini-go "PDF 문서 100개 요약해줘"
gemini-go "데이터베이스 스키마 분석 후 ERD 만들어줘"
```

**C. 구현·문서화**
```bash
gemini-go "회원가입 페이지 만들어줘"
gemini-go "README 작성해줘"
gemini-go "CHANGELOG 업데이트해줘"
gemini-go                            # 대화 모드
```

**D. 배치 처리 — 여러 작업 한꺼번에**
```bash
# Gemini 에게 task 파일 생성 요청
gemini-go "다음 3개를 tasks/task-001~003.md 로 정리해줘:
  1. 인증 모듈 보안 검증
  2. 로그 100MB 요약
  3. README 자동 생성"

# 큐 자동 처리
gemini-a --auto
```

### API 키 설정

```bash
# 1. 환경변수 (권장)
setx GOOGLE_API_KEY "YOUR_API_KEY"

# 2. .env 파일
copy .env.example .env
# [편집기로 GOOGLE_API_KEY 값 입력]

# 3. 명령줄
set GOOGLE_API_KEY=... && gemini-go "작업"
```

### 선택 설정

```env
# .env 또는 환경변수로 설정
GEMINI_MODEL=gemini-1.5-pro             # 모델 선택 (기본: gemini-2.0-flash)
GEMINI_DAILY_LIMIT_USD=20               # 일일 예산 상한
```

### 모델 비교

| 모델 | 컨텍스트 | 속도 | 가격 | 추천 |
|------|---------|------|------|------|
| **gemini-2.0-flash** | 일반 | 매우 빠름 | 매우 저가 | 기본 선택 |
| **gemini-1.5-pro** | **1M 토큰** | 빠름 | 저가 | 대용량 파일 분석 |

```bash
# 모델 변경
set GEMINI_MODEL=gemini-1.5-pro && gemini-go "..."
```

### 사용량 추적

```bash
# 사용량 확인
type .gemini\usage.jsonl

# 형식: JSON Lines (JSONL)
# 예: {"ts": "2026-04-24T10:30:00Z", "model": "gemini-2.0-flash", "in": 1500, "out": 800, "cost_usd": 0.001}
```

### 비용 예시 (gemini-2.0-flash)

| 작업 | 입력 토큰 | 출력 토큰 | 비용 |
|------|---------|---------|------|
| 코드 리뷰 | ~500 | ~300 | $0.0001 |
| 요약 (100MB) | ~50,000 | ~1,000 | $0.005 |
| 문서 생성 | ~1,000 | ~2,000 | $0.0005 |

일일 예산 `$20` 이면 대용량 작업 수천 개 처리 가능.

### 역할 비교: Standalone vs Full

| 역할 | Standalone Gemini | Full Mode Gemini |
|------|----------------|------------------|
| 설계 | 자신이 판단 | Claude (Opus) |
| 구현 | Gemini 직접 | Codex 담당 |
| 검증 | 자신이 판단 | Gemini가 자동 검증 |
| 채택 | 사용자 최종 결정 | Claude가 최종 결정 |

### 코드 규칙 (필수)

위의 "검증 규칙 § 코드 규칙" 섹션과 동일하게 적용 (orchestration 여부 무관).

---
