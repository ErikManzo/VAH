@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "ROOT=%CD%"
set "VENV_DIR=%ROOT%\.venv_aider_312"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"
set "ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "OUT_DIR=%ROOT%\dist\ERP_VAH"
set "TEMP_DIST=%ROOT%\dist\modulos_onedir"
set "TEMP_BUILD=%ROOT%\build\modulos_onedir"
set "SPEC_DIR=%ROOT%\build\modulos_onedir_specs"
set "ICON=%ROOT%\logo_00001.ico"
set "THIRD_PARTY_DEPS=--hidden-import reportlab --hidden-import pdfplumber --hidden-import openpyxl --hidden-import pandas --collect-all reportlab --collect-all pdfplumber --collect-all openpyxl --collect-all pandas"

if not exist "%PYTHON%" (
    echo ERROR: No se encontro el interprete requerido:
    echo %PYTHON%
    exit /b 1
)

if not exist "%ACTIVATE%" (
    echo ERROR: No se encontro el activador del entorno:
    echo %ACTIVATE%
    exit /b 1
)

call "%ACTIVATE%"
if errorlevel 1 (
    echo ERROR: No se pudo activar el entorno .venv_aider_312
    exit /b 1
)

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"
if not exist "%TEMP_DIST%" mkdir "%TEMP_DIST%"
if not exist "%TEMP_BUILD%" mkdir "%TEMP_BUILD%"
if not exist "%SPEC_DIR%" mkdir "%SPEC_DIR%"

echo ==========================================
echo  Recompilacion ONEDIR de modulos VAH
echo ==========================================
echo.
echo Python:  %PYTHON%
echo Entorno: %VENV_DIR%
echo Root:    %ROOT%
echo Dist:    %TEMP_DIST%
echo Salida:  %OUT_DIR%
echo.
echo Nota: ONEDIR mejora tiempo de arranque a cambio de entregar una carpeta por modulo.
echo.

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
echo  Modulos ONEDIR compilados con exito
echo ==========================================
dir /b "%OUT_DIR%\*.exe"
dir /b "%OUT_DIR%\Presupuestos" "%OUT_DIR%\Clientes" "%OUT_DIR%\Proveedores" "%OUT_DIR%\CXC" "%OUT_DIR%\Concentrador" "%OUT_DIR%\CatalogoGeneralMateriales" 2>nul
exit /b 0

:build
set "NAME=%~1"
set "REL_ENTRY=%~2"
set "ENTRY=%ROOT%\%REL_ENTRY%"
set "WORK_DIR=%TEMP_BUILD%\%NAME%"
set "TARGET_DIR=%OUT_DIR%\%NAME%"
set "DIST_DIR=%TEMP_DIST%\%NAME%"

echo.
echo [Compilando ONEDIR] %NAME%
echo Entry: %REL_ENTRY%

if not exist "%ENTRY%" (
    echo ERROR: No se encontro el entrypoint "%ENTRY%"
    exit /b 1
)

if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"

set "EXCLUDES=--exclude-module pytest --exclude-module _pytest --exclude-module pytest_asyncio --exclude-module pytest_cov --exclude-module hypothesis --exclude-module IPython --exclude-module jupyter --exclude-module notebook --exclude-module matplotlib.tests --exclude-module numpy.tests --exclude-module pandas.tests"
set "PYI_BASE=%PYTHON% -m PyInstaller --noconfirm --clean --onedir --windowed --name ""%NAME%"" --paths ""%ROOT%"" --distpath ""%TEMP_DIST%"" --workpath ""%WORK_DIR%"" --specpath ""%SPEC_DIR%"" --hidden-import PyQt6 --hidden-import PyQt6.sip --hidden-import pyodbc --hidden-import win32print %THIRD_PARTY_DEPS% --collect-all PyQt6 %EXCLUDES%"

if exist "%ICON%" (
    %PYI_BASE% ^
        --icon "%ICON%" ^
        --add-data "%ROOT%\logo_00001.ico;." ^
        --add-data "%ROOT%\logo.jpg;." ^
        --add-data "%ROOT%\logo.png;." ^
        --add-data "%ROOT%\logo_principal.jpg;." ^
        --add-data "%ROOT%\logo_principal_pagina.jpg;." ^
        "%ENTRY%"
) else (
    %PYI_BASE% ^
        --add-data "%ROOT%\logo_00001.ico;." ^
        --add-data "%ROOT%\logo.jpg;." ^
        --add-data "%ROOT%\logo.png;." ^
        --add-data "%ROOT%\logo_principal.jpg;." ^
        --add-data "%ROOT%\logo_principal_pagina.jpg;." ^
        "%ENTRY%"
)

if errorlevel 1 (
    echo ERROR: Fallo la compilacion ONEDIR de %NAME%
    exit /b 1
)

if exist "%TARGET_DIR%" rmdir /s /q "%TARGET_DIR%"
xcopy /e /i /y "%DIST_DIR%\*" "%TARGET_DIR%\" >nul
if errorlevel 1 (
    echo ERROR: No se pudo copiar la carpeta de %NAME% a "%TARGET_DIR%"
    exit /b 1
)

echo [OK] %TARGET_DIR%\%NAME%.exe
exit /b 0

:error
echo.
echo ==========================================
echo  Se detecto un error en la recompilacion
echo ==========================================
exit /b 1
