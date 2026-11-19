@echo off
setlocal
cd /d "%~dp0"
rem Cria um ambiente virtual local, instala as dependencias na primeira vez e abre o Livingplay.
rem Nao pede administrador e nao altera protecoes do Windows.
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto semPython
if exist ".venv\Scripts\python.exe" goto temVenv
echo Criando ambiente virtual...
%PY% -m venv .venv
if errorlevel 1 goto falha
:temVenv
if exist ".venv\instalado.txt" goto abrir
echo Instalando dependencias - so na primeira vez, pode demorar...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto falha
echo ok> ".venv\instalado.txt"
:abrir
start "" ".venv\Scripts\pythonw.exe" livingplay.py
goto fim
:semPython
echo Python 3 nao encontrado. Instale em https://www.python.org/downloads/ e marque a opcao Add python.exe to PATH.
pause
goto fim
:falha
echo Algo deu errado na preparacao. Veja as mensagens acima.
pause
:fim
endlocal
