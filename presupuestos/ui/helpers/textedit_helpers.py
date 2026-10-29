# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QTextEdit


def connect_upper_textedit_simple(text_edit: QTextEdit):
    """
    Conecta un QTextEdit para convertir su contenido a mayúsculas.
    Preserva la posición del cursor.
    """
    if not text_edit:
        return

    def to_upper():
        if text_edit.signalsBlocked():
            return

        cursor = text_edit.textCursor()
        pos = cursor.position()

        text_edit.blockSignals(True)
        current = text_edit.toPlainText()
        upper_text = current.upper()

        if current != upper_text:
            text_edit.setPlainText(upper_text)
            cursor.setPosition(min(pos, len(upper_text)))
            text_edit.setTextCursor(cursor)

        text_edit.blockSignals(False)

    text_edit.textChanged.connect(to_upper)


def obtener_texto_textedit(text_edit: QTextEdit) -> str:
    """Obtiene el texto plano de un QTextEdit."""
    return text_edit.toPlainText() if text_edit else ""


def establecer_texto_textedit(text_edit: QTextEdit, texto: str):
    """Establece el texto plano de un QTextEdit."""
    if text_edit:
        text_edit.blockSignals(True)
        text_edit.setPlainText(texto)
        text_edit.blockSignals(False)
