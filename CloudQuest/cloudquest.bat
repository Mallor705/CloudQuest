@echo off

set "ProfileName=%~1"

:: Salva o nome do perfil em um arquivo temporário
echo %ProfileName% > "%temp%\CloudQuest_Profile.txt"

:: Executa o script Python oculto
echo Set WshShell = CreateObject("WScript.Shell") > "%temp%\RunHidden.vbs"
echo WshShell.Run "pythonw.exe ""%~dp0main.py""", 0, False >> "%temp%\RunHidden.vbs"
wscript "%temp%\RunHidden.vbs"
exit