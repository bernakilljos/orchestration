# AGENTS.md — Multi-AI Orchestration Kit v1 (Codex용)

> Claude용: `CLAUDE.md` | Codex용: 이 파일 | Gemini용: `GEMINI.md`
> MCP 설정: `.codex/config.toml`
> 버전: v1.0.1 · 2026-04-24

---

## 시작: Standalone vs Full

**이 문서를 읽고 있다면:**
- **Standalone 모드**: `install_codex` 로 설치함. Claude 없이 Codex 단독. 자연어 한 줄로 끝.
- **Full 모드**: `install.bat` 로 설치함. Claude 설계 → Codex 구현 → Gemini 검증 자동화.

| 측면 | Standalone | Full Mode |
|------|-----------|-----------|
| 설치 | `install_codex <폴더>` | `install.bat <폴더>` |
| 설정 | `.codex/` 만 | `.codex/` + `.claude/` |
| 사용 | `codex-go "자연어"` | Claude가 task-*.md 작성 후 자동 라우팅 |
| 설계 | 사용자 → Codex 직접 | Claude (Opus) → task → Codex (구현) |
| 검증 | 수동 또는 별도 도구 | Gemini (자동) |
| 비용 | Codex만 (저가) | Codex+Gemini+Claude (높음) |
| 팀 크기 | 개인·소팀 | 팀/조직 |

**업그레이드 경로:**
```bash
# Standalone → Full 전환 (기존 .codex/ 유지)
install.bat <현재 폴더>
```

---

## Role
구현 담당 AI. 500줄 이상 코드, 반복 패턴, CRUD 구현을 맡는다.
설계·판단은 Claude가 한다. 검증은 Gemini가 한다.

---

## 태스크 읽기 규칙

1. `.claude/tasks/` 폴더에서 `task-*.md` 파일 확인
2. `.claude/tasks/locks/` 에 같은 이름 `.lock` 없는 태스크만 처리
3. 처리 시작 시 `.lock` 파일 생성 (동시 수정 방지)
4. 완료 시 `.claude/tasks/done/` 으로 이동

## 태스크 파일 구조 (task-instruction.md 형식)

```
# 태스크 제목
## Goal: 구현 목표
## Files: 수정할 파일 목록 (상대경로)
## Rules: 지켜야 할 규칙
## Expected Output: 완성물 설명
```

---

## 코드 규칙

- 하드코딩 금지 (경로·포트·도메인 → 환경변수)
- 서버 파일(.js/.ts/.java) 한글 문자열 금지 → 영어 사용
- 기존 변수명 임의 변경 금지
- 주석에 "주인" 사용 금지
- optional chaining(`?.`) 사용 금지
- 기존 파일 전체 재작성 금지 — 필요 부분만 수정
- task-instruction.md에 명시된 파일만 수정

---

## 플러그인 연동

각 플러그인의 `codex/` 폴더에 Codex 전용 지시서가 있다:

| 플러그인 | Codex 지시서 경로 |
|---------|----------------|
| exec_orch | `plugins/exec_orch/codex/instructions.md` |
| exec_persona | `plugins/exec_persona/codex/instructions.md` |
| design_ppt | `plugins/design_ppt/codex/instructions.md` |
| review_qa | `plugins/review_qa/codex/instructions.md` |

---

## MCP 설정
`.codex/config.toml` 참조.
플러그인별 추가 MCP는 해당 `codex/instructions.md` 에 설명됨.

---

## 완료 보고

태스크 완료 시 아래 형식으로 `.claude/tasks/done/TASK-ID-report.md` 생성:

```markdown
## 완료 보고
- Task: [태스크 ID]
- 수정 파일: [목록]
- 결과: [요약]
- 다음: Claude 검토 필요
```

---

## Standalone 모드 (Claude 없이 Codex 단독 사용)

`install_codex` 로 셋업한 환경에서는 Claude orchestration 없이 Codex 만으로 작업.
**task 파일 수동 편집 필요 없음 — 자연어 한 줄로 끝.**

### 특징

1. **즉시 시작** — API 키만 설정하면 `codex-go` 명령 사용 가능
2. **자동 로깅** — 모든 호출이 `.codex/usage.jsonl` 에 기록 (비용 추적)
3. **예산 관리** — `CODEX_DAILY_LIMIT_USD` 설정으로 일일 한도 경고 가능
4. **간단 구조** — `.codex/` 폴더만 필요, `.claude/` 의존 없음
5. **언제든 업그레이드** — `install.bat <폴더>` 로 Full 모드 전환 가능

### 사용법

**A. 자연어 한 줄 (권장)**
```bash
cd C:\myproject
codex-go "회원가입 페이지 만들어줘"
codex-go "이 모듈 리팩토링 — DRY 원칙"
codex-go                              # 대화 모드
```

**B. 배치 처리 — 여러 작업 한꺼번에**
```bash
# Codex 에게 task 파일 생성 요청
codex-go "다음 3개를 tasks/task-001~003.md 로 정리해줘:
  1. 로그인 페이지
  2. 회원가입 페이지
  3. 비밀번호 리셋"

# 큐 자동 처리
codex-a --auto
```

### API 키 설정

```bash
# 1. 환경변수 (권장)
setx OPENAI_API_KEY "sk-..."

# 2. .env 파일
copy .env.example .env
# [편집기로 OPENAI_API_KEY 값 입력]

# 3. 명령줄
set OPENAI_API_KEY=sk-... && codex-go "작업"
```

### 선택 설정

```env
# .env 또는 환경변수로 설정
CODEX_DAILY_LIMIT_USD=10        # 일일 예산 상한
CODEX_MODEL=gpt-4               # 모델 선택 (기본값: gpt-4)
```

### 사용량 추적

```bash
# 사용량 확인
type .codex\usage.jsonl

# 형식: JSON Lines (JSONL)
# 예: {"ts": "2026-04-24T10:30:00Z", "model": "gpt-4", "in": 150, "out": 420, "cost_usd": 0.015}
```

### 비용 예시 (GPT-4)

| 작업 | 입력 토큰 | 출력 토큰 | 비용 |
|------|---------|---------|------|
| 간단 코드 리뷰 | ~300 | ~500 | $0.005 |
| 페이지 구현 | ~500 | ~1,500 | $0.025 |
| 모듈 리팩토링 | ~1,000 | ~2,000 | $0.040 |

일일 예산 `$10` 이면 중형 작업 200~250개 처리 가능.

### 코드 규칙 (필수)

위의 "코드 규칙" 섹션과 동일하게 적용 (orchestration 여부 무관).

---
