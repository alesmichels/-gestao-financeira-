@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Primeira vez: instalando o aplicativo...
  call instalar.bat nopause
  if errorlevel 1 (
    pause
    exit /b 1
  )
)
echo.
echo Abrindo o aplicativo no navegador (http://localhost:8501)...
echo Deixe esta janela aberta enquanto usa. Para fechar o aplicativo, feche esta janela.
echo.
start "" cmd /c "timeout /t 6 /nobreak >nul & start http://localhost:8501"
".venv\Scripts\python.exe" -m streamlit run app\painel.py
pause
