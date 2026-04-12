# HOOK-05 — Post-Deploy (Auto-run after deploy completes)

## Trigger
Auto-run immediately after SKILL-05 deploy completes.

## Steps

### 1. Health check (re-confirm)
```bat
echo === Health Check ===
set /a RETRY=0
:HEALTH_LOOP
set /a RETRY+=1
curl -s -o nul -w "%%{http_code}" http://%REMOTE_HOST%:%SERVICE_PORT% > .tmp_hc.txt
set /p HC_STATUS=<.tmp_hc.txt
del .tmp_hc.txt
if "%HC_STATUS%"=="200" ( echo [OK] Service healthy & goto HC_DONE )
echo [%RETRY%/3] WAIT... status=%HC_STATUS%
if %RETRY% LSS 3 ( timeout /t 5 /nobreak >nul & goto HEALTH_LOOP )
echo [FAIL] Service not responding - run rollback
.claude\scripts\rollback.bat
:HC_DONE
```

### 2. Record deploy history
```bat
if not exist docs\deploy-history mkdir docs\deploy-history
echo. >> docs\deploy-history\history.md
echo ## Deploy %DATE% %TIME% >> docs\deploy-history\history.md
echo - Env : %TARGET_ENV% >> docs\deploy-history\history.md
echo - Host: %REMOTE_HOST% >> docs\deploy-history\history.md
echo - By  : Claude (auto) >> docs\deploy-history\history.md
echo - Result: Success >> docs\deploy-history\history.md
```

### 3. Update task-memory.json
Claude reads `.claude\tasks\task-memory.json` and appends
deploy record (deployed_at, env, host). Keep last 10 only.

### 4. Learning loop (v3)
Claude reads `.claude\learning\failure-patterns.json`,
checks for patterns with `count >= 2`,
prints warnings for patterns needing prevention rule review.

### 5. Release all locked_files
Claude reads `.claude\tasks\current-tasks.json`,
clears `locked_files: []` for all `status: "done"` tasks.

### 6. Send notification
```bat
.claude\scripts\notify.bat good "Deploy success: %TARGET_ENV% - http://%REMOTE_HOST%:%SERVICE_PORT%"
```

## Completion Report

```
## Deploy Complete

- Env    : [demo/upg/prod]
- URL    : http://HOST:PORT
- Time   : DATETIME
- Health : PASS
- Next   : check current-tasks.json for pending items
```

## Extension Points
- Auto-start next pending task on success
- Aggregate quality scores → team-performance.md
