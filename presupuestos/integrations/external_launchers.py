# -*- coding: utf-8 -*-
"""
Funciones para lanzar otros módulos del ERP desde Presupuestos.
Centraliza la lógica de subprocess y manejo de rutas.
"""
import os
import subprocess
import sys
from typing import Optional, Sequence
from PyQt6.QtWidgets import QMessageBox, QWidget
from common.app_paths import get_app_root
from common.logger_config import get_logger, setup_logger
setup_logger("presupuestos.integrations.launchers")
logger = get_logger("presupuestos.integrations.launchers")

# Mapeo de rutas de scripts (relativas a VAH_ROOT) a nombres de ejecutables amigables.
# Se incluyen alias para permitir lanzar el mismo módulo desde distintos entrypoints.
MAPEO_EJECUTABLES = {
    os.path.normpath(r"presupuestos\modulo_presupuestos.py").lower(): "Presupuestos.exe",
    os.path.normpath(r"clientes\main.py").lower(): "Clientes.exe",
    os.path.normpath(r"clientes\art\pantalla_clientes.py").lower(): "Clientes.exe",
    os.path.normpath(r"proveedores\main.py").lower(): "Proveedores.exe",
    os.path.normpath(r"proveedores\art\pantalla_proveedores.py").lower(): "Proveedores.exe",
    os.path.normpath(r"cxc\main.py").lower(): "CXC.exe",
    os.path.normpath(r"cxc\art\pantalla_cxc.py").lower(): "CXC.exe",
    os.path.normpath(r"concentrador_materiales\ui\pantalla_concentrador.py").lower(): "Concentrador.exe",
    os.path.normpath(r"materiales\pantalla_catalogo_general.py").lower(): "CatalogoGeneralMateriales.exe",
    os.path.normpath(r"materiales\aluminio\pantalla_materiales_aluminio.py").lower(): "MaterialesAluminio.exe",
    os.path.normpath(r"materiales\herrajes\pantalla_herrajes.py").lower(): "MaterialesHerrajes.exe",
    os.path.normpath(r"materiales\herreria\pantalla_herreria.py").lower(): "MaterialesHerreria.exe",
    os.path.normpath(r"materiales\otros\pantalla_otros.py").lower(): "MaterialesOtros.exe",
    os.path.normpath(r"materiales\plasticos\pantalla_plasticos.py").lower(): "MaterialesPlasticos.exe",
    os.path.normpath(r"materiales\vidrio\pantalla_vidrio.py").lower(): "MaterialesVidrio.exe",
    os.path.normpath(r"paquetes\aluminio\pantalla_paquete_aluminio.py").lower(): "PaquetesAluminio.exe",
    os.path.normpath(r"paquetes\herrajes\pantalla_paquete_herrajes.py").lower(): "PaquetesHerrajes.exe",
}

# Rutas base dinámicas
VAH_ROOT = get_app_root()

def _popen_kwargs() -> dict:
    """
    Retorna argumentos para subprocess.Popen que suprimen completamente
    la ventana de consola en Windows.
    """
    kwargs = {
        "shell": False,
        "creationflags": 0x08000000,  # CREATE_NO_WINDOW
        "close_fds": True if os.name == "nt" else False,
    }
    # En Windows, también usamos STARTUPINFO para ocultar la ventana.
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        kwargs["startupinfo"] = startupinfo
    return kwargs

def _normalizar_ruta_relativa(path: str) -> str:
    return os.path.normpath(path).lower()

def _obtener_ruta_relativa(path: str) -> str:
    if os.path.isabs(path):
        try:
            return _normalizar_ruta_relativa(os.path.relpath(path, VAH_ROOT))
        except ValueError:
            return _normalizar_ruta_relativa(path)
    return _normalizar_ruta_relativa(path)

def _obtener_bases_lanzamiento() -> list[str]:
    if not getattr(sys, "frozen", False):
        return [VAH_ROOT]
    exe_dir = os.path.dirname(sys.executable)
    candidates = [exe_dir]
    parent_dir = os.path.dirname(exe_dir)
    if parent_dir and parent_dir not in candidates:
        candidates.append(parent_dir)
    if VAH_ROOT not in candidates:
        candidates.append(VAH_ROOT)
    return candidates

