' Launches the Teams Shift Monitor silently (no console window) using pythonw.exe.
' Used by the Windows Scheduled Task "TeamsShiftMonitorAutoStart" so the app
' autoloads and runs fully in the background after every reboot/login.

Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

pythonwPath = "C:\Users\russf\AppData\Local\Programs\Python\Python313\pythonw.exe"
mainScript = scriptDir & "\main.py"

Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = scriptDir
' 0 = hidden window, False = don't wait for it to finish
shell.Run """" & pythonwPath & """ """ & mainScript & """", 0, False
