# Skill 38: Token Watchdog (토큰 감시 + 자동 재가동)

## 목적
codex/gemini 토큰이 소진되면 대기하고, 리셋되면 자동으로 워커를 재가동한다.
사람이 없어도 토큰 상태를 감시해서 자동으로 최대한 활용.

## 핵심 원칙
```
1. 토큰 소진 → 워커 중단 (에러 무한 반복 방지)
2. 주기적 체크 (10분 간격) → 토큰 복구 감지
3. 복구 확인 → 워커 자동 재시작
4. Claude 토큰도 감시 → 스냅샷 저장 후 대기
```

## 트리거
- codex-auto/gemini-auto 실행 중 rate limit 에러 감지 시
- `/check-agents` 실행 시 자동 체크
- 세션 시작 시 (Orca Auto에서 호출)

## 감지 방법

### Codex 토큰 체크
```bash
# codex 실행 시 exit code 또는 stderr에서 감지
# "rate limit" / "token limit" / "quota exceeded" 패턴
codex exec "echo test" 2>&1 | grep -i "rate\|limit\|quota"
→ 매칭되면: CODEX_AVAILABLE=false
→ 매칭 안 되면: CODEX_AVAILABLE=true
```

### Gemini 토큰 체크
```bash
# gemini 실행 시 에러 메시지 감지
gemini -p "test" 2>&1 | grep -i "rate\|limit\|quota\|429"
→ 매칭되면: GEMINI_AVAILABLE=false
→ 매칭 안 되면: GEMINI_AVAILABLE=true
```

### Claude 토큰 체크
```bash
# Claude는 5h limit 표시에서 감지
# .claude/context-cache/ 또는 에러 메시지
# "rate limit" / "0% left" 패턴
```

## 워커 관리 흐름

```
[정상 상태]
  codex-auto 10개 + gemini-auto 10개 실행 중

[codex 토큰 소진 감지]
  → codex 워커 전부 중단 (stop 파일 생성)
  → gemini는 계속 실행
  → .claude/token-status.json 업데이트
    {"codex": "exhausted", "codex_reset": "21:15", "gemini": "ok"}

[10분 간격 체크]
  → codex 토큰 복구? → 워커 재시작
  → gemini 토큰 소진? → gemini도 중단
  → 둘 다 소진? → Claude만 직접 작업

[전부 소진]
  → 스냅샷 저장 (skill-09 memory-reset)
  → 리셋 시간까지 대기
  → 리셋 후 전체 재가동

[Claude도 소진]
  → 스냅샷 저장
  → "리셋 후 이 세션 이어서 진행" 메시지 출력
  → 세션 종료
```

## codex-auto.bat 연동

```bat
rem codex 실행 후 에러 체크
call codex-a --auto "%PICKED_TASK%"
set "CODEX_EXIT=%errorlevel%"

rem rate limit 감지 (exit code 또는 로그)
if %CODEX_EXIT% NEQ 0 (
  findstr /i "rate limit\|quota\|429" "%TEMP%\codex-last-output.log" >nul 2>&1
  if not errorlevel 1 (
    echo [Worker-%CHILD_ID%] TOKEN EXHAUSTED — waiting for reset
    echo exhausted > "%PROJECT_ROOT%\.claude\codex-token-status"
    rem 10분 대기 후 재체크
    :TOKEN_WAIT
    timeout /t 600 /nobreak >nul
    codex exec "echo token-check" >nul 2>&1
    if errorlevel 1 goto TOKEN_WAIT
    echo [Worker-%CHILD_ID%] TOKEN RESTORED — resuming
    del "%PROJECT_ROOT%\.claude\codex-token-status" 2>nul
  )
)
```

## gemini-auto.bat 연동

```bat
rem gemini 실행 후 에러 체크 (동일 패턴)
call gemini-a --verify "%PICKED_REPORT%"
rem rate limit 감지 시 동일하게 대기 → 재체크 → 재개
```

## 상태 파일

```
.claude/codex-token-status    → "exhausted" 또는 파일 없음 (정상)
.claude/gemini-token-status   → "exhausted" 또는 파일 없음
.claude/token-status.json     → 통합 상태 (대시보드 표시용)
```

## 대시보드 연동

```
status-push가 token-status.json 읽어서 대시보드에 표시:
  [codex]  ✅ 정상 / ❌ 토큰 소진 (리셋: 21:15)
  [gemini] ✅ 정상 / ❌ 토큰 소진 (리셋: 02:14 4/17)
  [claude] ✅ 정상 / ⚠️ 80% 사용 / ❌ 소진
```