def _resolver_ejecutable_compilado(path: str) -> tuple[Optional[str], str]:
    ruta_relativa = _obtener_ruta_relativa(path)
    nombre_ejecutable = MAPEO_EJECUTABLES.get(ruta_relativa)
    if not nombre_ejecutable:
        return None, ruta_relativa
    nombre_modulo = os.path.splitext(nombre_ejecutable)[0]
    candidatos: list[str] = []
    for base_dir in _obtener_bases_lanzamiento():
        for exe_path in (
            os.path.join(base_dir, nombre_ejecutable),
            os.path.join(base_dir, nombre_modulo, nombre_ejecutable),
        ):
            if exe_path not in candidatos:
                candidatos.append(exe_path)
    for exe_path in candidatos:
        if os.path.isfile(exe_path):
            return exe_path, ruta_relativa
    return candidatos[0], ruta_relativa

def _launch_py_module(
    path: str,
    title: str,
    parent: Optional[QWidget] = None,
    args: Optional[Sequence[str]] = None,
) -> bool:
    """
    Lanza un módulo (archivo .py o ejecutable compilado).
    Primero intenta usar el ejecutable mapeado (modo compilado).
    Si no existe, intenta ejecutar el .py original (modo desarrollo o fallback).
    """
    # Siempre intentar resolver ejecutable compilado
    exe_path, ruta_relativa = _resolver_ejecutable_compilado(path)
    extra_args = list(args or [])
    # Si existe el ejecutable, usarlo
    if exe_path and os.path.exists(exe_path):
        try:
            subprocess.Popen(
                [exe_path, *extra_args],
                cwd=os.path.dirname(exe_path) or VAH_ROOT,
                **_popen_kwargs(),
            )
            logger.info("Módulo lanzado (compilado): %s - %s", title, exe_path)
            return True
        except Exception as e:
            logger.exception("Error al lanzar ejecutable %s: %s", title, e)
            # Si falla el ejecutable, no intentamos .py (podría ser opcional)
            if parent:
                QMessageBox.critical(parent, "Error", f"No se pudo abrir {title}:\n{str(e)}")
            return False
    # Si no hay ejecutable, intentar con el .py (modo desarrollo)
    if os.path.exists(path):
        try:
            subprocess.Popen(
                [sys.executable, path, *extra_args],
                cwd=VAH_ROOT,
                **_popen_kwargs(),
            )
            logger.info("Módulo lanzado (script): %s - %s", title, path)
            return True
        except Exception as e:
            logger.exception("Error al lanzar script %s: %s", title, e)
            if parent:
                QMessageBox.critical(parent, "Error", f"No se pudo abrir {title}:\n{str(e)}")
            return False
    # Si nada funciona, mostrar error
    message = (
        f"No se pudo abrir {title}.\n\n"
        f"No se encontró el ejecutable esperado:\n{exe_path if exe_path else 'No mapeado'}\n"
        f"Ni el script original:\n{path}\n\n"
        "Verifique la instalación."
    )
    logger.error("No se pudo lanzar %s: %s", title, message)
    if parent:
        QMessageBox.warning(parent, "Módulo no disponible", message)
    return False

# Las funciones de apertura permanecen igual (no cambian)
def abrir_catalogo_clientes(parent: Optional[QWidget] = None) -> bool:
    """Abre el catálogo de clientes."""
    path = os.path.join(VAH_ROOT, "clientes", "main.py")
    return _launch_py_module(path, "Clientes", parent)

def abrir_catalogo_proveedores(parent: Optional[QWidget] = None) -> bool:
    """Abre el catálogo de proveedores."""
    path = os.path.join(VAH_ROOT, "proveedores", "art", "pantalla_proveedores.py")
    return _launch_py_module(path, "Proveedores", parent)

def abrir_paquetes_aluminio(parent: Optional[QWidget] = None) -> bool:
    """Abre la ventana de paquetes de aluminio."""
    path = os.path.join(VAH_ROOT, "paquetes", "aluminio", "pantalla_paquete_aluminio.py")
    return _launch_py_module(path, "Paquetes Aluminio", parent)

