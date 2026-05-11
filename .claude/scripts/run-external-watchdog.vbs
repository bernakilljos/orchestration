' run-external-watchdog.vbs -- invisible wrapper for Task Scheduler.
'
' Reason: Task Scheduler runs .bat in a visible cmd window which flashes
' every 1 minute (annoying). VBS via WScript.Shell.Run with SW_HIDE=0
' executes the .bat completely hidden -- no cmd flash.
'
' Wait=True so the scheduler captures exit code accurately.

Set fso = CreateObject("Scripting.FileSystemObject")
batPath = fso.GetParentFolderName(WScript.ScriptFullName) & "\run-external-watchdog.bat"

Set shell = CreateObject("WScript.Shell")
exitCode = shell.Run("""" & batPath & """", 0, True)
WScript.Quit exitCode
