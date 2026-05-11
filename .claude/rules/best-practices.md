# Best Practices — Claude Code 프로젝트

> **출처**: docs/upgrade § 이미지 6 (Brij Kishore Pandey)

## 반복 개발 (Iterative Development)
- 작게 시작, 확인 후 확장 (no big-bang)
- 실패 빠르게 (fail fast) — 드라이런 활용
- Git 워크플로우 (feature branch → PR → merge)

## 명확한 Git 흐름
- commit 메시지: `feat/fix/refactor/docs/chore` 접두사
- PR 단위 작게, 리뷰 가능한 수준
- 커밋 전 검증: `validate-plugin-schema.py` + `check-agents`

## 모듈식 설계
- 단일 책임 (한 플러그인 = 한 목적)
- 플러그인 간 느슨한 결합 (dependencies 명시적)
- 공유 로직 → `.claude/rules/`, 공통 헬퍼 → `scripts/common.sh`

## 정기 테스트·감사
- 주 1회: `bash .claude/scripts/sync-plugins.sh --check` (드리프트·orphan)
- 주 1회: `python .claude/scripts/validate-plugin-schema.py --strict`
- 월 1회: CLAUDE.md + guide.txt 갱신
- 월 1회: 로드맵 리뷰 (Phase 이동 여부)

## Extended Thinking 활용 (Claude 4.x)
- 복잡한 아키텍처 결정 시: 긴 추론 모드 활성화
- 트레이드오프 비교 시: Extended Thinking 로 깊이 있는 분석
- 단순 구현 시: 빠른 모드 (Sonnet)

## 1M Token Window 활용
- 대용량 리팩토링: 프로젝트 전체 컨텍스트 로드 가능
- 코드리뷰: 여러 파일 동시 비교
- 단순 작업: 굳이 1M 불필요 — 비용 효율 고려

## Artifacts / Skills / Plugins / Commands 구분

| 형태 | 용도 | 예시 |
|---|---|---|
| **Artifact** | 한 번 생성되는 산출물 | PPT, 코드 파일, HTML |
| **Skill** | 자동 활성화되는 추론 로직 | `skill-rag-patterns`, `skill-arch-selector` |
| **Command** | 사용자가 명시적 호출 | `/check`, `/excel-make` |
| **Plugin** | 위 3가지를 묶은 단위 | `plugins/ai_rag/`, `plugins/bundles_cowork/` |

## 시크릿 관리
- `.env` 로드 (`scripts/common.sh load_env`)
- 절대 하드코딩 금지
- `.env` 는 gitignore

## 하드 경로 금지 (cross-machine 배포 필수)

orchestration_v1 은 **여러 머신·여러 사용자에서 동작**해야 함. 사용자명·Python 버전·OS 절대경로 박지 말 것.

### 금지 예시 → 대체

| 금지 | 대체 |
|---|---|
| `C:\Users\ja205\AppData\...` | `os.environ['TEMP']` 또는 `tempfile.gettempdir()` |
| `/home/ja205/...` | `Path.home()` 또는 `$HOME` |
| `C:\...\Python314\python.exe` | `shutil.which('python')` / `where python` 동적 검색 |
| `DESKTOP-AR8DB38` | `socket.gethostname()` / `%COMPUTERNAME%` |

### Task Scheduler / cron 패턴
스케줄러는 사용자 PATH 못 받으므로 절대 경로 필요 → **wrapper .bat / .sh 도입**.
- 스케줄러에는 wrapper 경로만 (프로젝트 내) 박음
- wrapper 내부에서 `where python` 등으로 런타임 검색
- 도구 위치 바뀌어도 wrapper 가 흡수 — 재등록 불필요

예: `.claude/scripts/run-external-watchdog.bat` 가 wrapper. schtasks 에는 이것만 등록.

## 농땡이 회피 (사용자 지시 처리 5단계)
사용자가 작업 지시 시 다음 5단계 완주 — 임의 축소 금지.

1. **전수조사** — 인접 시스템·전역까지 모든 위치 훑기 (단일 후보로 결론 X)
2. **분석** — 내용 직접 검증 (`diff`/`md5sum`/본문 읽기). 파일명만 보고 판정 X
3. **실행** — 발견한 누락·문제를 코드로 수정
4. **확인** — smoke test / dry-run / 로그 점검으로 동작 검증
5. **보고** — 표·목록으로 결과 + 남은 결정사항 명시

상세: `.claude/rules/failure-mode.md` § 농땡이 안티패턴

## Zero-touch 자동화 (사용자 액션 요구 금지)

새 기능·셋업·설치는 **사용자 명령 없이** 동작해야 함.

### 자동화 대상
- 패키지/MCP 설치, Task Scheduler 등록, 워커 spawn, sync, 마이그레이션
- "사용자가 .bat 한 번만 실행" 같은 안내는 SessionStart hook 으로 흡수

### 알림 허용 — 크리티컬 5가지만
1. 시크릿 노출 (PAT/키 commit·push 직전)
2. 데이터 손실 (대량 삭제·force push 등 비가역)
3. 보안 위협 (외부 유출, 권한 상승)
4. 비용 폭증 (일일 budget 80% 초과 또는 단발 $10+)
5. 시스템 손상 (OS 설정·레지스트리·계정 권한)

위 외 모든 진행은 **로그 파일에만** (.claude/logs/, .claude/state/).

### 금기
- "사용자 결정 필요" 빈발 — 가장 합리적 옵션 자동 선택 후 결과 보고
- "한 번만 실행해 주세요" — hook 으로 자동화 후 idempotent 보장

## 참조

- `.claude/rules/plugin-structure.md` — 플러그인 구조
- `.claude/rules/sync-workflow.md` — sync 플로우
- `docs/architecture-patterns.md` — 설계 원칙 9가지
