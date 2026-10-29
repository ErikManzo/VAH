# -*- coding: utf-8 -*-
"""
Widget reutilizable para búsqueda inteligente con autocompletado en tiempo real.
ERP VAH - Módulo CXC
"""
from PyQt6.QtWidgets import (
    QLineEdit, QListWidget, QListWidgetItem, QFrame, QVBoxLayout,
    QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QKeyEvent, QFocusEvent
from common.search_utils import configure_list_widget_for_search_results, popup_height_for_list_widget


class SmartSearchLineEdit(QLineEdit):
    """
    QLineEdit con búsqueda incremental, debounce y popup de resultados.
    """
    item_selected = pyqtSignal(dict)  # Emite el diccionario de datos seleccionado

    def __init__(self, search_type: str, placeholder: str, parent=None):
        super().__init__(parent)
        self.search_type = search_type  # 'cliente', 'obra', 'presupuesto'
        self.setPlaceholderText(placeholder)
        self.setMinimumWidth(200)

        # Timer para debounce (300ms)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self._execute_search)

        self.textChanged.connect(self._on_text_changed)

        # Configuración del Popup
        self.popup = QFrame(parent)
        self.popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.popup.setStyleSheet("""
            QFrame { 
                border: 1px solid #B0B0B0; 
                background-color: white;
                border-radius: 4px;
            }
        """)
        popup_layout = QVBoxLayout(self.popup)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        popup_layout.setSpacing(0)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget::item { 
                padding: 8px 12px; 
                border-bottom: 1px solid #f0f0f0; 
            }
            QListWidget::item:selected { 
                background-color: #005A9E; 
                color: white; 
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        popup_layout.addWidget(self.list_widget)
        configure_list_widget_for_search_results(self.list_widget)

        self.popup.hide()
        self.external_filter = {}
        self.search_callback = None
        self.last_search_text = ""

    def set_external_filter(self, criteria: dict):
        """Recibe filtros desde otros widgets (ej. cliente_id seleccionado)."""
        self.external_filter = criteria
        if self.text().strip():
            self._trigger_search()

    def set_search_callback(self, callback):
        """Asigna la función de búsqueda al repositorio."""
        self.search_callback = callback

    def _on_text_changed(self, text):
        if text.strip():
            self._trigger_search()
        else:
            self.popup.hide()
            self.last_search_text = ""

    def _trigger_search(self):
        text = self.text().strip()
        if text and len(text) >= 1:
            self.search_timer.start()

    def _execute_search(self):
        text = self.text().strip()
        if text and text != self.last_search_text:
            self.last_search_text = text
            if self.search_callback:
                self.search_callback(text, self.external_filter)

    def show_results(self, results: list):
        self.list_widget.clear()
        if not results:
            self.popup.hide()
            return

        for item_data in results:
            display_text = item_data.get('display', '')
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.ItemDataRole.UserRole, item_data)
            self.list_widget.addItem(list_item)

        configure_list_widget_for_search_results(self.list_widget)
        self._position_popup()
        self.popup.show()
        self.popup.raise_()
        self.popup.activateWindow()

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _position_popup(self):
        global_pos = self.mapToGlobal(QPoint(0, self.height()))
        self.popup.move(global_pos)
        popup_height = popup_height_for_list_widget(self.list_widget, min_visible_rows=6, max_visible_rows=8)
        self.popup.resize(self.width(), max(140, min(320, popup_height)))

    def _on_item_clicked(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self._select_item(data)

    def _select_item(self, data):
        # Mostramos solo el texto relevante en el input, no el string completo de display
        # Esto ayuda a que los filtros LIKE existentes funcionen mejor
        display_key = 'nombre' if self.search_type == 'cliente' else (
            'obra' if self.search_type == 'obra' else 'presupuesto'
        )
        simple_text = str(data.get(display_key, data.get('display', '')))

        self.blockSignals(True)
        self.setText(simple_text.upper())
        self.blockSignals(False)

        self.popup.hide()
        self.item_selected.emit(data)

    def keyPressEvent(self, event: QKeyEvent):
        if self.popup.isVisible() and self.popup.isActiveWindow():
            if event.key() == Qt.Key.Key_Down:
                row = self.list_widget.currentRow()
                if row < self.list_widget.count() - 1:
                    self.list_widget.setCurrentRow(row + 1)
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Up:
                row = self.list_widget.currentRow()
                if row > 0:
                    self.list_widget.setCurrentRow(row - 1)
                event.accept()
                return
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                current_item = self.list_widget.currentItem()
                if current_item:
                    self._on_item_clicked(current_item)
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Escape:
                self.popup.hide()
                event.accept()
                return

        super().keyPressEvent(event)

    def focusOutEvent(self, event: QFocusEvent):
        if self.popup.isVisible():
            QTimer.singleShot(150, lambda: self._hide_popup_if_needed())
        super().focusOutEvent(event)

    def _hide_popup_if_needed(self):
        if not self.popup.underMouse() and not self.hasFocus():
            self.popup.hide()
