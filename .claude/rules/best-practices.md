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
