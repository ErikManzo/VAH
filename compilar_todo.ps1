# -*- coding: utf-8 -*-
# Script de compilación completa para ERP VAH 2.0
# Compila 14 módulos independientes + ERP principal

param(
    [switch]$Limpio,  # Limpia build/dist antes de compilar
    [switch]$SoloModulos,  # Solo compila módulos, no el ERP principal
    [switch]$SoloERP  # Solo compila el ERP principal, no los módulos
)

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$VENV_DIR = Join-Path $ROOT ".venv_aider_312"
$PYTHON = Join-Path $VENV_DIR "Scripts\python.exe"
$ACTIVATE = Join-Path $VENV_DIR "Scripts\activate.ps1"
$OUT_DIR = Join-Path $ROOT "dist\ERP_VAH"
$BUILD_DIR = Join-Path $ROOT "build"
$ICON = Join-Path $ROOT "logo_00001.ico"

# Módulos a compilar
$MODULOS = @(
    @{Nombre="Presupuestos"; Entry="presupuestos\modulo_presupuestos.py"},
    @{Nombre="Clientes"; Entry="clientes\main.py"},
    @{Nombre="Proveedores"; Entry="proveedores\main.py"},
    @{Nombre="CXC"; Entry="cxc\main.py"},
    @{Nombre="Concentrador"; Entry="concentrador_materiales\ui\pantalla_concentrador.py"},
    @{Nombre="CatalogoGeneralMateriales"; Entry="materiales\pantalla_catalogo_general.py"},
    @{Nombre="MaterialesAluminio"; Entry="materiales\aluminio\pantalla_materiales_aluminio.py"},
    @{Nombre="MaterialesHerrajes"; Entry="materiales\herrajes\pantalla_herrajes.py"},
    @{Nombre="MaterialesHerreria"; Entry="materiales\herreria\pantalla_herreria.py"},
    @{Nombre="MaterialesOtros"; Entry="materiales\otros\pantalla_otros.py"},
    @{Nombre="MaterialesPlasticos"; Entry="materiales\plasticos\pantalla_plasticos.py"},
    @{Nombre="MaterialesVidrio"; Entry="materiales\vidrio\pantalla_vidrio.py"},
    @{Nombre="PaquetesAluminio"; Entry="paquetes\aluminio\pantalla_paquete_aluminio.py"},
    @{Nombre="PaquetesHerrajes"; Entry="paquetes\herrajes\pantalla_paquete_herrajes.py"}
)

# Dependencias de terceros para PyInstaller
$THIRD_PARTY_DEPS = @(
    "--hidden-import", "reportlab",
    "--hidden-import", "pdfplumber",
    "--hidden-import", "openpyxl",
    "--hidden-import", "pandas",
    "--collect-all", "reportlab",
    "--collect-all", "pdfplumber",
    "--collect-all", "openpyxl",
    "--collect-all", "pandas"
)

function Write-Header {
    param([string]$Texto)
    Write-Host "`n==========================================" -ForegroundColor Cyan
    Write-Host " $Texto" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
}

function Test-Entorno {
    Write-Header "Verificando entorno"

    if (-not (Test-Path $PYTHON)) {
        Write-Host "ERROR: No se encontró el intérprete: $PYTHON" -ForegroundColor Red
        exit 1
    }

    if (-not (Test-Path $ACTIVATE)) {
        Write-Host "ERROR: No se encontró el activador: $ACTIVATE" -ForegroundColor Red
        exit 1
    }

    Write-Host "Python: $PYTHON" -ForegroundColor Green
    Write-Host "Root: $ROOT" -ForegroundColor Green
}

function Install-Dependencias {
    Write-Header "Instalando dependencias"

    & $PYTHON -m pip install --upgrade pip setuptools wheel
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Fallo al actualizar pip" -ForegroundColor Red
        exit 1
    }

    $requirements = Join-Path $ROOT "requirements.txt"
    if (Test-Path $requirements) {
        & $PYTHON -m pip install -r $requirements
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Fallo al instalar requirements.txt" -ForegroundColor Red
            exit 1
        }
    }

    Write-Host "Dependencias instaladas correctamente" -ForegroundColor Green
}

function Clean-Build {
    Write-Header "Limpiando builds previos"

    $dirs_to_clean = @(
        (Join-Path $ROOT "build"),
        (Join-Path $ROOT "dist"),
        (Join-Path $ROOT "__pycache__")
    )

    foreach ($dir in $dirs_to_clean) {
        if (Test-Path $dir) {
            Write-Host "Eliminando: $dir" -ForegroundColor Yellow
            Remove-Item -Recurse -Force $dir
        }
    }

    # Limpiar __pycache__ en subdirectorios
    Get-ChildItem -Path $ROOT -Recurse -Directory -Filter "__pycache__" -Force | ForEach-Object {
        Remove-Item -Recurse -Force $_.FullName
    }

    Write-Host "Limpieza completada" -ForegroundColor Green
}

