@echo off
setlocal
cd /d "%~dp0"
rem Prepara o Livingplay na primeira vez (ambiente virtual + dependencias) e abre o programa.
rem Nao pede administrador e nao altera protecoes do Windows. Tudo fica dentro desta pasta (.venv).
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto semPython
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
rem 9009 = o "python" da Microsoft Store (atalho vazio), nao um Python de verdade
if errorlevel 9009 goto semPython
if errorlevel 1 goto pythonVelho
%PY% -c "import tkinter" >nul 2>nul
if errorlevel 1 goto semTk
if exist ".venv\Scripts\python.exe" goto temVenv
echo Criando ambiente virtual...
%PY% -m venv .venv
if errorlevel 1 goto falha
:temVenv
rem Reinstala as dependencias quando o requirements.txt mudar (por exemplo, depois de atualizar o programa).
if not exist ".venv\instalado.txt" goto instalar
fc /b requirements.txt ".venv\instalado.txt" >nul 2>nul
if errorlevel 1 goto instalar
goto abrir
:instalar
echo Instalando dependencias - so na primeira vez, pode levar alguns minutos...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto falha
copy /y requirements.txt ".venv\instalado.txt" >nul
:abrir
start "" ".venv\Scripts\pythonw.exe" livingplay.py
goto fim
:semPython
echo Python 3 nao encontrado. Instale em https://www.python.org/downloads/
echo e marque a opcao "Add python.exe to PATH". Depois rode este arquivo de novo.
echo Passo a passo completo: docs\INSTALAR.md
pause
goto fim
:pythonVelho
echo O Livingplay precisa do Python 3.11 ou mais novo. Instale a versao atual em https://www.python.org/downloads/
pause
goto fim
:semTk
echo Este Python nao tem o Tkinter (a parte que desenha as janelas).
echo Reinstale o Python pelo site python.org deixando marcada a opcao "tcl/tk and IDLE".
pause
goto fim
:falha
echo Algo deu errado na preparacao. Veja as mensagens acima.
echo Dicas: confira a internet e veja a secao "Problemas comuns" em docs\INSTALAR.md
pause
:fim
endlocal
