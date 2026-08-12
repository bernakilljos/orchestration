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

## Template kit 원칙 (orchestration_v1 = 공통 배포 kit)

이 프로젝트는 **install/setup 으로 다른 폴더에 배포**되는 공통 kit. 모든 변경은 다른 머신·다른 사용자에서도 동작해야 함.

### 새 기능·파일 추가 시 체크리스트
| 항목 | 위치 |
|---|---|
| 스크립트·hook | `.claude/scripts/` 또는 `plugins/<name>/` (target 자동 복사) |
| 글로벌 설정 (`~/.claude/`) | `setup/templates/` + `setup/modules/03-settings.bat` 배포 로직 |
| Task Scheduler / cron | `setup/modules/09-finalize.bat` 등록 호출 추가 |
| 사용자 가이드 | `guide.txt` 현행화 |

### 금기
- `~/.claude/` 직접 손대지 마 (install 결과물이어야)
- 다른 프로젝트 폴더 (ICM·IFRS·calc 등) 직접 수정 X → install 재배포
- 하드 경로 박지 마 (아래 § 하드 경로 금지)
- 사용자 액션 요구 X (§ Zero-touch 자동화)

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

## 전수조사 의무 (5단계 완주) (사용자 지시 처리 5단계)
사용자가 작업 지시 시 다음 5단계 완주 — 임의 축소 금지.

1. **전수조사** — 인접 시스템·전역까지 모든 위치 훑기 (단일 후보로 결론 X)
2. **분석** — 내용 직접 검증 (`diff`/`md5sum`/본문 읽기). 파일명만 보고 판정 X
3. **실행** — 발견한 누락·문제를 코드로 수정
4. **확인** — smoke test / dry-run / 로그 점검으로 동작 검증
5. **보고** — 표·목록으로 결과 + 남은 결정사항 명시

상세: `.claude/rules/failure-mode.md` § 전수조사 위반 안티패턴

## 검증 후 보고 — "수정했습니다" 만 X

수정·빌드 후 반드시 검증 도구 실행·PASS 확인 후 보고.

### 의무 흐름
1. 수정·빌드
2. 검증 도구 자동 발동 (PNG=verify-image-fit, docx=verify-docx-structure, pptx=verify-ppt-overflow)
3. PASS 확인
4. 보고
5. FAIL → 사용자 알리지 않고 즉시 재수정 (max 3회)
6. 3회 후에도 FAIL → 솔직히 보고 + 사용자 결정

### 금지
- 검증 X 하고 "완료" 보고 = 위반
- 사용자가 결과 보고 짚어줘야 알게 됨 = 전수조사 위반
- 검증 FAIL 무시하고 다음 작업 = 위반

상세 매트릭스: `feedback_verify_before_report.md`

## 자율 Plan — Auto-Planner 의무

사용자 요청 받으면 **auto-planner skill 즉시 활성** (description 매칭).

### 5단계 자율 진행
1. **전수조사** — 범위 + 인접 시스템 모두
2. **분석** — 누락·위험·rule 매핑
3. **실행** — 큰 작업 = codex/gemini 위임
4. **확인** — 자동 검증 hook
5. **보고** — 표·목록 + 남은 결정사항

### 자가 점검 의무
작업 시작 전 30+ rule (CLAUDE.md § 7 + .claude/rules/) 자동 체크.

### Claude → 외부 위임 기준
- **위임**: 코드 500줄+ / 반복 패턴 / 자동화 스크립트
- **직접**: 시스템 매핑 / rule 설계 / 디자인 결정

상세: `plugins/exec_orch/skills/auto-planner.md`

## 멈춤 방지 — 외부 의존 fail 시 자동 우회

빌드·실행 중 외부 의존 (파일 잠금·네트워크·권한·도구 누락) fail 시 **즉시 멈추지 말고 자동 우회**.

### 자동 우회 매트릭스

