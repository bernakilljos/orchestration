# 자동 최적화 룰 (Auto Optimization)

> **근거**: 2026-09-02 사용자 지적 — "최적화가 자동으로 안 됨".
> **이유**: 이미지·프롬프트·DB·캐시·로그가 시간 지나면 자동 정리·압축·최적화되어야 실전 운영.

## 절대 룰

**모든 최적화는 자동 hook 또는 스케줄 실행 · 사용자 수동 요청 X.**

## 최적화 6 축

| # | 축 | 방법 | 발동 |
|---|---|---|---|
| 1 | **프롬프트 압축** | Headroom (60~95% 절감) · `ANTHROPIC_BASE_URL=http://127.0.0.1:8787` | 다음 세션부터 · autostart 자동 |
| 2 | **컨텍스트 축소** | `lib/context_reducer.py` 활용 · CLAUDE.md 500줄 이하 유지 원칙 | 편집 시 자동 |
| 3 | **DB 자동 vacuum·retention** | `orca.db` VACUUM + `conversations` 30일 초과 압축 → session_summary 만 남김 | 매일 03:00 (Task Scheduler) |
| 4 | **이미지 자동 압축** | PNG → WebP · 대용량 이미지 자동 리사이즈 | 산출물 생성 후 자동 |
| 5 | **로그·캐시 자동 정리** | `cleanup-pollution.sh` 이미 실행 · 신규 파일 종류 추가 | SessionStart 자동 (기존) |
| 6 | **Hook 프로파일링** | 느린 hook 감지 · SessionStart 시간 측정 · 500ms+ 경고 | SessionEnd 자동 리포트 |

## 자동 실행 매트릭스

| 시점 | 자동 최적화 | 스크립트 |
|---|---|---|
| **SessionStart** | 로그·캐시 정리 · MCP proxy 시작 · 컨텍스트 로드 | 기존 hook 재활용 |
| **PostToolUse Write** | 이미지 파일 자동 압축 (신규 파일 감지) | `.claude/scripts/auto-optimize-image.py` |
| **Stop / SessionEnd** | Hook 실행 시간 프로파일 · session_summary 저장 | 기존 확장 |
| **매일 03:00 (Task Scheduler)** | DB VACUUM + retention 정리 + 백업 | `.claude/scripts/nightly-optimize.py` |
| **주 1회 (일요일 04:00)** | 중복 파일 감지 · 유사 파일 통합 제안 | `.claude/scripts/weekly-audit.py` |

## Retention & 압축 정책 (conversation-history + production-file-management 통합)

| 대상 | 정리 방식 |
|---|---|
| `conversations` (30일 초과) | content 삭제 · content_hash·tokens 만 유지 → session_summary 로 요약 통합 |
| `orca.db` (매일) | `VACUUM` + `ANALYZE` |
| `orca.db.bak.*` | 최근 30일 rolling 유지 |
| `.claude/logs/*.log` (14일 초과) | 자동 삭제 (cleanup-pollution 기존) |
| `docs/screens/**/*.png` (30일 초과 · 미참조) | archive/ 로 이동 |
| `outputs/**/*` (30일 초과) | archive/ 로 이동 |
| `.claude/tasks/done/*` (30일 초과) | 자동 삭제 (기존) |
| `image-cache/*` (7일 초과) | 자동 삭제 (기존) |

## 프롬프트 최적화 (Headroom 활용)

- 다음 세션부터 `mcp-autostart.sh` 가 Headroom proxy 시작
- 사용자가 `ANTHROPIC_BASE_URL=http://127.0.0.1:8787` env 세팅 시 자동 60~95% 압축
- MCP 도구 (`headroom_compress`·`retrieve`·`stats`) 상시 활용
- Anthropic prompt caching 90% 절감과 병행

## 컨텍스트 최적화

- CLAUDE.md 500줄 이하 유지 (Brij 5 rules)
- `lib/context_reducer.py` 자동 축소
- 룰 파일 참조 중심 (내용 중복 금지)
- claude-mem 2번째 세션부터 memory injection (자동 관측 축)

## Hook 프로파일링

`.claude/scripts/hook-profile.py`:
- SessionStart 시 각 hook 실행 시간 측정
- 500ms+ 초과 → warning 로그
- 5s+ 초과 → 알림 (systemMessage)
- 통계 저장: `orca.db.hook_profile` (예정)

## 이미지 자동 최적화

`.claude/scripts/auto-optimize-image.py`:
- 신규 PNG/JPG 감지 (PostToolUse Write hook)
- 3MB 초과 시 자동 리사이즈 (max 2000×2000)
- PNG → WebP 변환 옵션 (선택 · 사용자 명시 시)
- 원본 `.bak` 유지

## 야간 최적화 (매일 03:00)

`.claude/scripts/nightly-optimize.py`:
```text
1. orca.db 백업 (.bak.YYYYMMDD)
2. conversations 30일 초과 압축
3. orca.db VACUUM + ANALYZE
4. 로그 14일 초과 삭제
5. archive/ 30일 초과 완전 삭제 (사용자 명시 산출물은 예외)
6. image-cache 7일 초과 삭제
7. hook profile 리포트 생성
8. 다음날 SessionStart 알림 준비
```

Task Scheduler 등록: `setup/modules/16-mcp-headroom-claude-mem.bat` 확장 (또는 신규 module).

## 주간 감사 (주 1회 일요일 04:00)

`.claude/scripts/weekly-audit.py`:
- 중복 파일 감지 (md5)
- 유사 파일 (Levenshtein)
- 순수 숫자 파일 리스트 (rename 제안)
- 산출물 현행화 미준수 리스트
- 리포트: `.claude/logs/weekly-audit-YYYYMMDD.md`

## 금지

1. 최적화를 사용자에게 요청 X (Zero-touch)
2. 백업 없이 압축·삭제 X (rollback 가능해야)
3. 실전 산출물 자동 삭제 X (archive 만)
4. hook 실행 시간 무시 X (500ms+ 프로파일 필수)
5. 최적화 실패 → 크리티컬 5 아닌 이상 조용 (Zero-touch)

## 관련

- `.claude/rules/production-file-management.md` (2026-09-02 · retention 통합)
- `.claude/rules/conversation-history.md` (2026-09-02 · DB retention)
- `.claude/rules/cleanup-policy.md` (기존 · 정리 정책)
- `.claude/rules/mcp-integration.md` (Headroom 활용)
- `.claude/scripts/cleanup-pollution.sh` (기존)
- `.claude/scripts/nightly-optimize.py` (신설 예정)
- `.claude/scripts/weekly-audit.py` (신설 예정)
- `.claude/scripts/auto-optimize-image.py` (신설 예정)
