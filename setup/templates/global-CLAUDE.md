# GLOBAL CLAUDE.md — 모든 프로젝트 공통 협업 원칙

> **Scope**: Global (가장 약한 우선순위 — Folder > Project > Global, last wins)
> **목적**: 어느 프로젝트에서든 일관되게 적용되어야 할 협업 원칙·금기·자동화 정책
> **적용 대상**: 모든 프로젝트 (orchestration_v1, ICM, IFRS, calc, llm, teamclaude, …)

---

## ① 농땡이 금지 — 무조건 전수조사

사용자가 작업 지시 시 다음 **5단계 완주**. 임의 축소 금지.

1. **전수조사** — 인접 시스템·전역까지 모든 위치 훑기 (단일 후보로 결론 X)
2. **분석** — 내용 직접 검증 (`diff`/`md5sum`/본문 읽기). 파일명만 보고 판정 X
3. **실행** — 발견한 누락·문제를 코드로 수정
4. **확인** — smoke test / dry-run / 로그 점검으로 동작 검증
5. **보고** — 표·목록으로 결과 + 남은 결정사항 명시

### 농땡이 트리거 어휘
사용자가 "농땡이 피지마", "정신 차려", "말만 하지 말고", "안되니까 내가 계속 지시하잖아" 같은 표현 → **즉시 5단계 모드**.

### 금기
- 파일명·확장자만 보고 "중복" / "필요없다" 판정 X — `diff`/`md5sum` 으로 검증
- spec `.md` 만 보고 `.sh`/`.py` 본문 안 본 채 결정 X
- 작업 범위 임의 축소 — "공통 hook 점검" → agents·commands·skills·전역 까지
- 헤지 ("확인 못 함", "가능성 있음") 를 회피 수단으로 X — 실제 데이터 확인 후에만

---

## ② Zero-touch 자동화 — 사용자 액션 요구 금지

사용자가 **아무 명령도 실행 안 해도** 시스템이 동작해야 함.

### 자동화 대상
- 패키지·MCP 설치 / Task Scheduler 등록 / 워커 spawn / watchdog 시작 / sync / 마이그레이션
- "사용자가 .bat 한 번만 실행해주세요" 같은 안내 금지 — 그 한 번도 **SessionStart hook** 으로 흡수

### 사용자 알림 허용 — 크리티컬 5가지만
| # | 상황 | 예시 |
|---|---|---|
| 1 | 시크릿 노출 | PAT/API 키가 commit·push 직전 감지 |
| 2 | 데이터 손실 | 대량 파일 삭제·force push·비가역 DB 작업 |
| 3 | 보안 위협 | 외부 유출·권한 상승·신뢰 못한 소스 실행 |
| 4 | 비용 폭증 | 일일 budget 80% 초과 또는 단발 $10+ |
| 5 | 시스템 손상 | OS 설정·레지스트리·계정 권한 변경 |

위 외 모든 진행은 **자동 실행 + 로그만** (`.claude/logs/`, `.claude/state/`).

### 금기
- "사용자 결정 필요" 빈발 — 가장 합리적 옵션 자동 선택 후 결과 보고
- 옵션 A/B/C 나열 후 사용자에게 선택 강요 (크리티컬 5가지 외엔)

---

## ③ 하드 경로 금지 — cross-machine 배포 필수

코드·설정·스케줄러 등록 인자에 **절대 박지 말 것**:

| 금지 패턴 | 대체 |
|---|---|
| `C:\Users\<사용자>\...` | `os.environ['TEMP']` / `tempfile.gettempdir()` / `%USERPROFILE%` |
| `/home/<사용자>/...` | `Path.home()` / `$HOME` |
| `C:\...\Python3XX\python.exe` | `shutil.which('python')` / `where python` 동적 검색 |
| 호스트명 (`DESKTOP-XXX`) | `socket.gethostname()` / `%COMPUTERNAME%` |
| 고정 IP `192.168.x.x` | 환경변수 / 설정 파일 |

### Task Scheduler / cron 패턴
스케줄러는 user PATH 못 받음 → **wrapper .bat / .sh 도입**:
- 스케줄러에는 wrapper 의 **프로젝트 내 경로만** 박음
- wrapper 내부에서 `where python` 등 런타임 검색
- 도구 위치 바뀌어도 wrapper 가 흡수 — 재등록 불필요

### Commit 전 검증 grep 패턴
```text
grep -rn 'C:\\\\Users\\\\[a-z0-9_]+' .  # 사용자명
grep -rn '/home/[a-z0-9_]+' .            # Linux 사용자
grep -rn 'Python3(10|11|12|13|14)\\python\\.exe' .  # Python 버전
```

매치되면 **REJECT** + 동적 검색으로 교체.

허용 예외: 주석 안의 placeholder (`%USERNAME%`, `<username>`, `$HOME`).

---

## 우선순위 (충돌 시)

1. **User explicit instruction** (이번 turn 의 명시적 지시)
2. **Project CLAUDE.md** (`./CLAUDE.md`)
3. **Folder CLAUDE.md** (`./src/CLAUDE.md` 등)
4. **이 Global CLAUDE.md**
5. 기본 시스템 프롬프트

같은 규칙 충돌 시 **더 가까운 scope 가 이김** (Folder > Project > Global).

---

## 출처·강화

이 원칙은 다음 프로젝트에서 반복 실수로 학습됨 → 모든 프로젝트로 일반화:
- `C:\pjt\orchestration_v1` — 2026-05-11 사용자가 농땡이·하드경로 반복 지적

추가 강화 위치 (프로젝트별):
- `<proj>/CLAUDE.md` § 7 금지 사항
- `<proj>/.claude/rules/failure-mode.md`
- `<proj>/.claude/rules/best-practices.md`
- `<proj>/plugins/exec_orch/hooks/hook-00-init.sh` (매 세션 출력)
- `~/.claude/projects/<proj>/memory/feedback_*.md`
