# 세션 대화 히스토리 DB 룰

> **근거**: 2026-09-02 사용자 지적 — "세션 끊기면 다시 지시할 때 못 알아먹음. 메모리 부족. **히스토리는 DB 로 관리**".
> **이유**: 명시 memory (`memory/*.md`) 는 도메인 자산 · 세션 대화는 자동 축적 필요. 파일 기반 스냅샷 (`context-cache/session-snapshot.md`) 은 최근 1건만 · 다중 세션 조회 X.

## 절대 룰

**Claude Code 세션 대화 = `orca.db.conversations` · 세션 요약 = `orca.db.session_summary` · 새 세션 시작 시 최근 3 세션 자동 로드.**

## 저장 축 분리

| 축 | 저장소 | 대상 |
|---|---|---|
| **명시 memory (도메인 자산)** | `~/.claude/projects/<proj>/memory/*.md` + `MEMORY.md` 인덱스 | feedback·project·reference·user · **사용자 명시 등재** |
| **세션 대화 히스토리** | `orca.db.conversations` (자동) · `orca.db.session_summary` (자동) | 매 UserPrompt·Stop·SessionEnd · **자동 캡처** |
| **Codex/Gemini CLI 작업 히스토리** | `orca.db.tasks` + `activations` + `metrics` (기존) | task-instruction 실행 이력 |
| **파일 스냅샷** | `.claude/context-cache/session-snapshot.md` | 최근 1건 · exec_session_guard 관리 |
| **claude-mem (병행 자동 관측)** | `~/.claude-mem/` (SQLite + Chroma) · plugin marketplace | Observation 자동 분류·벡터 검색 (2026-09-02 통합) |

## DB 스키마

```sql
CREATE TABLE conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  turn INTEGER NOT NULL,
  role TEXT CHECK(role IN ('user','assistant','tool','system')) NOT NULL,
  content TEXT NOT NULL,      -- 최대 8000 chars
  content_hash TEXT,          -- SHA-256 첫 16 chars
  tokens INTEGER,             -- rough estimate
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  tags TEXT
);

CREATE TABLE session_summary (
  session_id TEXT PRIMARY KEY,
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  turns INTEGER,
  summary TEXT,               -- 최대 4000 chars · 최근 20 turns 압축
  key_decisions TEXT,         -- 최근 1시간 decisions 요약
  files_touched TEXT,
  tokens_total INTEGER,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Hook 등록 (자동 발동)

| 이벤트 | Hook | 동작 |
|---|---|---|
| **UserPromptSubmit** | `.claude/hooks/save-user-prompt.sh` | 사용자 프롬프트 → `conversations` INSERT (role=user) |
| **Stop** | `.claude/hooks/save-session-summary.sh` | 최근 20 turns + 결정 → `session_summary` UPSERT |
| **SessionEnd** | `.claude/hooks/save-session-summary.sh` | 위와 동일 (최종 저장) |
| **SessionStart** | `.claude/hooks/load-recent-conversations.sh` | 최근 3 세션 요약 → stdout (systemMessage 자동 주입) |

## 공통 라이브러리

`.claude/scripts/lib/conversation_logger.py` — 3 함수:
- `save_turn(role, content, tags)` — 한 turn 저장
- `save_session_summary(summary, key_decisions, files)` — 세션 요약 UPSERT
- `load_recent_context(n_sessions=3, max_chars=3000)` — SessionStart 주입용 markdown

CLI 사용:
```bash
echo "hello" | python conversation_logger.py save-turn user
echo '{"summary":"...","key_decisions":"..."}' | python conversation_logger.py save-summary
python conversation_logger.py load 3
```

## Claude/Codex/Gemini CLI 별 히스토리

| CLI | 대화 히스토리 저장 |
|---|---|
| **Claude Code** | `conversations` + `session_summary` (자동 hook) |
| **Codex CLI** | `orca.db.tasks` (task-instruction) + `activations` + `metrics` (기존 · 확장 불필요) |
| **Gemini CLI** | 위와 동일 |

**명령어 memory** = 각 CLI 의 도메인 지시 (rule·convention) 는 `memory/*.md` 유지.
**히스토리** = 세션 대화·실행 이력은 `orca.db` 자동 저장.

## Retention 정책

- `conversations`: 최근 30일 유지 · 이후 압축 후 `session_summary` 만 남김
- `session_summary`: 무기한 유지 (크기 작음)
- 압축·정리: `.claude/scripts/cleanup-pollution.sh` 확장 (예정)

## PII·시크릿 자동 마스킹

- content 저장 전 정규식 마스킹 (예정 · 개보법·시크릿 정책 정합)
- 지금은 단순 저장 · content[:8000] 로 truncate

## claude-mem 병행 원칙

- claude-mem = 벡터 검색·Observation 자동 분류
- 우리 conversations = 단순 순차 로그·session_id·turn 기반 정확 재현
- 서로 다른 축 · 병행 · 충돌 없음

## 금지

1. `memory/*.md` 에 세션 대화 자동 등재 X (도메인 자산 오염)
2. `conversations` 에 명시 memory·rule 저장 X (역할 반대)
3. content 8000 chars 이상 저장 시도 X (SQLite 쓰기 부하)
4. PII·시크릿 마스킹 없이 저장 (Retention 정책 확립 후)

## 관련

- `.claude/scripts/lib/conversation_logger.py` (구현)
- `.claude/hooks/save-user-prompt.sh` (UserPromptSubmit)
- `.claude/hooks/save-session-summary.sh` (Stop/SessionEnd)
- `.claude/hooks/load-recent-conversations.sh` (SessionStart)
- `.claude/rules/mcp-integration.md` (claude-mem 병행)
- CLAUDE.md § 3.1 Session Start (히스토리 로드 표기)
