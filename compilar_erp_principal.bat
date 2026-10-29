@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "ROOT=%CD%"
set "PYTHON=%ROOT%\.venv_aider_312\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo ERROR: No se encontro el interprete esperado:
    echo %PYTHON%
    exit /b 1
)

echo ==========================================
echo  Preparando entorno del ERP principal
echo ==========================================
echo Root:   %ROOT%
echo Python: %PYTHON%
echo.

call "%ROOT%\.venv_aider_312\Scripts\activate.bat"
if errorlevel 1 exit /b 1

"%PYTHON%" "%ROOT%\scripts\generar_requirements_erp.py"
if errorlevel 1 exit /b 1

"%PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1

"%PYTHON%" -m pip install -r "%ROOT%\requirements.txt"
if errorlevel 1 exit /b 1

echo.
echo ==========================================
echo  Compilando ERP_VAH.exe
echo ==========================================

"%PYTHON%" -m PyInstaller --noconfirm --clean "%ROOT%\ERP_VAH.spec"
if errorlevel 1 exit /b 1

echo.
echo ==========================================
echo  Compilacion finalizada
echo ==========================================
echo Salida esperada:
echo %ROOT%\dist\ERP_VAH\
exit /b 0
