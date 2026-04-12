@echo off
rem =====================================================
rem Module 04: 글로벌 명령어 설치 (codex-a, gemini-a 등)
rem Usage: 04-commands.bat [TARGET]
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
if "%TARGET%"=="" echo [ERROR] TARGET required & exit /b 1

echo.
echo [+] Installing global commands...
if not exist "%APPDATA%\npm" mkdir "%APPDATA%\npm" >nul 2>&1

for %%F in (codex-a codex-auto gemini-a gemini-auto gemini-verify claude-auto) do (
  if exist "%TARGET%\.claude\scripts\%%F.bat" (
    if exist "%APPDATA%\npm\%%F.bat" attrib -r "%APPDATA%\npm\%%F.bat" >nul 2>&1
    copy /Y "%TARGET%\.claude\scripts\%%F.bat" "%APPDATA%\npm\%%F.bat" >nul 2>&1
    if exist "%APPDATA%\npm\%%F.bat" (
      echo       %%F.bat installed
    ) else (
      echo       [WARN] %%F.bat copy failed
    )
  )
)

echo [+] Normalizing CRLF line endings...
powershell -NoProfile -Command ^
  "$enc=New-Object System.Text.UTF8Encoding($false); ^
   foreach($n in 'codex-a','codex-auto','gemini-a','gemini-auto','gemini-verify','claude-auto'){ ^
     $p=Join-Path '%APPDATA%\npm' ($n+'.bat'); ^
     if(Test-Path $p){$c=Get-Content $p -Raw -Encoding UTF8; $c=$c -replace '\r?\n',([char]13+[char]10); [System.IO.File]::WriteAllText($p,$c,$enc)} }" >nul 2>&1

rem Also fix scripts in .claude\scripts
powershell -NoProfile -Command ^
  "$enc=New-Object System.Text.UTF8Encoding($false); ^
   Get-ChildItem '%TARGET%\.claude\scripts' -Filter '*.bat' -File -ErrorAction SilentlyContinue | ^
   ForEach-Object { $c=Get-Content $_.FullName -Raw -Encoding UTF8; $c=$c -replace '\r?\n',([char]13+[char]10); [System.IO.File]::WriteAllText($_.FullName,$c,$enc) }" >nul 2>&1
echo       Done

echo [Module 04] Commands OK
endlocal
exit /b 0
