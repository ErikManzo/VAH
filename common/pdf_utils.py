# -*- coding: utf-8 -*-
import os

from common.app_paths import get_app_root


def get_pdf_dir(modulo: str) -> str:
    """
    Retorna la ruta absoluta donde deben guardarse los PDFs de un modulo.
    Crea la carpeta si no existe.
    """
    base = os.path.join(get_app_root(), "pdfs")
    dir_modulo = os.path.join(base, modulo)
    os.makedirs(dir_modulo, exist_ok=True)
    return dir_modulo


def get_pdf_path(modulo: str, nombre_archivo: str) -> str:
    """Retorna la ruta completa para un archivo PDF dentro de la carpeta del modulo."""
    return os.path.join(get_pdf_dir(modulo), nombre_archivo)


def get_pdfs_path(modulo: str, nombre_archivo: str) -> str:
    """Alias compatible para codigo legado que espera un nombre plural."""
    return get_pdf_path(modulo, nombre_archivo)
