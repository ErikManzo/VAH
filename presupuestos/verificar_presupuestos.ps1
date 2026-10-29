# verificar_presupuestos.ps1
# Script de verificación completo para el módulo de presupuestos VAH

Write-Host "`n" + "="*70 -ForegroundColor Cyan
Write-Host "           VERIFICACIÓN DEL SISTEMA PRESUPUESTOS VAH" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""

# 1. VERIFICAR RUTA ACTUAL
Write-Host "1. VERIFICANDO RUTA ACTUAL..." -ForegroundColor Yellow
$rutaActual = Get-Location
Write-Host "   📁 Ruta: $rutaActual" -ForegroundColor White

# Verificar si estamos en la ruta correcta
$rutaEsperada = "D:\vah\presupuestos"
if ($rutaActual.Path -eq $rutaEsperada) {
    Write-Host "   ✅ Estás en la ubicación correcta" -ForegroundColor Green
} else {
    Write-Host "   ⚠ No estás en la ruta esperada" -ForegroundColor Yellow
    Write-Host "   Ruta esperada: $rutaEsperada" -ForegroundColor Gray
    Write-Host "   Usa: cd '$rutaEsperada'" -ForegroundColor Gray
}
Write-Host ""

# 2. VERIFICAR ESTRUCTURA DE ARCHIVOS
Write-Host "2. VERIFICANDO ESTRUCTURA DE ARCHIVOS..." -ForegroundColor Yellow

