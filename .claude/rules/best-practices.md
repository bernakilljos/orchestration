---
paths:
  - ".claude/hooks/**"
  - ".claude/scripts/**"
  - ".claude/settings.json"
  - "plugins/**"
  - "setup/**"
---
# Best Practices — Claude Code 프로젝트

> **전문**: `.claude/rules-ref/best-practices.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

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
