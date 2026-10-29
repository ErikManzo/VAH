@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "ROOT=%CD%"
set "VENV_DIR=%ROOT%\.venv_aider_312"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"
set "ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "FINAL_DIST=%ROOT%\dist\ERP_VAH"
set "FINAL_BUILD=%ROOT%\build\ERP_VAH_final"
set "FINAL_SPEC=%ROOT%\build\ERP_VAH_final_spec"
set "ICON=%ROOT%\logo_00001.ico"
set "ENTRY=%ROOT%\principal\pantalla_principal.py"
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

echo ==========================================
echo  Limpieza de builds previos
echo ==========================================
if exist "%FINAL_BUILD%" rmdir /s /q "%FINAL_BUILD%"
if exist "%FINAL_SPEC%" rmdir /s /q "%FINAL_SPEC%"
if exist "%ROOT%\build\modulos_onedir" rmdir /s /q "%ROOT%\build\modulos_onedir"
if exist "%ROOT%\build\modulos_onedir_specs" rmdir /s /q "%ROOT%\build\modulos_onedir_specs"
if exist "%ROOT%\dist\modulos_onedir" rmdir /s /q "%ROOT%\dist\modulos_onedir"
if exist "%FINAL_DIST%" rmdir /s /q "%FINAL_DIST%"

mkdir "%FINAL_BUILD%"
mkdir "%FINAL_SPEC%"
mkdir "%FINAL_DIST%"

echo.
echo ==========================================
echo  Recompilando submodulos ONEDIR
echo ==========================================
call "%ROOT%\recompilar_modulos_onedir.bat"
if errorlevel 1 (
    echo ERROR: Fallo la recompilacion ONEDIR de submodulos.
    exit /b 1
)

echo.
echo ==========================================
echo  Compilando ERP_VAH.exe final
echo ==========================================

if exist "%ICON%" (
    "%PYTHON%" -m PyInstaller --noconfirm --clean --onefile --windowed ^
        --name ERP_VAH ^
        --distpath "%FINAL_DIST%" ^
        --workpath "%FINAL_BUILD%" ^
        --specpath "%FINAL_SPEC%" ^
        --paths "%ROOT%" ^
        --hidden-import PyQt6 ^
        --hidden-import common ^
        %THIRD_PARTY_DEPS% ^
        --collect-all PyQt6 ^
        --icon "%ICON%" ^
        --add-data "%ROOT%\common;common" ^
        --add-data "%ROOT%\logo.jpg;." ^
        --add-data "%ROOT%\logo.png;." ^
        --add-data "%ROOT%\logo_principal.jpg;." ^
        --add-data "%ROOT%\logo_principal_pagina.jpg;." ^
        --add-data "%ROOT%\logo_00001.ico;." ^
        --add-data "%ROOT%\manuales\imagenes\comunes\logo_vah.png;manuales/imagenes/comunes" ^
        "%ENTRY%"
) else (
    "%PYTHON%" -m PyInstaller --noconfirm --clean --onefile --windowed ^
        --name ERP_VAH ^
        --distpath "%FINAL_DIST%" ^
        --workpath "%FINAL_BUILD%" ^
        --specpath "%FINAL_SPEC%" ^
        --paths "%ROOT%" ^
        --hidden-import PyQt6 ^
        --hidden-import common ^
        %THIRD_PARTY_DEPS% ^
        --collect-all PyQt6 ^
        --add-data "%ROOT%\common;common" ^
        --add-data "%ROOT%\logo.jpg;." ^
        --add-data "%ROOT%\logo.png;." ^
        --add-data "%ROOT%\logo_principal.jpg;." ^
        --add-data "%ROOT%\logo_principal_pagina.jpg;." ^
        --add-data "%ROOT%\logo_00001.ico;." ^
        --add-data "%ROOT%\manuales\imagenes\comunes\logo_vah.png;manuales/imagenes/comunes" ^
        "%ENTRY%"
)

if errorlevel 1 (
    echo ERROR: Fallo la compilacion del ejecutable principal.
    exit /b 1
)

echo.
echo ==========================================
echo  Compilacion final completada
echo ==========================================
echo Principal:
echo %FINAL_DIST%\ERP_VAH.exe
echo.
echo Modulos:
dir /b "%FINAL_DIST%\*.exe" 2>nul
dir /b "%FINAL_DIST%\Presupuestos" "%FINAL_DIST%\Clientes" "%FINAL_DIST%\Proveedores" "%FINAL_DIST%\CXC" "%FINAL_DIST%\Concentrador" "%FINAL_DIST%\CatalogoGeneralMateriales" 2>nul
exit /b 0
