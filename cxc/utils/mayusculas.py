# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QLineEdit, QTextEdit
from PyQt6.QtCore import Qt
from common.logger_config import get_logger

logger = get_logger("cxc.utils.mayusculas")


def aplicar_mayusculas(widget):
    """Convierte automáticamente a mayúsculas el texto de QLineEdit y QTextEdit."""
    if isinstance(widget, QLineEdit):
        # Guardar la posición del cursor
        cursor_pos = widget.cursorPosition()
        # Convertir texto a mayúsculas si es diferente
        texto = widget.text()
        if texto != texto.upper():
            widget.blockSignals(True)
            widget.setText(texto.upper())
            widget.blockSignals(False)
            widget.setCursorPosition(cursor_pos)
        # Conectar señal solo si no está ya conectada
        try:
            widget.textChanged.disconnect()
        except TypeError:
            pass  # No había conexión
        widget.textChanged.connect(lambda: aplicar_mayusculas(widget))

    elif isinstance(widget, QTextEdit):
        def to_upper():
            if widget.toPlainText() != widget.toPlainText().upper():
                cursor = widget.textCursor()
                widget.blockSignals(True)
                widget.setPlainText(widget.toPlainText().upper())
                widget.blockSignals(False)
                widget.setTextCursor(cursor)

        try:
            widget.textChanged.disconnect()
        except TypeError:
            pass
        widget.textChanged.connect(to_upper)