| Fail 원인 | 자동 대응 |
|---|---|
| 파일 잠금 (PermissionError) | 60초 폴링 (`_wait_unlock`) + 1회 알림 |
| 네트워크 fail | 지수 backoff (10s/30s/60s/2m) |
| 도구 미설치 | `pip`/`npm` 자동 install + retry |
| 의존성 충돌 | 대안 도구 자동 사용 (tesseract → easyocr → PIL) |
| 권한 부족 | elevation 시도, 안 되면 alternate path |

### 금기

- `sys.exit(1)` + "사용자가 X 해주세요" 노동 떠넘김 = 위반
- 사용자가 같은 명령 반복 입력 = 시스템 결함

### 강추 패턴

```python
def _wait_unlock(path, max_sec=60, interval=2):
    elapsed = 0
    while elapsed < max_sec:
        try:
            test = path.with_suffix(path.suffix + ".lock-test")
            path.rename(test); test.rename(path)
            return True
        except (PermissionError, OSError):
            if elapsed == 0:
                print(f"[WAIT] {path.name} 잠김 — {max_sec}초 폴링")
            time.sleep(interval); elapsed += interval
    return False
```

## 실전 원칙 (No 데모·MVP·목업·시연) — 2026-08-12 사용자 강조

**"뭐든 실전이고 뭐든 공용이고 뭐든 실제로 해야 해. 데모·MVP 아니야. 데이터가 필요하면 DB 연결이 필요합니다 하고"** + **"목업을 해주세요 라고 얘기 없으면 (실전으로)"** + **"나는 데모 mvp 가짜 시연 이런거 별로야"**.

### 원칙

사용자 명시 지시 (`목업`·`mock`·`demo`·`MVP`·`시연`) 없으면 **모든 산출물·코드·데이터·시연 = 실전 기준**.

### 매트릭스

| 상황 | 실전 (기본) | 목업 (사용자 명시 시만) |
|---|---|---|
| 데이터 필요 | DB 연결 요구 (MongoDB·PostgreSQL·MySQL 등 추천) | mock JSON |
| 인증 | 실제 OAuth·JWT | dummy token |
| API 응답 | 실제 endpoint 호출 | stub |
| UI 데이터 | 실제 API → 화면 반영 | 하드코딩 sample |
| 배포 대상 | 실제 target 프로젝트 (kit 배포) | 예시 폴더 |
| 검증 | 실제 smoke test (curl·Playwright) | 스킵 |
| 성능 | 실제 부하 측정 | 로컬 소량 |

### DB 필요 시 추천 (사용자 요청 시 자동 매핑)

| 데이터 특성 | 추천 |
|---|---|
| 문서·비정형·유연 스키마 | **MongoDB** (Atlas 무료 tier) |
| 관계형·트랜잭션 강력 | **PostgreSQL** (Supabase·Neon 무료) |
| 웹 앱·간단 | **MySQL** (PlanetScale·MariaDB) |
| 실시간·in-memory | **Redis** (Upstash 무료) |
| 벡터 검색 | **Pinecone**·**ChromaDB** (로컬) |
| 그래프 | **Neo4j Aura 무료** |
| 시계열 | **TimescaleDB**·**InfluxDB** |

### 금지

1. 데모 데이터 하드코딩 (A2 정합)
2. mock API 응답 → 실제 endpoint 인 척
3. "이 정도면 시연 되지 않을까" 판단
4. 사용자에게 목업 알림 없이 목업 반영
5. DB 필요한데 하드코딩 리스트로 대체

### 확인 절차

1. 사용자 지시에 `목업`·`mock`·`demo` 명시 없으면 실전
2. 데이터 필요 시 → **"DB 연결 필요. <추천> 사용 예정"** 사용자에게 명시 후 진행
3. 목업으로 진행하려면 사용자 명시 승인 받기

### 사용자가 목업 참조를 주면 (2026-08-12 강조)

**"목업 위치로 목업을 주면 기능을 만들어야 하는데 안만들어"** — 사용자가 mockup·wireframe·PPT slide·mock JSON·design 참조를 주면 그것을 **실제 기능으로 구현** 필수. mockup 그대로 두고 mockup 인 척 X.

