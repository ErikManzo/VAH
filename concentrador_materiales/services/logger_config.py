# -*- coding: utf-8 -*-
"""
Configuración de logging para el concentrador de materiales.

Los logs se guardan en:
D:\vah\concentrador_materiales\logs\concentrador_YYYYMMDD_HHMMSS.log

Formato: [NIVEL] codigo - mensaje | datos_adicionales
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Directorio de logs
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


def _asegurar_directorio_logs():
    """Asegura que el directorio de logs exista."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR, exist_ok=True)


def configurar_logger() -> logging.Logger:
    """
    Configura y retorna un logger para el concentrador.

    Returns:
        logging.Logger configurado
    """
    _asegurar_directorio_logs()

    # Nombre del archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"concentrador_{timestamp}.log"
    log_path = os.path.join(LOGS_DIR, log_filename)

    # Crear logger
    logger = logging.getLogger("concentrador_materiales")
    logger.setLevel(logging.INFO)

    # Limpiar handlers existentes para evitar duplicados
    if logger.handlers:
        logger.handlers.clear()

    # Handler para archivo
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    # Formato: [NIVEL] codigo - mensaje | datos
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # Registrar inicio
    logger.info(f"Log iniciado: {log_path}")

    return logger


def obtener_logger() -> logging.Logger:
    """
    Obtiene el logger configurado o crea uno nuevo.

    Returns:
        logging.Logger
    """
    logger = logging.getLogger("concentrador_materiales")
    if not logger.handlers:
        return configurar_logger()
    return logger


def registrar_advertencia(codigo: str, mensaje: str, datos: Optional[Dict[str, Any]] = None):
    """
    Registra una advertencia en el log.

    Args:
        codigo: Código de la advertencia (ej: "LARGO_NULO")
        mensaje: Mensaje descriptivo
        datos: Datos adicionales para contexto
    """
    logger = obtener_logger()
    log_msg = f"[ADVERTENCIA] {codigo} - {mensaje}"
    if datos:
        log_msg += f" | {datos}"
    logger.warning(log_msg)


def registrar_error(codigo: str, mensaje: str, datos: Optional[Dict[str, Any]] = None):
    """
    Registra un error en el log.

    Args:
        codigo: Código del error (ej: "CONEXION_FALLIDA")
        mensaje: Mensaje descriptivo
        datos: Datos adicionales para contexto
    """
    logger = obtener_logger()
    log_msg = f"[ERROR] {codigo} - {mensaje}"
    if datos:
        log_msg += f" | {datos}"
    logger.error(log_msg)


def registrar_info(codigo: str, mensaje: str, datos: Optional[Dict[str, Any]] = None):
    """
    Registra información en el log.

    Args:
        codigo: Código de información
        mensaje: Mensaje descriptivo
        datos: Datos adicionales para contexto
    """
    logger = obtener_logger()
    log_msg = f"[INFO] {codigo} - {mensaje}"
    if datos:
        log_msg += f" | {datos}"
    logger.info(log_msg)