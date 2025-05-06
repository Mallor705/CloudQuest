@echo off
set "psScript=%~dp0CloudQuest.ps1"
set "gameProfile=%~1"

echo Set WshShell = CreateObject("WScript.Shell") > "%temp%\RunHidden.vbs"
echo WshShell.Run "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File ""%psScript%"" ""%gameProfile%""", 0, False >> "%temp%\RunHidden.vbs"
wscript "%temp%\RunHidden.vbs"
exit