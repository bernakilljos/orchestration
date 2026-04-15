# exec_orca-auto — Orca Auto Worker 관리

> **분류:** `exec_` (실행 계열)
> **레거시 커맨드:** `/orcauto-start`, `/orcauto-stop`
> **참조 plugin:** `.claude-plugin/plugin.json` → `entry_points.session_start`

## 목적
codex-auto / gemini-auto 워커를 시작·중단·상태 조회한다.
세션 시작 시 CLAUDE.md의 Step 1에서 자동 호출되며,
`/orcauto-start` / `/orcauto-stop` 커맨드의 실제 로직을 담당한다.

---

## 상태 파일 (`.claude/` 루트 — 하위 호환 유지)

| 파일 | 의미 | 읽기/쓰기 |
|------|------|---------|
| `orca-enabled`   | 자동 시작 활성화 플래그 | 쓰기 (START) |
| `orca-stopped`   | 비활성화 플래그 | 쓰기 (STOP) / 삭제 (START) |
| `orca-heartbeat` | 마지막 활동 시각 | 쓰기 (매 툴 사용) |
| `orca-workers`   | 워커 수 (없으면 기본값 1) | 읽기 |

---

## 액션: START (활성화 + 워커 시작)

```
전제 조건:
  - .claude/orca-enabled 존재 OR /orcauto-start 커맨드 호출
  - .claude/orca-stopped 없음

실행 순서:
1. orca-stopped 삭제:
     del .claude\orca-stopped 2>nul      (Windows)
     rm -f .claude/orca-stopped           (bash)

2. orca-enabled 생성:
     echo enabled > .claude\orca-enabled

3. orca-heartbeat 갱신 (현재 시각):
     date +%Y-%m-%dT%H:%M:%S > .claude/orca-heartbeat

4. 워커 수 결정:
     if exist .claude\orca-workers → type .claude\orca-workers
     없으면 → 1

5. codex-auto 가용 확인:
     where codex-auto 2>nul && echo YES || echo NO

6. codex-auto YES → 시작:
     start "Codex-Worker-1" cmd /c "cd /d %CD% && codex-auto [N]"

7. gemini-auto 가용 확인:
     where gemini-auto 2>nul && echo YES || echo NO

8. gemini-auto YES → 시작:
     start "Gemini-Verifier-1" cmd /c "cd /d %CD% && gemini-auto [N]"

9. 결과 보고:
   | 에이전트    | 상태       | 워커 수 |
   |------------|-----------|--------|
   | codex-auto  | 시작됨/없음 | N     |
   | gemini-auto | 시작됨/없음 | N     |
   "자동 종료: Claude 종료 후 5분 이내 자동 중단됩니다."
```

---

## 액션: STOP (비활성화 + 워커 종료)

```
실행 순서:
1. orca-stopped 생성:
     echo disabled > .claude\orca-stopped

2. orca-enabled 삭제:
     del .claude\orca-enabled 2>nul

3. 실행 중인 워커 윈도우 종료:
     powershell: Get-Process cmd -ErrorAction SilentlyContinue |
       Where-Object { $_.MainWindowTitle -match 'Codex-Worker|Gemini-Verifier' } |
       Stop-Process -Force

4. 결과 보고:
   - orca-stopped 플래그 생성됨
   - 종료된 워커 수
   - "Claude 단독 모드. 재활성화: /orcauto-start"
```

---

## 액션: STATUS (상태 조회)

```
출력:
  codex-auto:  where codex-auto → AVAILABLE / NOT FOUND
  gemini-auto: where gemini-auto → AVAILABLE / NOT FOUND
  heartbeat:   cat .claude/orca-heartbeat
  workers:     cat .claude/orca-workers (없으면 "1 (default)")
  enabled:     .claude/orca-enabled 존재 여부
  stopped:     .claude/orca-stopped 존재 여부
```

---

## 자동 종료 규칙
- Claude 종료 후 5분 → heartbeat 갱신 없음 → 워커 내부 타임아웃으로 자동 종료
- 이 규칙은 `.claude/scripts/codex-auto.bat` / `gemini-auto.bat` 내부에 구현됨

---

## 워커 수 변경

사용자가 숫자를 입력하면:
```
echo [N] > .claude\orca-workers
→ STOP 액션 실행
→ START 액션 실행 (새 워커 수 적용)
```