| 사용자 제공 | 잘못된 대응 | 올바른 대응 |
|---|---|---|
| HTML wireframe URL/파일 | wireframe 그대로 복붙 | wireframe 참고 → 실제 컴포넌트 + API 연결 구현 |
| PPT slide (기능 명세) | slide 그대로 정리 | slide 요구사항 → 실제 코드·DB·API 구현 |
| mock JSON 데이터 | mock JSON 그대로 리턴 | mock 을 스키마 참고 → 실제 DB + 실제 endpoint 구현 |
| Figma 링크 | Figma 화면 그대로 embed | Figma → CSS·컴포넌트 코드 + 실제 데이터 바인딩 |
| "이 화면처럼" 요청 | 스크린샷만 참고 | 스크린샷 → 실제 라우팅·상태·API 완성 |

### 금지 (실전 원칙 위반)

1. 데모 데이터 하드코딩 (A2 정합)
2. mock API 응답 → 실제 endpoint 인 척
3. "이 정도면 시연 되지 않을까" 판단
4. 사용자에게 목업 알림 없이 목업 반영
5. DB 필요한데 하드코딩 리스트로 대체
6. **사용자 목업 참조 → mockup 그대로 재현** (기능 구현 skip)

memory: [[feedback_no_mock_default]] (별도 등재)

## FIFO 큐 + 지시 분리 (2026-08-12 사용자 강조)

**"내가 요청하는 것들은 FIFO 로 작업 등재하고 순서대로 하라고 해도 그래"** + **"내가 문장으로 보낼지 문단으로 보낼지 한 줄로 보낼지 모르자나"** — 사용자 지시 형식 예측 불가 → **자동 분리·큐잉 필요**.

### 지시 분리 감지 (사용자 입력 형식 무관)

| 사용자 입력 형식 | 분리 규칙 |
|---|---|
| **연속 짧은 문장** (여러 프롬프트 연속) | 각 프롬프트 = 별도 Task |
| **한 문단 안 여러 지시** | 마침표·개행·번호로 분리 → 각 Task |
| **한 줄 하나** | 단일 Task |
| **번호 리스트** | 각 항목 = Task |
| **긴 서술문 + 여러 요구** | 동사 (해줘·만들어·확인·수정·설치) 별로 분리 |
| **질문·감정 표현** (짜증·답답·중복) | Task 등재 X · `detect-user-emotion` 매핑으로 자동 대응 |

### 큐 관리

- 사용자가 한 턴에 여러 지시를 던지면 → `TaskCreate` 로 각 지시를 Task 로 등재
- Task ID 낮은 것부터 처리 (`TaskList` 참조)
- 완료 시 `TaskUpdate status=completed`
- 새 지시가 진행 중 지시를 대체하는지 (override) 아니면 추가인지 (append) 판단 → 애매하면 append

### 금지

1. 최신 지시만 반응 · 앞 지시 유실
2. 사용자 지시를 여러 개 받고 하나만 처리
3. Task 등재 skip
4. 완료 처리 (`TaskUpdate`) skip

## install 순서 강제 (2026-08-12 사용자 강조)

**kit 편집 중 install (다른 프로젝트 배포) 병렬 실행 금지.**

```text
[Phase 1] kit 편집 (rules·hooks·CLAUDE.md·memory)
[Phase 2] git commit (kit 상태 스냅샷)
[Phase 3] sync (plugins → .claude fanout)
[Phase 4] install / sync-team (target 배포)
[Phase 5] 검증 (target 에서 반영 확인)
```

Phase 1~3 미완 → Phase 4 = 룰 위반. **감지 hook**: `.claude/hooks/pre-install-lock.sh` (PreToolUse Bash) — `install.bat`·`sync-to-team.sh` 감지 시 git uncommitted 있으면 block.

### 금지

1. kit 편집 중 subagent 로 install 병렬 dispatch
2. uncommitted 상태에서 sync-to-team
3. install 후 검증 skip
4. "빨리 배포하고 kit 은 나중에 fix" — 오염 확산

memory: [[feedback_install_order]]

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