function Build-Modulo {
    param(
        [string]$Nombre,
        [string]$Entry
    )

    $entry_path = Join-Path $ROOT $Entry
    if (-not (Test-Path $entry_path)) {
        Write-Host "[ERROR] No existe: $entry_path" -ForegroundColor Red
        return $false
    }

    Write-Host "`n[Compilando] $Nombre" -ForegroundColor Cyan
    Write-Host "  Entry: $Entry" -ForegroundColor Gray

    $work_dir = Join-Path (Join-Path $ROOT "build") "modulos\$Nombre"
    $spec_dir = Join-Path (Join-Path $ROOT "build") "modulos_specs"

    if (Test-Path $work_dir) { Remove-Item -Recurse -Force $work_dir }
    New-Item -ItemType Directory -Force -Path $work_dir | Out-Null
    New-Item -ItemType Directory -Force -Path $spec_dir | Out-Null

    $pyi_args = @(
        "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile", "--windowed",
        "--name", $Nombre,
        "--paths", $ROOT,
        "--distpath", (Join-Path $ROOT "dist\modulos_temp"),
        "--workpath", $work_dir,
        "--specpath", $spec_dir,
        "--hidden-import", "PyQt6",
        "--hidden-import", "PyQt6.sip",
        "--hidden-import", "pyodbc",
        "--hidden-import", "win32print"
    ) + $THIRD_PARTY_DEPS

    if (Test-Path $ICON) {
        $pyi_args += @("--icon", $ICON, "--add-data", "$ROOT\logo_00001.ico;.", "--add-data", "$ROOT\logo.jpg;.", "--add-data", "$ROOT\logo.png;.")
    } else {
        $pyi_args += @("--add-data", "$ROOT\logo_00001.ico;.", "--add-data", "$ROOT\logo.jpg;.", "--add-data", "$ROOT\logo.png;.")
    }

    $pyi_args += $entry_path

    & $PYTHON @pyi_args

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [FALLÓ] $Nombre" -ForegroundColor Red
        return $false
    }

    $exe_temp = Join-Path (Join-Path $ROOT "dist\modulos_temp") "$Nombre.exe"
    if (Test-Path $exe_temp) {
        Copy-Item -Force $exe_temp (Join-Path $OUT_DIR "$Nombre.exe")
        Write-Host "  [OK] $Nombre.exe" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  [FALLÓ] No se generó $Nombre.exe" -ForegroundColor Red
        return $false
    }
}

function Build-ERP-Principal {
    Write-Header "Compilando ERP_VAH.exe (principal)"

    $spec_file = Join-Path $ROOT "vah.spec"
    if (-not (Test-Path $spec_file)) {
        Write-Host "ERROR: No existe vah.spec" -ForegroundColor Red
        return $false
    }

    # Cuando se usa un archivo .spec, SOLO se pasan --noconfirm y --clean
    # NO se pasan --specpath, --icon, --distpath, --workpath porque ya están en el .spec
    $pyi_args = @(
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        $spec_file
    )

    & $PYTHON @pyi_args

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Fallo la compilación del ERP principal" -ForegroundColor Red
        return $false
    }

    # vah.spec genera ERP_VAH.exe en dist/ (raíz), no en dist/ERP_VAH/
    $exe_source = Join-Path $ROOT "dist\ERP_VAH.exe"
    if (Test-Path $exe_source) {
        # Copiar a la carpeta de módulos para mantener consistencia
        Copy-Item -Force $exe_source (Join-Path $OUT_DIR "ERP_VAH.exe")
        Write-Host "ERP_VAH.exe generado y copiado correctamente" -ForegroundColor Green
        return $true
    } else {
        Write-Host "ERROR: No se generó ERP_VAH.exe en $exe_source" -ForegroundColor Red
        return $false
    }
}

# ===================== MAIN =====================
Write-Header "COMPILACIÓN COMPLETA - ERP VAH 2.0"

Test-Entorno

# Activar entorno virtual
. $ACTIVATE

if ($Limpio) {
    Clean-Build
}

Install-Dependencias

if (-not (Test-Path $OUT_DIR)) {
    New-Item -ItemType Directory -Force -Path $OUT_DIR | Out-Null
}

$resultados = @{
    Exitosos = @()
    Fallidos = @()
}

# Compilar módulos
if (-not $SoloERP) {
    Write-Header "Compilando módulos independientes"

    foreach ($modulo in $MODULOS) {
        $exito = Build-Modulo -Nombre $modulo.Nombre -Entry $modulo.Entry
        if ($exito) {
            $resultados.Exitosos += $modulo.Nombre
        } else {
            $resultados.Fallidos += $modulo.Nombre
        }
    }
}

# Compilar ERP principal
if (-not $SoloModulos) {
    $exito_erp = Build-ERP-Principal
    if ($exito_erp) {
        $resultados.Exitosos += "ERP_VAH (principal)"
    } else {
        $resultados.Fallidos += "ERP_VAH (principal)"
    }
}

# Resumen final
Write-Header "RESUMEN DE COMPILACIÓN"
Write-Host "`nExitosos ($($resultados.Exitosos.Count)):" -ForegroundColor Green
$resultados.Exitosos | ForEach-Object { Write-Host "  ✓ $_" -ForegroundColor Green }

if ($resultados.Fallidos.Count -gt 0) {
    Write-Host "`nFallidos ($($resultados.Fallidos.Count)):" -ForegroundColor Red
    $resultados.Fallidos | ForEach-Object { Write-Host "  ✗ $_" -ForegroundColor Red }
}

Write-Host "`nArchivos generados en: $OUT_DIR" -ForegroundColor Cyan
if (Test-Path $OUT_DIR) {
    Get-ChildItem $OUT_DIR -Filter "*.exe" | ForEach-Object {
        Write-Host "  $($_.Name) ($([math]::Round($_.Length / 1MB, 2)) MB)" -ForegroundColor Gray
    }
}

Write-Host "`n==========================================" -ForegroundColor Cyan
if ($resultados.Fallidos.Count -eq 0) {
    Write-Host "COMPILACIÓN COMPLETADA EXITOSAMENTE" -ForegroundColor Green
} else {
    Write-Host "COMPILACIÓN COMPLETADA CON ERRORES" -ForegroundColor Yellow
}
Write-Host "==========================================`n" -ForegroundColor Cyan