$estructuraCompleta = @(
    # Archivos principales
    @{Nombre = "modulo_presupuestos.py"; Tipo = "Archivo"; Critico = $true},
    @{Nombre = "__init__.py"; Tipo = "Archivo"; Critico = $true},
    @{Nombre = "busquedas.py"; Tipo = "Archivo"; Critico = $true},
    @{Nombre = "foco.py"; Tipo = "Archivo"; Critico = $true},
    @{Nombre = "service.py"; Tipo = "Archivo"; Critico = $false},
    @{Nombre = "rules_zero_price.py"; Tipo = "Archivo"; Critico = $false},
    
    # Directorios
    @{Nombre = "core\"; Tipo = "Directorio"; Critico = $true},
    @{Nombre = "calculators\"; Tipo = "Directorio"; Critico = $false},
    
    # Archivos dentro de core
    @{Nombre = "core\__init__.py"; Tipo = "Archivo"; Critico = $true},
    @{Nombre = "core\constants.py"; Tipo = "Archivo"; Critico = $true},
    @{Nombre = "core\utils.py"; Tipo = "Archivo"; Critico = $true},
    
    # Archivos dentro de calculators
    @{Nombre = "calculators\__init__.py"; Tipo = "Archivo"; Critico = $false},
    @{Nombre = "calculators\dimensioning.py"; Tipo = "Archivo"; Critico = $false}
)

$faltantesCriticos = @()
$faltantesNoCriticos = @()

foreach ($item in $estructuraCompleta) {
    $nombre = $item.Nombre
    $tipo = $item.Tipo
    $critico = $item.Critico
    
    if (Test-Path $nombre) {
        $icono = "✓"
        $color = "Green"
        $estado = "Encontrado"
    } else {
        $icono = "✗"
        $color = "Red"
        $estado = "Faltante"
        
        if ($critico) {
            $faltantesCriticos += $nombre
        } else {
            $faltantesNoCriticos += $nombre
        }
    }
    
    $tipoTexto = if ($tipo -eq "Directorio") { "(Dir)" } else { "(Arch)" }
    Write-Host "   $icono $nombre $tipoTexto" -ForegroundColor $color
}
Write-Host ""

# 3. CREAR ARCHIVOS FALTANTES CRÍTICOS
if ($faltantesCriticos.Count -gt 0) {
    Write-Host "3. CREANDO ARCHIVOS FALTANTES CRÍTICOS..." -ForegroundColor Yellow
    
    foreach ($archivo in $faltantesCriticos) {
        if ($archivo -eq "core\__init__.py") {
            # Crear __init__.py para core
            $contenido = @'
# Core module for presupuestos
from .utils import *
from .constants import *

__all__ = ['utils', 'constants']
'@
            New-Item -Path $archivo -Force -ItemType File | Out-Null
            Set-Content -Path $archivo -Value $contenido -Encoding UTF8
            Write-Host "   ✅ Creado: $archivo" -ForegroundColor Green
            
        } elseif ($archivo -eq "calculators\__init__.py") {
            # Crear __init__.py para calculators
            $contenido = @'
# Calculators module for presupuestos
'@
            # Asegurar que existe el directorio calculators
            if (-not (Test-Path "calculators\")) {
                New-Item -Path "calculators\" -ItemType Directory | Out-Null
            }
            New-Item -Path $archivo -Force -ItemType File | Out-Null
            Set-Content -Path $archivo -Value $contenido -Encoding UTF8
            Write-Host "   ✅ Creado: $archivo" -ForegroundColor Green
            
        } elseif ($archivo.EndsWith("\")) {
            # Es un directorio
            New-Item -Path $archivo -ItemType Directory -Force | Out-Null
            Write-Host "   ✅ Creado directorio: $archivo" -ForegroundColor Green
        }
    }
    Write-Host ""
}

# 4. VERIFICAR PYTHON Y DEPENDENCIAS
Write-Host "4. VERIFICANDO ENTORNO PYTHON..." -ForegroundColor Yellow

try {
    # Verificar versión de Python
    $pythonVersion = python --version 2>&1
    Write-Host "   $pythonVersion" -ForegroundColor White
    
    # Verificar PyQt6
    $testPyQt = @'
try:
    import PyQt6
    from PyQt6.QtCore import PYQT_VERSION_STR
    print(f"PyQt6 {PYQT_VERSION_STR}")
except ImportError:
    print("NO_INSTALADO")
'@
    
    $testPyQt | Out-File -FilePath "test_pyqt.py" -Encoding UTF8
    $pyqtResult = python test_pyqt.py 2>&1
    Remove-Item "test_pyqt.py" -ErrorAction SilentlyContinue
    
    if ($pyqtResult -like "NO_INSTALADO") {
        Write-Host "   ⚠ PyQt6: NO instalado" -ForegroundColor Yellow
        Write-Host "     Ejecuta: pip install PyQt6" -ForegroundColor Gray
    } else {
        Write-Host "   ✅ $pyqtResult" -ForegroundColor Green
    }
    
} catch {
    Write-Host "   ❌ Error al verificar Python: $_" -ForegroundColor Red
}
Write-Host ""

# 5. PROBAR IMPORTACIÓN DEL PAQUETE
Write-Host "5. PROBANDO IMPORTACIÓN DEL PAQUETE..." -ForegroundColor Yellow

$testImport = @'
import sys
import os

print("=== PRUEBA DE IMPORTACIÓN ===")

# Añadir ruta actual
sys.path.insert(0, os.path.abspath('.'))

# Prueba 1: Importar el paquete completo
try:
    import presupuestos
    print("✓ Paquete 'presupuestos' importado")
    
    # Verificar información del paquete
    info = presupuestos.get_package_info()
    print(f"✓ Versión: {info['version']}")
    print(f"✓ Ruta: {info['ruta']}")
    
    # Verificar módulos cargados
    for modulo, estado in info['modulos_cargados'].items():
        status = "CARGADO" if estado else "NO CARGADO"
        print(f"✓ Módulo {modulo}: {status}")
        
except Exception as e:
    print(f"✗ Error importando paquete: {e}")

# Prueba 2: Importar la clase principal
print("\n=== PRUEBA DE CLASE PRINCIPAL ===")
try:
    from presupuestos import PresupuestosWindow
    print("✓ Clase PresupuestosWindow importada")
except Exception as e:
    print(f"✗ Error importando clase: {e}")

# Prueba 3: Verificar imports internos
print("\n=== PRUEBA DE IMPORTS INTERNOS ===")
try:
    from presupuestos.core.constants import C_TIPO, C_CLAVE, WINDOW_TITLE
    print("✓ Constantes importadas")
except Exception as e:
    print(f"✗ Error importando constantes: {e}")

try:
    from presupuestos.core.utils import to_float, to_int
    print("✓ Utilidades importadas")
except Exception as e:
    print(f"✗ Error importando utilidades: {e}")

print("\n=== RESUMEN ===")
try:
    presupuestos.print_package_status()
except:
    print("No se pudo mostrar el estado del paquete")
'@

$testImport | Out-File -FilePath "test_importacion.py" -Encoding UTF8
python test_importacion.py
Remove-Item "test_importacion.py" -ErrorAction SilentlyContinue
Write-Host ""

# 6. PROBAR EJECUCIÓN DIRECTA
Write-Host "6. PROBANDO EJECUCIÓN DIRECTA..." -ForegroundColor Yellow

$testEjecucion = @'
import sys
import os

print("=== PRUEBA DE EJECUCIÓN DIRECTA ===")

# Opción 1: Ejecutar como módulo
print("1. Probando ejecución como módulo...")
try:
    # Simular ejecución como módulo
    sys.path.insert(0, os.path.abspath('.'))
    
    # Cargar el módulo
    import presupuestos
    
    if hasattr(presupuestos, 'main'):
        print("✓ Función main() disponible")
        print("✓ Listo para ejecutar: python -m presupuestos")
    else:
        print("✗ Función main() no disponible")
        
except Exception as e:
    print(f"✗ Error: {e}")

print("\n2. Probando lectura del módulo principal...")
try:
    with open('modulo_presupuestos.py', 'r', encoding='utf-8') as f:
        contenido = f.read(500)
        print("✓ Archivo principal se puede leer")
        print(f"  Primeras líneas:\n  {contenido[:100]}...")
except Exception as e:
    print(f"✗ Error leyendo archivo: {e}")
'@

$testEjecucion | Out-File -FilePath "test_ejecucion.py" -Encoding UTF8
python test_ejecucion.py
Remove-Item "test_ejecucion.py" -ErrorAction SilentlyContinue
Write-Host ""

# 7. MOSTRAR OPCIONES DE EJECUCIÓN
Write-Host "7. OPCIONES DE EJECUCIÓN DISPONIBLES:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   📌 Como módulo (recomendado):" -ForegroundColor White
Write-Host "      python -m presupuestos" -ForegroundColor Cyan
Write-Host ""
Write-Host "   📌 Ejecución directa:" -ForegroundColor White
Write-Host "      python modulo_presupuestos.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "   📌 Desde Python interactivo:" -ForegroundColor White
Write-Host "      python" -ForegroundColor Gray
Write-Host "      >>> import sys" -ForegroundColor DarkGray
Write-Host "      >>> sys.path.insert(0, '.')" -ForegroundColor DarkGray
Write-Host "      >>> from presupuestos import PresupuestosWindow" -ForegroundColor DarkGray
Write-Host "      >>> ventana = PresupuestosWindow()" -ForegroundColor DarkGray
Write-Host ""

# 8. DIAGNÓSTICO FINAL
Write-Host "8. DIAGNÓSTICO FINAL:" -ForegroundColor Yellow

$diagnosticoFinal = @'
import sys
import os

def diagnostico_completo():
    print("="*60)
    print("DIAGNÓSTICO COMPLETO DEL SISTEMA PRESUPUESTOS")
    print("="*60)
    
    # Estado general
    sys.path.insert(0, os.path.abspath('.'))
    
    try:
        import presupuestos
        
        # Obtener información
        info = presupuestos.get_package_info()
        verificacion = presupuestos.verify_installation()
        
        print(f"\n📦 PAQUETE: {info['nombre']} v{info['version']}")
        print(f"📝 {info['descripcion']}")
        print(f"👤 {info['autor']}")
        
        print(f"\n📍 RUTA: {info['ruta']}")
        
        print("\n✅ MÓDULOS CARGADOS:")
        for modulo, estado in info['modulos_cargados'].items():
            icono = "✓" if estado else "✗"
            print(f"   {icono} {modulo}")
        
        print("\n📋 VERIFICACIÓN DE ARCHIVOS:")
        todo_ok = True
        for check, estado in verificacion.items():
            if check != "completo":
                icono = "✓" if estado else "✗"
                color = "\033[92m" if estado else "\033[91m"  # Verde o Rojo
                reset = "\033[0m"
                print(f"   {color}{icono}{reset} {check}")
                if not estado:
                    todo_ok = False
        
        print("\n" + "="*60)
        
        if todo_ok and verificacion.get("completo", False):
            print("🎉 SISTEMA COMPLETAMENTE OPERATIVO")
            print("\n🚀 EJECUTA CON: python -m presupuestos")
            return True
        else:
            print("⚠ PROBLEMAS DETECTADOS")
            print("\n🔧 CORRIGE LOS ARCHIVOS FALTANTES:")
            for check, estado in verificacion.items():
                if check != "completo" and not estado:
                    print(f"   - {check}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print("\n🔧 ACCIONES REQUERIDAS:")
        print("   1. Verifica que todos los archivos existen")
        print("   2. Asegúrate de tener Python 3.8+ instalado")
        print("   3. Instala PyQt6: pip install PyQt6")
        print("   4. Verifica que __init__.py esté presente")
        return False

if __name__ == "__main__":
    if diagnostico_completo():
        # Preguntar si ejecutar
        try:
            respuesta = input("\n¿Ejecutar aplicación ahora? (s/n): ")
            if respuesta.lower() == 's':
                print("\n▶ Iniciando aplicación...")
                from presupuestos import main
                main()
        except:
            pass
    else:
        print("\n❌ No se puede ejecutar hasta resolver los problemas.")
'@

$diagnosticoFinal | Out-File -FilePath "diagnostico_final.py" -Encoding UTF8
python diagnostico_final.py
Remove-Item "diagnostico_final.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "="*70 -ForegroundColor Cyan
Write-Host "           VERIFICACIÓN COMPLETADA" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""

# 9. CREAR SCRIPT DE EJECUCIÓN RÁPIDA
Write-Host "9. CREANDO SCRIPT DE EJECUCIÓN RÁPIDA..." -ForegroundColor Yellow

$scriptEjecucion = @'
@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    SISTEMA DE PRESUPUESTOS VAH v2.0
echo ========================================
echo.
cd /d "%~dp0"
python -m presupuestos
pause
'@

$scriptEjecucion | Out-File -FilePath "ejecutar_presupuestos.bat" -Encoding UTF8
Write-Host "   ✅ Creado: ejecutar_presupuestos.bat" -ForegroundColor Green
Write-Host "   📌 Ejecuta este archivo para iniciar la aplicación" -ForegroundColor White

Write-Host "`n🎯 RESUMEN:" -ForegroundColor Cyan
Write-Host "   • Verifica que todos los archivos críticos existen" -ForegroundColor White
Write-Host "   • Asegúrate de tener PyQt6 instalado" -ForegroundColor White
Write-Host "   • Usa 'python -m presupuestos' para ejecutar" -ForegroundColor White
Write-Host "   • O haz doble clic en 'ejecutar_presupuestos.bat'" -ForegroundColor White

Write-Host "`n✅ PROCESO DE VERIFICACIÓN COMPLETADO" -ForegroundColor Green