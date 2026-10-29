@echo off
REM ============================================================
REM COMPILAR RAPIDO - Mantiene caché de compilaciones previas
REM Solo recompila lo que cambió
REM Tiempo: 30-60 segundos
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo   COMPILANDO ERP VAH (MODO RAPIDO)
echo   Esto toma aproximadamente 30-60 segundos
echo ============================================================
echo.

REM Activar entorno virtual
call .venv_aider_312\Scripts\activate.bat

REM Compilar SIN borrar build/dist (más rápido)
pyinstaller vah.spec

echo.
if errorlevel 1 (
    echo ============================================================
    echo   ERROR EN LA COMPILACION
    echo   Usa compilar_limpio.bat si el problema persiste
    echo ============================================================
) else (
    echo ============================================================
    echo   COMPILACION EXITOSA
    echo   Ejecutable en: dist\ERP_VAH.exe
    echo ============================================================
)
pause