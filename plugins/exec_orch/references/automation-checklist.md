# 자동화 의무 체크리스트 — 매 커밋·매 세션·매일·매주·매월

> **목적**: Claude가 자동으로 해야 할 모든 것 한눈에. 누락 방지.

---

## A. 매 커밋 시 (기능 추가/변경할 때마다)

### 문서 갱신
| # | 파일 | 갱신 내용 | hook 강제 |
|---|------|----------|----------|
| 1 | `guide.txt` | 관련 섹션 (§6·§12·§15·§17) | ✅ check-infra-sync.sh |
| 2 | `CLAUDE.md` | AUTO-STATS 라인 (plugins·rules·hooks·scripts 수) | ❌ → 자동화 필요 |
| 3 | `setup/BUILD.md` | 모듈 설명표 | ❌ |
| 4 | `.claude-plugin/marketplace.json` | 플러그인 목록 | ❌ |
| 5 | 해당 `plugins/<name>/README.md` | 커맨드/스킬 목록 | ❌ |
| 6 | 해당 `plugins/<name>/plugin.json` | version, updated 날짜 | ❌ |

### 인프라 등록
| # | 파일 | 갱신 내용 | hook 강제 |
|---|------|----------|----------|
| 7 | `.claude/settings.json` | 신규 hook 등록 | ❌ |
| 8 | `setup/modules/01-core.bat` | sanity check 목록 | ❌ |
| 9 | `setup/setup.bat` | 모듈 호출 순서 (새 모듈 시) | ❌ |

### 검증
| # | 검증 | 도구 | hook 강제 |
|---|------|------|----------|
| 10 | sync 정합성 | `sync-plugins.sh` | ✅ 자동 실행 |
| 11 | 스키마 검증 | `validate-plugin-schema.py` | ❌ |
| 12 | 하드코딩 경로 | `check-hardcoded-paths.sh` | ✅ PreToolUse |
| 13 | 미등록 hook 없는지 | plugins hooks vs settings.json 비교 | ❌ |

---

## B. 매 세션 시작 시 (SessionStart)

| # | 작업 | 도구 | 현재 상태 |
|---|------|------|----------|
| 1 | 스택 감지 + 폴더 생성 | hook-00-init.sh | ✅ |
| 2 | external watchdog 등록 | install-external-watchdog.sh | ✅ |
| 3 | outbox 처리 | process-outbox.sh | ✅ |
| 4 | 워커 heartbeat 체크 | check-workers.sh | ✅ |
| 5 | 오염 파일 정리 | cleanup-pollution.sh | ✅ |
| 6 | sync drift 점검 | check-sync-drift.sh | ✅ |
| 7 | 보안 도구 설치 | install-sec-tools.sh | ✅ (async) |
| 8 | 공식 신기능 체크 | check-official-features.sh | ✅ (async) |
| 9 | **MCP 연결 점검** | check-mcp-health.sh | ✅ (async) |
| 10 | 오프라인 시스템 감지 | install-on-session-start.sh | ✅ (async) |
| 11 | 메모리 가드 | memory_guard.sh | ✅ (async) |
| 12 | **session-snapshot 복구 제안** | context-cache 확인 | ❌ → Claude 능동 |
| 13 | **레퍼런스 갭 체크** | 최신 도구 누락 확인 | ❌ → Claude 능동 |
| 14 | **안 지켜진 규칙 리마인드** | 메모리 기반 자가 점검 | ❌ → Claude 능동 |

---

## C. 매일 (24시간마다)

| # | 작업 | 방법 | 현재 상태 |
|---|------|------|----------|
| 1 | **레퍼런스/툴킷 갭 점검** | 웹 검색으로 새 도구 확인 | ❌ 메모리만 |
| 2 | **MCP 서버 전체 헬스체크** | claude mcp list | ✅ SessionStart |
| 3 | **미커밋 변경 경고** | git status -s | ❌ |
| 4 | **stale task 정리** | .claude/tasks/ 30일+ | ✅ cleanup-pollution.sh |
| 5 | **로그 크기 관리** | .claude/logs/ 14일+ | ✅ cleanup-pollution.sh |
| 6 | **auto-dev 실행** | Task Scheduler 4h 간격 | ✅ Module 15 |
| 7 | **orca.db 백업** | SQLite 스냅샷 | ❌ |
| 8 | **의존성 취약점 스캔** | pip audit / npm audit | ❌ |

---

## D. 매주

| # | 작업 | 방법 | 현재 상태 |
|---|------|------|----------|
| 1 | sync-plugins.sh --check | 드리프트·orphan 점검 | ✅ (수동) |
| 2 | validate-plugin-schema.py --strict | 스키마 전수 검증 | ✅ (수동) |
| 3 | **전체 hook 미등록 점검** | plugins hooks vs settings.json | ❌ |
| 4 | **전체 플러그인 README 현행화 점검** | 빈 README, 오래된 내용 | ❌ |
| 5 | **git log 분석 → 누락 문서 감지** | 코드 변경 있는데 문서 변경 없는 커밋 | ❌ |

---

## E. 매월

| # | 작업 | 방법 | 현재 상태 |
|---|------|------|----------|
| 1 | CLAUDE.md 갱신 | 500줄 이하 유지 + 최신화 | ✅ (수동) |
| 2 | guide.txt 전체 리뷰 | 오래된 섹션 제거/갱신 | ❌ |
| 3 | 로드맵 리뷰 | Phase 이동 여부 | ❌ |
| 4 | **레퍼런스 18개 전체 최신화** | 버전 업데이트, 신규 도구 | ❌ |
| 5 | **메모리 정리** | 오래된 메모리 제거/갱신 | ❌ |
| 6 | **setup 테스트** | 새 폴더에 install 후 검증 | ❌ |

---

## F. 현재 자동화 현황

| 카테고리 | 총 항목 | 자동화 | 수동 | 미구현 |
|---------|--------|--------|------|--------|
| A. 매 커밋 | 13 | 3 | 0 | **10** |
| B. 매 세션 | 14 | 11 | 0 | **3** |
| C. 매일 | 8 | 4 | 0 | **4** |
| D. 매주 | 5 | 2 | 0 | **3** |
| E. 매월 | 6 | 1 | 0 | **5** |
| **합계** | **46** | **21** | **0** | **25** |

→ **자동화율 46%** (21/46). 25개 미구현.
