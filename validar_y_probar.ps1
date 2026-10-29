# -*- coding: utf-8 -*-
# Script de validación y pruebas post-compilación para ERP VAH 2.0
# Valida ejecutables, recursos y permite lanzar el ERP para pruebas

param(
    [switch]$SoloValidar,      # Solo valida sin lanzar nada
    [switch]$LanzarERP,        # Lanza el ERP principal después de validar
    [switch]$LanzarModulos,    # Lanza todos los módulos para pruebas
    [string]$Modulo,           # Lanza un módulo específico (ej: -Modulo Presupuestos)
    [switch]$Limpio            # Recompila todo antes de validar
)

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$DIST_DIR = Join-Path $ROOT "dist"
$ERP_EXE = Join-Path $DIST_DIR "ERP_VAH.exe"
$MODULOS_DIR = Join-Path $DIST_DIR "ERP_VAH"

# Lista de módulos esperados
$MODULOS_ESPERADOS = @(
    "Presupuestos",
    "Clientes",
    "Proveedores",
    "CXC",
    "Concentrador",
    "CatalogoGeneralMateriales",
    "MaterialesAluminio",
    "MaterialesHerrajes",
    "MaterialesHerreria",
    "MaterialesOtros",
    "MaterialesPlasticos",
    "MaterialesVidrio",
    "PaquetesAluminio",
    "PaquetesHerrajes"
)

# Recursos críticos que deben existir
$RECURSOS_CRITICOS = @(
    "logo.jpg",
    "logo.png",
    "logo_00001.ico",
    "logo_principal.jpg",
    "logo_principal_pagina.jpg",
    "manuales\pdf\operativo",
    "manuales\pdf\técnico"
)

function Write-Header {
    param([string]$Texto)
    Write-Host "`n==========================================" -ForegroundColor Cyan
    Write-Host " $Texto" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
}

function Test-Executables {
    Write-Header "Validación de Ejecutables"

    $resultados = @{
        Existentes = @()
        Faltantes = @()
        Sospechosos = @()
    }

    # Validar ERP principal
    if (Test-Path $ERP_EXE) {
        $size = (Get-Item $ERP_EXE).Length / 1MB
        $resultados.Existentes += "ERP_VAH.exe ($([math]::Round($size, 2)) MB)"
        if ($size -lt 50) {
            $resultados.Sospechosos += "ERP_VAH.exe (tamaño sospechoso: $([math]::Round($size, 2)) MB)"
        }
    } else {
        $resultados.Faltantes += "ERP_VAH.exe"
    }

    # Validar módulos
    foreach ($modulo in $MODULOS_ESPERADOS) {
        $exe_path = Join-Path $MODULOS_DIR "$modulo.exe"
        if (Test-Path $exe_path) {
            $size = (Get-Item $exe_path).Length / 1MB
            $resultados.Existentes += "$modulo.exe ($([math]::Round($size, 2)) MB)"
            if ($size -lt 10) {
                $resultados.Sospechosos += "$modulo.exe (tamaño sospechoso: $([math]::Round($size, 2)) MB)"
            }
        } else {
            $resultados.Faltantes += "$modulo.exe"
        }
    }

    Write-Host "`nExistentes ($($resultados.Existentes.Count)):" -ForegroundColor Green
    $resultados.Existentes | ForEach-Object { Write-Host "  ✓ $_" -ForegroundColor Green }

    if ($resultados.Faltantes.Count -gt 0) {
        Write-Host "`nFaltantes ($($resultados.Faltantes.Count)):" -ForegroundColor Red
        $resultados.Faltantes | ForEach-Object { Write-Host "  ✗ $_" -ForegroundColor Red }
    }

    if ($resultados.Sospechosos.Count -gt 0) {
        Write-Host "`nSospechosos ($($resultados.Sospechosos.Count)):" -ForegroundColor Yellow
        $resultados.Sospechosos | ForEach-Object { Write-Host "  ⚠ $_" -ForegroundColor Yellow }
    }

    return ($resultados.Faltantes.Count -eq 0)
}

function Test-Recursos {
    Write-Header "Validación de Recursos"

    $resultados = @{
        Existentes = @()
        Faltantes = @()
    }

    foreach ($recurso in $RECURSOS_CRITICOS) {
        $path = Join-Path $ROOT $recurso
        if (Test-Path $path) {
            $resultados.Existentes += $recurso
        } else {
            $resultados.Faltantes += $recurso
        }
    }

    Write-Host "`nExistentes ($($resultados.Existentes.Count)):" -ForegroundColor Green
    $resultados.Existentes | ForEach-Object { Write-Host "  ✓ $_" -ForegroundColor Green }

    if ($resultados.Faltantes.Count -gt 0) {
        Write-Host "`nFaltantes ($($resultados.Faltantes.Count)):" -ForegroundColor Yellow
        $resultados.Faltantes | ForEach-Object { Write-Host "   $_" -ForegroundColor Yellow }
    }

    return ($resultados.Faltantes.Count -eq 0)
}

