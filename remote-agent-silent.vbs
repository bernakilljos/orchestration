Dim ps1
ps1 = CreateObject("WScript.Shell").ExpandEnvironmentStrings("%USERPROFILE%") & "\.claude\remote-agent.ps1"
CreateObject("WScript.Shell").Run "powershell.exe -WindowStyle Hidden -NonInteractive -ExecutionPolicy Bypass -File """ & ps1 & """", 0, False
