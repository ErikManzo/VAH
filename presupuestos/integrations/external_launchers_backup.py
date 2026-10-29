# -*- coding: utf-8 -*-
"""
Funciones para lanzar otros modulos del ERP desde Presupuestos.
Centraliza la logica de subprocess y manejo de rutas.
"""
import os
import subprocess
import sys
from typing import Optional

from PyQt6.QtWidgets import QMessageBox, QWidget

from common.app_paths import get_app_root
from common.logger_config import get_logger, setup_logger

setup_logger("presupuestos.integrations.launchers")
logger = get_logger("presupuestos.integrations.launchers")

# Mapeo de rutas de scripts (relativas a VAH_ROOT) a nombres de ejecutables amigables.
# Se incluyen alias para permitir lanzar el mismo modulo desde distintos entrypoints.
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

# Rutas base dinamicas
VAH_ROOT = get_app_root()


def _normalizar_ruta_relativa(path: str) -> str:
    return os.path.normpath(path).lower()


def _obtener_ruta_relativa(path: str) -> str:
    if os.path.isabs(path):
        try:
            return _normalizar_ruta_relativa(os.path.relpath(path, VAH_ROOT))
        except ValueError:
            return _normalizar_ruta_relativa(path)
    return _normalizar_ruta_relativa(path)


def _resolver_ejecutable_compilado(path: str) -> tuple[Optional[str], str]:
    ruta_relativa = _obtener_ruta_relativa(path)
    nombre_ejecutable = MAPEO_EJECUTABLES.get(ruta_relativa)
    if not nombre_ejecutable:
        return None, ruta_relativa
    return os.path.join(VAH_ROOT, nombre_ejecutable), ruta_relativa


def _launch_py_module(path: str, title: str, parent: Optional[QWidget] = None) -> bool:
    """Lanza un archivo .py como proceso independiente."""
    is_frozen = getattr(sys, "frozen", False)
    if is_frozen:
        exe_path, ruta_relativa = _resolver_ejecutable_compilado(path)
        if not exe_path:
            message = (
                f"No se pudo abrir {title} en modo compilado.\n\n"
                f"No existe un ejecutable mapeado para:\n{ruta_relativa}\n\n"
                "Agregue el modulo al MAPEO_EJECUTABLES y recompílelo."
            )
            logger.error("No hay mapeo de ejecutable para %s (%s)", title, ruta_relativa)
            if parent:
                QMessageBox.warning(parent, "Modulo no disponible", message)
            return False
        if not os.path.exists(exe_path):
            message = (
                f"No se pudo abrir {title} en modo compilado.\n\n"
                f"Ejecutable esperado:\n{exe_path}\n\n"
                "Verifique que el modulo haya sido compilado y copiado a la carpeta del ERP."
            )
            logger.error("Ejecutable compilado no encontrado para %s: %s", title, exe_path)
            if parent:
                QMessageBox.warning(parent, "Modulo no disponible", message)
            return False
        try:
            subprocess.Popen([exe_path], cwd=VAH_ROOT)
            logger.info("Modulo compilado lanzado: %s - %s", title, exe_path)
            return True
        except Exception as e:
            logger.exception("Error al lanzar ejecutable compilado de %s: %s", title, e)
            if parent:
                QMessageBox.critical(parent, "Error", f"No se pudo abrir {title}:\n{str(e)}")
            return False
    if not os.path.exists(path):
        logger.error("No se encontro el modulo: %s", path)
        if parent:
            QMessageBox.warning(parent, "No encontrado", f"Archivo no encontrado:\n{path}")
        return False
    try:
        subprocess.Popen([sys.executable, path], cwd=VAH_ROOT)
        logger.info("Modulo lanzado: %s - %s", title, path)
        return True
    except Exception as e:
        logger.exception("Error al lanzar %s: %s", title, e)
        if parent:
            QMessageBox.critical(parent, "Error", f"No se pudo abrir {title}:\n{str(e)}")
        return False


def abrir_catalogo_clientes(parent: Optional[QWidget] = None) -> bool:
    """Abre el catalogo de clientes."""
    path = os.path.join(VAH_ROOT, "clientes", "main.py")
    return _launch_py_module(path, "Clientes", parent)


def abrir_catalogo_proveedores(parent: Optional[QWidget] = None) -> bool:
    """Abre el catalogo de proveedores."""
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
    """Abre el concentrador de materiales (explosion)."""
    path = os.path.join(VAH_ROOT, "concentrador_materiales", "ui", "pantalla_concentrador.py")
    return _launch_py_module(path, "Concentrador de Materiales", parent)


def abrir_catalogo_general_materiales(parent: Optional[QWidget] = None) -> bool:
    """Abre el catalogo general de materiales."""
    path = os.path.join(VAH_ROOT, "materiales", "pantalla_catalogo_general.py")
    return _launch_py_module(path, "Catalogo General de Materiales", parent)


def abrir_lista_materiales(parent: Optional[QWidget] = None) -> bool:
    """Abre el concentrador (alias de abrir_concentrador_materiales)."""
    return abrir_concentrador_materiales(parent)


def abrir_modulo_presupuestos_otra_ventana(parent: Optional[QWidget] = None):
    """Abre una nueva ventana de Presupuestos (mismo modulo)."""
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
