# -*- coding: utf-8 -*-
"""
Navegación simple con Enter = Tab
Clases probadas y funcionales para reemplazar focus_utils.py módulo por módulo.
Incluyen auto-selección del texto al recibir foco.
"""
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox


class _AutoSelectOnFocusMixin:
    """Selecciona el contenido automáticamente al recibir foco."""

    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self._select_all_content)

    def _select_all_content(self) -> None:
        if not self.isEnabled() or not self.isVisible():
            return

        if isinstance(self, QLineEdit):
            self.selectAll()
            return

        if isinstance(self, QComboBox):
            if self.isEditable() and self.lineEdit() is not None:
                self.lineEdit().selectAll()
            return

        if isinstance(self, (QSpinBox, QDoubleSpinBox)) and self.lineEdit() is not None:
            self.lineEdit().selectAll()


class NavLineEdit(_AutoSelectOnFocusMixin, QLineEdit):
    """QLineEdit con Enter=Tab y mayúsculas forzadas automáticamente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Conectar signal para forzar mayúsculas en tiempo real
        self.textChanged.connect(self._forzar_mayusculas)

    def _forzar_mayusculas(self, texto: str):
        """Convierte todo el texto a mayúsculas manteniendo la posición del cursor."""
        if texto and texto != texto.upper():
            pos = self.cursorPosition()
            self.blockSignals(True)
            self.setText(texto.upper())
            self.setCursorPosition(min(pos, len(texto.upper())))
            self.blockSignals(False)

    def keyPressEvent(self, event):
        """Enter = Tab hacia adelante; Shift+Tab retrocede."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.focusNextPrevChild(True)
            return
        super().keyPressEvent(event)


class NavComboBox(_AutoSelectOnFocusMixin, QComboBox):
    """QComboBox donde Enter = Tab (avanza al siguiente campo).
    Maneja correctamente el popup abierto/cerrado."""

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Si el popup está visible, dejar que Qt procese la selección
            view = self.view()
            if view is not None and view.isVisible():
                # Procesar el evento normalmente (selecciona item y cierra popup)
                super().keyPressEvent(event)
                # Después de procesar, avanzar al siguiente campo
                QTimer.singleShot(0, lambda: self.focusNextPrevChild(True))
                return
            # Si el popup está cerrado, avanzar directamente
            self.focusNextPrevChild(True)
            return
        super().keyPressEvent(event)


class NavSpinBox(_AutoSelectOnFocusMixin, QSpinBox):
    """QSpinBox donde Enter = Tab (avanza al siguiente campo)."""

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.focusNextPrevChild(True)
            return
        super().keyPressEvent(event)


class NavDoubleSpinBox(_AutoSelectOnFocusMixin, QDoubleSpinBox):
    """QDoubleSpinBox donde Enter = Tab (avanza al siguiente campo)."""

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.focusNextPrevChild(True)
            return
        super().keyPressEvent(event)
