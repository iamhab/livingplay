@echo off
setlocal
cd /d "%~dp0"
rem Cria atalhos do Livingplay na Area de Trabalho e no Menu Iniciar (so para o seu usuario).
if exist ".venv\Scripts\pythonw.exe" goto criar
echo Rode primeiro o iniciar.bat (ele prepara o programa). Depois rode este arquivo de novo.
pause
goto fim
:criar
powershell -NoProfile -Command "$d=(Get-Location).Path; $s=New-Object -ComObject WScript.Shell; foreach($p in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))){ $l=$s.CreateShortcut((Join-Path $p 'Livingplay.lnk')); $l.TargetPath=(Join-Path $d '.venv\Scripts\pythonw.exe'); $l.Arguments='livingplay.py'; $l.WorkingDirectory=$d; $l.IconLocation=(Join-Path $d 'icon.ico'); $l.Description='Livingplay'; $l.Save() }"
if errorlevel 1 goto falha
echo Pronto! O Livingplay agora aparece na Area de Trabalho e no Menu Iniciar.
pause
goto fim
:falha
echo Nao foi possivel criar os atalhos. Voce pode abrir o programa pelo iniciar.bat.
pause
:fim
endlocal
