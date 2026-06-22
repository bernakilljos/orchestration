' run-watchdog-silent.vbs
' Launch Python watchdog completely hidden (no cmd window, no taskbar entry).
' Detection responsibility lives in watchdog-start.bat — this script just executes
' a python interpreter against watchdog.py with SW_HIDE.
'
' Optional argument: explicit python.exe path (passed by watchdog-start.bat).
' If absent, falls back to "python" via PATH.

Option Explicit

Dim shell, fso, scriptDir, projectRoot, watchdogPy, logFile, pythonExe, cmd

Set shell = CreateObject("WScript.Shell")
Set fso   = CreateObject("Scripting.FileSystemObject")

scriptDir   = fso.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fso.GetParentFolderName(fso.GetParentFolderName(scriptDir))

watchdogPy = scriptDir & "\watchdog.py"
logFile    = projectRoot & "\.claude\state\watchdog.log"

If WScript.Arguments.Count >= 1 Then
    pythonExe = WScript.Arguments(0)
Else
    pythonExe = "python"
End If

' SW_HIDE = 0, bWaitOnReturn = False (fire-and-forget background)
cmd = "cmd /c """"" & pythonExe & """" """ & watchdogPy & """ >> """ & logFile & """ 2>&1"""
shell.Run cmd, 0, False

Set shell = Nothing
Set fso   = Nothing
