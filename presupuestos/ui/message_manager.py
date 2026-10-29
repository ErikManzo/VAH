# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/ui/message_manager.py
Gestor centralizado de mensajes para el sistema VAH.

Permite:
- Centralizar todos los mensajes del sistema
- Activar/desactivar mensajes por categoría
- Cambiar entre QMessageBox y print() silencioso
- Mantener un registro de mensajes para depuración
"""

from PyQt6.QtWidgets import QMessageBox, QWidget
from enum import Enum
from typing import Optional


class MessageCategory(Enum):
    """Categorías de mensajes para controlar su comportamiento."""
    ERROR_CALCULO = "error_calculo"  # Errores de cálculo (silenciosos)
    CONFIRMACION = "confirmacion"  # Confirmaciones importantes (mostrar)
    INFO_GENERAL = "info_general"  # Información general (mostrar)
    ADVERTENCIA = "advertencia"  # Advertencias (mostrar)
    PLACEHOLDER = "placeholder"  # Placeholders (silenciosos)
    DEBUG = "debug"  # Solo desarrollo
    CRITICO = "critico"  # Errores críticos (mostrar siempre)


class MessageManager:
    """
    Gestor centralizado de mensajes.

    Uso:
        # Mostrar mensaje
        MessageManager.info(parent, "Título", "Mensaje")

        # Error de cálculo (silencioso)
        MessageManager.error_calculo(parent, "Error al calcular fila 3")

        # Confirmación
        if MessageManager.confirmar_dimensiones(parent):
            # Aplicar dimensiones

        # Configurar categoría
        MessageManager.set_show_category(MessageCategory.ERROR_CALCULO, True)
    """

    # Configuración por categoría
    _config = {
        MessageCategory.ERROR_CALCULO: {"show": False, "log": True, "level": "ERROR"},
        MessageCategory.CONFIRMACION: {"show": True, "log": False, "level": "INFO"},
        MessageCategory.INFO_GENERAL: {"show": True, "log": False, "level": "INFO"},
        MessageCategory.ADVERTENCIA: {"show": True, "log": True, "level": "WARNING"},
        MessageCategory.PLACEHOLDER: {"show": False, "log": False, "level": "DEBUG"},
        MessageCategory.DEBUG: {"show": False, "log": True, "level": "DEBUG"},
        MessageCategory.CRITICO: {"show": True, "log": True, "level": "CRITICAL"},
    }

    # Contador de mensajes para estadísticas
    _message_count = {cat: 0 for cat in MessageCategory}

    @classmethod
    def set_show_category(cls, category: MessageCategory, show: bool) -> None:
        """
        Configura si una categoría de mensajes debe mostrarse.

        Args:
            category: Categoría a configurar
            show: True para mostrar, False para ocultar
        """
        if category in cls._config:
            cls._config[category]["show"] = show

    @classmethod
    def set_log_category(cls, category: MessageCategory, log: bool) -> None:
        """
        Configura si una categoría de mensajes debe registrarse en consola.

        Args:
            category: Categoría a configurar
            log: True para registrar, False para no hacerlo
        """
        if category in cls._config:
            cls._config[category]["log"] = log

    @classmethod
    def enable_all(cls) -> None:
        """Activa todos los mensajes (modo depuración)."""
        for category in cls._config:
            cls._config[category]["show"] = True
            cls._config[category]["log"] = True

    @classmethod
    def silence_all(cls) -> None:
        """Silencia todos los mensajes (modo producción)."""
        for category in cls._config:
            if category != MessageCategory.CRITICO:
                cls._config[category]["show"] = False

    @classmethod
    def get_stats(cls) -> dict:
        """Retorna estadísticas de mensajes mostrados."""
        return dict(cls._message_count)

    @classmethod
    def reset_stats(cls) -> None:
        """Reinicia el contador de mensajes."""
        for cat in cls._message_count:
            cls._message_count[cat] = 0

    @classmethod
    def _log(cls, message: str, level: str = "INFO") -> None:
        """Registra el mensaje en consola."""
        print(f"[VAH][{level}] {message}")

    @classmethod
    def _show_message(cls, parent: Optional[QWidget], title: str, message: str,
                      category: MessageCategory, icon: QMessageBox.Icon) -> None:
        """
        Muestra un mensaje según la configuración de su categoría.
        """
        config = cls._config.get(category, {"show": True, "log": False, "level": "INFO"})

        cls._message_count[category] += 1

        if config["log"]:
            cls._log(f"{title}: {message}", config["level"])

        if config["show"] and parent is not None:
            if icon == QMessageBox.Icon.Information:
                QMessageBox.information(parent, title, message)
            elif icon == QMessageBox.Icon.Warning:
                QMessageBox.warning(parent, title, message)
            elif icon == QMessageBox.Icon.Critical:
                QMessageBox.critical(parent, title, message)
            elif icon == QMessageBox.Icon.Question:
                return QMessageBox.question(parent, title, message)

    # ========================================================================
    # MÉTODOS ESPECÍFICOS POR TIPO DE MENSAJE
    # ========================================================================

    @classmethod
    def info(cls, parent: QWidget, title: str, message: str) -> None:
        """Muestra un mensaje informativo."""
        cls._show_message(parent, title, message, MessageCategory.INFO_GENERAL,
                          QMessageBox.Icon.Information)

    @classmethod
    def warning(cls, parent: QWidget, title: str, message: str) -> None:
        """Muestra un mensaje de advertencia."""
        cls._show_message(parent, title, message, MessageCategory.ADVERTENCIA,
                          QMessageBox.Icon.Warning)

    @classmethod
    def critical(cls, parent: QWidget, title: str, message: str) -> None:
        """Muestra un mensaje de error crítico."""
        cls._show_message(parent, title, message, MessageCategory.CRITICO,
                          QMessageBox.Icon.Critical)

    @classmethod
    def error_calculo(cls, parent: Optional[QWidget], message: str) -> None:
        """
        Error de cálculo (silencioso por defecto, solo log).

        Args:
            parent: Widget padre (puede ser None)
            message: Mensaje de error
        """
        config = cls._config[MessageCategory.ERROR_CALCULO]
        cls._message_count[MessageCategory.ERROR_CALCULO] += 1

        if config["log"]:
            cls._log(f"ERROR CÁLCULO: {message}", "ERROR")

        if config["show"] and parent is not None:
            QMessageBox.warning(parent, "Error de Cálculo", message)

    @classmethod
    def error_validacion(cls, parent: Optional[QWidget], message: str) -> None:
        """Error de validación (silencioso por defecto)."""
        cls.error_calculo(parent, message)

    @classmethod
    def confirmar_dimensiones(cls, parent: QWidget) -> bool:
        """
        Confirmación para aplicar dimensiones globales.

        Args:
            parent: Widget padre

        Returns:
            True si el usuario acepta, False en caso contrario
        """
        config = cls._config[MessageCategory.CONFIRMACION]
        cls._message_count[MessageCategory.CONFIRMACION] += 1

        if not config["show"]:
            if config["log"]:
                cls._log("Confirmación dimensiones: auto-aceptado", "INFO")
            return True

        reply = QMessageBox.question(
            parent,
            "Aplicar dimensiones",
            "¿Desea aplicar los nuevos valores de ancho/alto a todos los materiales de la partida?\n"
            "Los valores personalizados se sobrescribirán.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )

        if config["log"]:
            cls._log(f"Confirmación dimensiones: {reply.name}", "INFO")

        return reply == QMessageBox.StandardButton.Yes

    @classmethod
    def confirmar_guardar_cambios(cls, parent: QWidget) -> str:
        """
        Confirmación para guardar cambios antes de cambiar de partida.

        Args:
            parent: Widget padre

        Returns:
            "yes", "no", o "cancel"
        """
        config = cls._config[MessageCategory.CONFIRMACION]
        cls._message_count[MessageCategory.CONFIRMACION] += 1

        if not config["show"]:
            if config["log"]:
                cls._log("Confirmación guardar cambios: auto-yes", "INFO")
            return "yes"

        reply = QMessageBox.question(
            parent,
            "Guardar cambios",
            "La partida actual tiene cambios. ¿Desea guardarlos antes de cambiar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )

        if config["log"]:
            cls._log(f"Confirmación guardar cambios: {reply.name}", "INFO")

        if reply == QMessageBox.StandardButton.Yes:
            return "yes"
        elif reply == QMessageBox.StandardButton.No:
            return "no"
        else:
            return "cancel"

    @classmethod
    def placeholder(cls, funcionalidad: str) -> None:
        """
        Placeholder para funcionalidades no implementadas (silencioso por defecto).

        Args:
            funcionalidad: Nombre de la funcionalidad
        """
        config = cls._config[MessageCategory.PLACEHOLDER]
        cls._message_count[MessageCategory.PLACEHOLDER] += 1

        if config["log"]:
            cls._log(f"PLACEHOLDER: {funcionalidad}", "DEBUG")

        # Nunca se muestra en UI, solo log

    @classmethod
    def debug(cls, message: str) -> None:
        """
        Mensaje de depuración (solo log).

        Args:
            message: Mensaje de depuración
        """
        config = cls._config[MessageCategory.DEBUG]
        cls._message_count[MessageCategory.DEBUG] += 1

        if config["log"]:
            cls._log(message, "DEBUG")