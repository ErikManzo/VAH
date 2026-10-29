# -*- coding: utf-8 -*-
"""
Helpers para abrir manuales PDF del ERP VAH.
"""
import os
from typing import Optional
from PyQt6.QtWidgets import QMessageBox, QWidget
from common.app_paths import get_manuales_dir
from common.logger_config import get_logger

logger = get_logger("common.manuales")


def _resolver_subcarpeta(tipo: str) -> str:
    """Resuelve el nombre de la subcarpeta según el tipo de manual."""
    normalizado = (tipo or "").strip().lower()
    if normalizado in ("tecnico", "técnico"):
        return "tecnico"
    return "operativo"


def obtener_ruta_manual(modulo: str, tipo: str) -> str:
    """Construye la ruta completa al archivo PDF del manual."""
    subcarpeta = _resolver_subcarpeta(tipo)
    nombre_tipo = "Tecnico" if subcarpeta == "tecnico" else "Operativo"
    nombre_archivo = f"VAH_Manual_{nombre_tipo}_{modulo}.pdf"
    ruta_principal = os.path.join(get_manuales_dir(), "pdf", subcarpeta, nombre_archivo)
    
    if os.path.exists(ruta_principal):
        return ruta_principal
    
    # Fallback para carpeta "técnico" con tilde (legacy)
    if subcarpeta == "tecnico":
        ruta_legacy = os.path.join(get_manuales_dir(), "pdf", "técnico", nombre_archivo)
        if os.path.exists(ruta_legacy):
            return ruta_legacy
    
    return ruta_principal


def abrir_manual_pdf(modulo: str, tipo: str, parent: Optional[QWidget] = None) -> bool:
    """Abre el manual PDF correspondiente al módulo y tipo especificado."""
    ruta = obtener_ruta_manual(modulo, tipo)
    
    if not os.path.exists(ruta):
        logger.warning("Manual no encontrado: %s", ruta)
        if parent:
            QMessageBox.warning(
                parent,
                "Manual no disponible",
                f"No se encontró el manual solicitado:\n{ruta}",
            )
        return False
    
    try:
        os.startfile(ruta)
        logger.info("Manual abierto: %s", ruta)
        return True
    except Exception:
        logger.exception("No se pudo abrir el manual: %s", ruta)
        if parent:
            QMessageBox.critical(
                parent,
                "Error",
                f"No se pudo abrir el manual:\n{ruta}",
            )
        return False