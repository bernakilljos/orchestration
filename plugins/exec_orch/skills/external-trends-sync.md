---
name: external-trends-sync
description: 매시간 외부 프롬프트 엔지니어링 트렌드 (Claude doc · promptingguide · Reddit · HN) 자동 fetch, 변경 발견 시 task-instruction + git branch + PR 자동 생성. "최신 적용", "트렌드", "external sync", "Claude doc 변경" 키워드 활성.
---

# Skill: External Trends Sync (매시간 자동)

> **목적**: kit 의 prompt-techniques skill 과 룰을 외부 트렌드 (Anthropic 공식 doc · DAIR.AI promptingguide · Reddit r/PromptEngineering · HackerNews) 와 항상 동기화.
> **트리거**: Windows Task Scheduler 매시간 17분 (`:00`/`:30` 회피) OR CronCreate durable.

## 1. 왜

12 프롬프팅 기법 (`prompt-techniques.md`) 만 정적으로 두면 외부 새 기법 (예: "Constitutional AI prompting", "Reflexion") 놓침. 매시간 변경 감지 → 자동 task → PR → Claude 가 review 만 하면 됨.

## 2. 소스 (인스타 fetch 불가 → 공개 소스로 대체)

| 소스 | URL | 캐시 키 |
|---|---|---|
| Anthropic Claude Code release notes | `docs.anthropic.com/en/release-notes/claude-code` | `anthropic-release-notes` |
| Anthropic Prompting overview | `docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview` | `anthropic-docs-prompting` |
| DAIR.AI Prompting Guide sitemap | `promptingguide.ai/sitemap.xml` | `promptingguide-sitemap` |
| Reddit r/PromptEngineering RSS | `reddit.com/r/PromptEngineering/.rss` | `reddit-prompt-engineering` |
| HackerNews search RSS | `hnrss.org/newest?q=prompt+engineering` | `hn-prompt-engineering` |

> **Instagram·X·LinkedIn 공식 트렌드 페이지는 인증 게이트** — WebFetch / curl 불가. 위 5개로 대체.

## 3. 흐름

```sql
[Task Scheduler 매시간] 
  → external-trends-sync.bat (wrapper)
  → external-trends-sync.sh
    1. 5개 소스 curl + sha256
    2. .claude/state/external-trends/<key>.sha 비교
    3. 변경 → diff 추출 + raw 캐시 갱신
    4. 변경 있음:
       a. task-instruction.md 자동 생성 (.claude/tasks/task-external-trends-YYYY-MM-DD_HHMM.md)
       b. git branch auto/external-trends-... 생성
       c. git commit
       d. git push -u origin <branch>
       e. gh pr create (gh 있을 때만)
    5. main 복귀
  → log: .claude/logs/external-trends.log
```

## 4. 설치

### Windows (영속, 7일 X)
```powershell
powershell -ExecutionPolicy Bypass -File .claude\scripts\register-external-trends-task.ps1
# 매시간 17분에 자동 실행 등록
```

### CronCreate (이 세션 한정, 7일 후 expire)
```text
CronCreate(cron="17 * * * *", prompt="외부 트렌드 sync 체크: bash .claude/scripts/external-trends-sync.sh — 변경 있으면 결과 보고", durable=true)
```

### 제거
```powershell
powershell -ExecutionPolicy Bypass -File .claude\scripts\register-external-trends-task.ps1 -Remove
```

## 5. PR 본문 표준

```markdown
## 외부 트렌드 변경 감지 — YYYY-MM-DD HH:MM:SS

다음 소스에서 변경:
- `anthropic-release-notes`
- `promptingguide-sitemap`

Task: `.claude/tasks/task-external-trends-YYYY-MM-DD_HHMM.md`

## 적용 가이드
- 12 기법 매트릭스 (prompt-techniques.md) 와 비교
- 신규 기법 → WHAT/WHEN/HOW 한 줄씩 추가
- 보강이면 example 갱신
```

## 6. Claude 가 review 시 행동

매시간 PR 알림 받으면:

1. task-instruction.md 의 § 7 "변경 디테일" 읽기
2. 12 기법 매트릭스와 비교
3. 신규 기법이면:
   - prompt-techniques.md § 1 표에 행 추가 (WHAT/WHEN/HOW)
   - 라우팅 별 기본 적용 표에 매핑
4. 보강이면:
   - 기존 행의 예시·트리거 갱신
5. 무관 (예: 단순 typo, copy edit) 면 close

## 7. 비용 안전

| 항목 | 안전 장치 |
|---|---|
| 매시간 curl 5회 | 정적 RSS — 비용 0 |
| 변경 없으면 PR 0 | sha 캐시 비교 |
| PR 양 | 변경 있을 때만 (보통 일 1~3 개) |
| 7일 limit (CronCreate) | Task Scheduler 등록 시 영속 |

## 8. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `[skip] fetch failed` | 네트워크·robots.txt | UA 헤더 확인. 다음 사이클에서 재시도. |
| `gh pr create failed` | gh CLI 없음·인증 안 됨 | `gh auth login` 후 다시. task 파일은 남음. |
| Task Scheduler 안 뜸 | wrapper 못 찾음 | 등록 시 admin 권한 확인. ScheduledTasks GUI 검토. |
| 변경 너무 자주 | 트래픽 많은 RSS | source 빈도 조절 (스크립트 SOURCES 배열 편집) |

## 9. 금지

- 새 소스 추가 시 인증 게이트 사이트 (Instagram·X·LinkedIn) — 무력
- task-instruction.md 자동 생성 후 자동 merge — 사용자 review 의무
- diff 큰 PR 자동 close — 매시간 누적 의도
- 변경 없는 sha 도 PR 생성 — 노이즈

## 10. 참조

- `plugins/exec_orch/skills/prompt-techniques.md` — 12 기법 매트릭스
- `plugins/exec_orch/codex/task-instruction-template.md` — task 표준
- `.claude/scripts/external-trends-sync.sh` — handler
- `.claude/scripts/register-external-trends-task.ps1` — 등록 wrapper
- `.claude/state/external-trends/` — sha 캐시 + raw + change md
- `.claude/logs/external-trends.log` — 매시간 실행 로그
