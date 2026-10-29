@echo off
REM ============================================================
REM COMPILAR LIMPIO - Borra todo y recompila desde cero
REM Usar SOLO cuando compilar_rapido.bat falle
REM Tiempo: 1-3 minutos
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo   COMPILANDO ERP VAH (MODO LIMPIO)
echo   Esto toma aproximadamente 1-3 minutos
echo ============================================================
echo.

REM Activar entorno virtual
call .venv_aider_312\Scripts\activate.bat

REM Borrar builds anteriores
echo Borrando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Compilar desde cero
pyinstaller vah.spec --clean

echo.
if errorlevel 1 (
    echo ============================================================
    echo   ERROR EN LA COMPILACION LIMPIA
    echo   Revisa los mensajes de error arriba
    echo ============================================================
) else (
    echo ============================================================
    echo   COMPILACION EXITOSA
    echo   Ejecutable en: dist\ERP_VAH.exe
    echo ============================================================
)
pause