# -*- coding: utf-8 -*-
"""
Modulo centralizado de logging para el ERP VAH.
Proporciona un logger configurado para escribir en archivo y opcionalmente en consola.
"""
import logging
import os
from datetime import datetime

# Directorio de logs (relativo a la raiz del proyecto)
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Nombre del archivo de log con fecha
LOG_FILE = os.path.join(LOG_DIR, f"vah_erp_{datetime.now().strftime('%Y%m%d')}.log")

# Formato de log
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def _resolve_default_log_level() -> int:
    """Resuelve el nivel de log desde entorno, con DEBUG como valor actual de desarrollo."""
    raw = os.environ.get("VAH_LOG_LEVEL", "DEBUG").strip().upper()
    return getattr(logging, raw, logging.DEBUG)


# Nivel por defecto (puede cambiarse por variable de entorno o config.json)
DEFAULT_LOG_LEVEL = _resolve_default_log_level()  # DEBUG en desarrollo, INFO en produccion


def setup_logger(name: str, level: int = None) -> logging.Logger:
    """
    Configura y retorna un logger con el nombre especificado.
    Si ya existe, lo reutiliza.
    """
    if level is None:
        level = DEFAULT_LOG_LEVEL

    logger = logging.getLogger(name)

    # Evitar duplicar handlers si ya esta configurado
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # Handler para archivo
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Handler para consola (opcional, util en desarrollo)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter("%(levelname)s - %(name)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger sin reconfigurar (para usar en modulos)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
