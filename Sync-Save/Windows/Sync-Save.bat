@echo off
set "psScript=F:\messi\Games\Steam\steamapps\common\ELDEN RING\Game\Sync-Save.ps1"
echo Set WshShell = CreateObject("WScript.Shell") > "%temp%\RunHidden.vbs"
echo WshShell.Run "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File ""%psScript%""", 0, False >> "%temp%\RunHidden.vbs"
wscript "%temp%\RunHidden.vbs"
exit