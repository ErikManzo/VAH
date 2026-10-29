@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "ROOT=%CD%"
set "PYTHON=python"

if exist "%ROOT%\.venv\Scripts\python.exe" set "PYTHON=%ROOT%\.venv\Scripts\python.exe"
if exist "%ROOT%\.venv_aider_312\Scripts\python.exe" set "PYTHON=%ROOT%\.venv_aider_312\Scripts\python.exe"

set "OUT_DIR=%ROOT%\dist\ERP_VAH"
set "TEMP_DIST=%ROOT%\dist\modulos_temp"
set "TEMP_BUILD=%ROOT%\build\modulos"
set "SPEC_DIR=%ROOT%\build\modulos_specs"
set "ICON=%ROOT%\logo_00001.ico"

echo ==========================================
echo  Compilacion de modulos independientes VAH
echo ==========================================
echo.
echo Python: %PYTHON%
echo Root:   %ROOT%
echo Salida: %OUT_DIR%
echo.

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"
if exist "%TEMP_DIST%" rmdir /s /q "%TEMP_DIST%"
if exist "%TEMP_BUILD%" rmdir /s /q "%TEMP_BUILD%"
if exist "%SPEC_DIR%" rmdir /s /q "%SPEC_DIR%"

mkdir "%TEMP_DIST%"
mkdir "%TEMP_BUILD%"
mkdir "%SPEC_DIR%"

call :build "Presupuestos" "presupuestos\modulo_presupuestos.py"
if errorlevel 1 goto :error

call :build "Clientes" "clientes\main.py"
if errorlevel 1 goto :error

call :build "Proveedores" "proveedores\main.py"
if errorlevel 1 goto :error

call :build "CXC" "cxc\main.py"
if errorlevel 1 goto :error

call :build "Concentrador" "concentrador_materiales\ui\pantalla_concentrador.py"
if errorlevel 1 goto :error

call :build "CatalogoGeneralMateriales" "materiales\pantalla_catalogo_general.py"
if errorlevel 1 goto :error

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
echo  Modulos compilados y copiados con exito
echo ==========================================
dir /b "%OUT_DIR%\*.exe"
exit /b 0

:build
set "NAME=%~1"
set "REL_ENTRY=%~2"
set "ENTRY=%ROOT%\%REL_ENTRY%"
set "WORK_DIR=%TEMP_BUILD%\%NAME%"

echo.
echo [Compilando] %NAME%
echo Entry: %REL_ENTRY%

if not exist "%ENTRY%" (
    echo ERROR: No se encontro el entrypoint "%ENTRY%"
    exit /b 1
)

if exist "%WORK_DIR%" rmdir /s /q "%WORK_DIR%"
mkdir "%WORK_DIR%"

if exist "%ICON%" (
    "%PYTHON%" -m PyInstaller ^
        --noconfirm ^
        --clean ^
        --onefile ^
        --windowed ^
        --name "%NAME%" ^
        --paths "%ROOT%" ^
        --distpath "%TEMP_DIST%" ^
        --workpath "%WORK_DIR%" ^
        --specpath "%SPEC_DIR%" ^
        --hidden-import pyodbc ^
        --hidden-import PyQt6.sip ^
        --hidden-import win32print ^
        --icon "%ICON%" ^
        "%ENTRY%"
) else (
    "%PYTHON%" -m PyInstaller ^
        --noconfirm ^
        --clean ^
        --onefile ^
        --windowed ^
        --name "%NAME%" ^
        --paths "%ROOT%" ^
        --distpath "%TEMP_DIST%" ^
        --workpath "%WORK_DIR%" ^
        --specpath "%SPEC_DIR%" ^
        --hidden-import pyodbc ^
        --hidden-import PyQt6.sip ^
        --hidden-import win32print ^
        "%ENTRY%"
)

if errorlevel 1 (
    echo ERROR: Fallo la compilacion de %NAME%
    exit /b 1
)

copy /y "%TEMP_DIST%\%NAME%.exe" "%OUT_DIR%\%NAME%.exe" >nul
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
