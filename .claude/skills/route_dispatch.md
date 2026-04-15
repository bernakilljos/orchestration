# route_dispatch — AI 라우팅 · 판단

> **분류:** `route_` (라우팅/판단 계열)
> **통합 레거시:** `vibe-loop` command, CLAUDE.md `Multi-Agent Auto-Detection`
> **참조 plugin:** `.claude-plugin/plugin.json` → `entry_points.task_route`

## 목적
태스크 규모와 가용 AI 도구를 자동 감지해 최적 실행 경로를 결정한다.
사용자에게 묻지 않고 자동으로 결정한다.

---

## Step 1: 가용 AI 감지

```
1. codex-auto 가용 확인:
     where codex-auto 2>nul && echo YES || echo NO
     CODEX_AVAILABLE = true / false

2. gemini-auto 가용 확인:
     where gemini-auto 2>nul && echo YES || echo NO
     GEMINI_AVAILABLE = true / false
```

---

## Step 2: 태스크 규모 판단

| 규모 | 판단 기준 |
|------|---------|
| `LARGE`  | 예상 코드 500줄+, CRUD 전체, 새 기능 |
| `VERIFY` | 검증·문서·다이어그램·리서치 요청 |
| `SMALL`  | 500줄 미만 구현, 버그 수정, 단순 수정 |

---

## Step 3: 라우팅 결정표

| CODEX | GEMINI | 태스크 | 실행 경로 |
|-------|--------|--------|---------|
| ✅ | ✅ | LARGE  | `task-instruction.md` → `codex-auto` → Claude 보완 → `gemini-auto` |
| ✅ | ✅ | VERIFY | `task-instruction.md` → `gemini-auto --verify` |
| ✅ | ✅ | SMALL  | Claude 직접 구현 → `gemini-auto --verify` |
| ✅ | ❌ | LARGE  | `task-instruction.md` → `codex-auto` → Claude 검증 |
| ✅ | ❌ | SMALL  | Claude 직접 구현 (codex-auto 필요 시 선택) |
| ❌ | ✅ | VERIFY | `task-instruction.md` → `gemini-auto` |
| ❌ | ❌ | ANY    | Claude 직접 구현 + 검증 (`task-instruction.md` 불필요) |

---

## Vibe Loop 모드 (CODEX + GEMINI 모두 가용)

```
전제: .claude/tasks/stop 파일 없음

1. stop 파일 제거 (있으면): del .claude\tasks\stop 2>nul

2. 사용자 안내:
   "codex-auto + gemini-auto 루프를 시작합니다.
    터미널 두 개를 열어 각각 실행하세요:"
   
   Terminal 1: codex-auto    ← 구현 워커
   Terminal 2: gemini-auto   ← 검증 워커

3. 중단 방법 안내:
   /loop-stop 커맨드 실행
   또는 .claude/tasks/stop 파일 생성
```

---

## 단독 모드 (CODEX만 가용)

```
- codex-auto 1  ← 단일 워커 실행
- Claude가 gemini 역할 대행 (검증 + 문서화)
```

---

## 직접 모드 (둘 다 없음)

```
- Claude가 구현 + 검증 모두 직접 처리
- task-instruction.md 작성 불필요
- 즉시 구현 시작
```

---

## task-instruction.md 작성 조건

| 조건 | task-instruction.md 필요 여부 |
|------|---------------------------|
| CODEX_AVAILABLE AND LARGE | ✅ 필요 |
| GEMINI_AVAILABLE AND VERIFY | ✅ 필요 |
| Claude 직접 (SMALL 또는 둘 다 없음) | ❌ 불필요 |

---

## 금지 사항

- 사용자에게 "어떤 AI 사용할까요?" 묻지 않는다
- codex-auto 없이 task-instruction.md만 작성하지 않는다
- gemini 리뷰 의견을 Claude 승인 없이 자동 적용하지 않는다
