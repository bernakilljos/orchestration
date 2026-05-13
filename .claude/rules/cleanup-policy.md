# 오염 파일 정리 정책

> **목적**: Windows redirect 잔재 · 임시 파일 · nested 폴더 등 자동 정리
> **자동화**: SessionStart hook 으로 매 세션 시작 시 실행
> **스크립트**: `.claude/scripts/cleanup-pollution.sh`
> **로그**: `.claude/logs/cleanup-pollution.log`

---

## 자동 정리 대상

| 타입 | 패턴 | TTL | 이유 |
|---|---|---|---|
| **Windows nul redirect** | `nul`, `NUL` (파일) | 즉시 | `2>nul` (cmd 스타일) 이 bash 에서 실행되면 실제 파일 생성 |
| **nested `.claude/.claude/`** | 폴더 | 즉시 | `PROJECT_ROOT` 계산 버그 잔재 |
| **임시 파일** | `*.bak`, `*.orig`, `*.tmp`, `*.swp`, `*~` | 3일 | 편집기 자동 백업 |
| **작업 log** | `docs/screens/_*.log` | 3일 | 크롤링·분류 완료 후 잔재 |
| **시스템 log** | `.claude/logs/*.log` | 14일 | watchdog·hook trace 장기 보존 |
| **완료 task** | `.claude/tasks/done/*` | 30일 | task-instruction 완료 후 |
| **tool result cache** | `~/.claude/projects/<proj>/tool-results/*` | 7일 | fetch_html·fetch_json 캐시 |
| **빈 task 폴더** | `.claude/tasks/{done,locks,...}` (empty) | 즉시 | 잔존 빈 디렉토리 |

---

## `2>nul` 사용 금지

bash 환경에서 `2>nul` (Windows cmd 스타일) 실행 시 실제 `nul` 파일 생성.

| 환경 | 올바른 사용 |
|---|---|
| **bash (.md / .sh)** | `2>/dev/null` |
| **Windows cmd (.bat)** | `2>nul` (정상) |
| **PowerShell** | `2>$null` |

### 검증 grep
```bash
grep -rn ">nul\|2>nul" plugins/ .claude/
```

매치되면 → bash 환경 대상 파일이면 `2>/dev/null` 로 교체.

---

## `PROJECT_ROOT` 계산 패턴

hook 스크립트는 `.claude/hooks/` 또는 `plugins/<name>/hooks/` 위치. PROJECT_ROOT 계산 시 깊이 주의.

| 위치 | 올바른 패턴 |
|---|---|
| `.claude/hooks/<script>.sh` | `cd "$(dirname "$0")/../.." && pwd` |
| `.claude/scripts/<script>.sh` | `cd "$(dirname "$0")/../.." && pwd` |
| `plugins/<name>/hooks/<script>.sh` | `cd "$(dirname "$0")/../../.." && pwd` |

### 흔한 실수
- `..` 1번만 — `.claude/` 디렉토리만 return → `LOG_DIR` 가 `.claude/.claude/logs/` 됨
- `realpath` 미지원 머신 → `cd ... && pwd` 사용

---

## 수동 실행

```bash
bash .claude/scripts/cleanup-pollution.sh
tail -20 .claude/logs/cleanup-pollution.log
```

---

## 강화 (5중 박기)

1. 스크립트: `.claude/scripts/cleanup-pollution.sh`
2. SessionStart hook: `.claude/settings.json`
3. 규칙 문서: 이 파일
4. CLAUDE.md § 7-22 금지
5. `plugins/exec_orch/hooks/hook-00-init.sh` 매 세션 출력

---

## 참조

- `.claude/rules/best-practices.md` § 멈춤 방지
- `.claude/rules/failure-mode.md` § 전수조사 위반 안티패턴
- 글로벌 CLAUDE.md § ② Zero-touch 자동화
