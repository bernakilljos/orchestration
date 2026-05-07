@echo off
rem =====================================================
rem Module 07: Git 초기화 + GitHub 저장소 생성
rem Usage: 07-github.bat [TARGET]
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
if "%TARGET%"=="" echo [ERROR] TARGET required & exit /b 1

echo.
echo [+] Git / GitHub setup...

where git >nul 2>&1
if errorlevel 1 (
  echo       [WARN] git not found - skipping
  goto DONE
)

if exist "%TARGET%\.git" (
  echo       [OK] Git already initialized
  goto DONE
)

rem --- GitHub PAT (env var → docs/ini/github.ini → SKIP) ---
echo [+] GitHub PAT 확인 중...

rem 1) 환경변수 우선
powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN','User')" > "%TEMP%\_ghpat.txt" 2>nul
set "GITHUB_PAT="
set /p "GITHUB_PAT=" < "%TEMP%\_ghpat.txt"
del "%TEMP%\_ghpat.txt" >nul 2>&1
if not "!GITHUB_PAT!"=="" (
  echo       GITHUB_PAT = configured [OK]
  goto PAT_READY
)

rem 2) docs/ini/github.ini 단계별 검사
set "INI_DIR=%~dp0..\..\docs\ini"
set "INI_FILE=%INI_DIR%\github.ini"
set "INI_PAT="

if not exist "%INI_DIR%" (
  echo [ERROR] docs\ini\ 폴더가 없습니다
  echo         생성: mkdir "%INI_DIR%"
  goto PAT_GUIDE
)
if not exist "%INI_FILE%" (
  echo [ERROR] %INI_FILE% 파일이 없습니다
  echo         아래 내용으로 작성:
  echo             GITHUB_PAT=ghp_YOUR_TOKEN_HERE
  goto PAT_GUIDE
)

for /f "tokens=2 delims==" %%A in ('findstr /i "^GITHUB_PAT" "%INI_FILE%" 2^>nul') do set "INI_PAT=%%A"
set "INI_PAT=!INI_PAT: =!"

if "!INI_PAT!"=="" (
  echo [ERROR] %INI_FILE% 의 GITHUB_PAT= 값이 비어있습니다
  echo         예시: GITHUB_PAT=ghp_YOUR_TOKEN_HERE
  goto PAT_GUIDE
)

echo       docs\ini\github.ini 에서 PAT 로드됨
powershell -NoProfile -Command "[System.Environment]::SetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN','!INI_PAT!','User')" >nul 2>&1
set "GITHUB_PAT=!INI_PAT!"
echo       GITHUB_PAT = saved [OK]
goto PAT_READY

:PAT_GUIDE
echo.
echo ============================================================
echo   해결 방법 ^(둘 중 하나^)
echo ============================================================
echo   [방법 A] setx GITHUB_PERSONAL_ACCESS_TOKEN "ghp_..."
echo   [방법 B] %INI_FILE% 작성: GITHUB_PAT=ghp_...
echo   PAT 발급: https://github.com/settings/tokens
echo   [SKIP] PAT 없이 계속 — GitHub 자동 repo 생성 비활성화
echo ============================================================
goto DONE

:PAT_READY

rem --- Create GitHub repo ---
for %%P in ("%TARGET%") do set "PROJ_BASE=%%~nxP"
set "PROJ_BASE=!PROJ_BASE: =-!"
echo       Creating GitHub repo: !PROJ_BASE!...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$pat='!GITHUB_PAT!';$base='!PROJ_BASE!'; $headers=@{Authorization=('token '+$pat);Accept='application/vnd.github.v3+json'}; $url=''; for($i=0;$i-le10;$i++){$name=if($i-eq0){$base}else{$base+'-'+$i}; try{$b=@{name=$name;private=$false;auto_init=$false}|ConvertTo-Json; $r=Invoke-RestMethod -Uri 'https://api.github.com/user/repos' -Method Post -Headers $headers -Body $b -ContentType 'application/json' -ErrorAction Stop -TimeoutSec 15; $url=$r.clone_url;break }catch{if($_.Exception.Response.StatusCode.value__ -eq 422){continue}else{break}}}; if($url){$url|Set-Content('%TARGET%\.github-repo-url.txt') -Encoding UTF8; Write-Host('[OK] '+$url)}else{Write-Host '[WARN] GitHub repo creation failed'}"

rem --- Git init ---
cd /d "%TARGET%"
git init >nul 2>&1

if exist "%TARGET%\.github-repo-url.txt" (
  for /f "usebackq tokens=*" %%U in ("%TARGET%\.github-repo-url.txt") do set "GH_URL=%%U"
  if not "!GH_URL!"=="" git remote add origin "!GH_URL!" >nul 2>&1
)

git add . >nul 2>&1
git commit -m "Initial commit from orchestration setup" >nul 2>&1
if not errorlevel 1 echo       [OK] Initial commit done

:DONE
echo [Module 07] GitHub OK
endlocal
exit /b 0
