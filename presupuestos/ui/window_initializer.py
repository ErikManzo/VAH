# -*- coding: utf-8 -*-
"""
Inicializacion de la ventana principal de Presupuestos.
Centraliza configuracion visual, iconos, maximizacion y parametros por defecto.
"""
import os

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow

from common.logger_config import get_logger, setup_logger
from presupuestos.bootstrap import is_corrector_available, is_spellchecker_available
from presupuestos.ui.helpers.textedit_helpers import connect_upper_textedit_simple

setup_logger("presupuestos.ui.window_initializer")
logger = get_logger("presupuestos.ui.window_initializer")


def setup_window_icon(window: QMainWindow) -> None:
    """Configura el icono de la ventana principal."""
    logo_candidates = [
        r"D:\VAH\logo.jpg",
        r"D:\VAH\logo.png",
        r"D:\VAH\logo_00001.ico",
    ]
    for logo_path in logo_candidates:
        if os.path.exists(logo_path):
            window.setWindowIcon(QIcon(logo_path))
            logger.debug("Icono cargado desde %s", logo_path)
            break


def setup_maximization_behavior(window: QMainWindow) -> None:
    """Configura la maximizacion al mostrar la ventana."""

    def force_maximized():
        screen = window.screen()
        if screen:
            window.setGeometry(screen.availableGeometry())
        window.setWindowState(window.windowState() | Qt.WindowState.WindowMaximized)
        QTimer.singleShot(0, window.showMaximized)

    window._force_maximized = force_maximized
    logger.debug("Comportamiento de maximizacion configurado")


def apply_default_parameters(window) -> None:
    """Aplica los parametros del sistema a los controles iniciales."""
    try:
        params = window.svc.obtener_parametros_sistema()
        color_def = params.get("color_global_defecto", "VARIOS")
        if hasattr(window, "cbo_color_global"):
            window.cbo_color_global.setCurrentText(color_def)
        if hasattr(window, "cbo_color"):
            window.cbo_color.setCurrentText(color_def)
        if hasattr(window, "sb_desperdicio"):
            window.sb_desperdicio.setValue(params.get("desperdicio_defecto", 2.0))
        if hasattr(window, "sb_fv_pct"):
            window.sb_fv_pct.setValue(params.get("fv_defecto", 25.0))
        logger.debug("Parametros de defecto aplicados: Color=%s", color_def)
    except Exception as e:
        logger.exception("Error aplicando parametros de defecto: %s", e)


def setup_corrector(window) -> None:
    """Activa el corrector ortografico en los campos de texto si esta disponible."""
    if not is_corrector_available() or not is_spellchecker_available():
        logger.warning("Corrector ortografico no disponible")
        return
    try:
        from presupuestos.reports.textedit_con_corrector import habilitar_corrector_para_campos

        habilitar_corrector_para_campos(window)
        logger.debug("Corrector ortografico profesional activado")
    except Exception as e:
        logger.exception("Error activando corrector ortografico: %s", e)


def connect_upper_case_helpers(window) -> None:
    """Convierte los QTextEdit a mayusculas automaticas."""
    if hasattr(window, "le_titulo") and window.le_titulo:
        connect_upper_textedit_simple(window.le_titulo)
    if hasattr(window, "le_obra") and window.le_obra:
        connect_upper_textedit_simple(window.le_obra)
    logger.debug("Helpers de mayusculas conectados")


def setup_splitter_behavior(window) -> None:
    """Define el comportamiento del splitter (20/80)."""

    def apply_split():
        split_widget = getattr(window, "splitter", None) or getattr(window, "split", None)
        if split_widget is not None:
            total = split_widget.width() or window.width()
            if total > 0:
                split_widget.setSizes([int(total * 0.2), int(total * 0.8)])
        logger.debug("Splitter 20/80 aplicado")

    QTimer.singleShot(0, apply_split)
    window._apply_split_20_80 = apply_split
