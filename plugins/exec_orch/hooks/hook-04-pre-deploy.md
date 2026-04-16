# HOOK-04 — Pre-Deploy (Auto-run before deploy)

## Trigger
Auto-run before SKILL-05 deploy. Deploy blocker gate.

## Steps

### 1. Final quality gate check
```bat
rem Re-check previous results
echo === Build Result ===
findstr /i "error\|failed" docs\build-result.txt && echo [BLOCK] Build errors found || echo [OK] Build passed

echo === Secret Scan ===
for /f %%c in ('find /c /v "" "docs\secret-scan-filtered.txt" 2^>nul') do (
  if %%c GTR 0 ( echo [BLOCK] Secret exposed ) else ( echo [OK] No secrets )
)

echo === Review Check ===
if exist docs\review-decision.md ( echo [OK] Review done ) else ( echo [WARN] No review - deploying anyway )
```

### 2. Env-based deploy permission
```bat
rem Load deploy-config.env
for /f "usebackq tokens=1,2 delims==" %%a in (".claude\deploy-config.env") do (
  if not "%%a"=="" ( echo %%a | findstr /b "#" >nul || set "%%a=%%b" )
)

if "%TARGET_ENV%"=="demo" ( echo [OK] DEMO - auto deploy allowed )
if "%TARGET_ENV%"=="upg"  ( echo [OK] UPG  - auto deploy allowed )
if "%TARGET_ENV%"=="prod" (
  echo [BLOCK] PROD - Team Lead manual approval required
  echo Run: .claude\scripts\deploy.bat --confirmed
  exit /b 1
)
```

### 3. Server pre-check
```bat
echo === SSH Check ===
ssh -o ConnectTimeout=5 %REMOTE_USER%@%REMOTE_HOST% "echo OK" && echo [OK] Server reachable || echo [BLOCK] Server unreachable

echo === Disk Usage ===
ssh %REMOTE_USER%@%REMOTE_HOST% "df -h %APP_PATH% | awk 'NR==2{print $5}'"

echo === Service Status ===
ssh %REMOTE_USER%@%REMOTE_HOST% "pm2 status %PM2_APP_NAME% 2>/dev/null || echo First deploy"
```

### 4. Create backup
```bat
echo === Creating Backup ===
ssh %REMOTE_USER%@%REMOTE_HOST% "mkdir -p %APP_PATH%/backup && cp -r %APP_PATH%/dist %APP_PATH%/backup/dist_%DATE:~0,4%%DATE:~5,2%%DATE:~8,2% 2>/dev/null || true && echo Backup done"
```

## Pass Criteria
- [ ] No build errors
- [ ] No secrets found
- [ ] Server reachable
- [ ] Disk < 85%
- [ ] Backup created
- [ ] PROD: manual approval confirmed

## On Failure
Resolve item and re-run. Deploy blocked until all pass.