function Test-Compilacion {
    Write-Header "Validación de Compilación"

    $spec_file = Join-Path $ROOT "vah.spec"
    $compilar_script = Join-Path $ROOT "compilar_todo.ps1"

    if (-not (Test-Path $spec_file)) {
        Write-Host "ERROR: No existe vah.spec" -ForegroundColor Red
        return $false
    }

    if (-not (Test-Path $compilar_script)) {
        Write-Host "ERROR: No existe compilar_todo.ps1" -ForegroundColor Red
        return $false
    }

    Write-Host "✓ vah.spec existe" -ForegroundColor Green
    Write-Host "✓ compilar_todo.ps1 existe" -ForegroundColor Green

    return $true
}

function Start-ERP {
    Write-Header "Lanzando ERP Principal"

    if (-not (Test-Path $ERP_EXE)) {
        Write-Host "ERROR: No existe ERP_VAH.exe" -ForegroundColor Red
        return
    }

    Write-Host "Ejecutando: $ERP_EXE" -ForegroundColor Cyan
    Start-Process -FilePath $ERP_EXE -WorkingDirectory $ROOT
    Write-Host "ERP lanzado correctamente" -ForegroundColor Green
}

function Start-Modulo {
    param([string]$NombreModulo)

    $exe_path = Join-Path $MODULOS_DIR "$NombreModulo.exe"

    if (-not (Test-Path $exe_path)) {
        Write-Host "ERROR: No existe $NombreModulo.exe" -ForegroundColor Red
        return
    }

    Write-Host "Ejecutando: $exe_path" -ForegroundColor Cyan
    Start-Process -FilePath $exe_path -WorkingDirectory $ROOT
    Write-Host "$NombreModulo lanzado correctamente" -ForegroundColor Green
}

function Start-TodosModulos {
    Write-Header "Lanzando Todos los Módulos"

    foreach ($modulo in $MODULOS_ESPERADOS) {
        Start-Modulo -NombreModulo $modulo
        Start-Sleep -Seconds 1
    }
}

# ===================== MAIN =====================
Write-Header "VALIDACIÓN Y PRUEBAS - ERP VAH 2.0"

# Si se solicita recompilación limpia
if ($Limpio) {
    Write-Host "Recompilando todo..." -ForegroundColor Yellow
    & (Join-Path $ROOT "compilar_todo.ps1") -Limpio
}

# Validaciones
$compilacion_ok = Test-Compilacion
$ejecutables_ok = Test-Executables
$recursos_ok = Test-Recursos

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host " RESUMEN DE VALIDACIÓN" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Compilación:    $(if ($compilacion_ok) { '✓ OK' } else { '✗ FALLÓ' })" -ForegroundColor $(if ($compilacion_ok) { 'Green' } else { 'Red' })
Write-Host "Ejecutables:    $(if ($ejecutables_ok) { '✓ OK' } else { ' FALLÓ' })" -ForegroundColor $(if ($ejecutables_ok) { 'Green' } else { 'Red' })
Write-Host "Recursos:       $(if ($recursos_ok) { '✓ OK' } else { '⚠ INCOMPLETO' })" -ForegroundColor $(if ($recursos_ok) { 'Green' } else { 'Yellow' })

if (-not ($ejecutables_ok -and $compilacion_ok)) {
    Write-Host "`nERROR: La validación falló. Ejecute compilar_todo.ps1 -Limpio" -ForegroundColor Red
    exit 1
}

# Acciones post-validación
if ($SoloValidar) {
    Write-Host "`nValidación completada. No se lanzó ningún ejecutable." -ForegroundColor Cyan
    exit 0
}

if ($Modulo) {
    Write-Header "Lanzando Módulo: $Modulo"
    Start-Modulo -NombreModulo $Modulo
    exit 0
}

if ($LanzarModulos) {
    Start-TodosModulos
    exit 0
}

if ($LanzarERP) {
    Start-ERP
    exit 0
}

# Por defecto, lanzar el ERP principal
Write-Host "`nLanzando ERP principal para pruebas..." -ForegroundColor Cyan
Start-ERP
