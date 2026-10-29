# -*- coding: utf-8 -*-
# Script de compilación del ERP principal VAH
# Usa vah.spec en lugar de ERP_VAH.spec

param(
    [switch]$Limpio  # Limpia builds previos
)

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$VENV_DIR = Join-Path $ROOT ".venv_aider_312"
$PYTHON = Join-Path $VENV_DIR "Scripts\python.exe"
$ACTIVATE = Join-Path $VENV_DIR "Scripts\activate.ps1"
$SPEC_FILE = Join-Path $ROOT "vah.spec"
$BUILD_DIR = Join-Path $ROOT "build\vah"
$DIST_DIR = Join-Path $ROOT "dist"
$ERP_EXE = Join-Path $DIST_DIR "ERP_VAH.exe"

function Write-Header {
    param([string]$Texto)
    Write-Host "`n==========================================" -ForegroundColor Cyan
    Write-Host " $Texto" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
}

Write-Header "COMPILACIÓN ERP_VAH.exe - PRINCIPAL"

# Verificar Python
if (-not (Test-Path $PYTHON)) {
    Write-Host "ERROR: No se encontró Python en: $PYTHON" -ForegroundColor Red
    exit 1
}
Write-Host "Python: $PYTHON" -ForegroundColor Green

# Verificar vah.spec
if (-not (Test-Path $SPEC_FILE)) {
    Write-Host "ERROR: No se encontró vah.spec en: $SPEC_FILE" -ForegroundColor Red
    exit 1
}
Write-Host "Spec file: $SPEC_FILE" -ForegroundColor Green

# Activar entorno virtual
Write-Host "`nActivando entorno virtual..." -ForegroundColor Yellow
. $ACTIVATE

# Limpiar si se solicita
if ($Limpio) {
    Write-Header "Limpieza de builds previos"
    if (Test-Path $BUILD_DIR) {
        Write-Host "Eliminando: $BUILD_DIR" -ForegroundColor Yellow
        Remove-Item -Recurse -Force $BUILD_DIR
    }
    if (Test-Path $ERP_EXE) {
        Write-Host "Eliminando: $ERP_EXE" -ForegroundColor Yellow
        Remove-Item -Force $ERP_EXE
    }
    # Limpiar archivos temporales de PyInstaller
    Get-ChildItem $ROOT -Filter "*.spec" | Where-Object { $_.Name -ne "vah.spec" } | Remove-Item -Force
}

# Instalar dependencias
Write-Header "Instalando dependencias"
& $PYTHON -m pip install --upgrade pip setuptools wheel
$requirements = Join-Path $ROOT "requirements.txt"
if (Test-Path $requirements) {
    & $PYTHON -m pip install -r $requirements
}

# Compilar con PyInstaller
Write-Header "Compilando ERP_VAH.exe"
Write-Host "Ejecutando PyInstaller..." -ForegroundColor Yellow

$pyiArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    $SPEC_FILE
)

& $PYTHON @pyiArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nERROR: Fallo la compilación con PyInstaller" -ForegroundColor Red
    exit 1
}

# Verificar resultado
Write-Header "Verificando resultado"
if (Test-Path $ERP_EXE) {
    $exeInfo = Get-Item $ERP_EXE
    $sizeMB = [math]::Round($exeInfo.Length / 1MB, 2)
    Write-Host "`n✓ ERP_VAH.exe generado exitosamente" -ForegroundColor Green
    Write-Host "  Ubicación: $ERP_EXE" -ForegroundColor Gray
    Write-Host "  Tamaño: $sizeMB MB" -ForegroundColor Gray
    Write-Host "  Fecha: $($exeInfo.LastWriteTime)" -ForegroundColor Gray
} else {
    Write-Host "`nERROR: No se generó ERP_VAH.exe" -ForegroundColor Red
    Write-Host "Buscando ejecutables en dist/..." -ForegroundColor Yellow
    Get-ChildItem $DIST_DIR -Filter "*.exe" -Recurse | ForEach-Object {
        Write-Host "  Encontrado: $($_.Name)" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host " COMPILACIÓN COMPLETADA EXITOSAMENTE" -ForegroundColor Green
Write-Host "==========================================`n" -ForegroundColor Green
