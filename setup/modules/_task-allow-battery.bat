@echo off
REM _task-allow-battery.bat <TaskName>
REM Turns off the schtasks /create defaults "do not start on battery" and "stop when going on battery",
REM and turns on StartWhenAvailable (missed runs execute at the next chance).
REM Why (2026-10-16): Orca_10MinLoop did not run for 2h+ after the laptop was unplugged (DisallowStartIfOnBatteries=True).
REM ASCII only on purpose: cmd reads .bat in the OEM code page and mis-splits UTF-8 Korean comment lines.
if "%~1"=="" exit /b 0
powershell -NoProfile -ExecutionPolicy Bypass -Command "$t=Get-ScheduledTask -TaskName '%~1' -ErrorAction SilentlyContinue; if($t){$s=$t.Settings; $s.DisallowStartIfOnBatteries=$false; $s.StopIfGoingOnBatteries=$false; $s.StartWhenAvailable=$true; Set-ScheduledTask -TaskName '%~1' -Settings $s | Out-Null}" >nul 2>&1
exit /b 0