def abrir_paquetes_herrajes(parent: Optional[QWidget] = None) -> bool:
    """Abre la ventana de paquetes de herrajes."""
    path = os.path.join(VAH_ROOT, "paquetes", "herrajes", "pantalla_paquete_herrajes.py")
    return _launch_py_module(path, "Paquetes Herrajes", parent)

def abrir_concentrador_materiales(parent: Optional[QWidget] = None) -> bool:
    """Abre el concentrador de materiales (explosión)."""
    path = os.path.join(VAH_ROOT, "concentrador_materiales", "ui", "pantalla_concentrador.py")
    return _launch_py_module(path, "Concentrador de Materiales", parent)

def abrir_catalogo_general_materiales(parent: Optional[QWidget] = None) -> bool:
    """Abre el catálogo general de materiales."""
    path = os.path.join(VAH_ROOT, "materiales", "pantalla_catalogo_general.py")
    return _launch_py_module(path, "Catálogo General de Materiales", parent)

def abrir_materiales_aluminio(parent: Optional[QWidget] = None) -> bool:
    """Abre el catálogo de materiales de aluminio."""
    path = os.path.join(VAH_ROOT, "materiales", "aluminio", "pantalla_materiales_aluminio.py")
    return _launch_py_module(path, "Materiales Aluminio", parent)

def abrir_materiales_herrajes(parent: Optional[QWidget] = None) -> bool:
    """Abre el catálogo de materiales de herrajes."""
    path = os.path.join(VAH_ROOT, "materiales", "herrajes", "pantalla_herrajes.py")
    return _launch_py_module(path, "Materiales Herrajes", parent)

def abrir_materiales_herreria(parent: Optional[QWidget] = None) -> bool:
    """Abre el catálogo de materiales de herrería."""
    path = os.path.join(VAH_ROOT, "materiales", "herreria", "pantalla_herreria.py")
    return _launch_py_module(path, "Materiales Herrería", parent)

def abrir_materiales_vidrio(parent: Optional[QWidget] = None) -> bool:
    """Abre el catálogo de materiales de vidrio."""
    path = os.path.join(VAH_ROOT, "materiales", "vidrio", "pantalla_vidrio.py")
    return _launch_py_module(path, "Materiales Vidrio", parent)

def abrir_materiales_plasticos(parent: Optional[QWidget] = None) -> bool:
    """Abre el catálogo de materiales plásticos."""
    path = os.path.join(VAH_ROOT, "materiales", "plasticos", "pantalla_plasticos.py")
    return _launch_py_module(path, "Materiales Plásticos", parent)

def abrir_materiales_otros(parent: Optional[QWidget] = None) -> bool:
    """Abre el catálogo de materiales de otros."""
    path = os.path.join(VAH_ROOT, "materiales", "otros", "pantalla_otros.py")
    return _launch_py_module(path, "Materiales Otros", parent)

def abrir_paquetes_herrajes_con_args(
    parent: Optional[QWidget] = None,
    server: Optional[str] = None,
    database: Optional[str] = None,
) -> bool:
    """Abre el módulo de paquetes de herrajes conservando parámetros de conexión."""
    path = os.path.join(VAH_ROOT, "paquetes", "herrajes", "pantalla_paquete_herrajes.py")
    args = []
    if server:
        args.extend(["--server", server])
    if database:
        args.extend(["--database", database])
    return _launch_py_module(path, "Paquetes Herrajes", parent, args=args)

def abrir_lista_materiales(parent: Optional[QWidget] = None) -> bool:
    """Abre el concentrador (alias de abrir_concentrador_materiales)."""
    return abrir_concentrador_materiales(parent)

def abrir_modulo_presupuestos_otra_ventana(parent: Optional[QWidget] = None):
    """Abre una nueva ventana de Presupuestos (mismo módulo)."""
    from presupuestos.modulo_presupuestos import PresupuestosWindow
    nueva = PresupuestosWindow()
    nueva.show()
    if parent is not None:
        ventanas = getattr(parent, "_ventanas_hijas", None)
        if ventanas is None:
            ventanas = []
            setattr(parent, "_ventanas_hijas", ventanas)
        ventanas.append(nueva)
    logger.info("Nueva ventana de Presupuestos abierta")
    return nueva