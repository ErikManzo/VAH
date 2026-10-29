# -*- coding: utf-8 -*-
import os
import sys


def get_app_root():
    """Retorna la raiz de la aplicacion (modo desarrollo o compilado)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_logs_dir():
    return os.path.join(get_app_root(), "logs")


def get_pdfs_dir(subfolder="Presupuestos"):
    return os.path.join(get_app_root(), "pdfs", subfolder)


def get_cache_dir():
    return os.path.join(get_app_root(), "cache")


def get_manuales_dir():
    return os.path.join(get_app_root(), "manuales")


def get_resource_root():
    """
    Retorna la raiz real desde la que PyInstaller expone los recursos.
    En desarrollo coincide con la raiz del proyecto.
    """
    return getattr(sys, "_MEIPASS", get_app_root())


def get_resource_path(*relative_parts):
    """
    Resuelve recursos empaquetados buscando primero junto al ejecutable y luego
    dentro del directorio temporal de PyInstaller.
    """
    app_root = get_app_root()
    resource_root = get_resource_root()
    for base in (app_root, resource_root):
        candidate = os.path.join(base, *relative_parts)
        if os.path.exists(candidate):
            return candidate
    return os.path.join(app_root, *relative_parts)
