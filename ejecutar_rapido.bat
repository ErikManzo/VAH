@echo off
REM ============================================================
REM EJECUTAR RAPIDO - Para desarrollo y pruebas
REM NO compila, ejecuta directamente con Python
REM Tiempo: 2-3 segundos
REM ============================================================

REM Ir a la carpeta donde está este archivo
cd /d "%~dp0"

echo.
echo ============================================================
echo   EJECUTANDO ERP VAH (MODO DESARROLLO)
echo ============================================================
echo.

REM Activar el entorno virtual
call .venv_aider_312\Scripts\activate.bat

REM Ejecutar la pantalla principal directamente
python principal\pantalla_principal.py

REM Si hay error, pausar para ver el mensaje
if errorlevel 1 (
    echo.
    echo ============================================================
    echo   HUBO UN ERROR - Revisa el mensaje arriba
    echo ============================================================
    pause
)