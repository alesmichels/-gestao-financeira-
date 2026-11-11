@echo off
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
  echo.
  echo Python nao encontrado.
  echo Instale em https://www.python.org/downloads/ marcando "Add Python to PATH"
  echo ou rode no Prompt de Comando: winget install --id Python.Python.3.12 -e
  echo Depois feche esta janela e de dois cliques de novo.
  if not "%1"=="nopause" pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente do aplicativo...
  python -m venv .venv
)
echo Instalando dependencias, aguarde de 1 a 3 minutos...
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
if errorlevel 1 (
  echo.
  echo Erro na instalacao. Mande um print desta janela.
  if not "%1"=="nopause" pause
  exit /b 1
)
echo.
echo Instalacao concluida. Para abrir, de dois cliques em abrir-aplicativo.bat
if not "%1"=="nopause" pause
