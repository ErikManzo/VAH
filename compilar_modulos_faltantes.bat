@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "ROOT=%CD%"
set "VENV_DIR=%ROOT%\.venv_aider_312"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"
set "ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "DIST_DIR=%ROOT%\dist\modulos_temp"
set "OUT_DIR=%ROOT%\dist\ERP_VAH"
set "WORK_ROOT=%ROOT%\build\modulos_faltantes"
set "SPEC_DIR=%ROOT%\build\modulos_specs"
set "ICON=%ROOT%\logo_00001.ico"
set "THIRD_PARTY_DEPS=--hidden-import reportlab --hidden-import pdfplumber --hidden-import openpyxl --hidden-import pandas --collect-all reportlab --collect-all pdfplumber --collect-all openpyxl --collect-all pandas"

if not exist "%PYTHON%" (
    echo ERROR: No se encontro %PYTHON%
    exit /b 1
)

if not exist "%ACTIVATE%" (
    echo ERROR: No se encontro %ACTIVATE%
    exit /b 1
)

call "%ACTIVATE%"
if errorlevel 1 (
    echo ERROR: No se pudo activar .venv_aider_312
    exit /b 1
)

if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"
if not exist "%WORK_ROOT%" mkdir "%WORK_ROOT%"
if not exist "%SPEC_DIR%" mkdir "%SPEC_DIR%"

echo ==========================================
echo  Compilacion de modulos faltantes VAH
echo ==========================================
echo Python:  %PYTHON%
echo Origen:  %ROOT%
echo Dist:    %DIST_DIR%
echo Salida:  %OUT_DIR%
echo.

call :build "MaterialesAluminio" "materiales\aluminio\pantalla_materiales_aluminio.py"
if errorlevel 1 goto :error
call :build "MaterialesHerrajes" "materiales\herrajes\pantalla_herrajes.py"
if errorlevel 1 goto :error
call :build "MaterialesHerreria" "materiales\herreria\pantalla_herreria.py"
if errorlevel 1 goto :error
call :build "MaterialesOtros" "materiales\otros\pantalla_otros.py"
if errorlevel 1 goto :error
call :build "MaterialesPlasticos" "materiales\plasticos\pantalla_plasticos.py"
if errorlevel 1 goto :error
call :build "MaterialesVidrio" "materiales\vidrio\pantalla_vidrio.py"
if errorlevel 1 goto :error
call :build "PaquetesAluminio" "paquetes\aluminio\pantalla_paquete_aluminio.py"
if errorlevel 1 goto :error
call :build "PaquetesHerrajes" "paquetes\herrajes\pantalla_paquete_herrajes.py"
if errorlevel 1 goto :error

echo.
echo ==========================================
echo  Modulos faltantes compilados con exito
echo ==========================================
dir /b "%OUT_DIR%\Materiales*.exe" "%OUT_DIR%\Paquetes*.exe"
exit /b 0

:build
set "NAME=%~1"
set "ENTRY=%ROOT%\%~2"
set "WORK_DIR=%WORK_ROOT%\%NAME%"

echo.
echo [Compilando] %NAME%
echo Entry: %ENTRY%

if not exist "%ENTRY%" (
    echo ERROR: No se encontro el entrypoint "%ENTRY%"
    exit /b 1
)

if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"

if exist "%ICON%" (
    "%PYTHON%" -m PyInstaller ^
        --noconfirm ^
        --onefile ^
        --windowed ^
        --name "%NAME%" ^
        --paths "%ROOT%" ^
        --distpath "%DIST_DIR%" ^
        --workpath "%WORK_DIR%" ^
        --specpath "%SPEC_DIR%" ^
        --hidden-import PyQt6 ^
        --hidden-import PyQt6.sip ^
        --hidden-import pyodbc ^
        --hidden-import win32print ^
        %THIRD_PARTY_DEPS% ^
        --collect-all PyQt6 ^
        --icon "%ICON%" ^
        --add-data "%ROOT%\logo_00001.ico;." ^
        --add-data "%ROOT%\logo.jpg;." ^
        --add-data "%ROOT%\logo.png;." ^
        "%ENTRY%"
) else (
    "%PYTHON%" -m PyInstaller ^
        --noconfirm ^
        --onefile ^
        --windowed ^
        --name "%NAME%" ^
        --paths "%ROOT%" ^
        --distpath "%DIST_DIR%" ^
        --workpath "%WORK_DIR%" ^
        --specpath "%SPEC_DIR%" ^
        --hidden-import PyQt6 ^
        --hidden-import PyQt6.sip ^
        --hidden-import pyodbc ^
        --hidden-import win32print ^
        %THIRD_PARTY_DEPS% ^
        --collect-all PyQt6 ^
        --add-data "%ROOT%\logo_00001.ico;." ^
        --add-data "%ROOT%\logo.jpg;." ^
        --add-data "%ROOT%\logo.png;." ^
        "%ENTRY%"
)

if errorlevel 1 (
    echo ERROR: Fallo la compilacion de %NAME%
    exit /b 1
)

copy /y "%DIST_DIR%\%NAME%.exe" "%OUT_DIR%\%NAME%.exe" >nul
if errorlevel 1 (
    echo ERROR: No se pudo copiar %NAME%.exe a "%OUT_DIR%"
    exit /b 1
)

echo [OK] %NAME%.exe
exit /b 0

:error
echo.
echo ==========================================
echo  Se detecto un error en la compilacion
echo ==========================================
exit /b 1
