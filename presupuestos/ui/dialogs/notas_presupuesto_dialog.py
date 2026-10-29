# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/ui/dialogs/notas_presupuesto_dialog.py
DIÁLOGO PARA NOTAS, FORMA DE PAGO, DESCUENTO Y PLAZO DE ENTREGA DEL PRESUPUESTO
Permite:
Ingresar notas aclaratorias (en mayúsculas automáticamente)
Seleccionar forma de pago (Al terminar / Estimación semanal / Personalizada)
Capturar DESCUENTO (%) modificable por el usuario (default 0.00)
Seleccionar plazo de entrega (Común acuerdo / Fecha específica)
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QTextEdit, QComboBox, QDateEdit, QPushButton, QMessageBox,
    QDialogButtonBox, QGroupBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from presupuestos.core.constants import ICON_PATH
from common.focus_utils import install_auto_popup_on_focus

class NotasPresupuestoDialog(QDialog):
    """
    Diálogo para configurar notas, forma de pago, descuento y plazo de entrega.
    """
    # Opciones predefinidas para forma de pago
    FORMAS_PAGO = [
        "60% AL ACEPTAR EL PRESUPUESTO / 40% AL TERMINAR",
        "60% AL ACEPTAR / 40% A ESTIMACIÓN SEMANAL",
        "50% AL ACEPTAR / 50% AL TERMINAR",
        "CONTADO",
        "CRÉDITO A 30 DÍAS",
        "ESTIMACIÓN SEMANAL",
        "OTRO (ESPECIFICAR)"
    ]
    # Opciones predefinidas para plazo de entrega
    PLAZOS_ENTREGA = [
        "SERÁ DE COMÚN ACUERDO",
        "15 DÍAS HÁBILES",
        "20 DÍAS HÁBILES",
        "30 DÍAS HÁBILES",
        "FECHA ESPECÍFICA"
    ]

    def __init__(self, parent=None, notas_actual: str = "", forma_pago_actual: str = "",
                 plazo_entrega_actual: str = "", descuento_actual: float = 0.0):
        super().__init__(parent)
        self.setWindowTitle("Configuración del Presupuesto")
        self.setModal(True)
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        self.notas_actual = notas_actual
        self.forma_pago_actual = forma_pago_actual
        self.plazo_entrega_actual = plazo_entrega_actual
        self.descuento_actual = descuento_actual
        self._build_ui()
        self._combo_popup = install_auto_popup_on_focus(self)
        self._cargar_valores()

    def _build_ui(self):
        """Construye la interfaz del diálogo."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        # Grupo: Notas aclaratorias
        gb_notas = QGroupBox("📝 NOTAS ACLARATORIAS")
        notas_layout = QVBoxLayout(gb_notas)
        self.text_notas = QTextEdit()
        self.text_notas.setPlaceholderText(
            "Ingrese las notas aclaratorias (una por línea).\n"
            "Ejemplo:\n"
            "* La herrería llevará una mano de pintura anticorrosiva\n"
            "* No incluye trabajos de albañilería\n"
            "* Las medidas son aproximadas"
        )
        self.text_notas.setMinimumHeight(120)
        # Convertir a mayúsculas automáticamente
        self.text_notas.textChanged.connect(self._convertir_notas_mayusculas)
        notas_layout.addWidget(self.text_notas)
        info_notas = QLabel("✓ Las notas se guardarán y se mostrarán automáticamente al reabrir el presupuesto")
        info_notas.setStyleSheet("QLabel { color: #666; font-size: 9px; }")
        notas_layout.addWidget(info_notas)
        main_layout.addWidget(gb_notas)
        # Grupo: Forma de pago
        gb_pago = QGroupBox("💰 FORMA DE PAGO")
        pago_layout = QFormLayout(gb_pago)
        pago_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.cbo_forma_pago = QComboBox()
        self.cbo_forma_pago.addItems(self.FORMAS_PAGO)
        self.cbo_forma_pago.setEditable(True)
        self.cbo_forma_pago.currentTextChanged.connect(self._on_forma_pago_changed)
        pago_layout.addRow("Seleccionar:", self.cbo_forma_pago)
        self.edit_forma_pago_personalizada = QTextEdit()
        self.edit_forma_pago_personalizada.setPlaceholderText("Escriba aquí la forma de pago personalizada...")
        self.edit_forma_pago_personalizada.setMaximumHeight(60)
        self.edit_forma_pago_personalizada.setVisible(False)
        self.edit_forma_pago_personalizada.textChanged.connect(self._convertir_a_mayusculas)
        pago_layout.addRow("Personalizada:", self.edit_forma_pago_personalizada)
        main_layout.addWidget(gb_pago)
        # Grupo: Descuento (NUEVO, modificable por el usuario, default 0.00)
        gb_desc = QGroupBox("💵 DESCUENTO")
        desc_layout = QFormLayout(gb_desc)
        desc_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.sp_descuento = QDoubleSpinBox()
        self.sp_descuento.setDecimals(2)
        self.sp_descuento.setMinimum(0.0)
        self.sp_descuento.setMaximum(100.0)
        self.sp_descuento.setSuffix(" %")
        self.sp_descuento.setValue(0.00)
        self.sp_descuento.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sp_descuento.focusInEvent = lambda event: self.sp_descuento.selectAll()
        desc_layout.addRow("Porcentaje:", self.sp_descuento)
        info_desc = QLabel("✓ Se aplica sobre el SUBTOTAL; el I.V.A. y el TOTAL se calculan sobre el subtotal ya descontado.")
        info_desc.setStyleSheet("QLabel { color: #666; font-size: 9px; }")
        desc_layout.addRow("", info_desc)
        main_layout.addWidget(gb_desc)
        # Grupo: Plazo de entrega
        gb_plazo = QGroupBox("📅 PLAZO DE ENTREGA")
        plazo_layout = QFormLayout(gb_plazo)
        plazo_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.cbo_plazo_entrega = QComboBox()
        self.cbo_plazo_entrega.addItems(self.PLAZOS_ENTREGA)
        self.cbo_plazo_entrega.setEditable(True)
        self.cbo_plazo_entrega.currentTextChanged.connect(self._on_plazo_changed)
        plazo_layout.addRow("Seleccionar:", self.cbo_plazo_entrega)
        # Fecha específica
        fecha_layout = QHBoxLayout()
        self.date_fecha_entrega = QDateEdit()
        self.date_fecha_entrega.setCalendarPopup(True)
        self.date_fecha_entrega.setDate(QDate.currentDate().addDays(15))
        self.date_fecha_entrega.setVisible(False)
        fecha_layout.addWidget(QLabel("Fecha:"))
        fecha_layout.addWidget(self.date_fecha_entrega)
        fecha_layout.addStretch()
        plazo_layout.addRow("", fecha_layout)
        main_layout.addWidget(gb_plazo)
        # Botones
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _convertir_notas_mayusculas(self):
        """Convierte el texto de notas a mayúsculas."""
        if self.text_notas.toPlainText() != self.text_notas.toPlainText().upper():
            self.text_notas.blockSignals(True)
            self.text_notas.setText(self.text_notas.toPlainText().upper())
            self.text_notas.blockSignals(False)
            cursor = self.text_notas.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.text_notas.setTextCursor(cursor)

    def _convertir_a_mayusculas(self):
        """Convierte texto a mayúsculas para widgets QTextEdit."""
        sender = self.sender()
        if sender and isinstance(sender, QTextEdit):
            if sender.toPlainText() != sender.toPlainText().upper():
                sender.blockSignals(True)
                sender.setText(sender.toPlainText().upper())
                sender.blockSignals(False)
                cursor = sender.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                sender.setTextCursor(cursor)

    def _on_forma_pago_changed(self, texto: str):
        """Muestra el campo personalizado si se selecciona 'OTRO'."""
        if texto == "OTRO (ESPECIFICAR)":
            self.edit_forma_pago_personalizada.setVisible(True)
        else:
            self.edit_forma_pago_personalizada.setVisible(False)

    def _on_plazo_changed(self, texto: str):
        """Muestra el selector de fecha si se selecciona 'FECHA ESPECÍFICA'."""
        if texto == "FECHA ESPECÍFICA":
            self.date_fecha_entrega.setVisible(True)
        else:
            self.date_fecha_entrega.setVisible(False)

    def _cargar_valores(self):
        """Carga los valores actuales en el diálogo."""
        # Cargar notas
        if self.notas_actual:
            self.text_notas.setText(self.notas_actual)
        # Cargar forma de pago
        if self.forma_pago_actual:
            if self.forma_pago_actual in self.FORMAS_PAGO:
                self.cbo_forma_pago.setCurrentText(self.forma_pago_actual)
            else:
                self.cbo_forma_pago.setCurrentText("OTRO (ESPECIFICAR)")
                self.edit_forma_pago_personalizada.setText(self.forma_pago_actual)
        # Cargar descuento (NUEVO)
        try:
            self.sp_descuento.setValue(float(self.descuento_actual or 0.0))
        except (TypeError, ValueError):
            self.sp_descuento.setValue(0.00)
        # Cargar plazo de entrega
        if self.plazo_entrega_actual:
            if self.plazo_entrega_actual in self.PLAZOS_ENTREGA:
                self.cbo_plazo_entrega.setCurrentText(self.plazo_entrega_actual)
            elif "FECHA ESPECÍFICA" in self.plazo_entrega_actual or "FECHA ESPECÍFICA" in self.plazo_entrega_actual.upper():
                self.cbo_plazo_entrega.setCurrentText("FECHA ESPECÍFICA")
                try:
                    self.date_fecha_entrega.setDate(QDate.currentDate().addDays(15))
                except Exception:
                    pass
            else:
                self.cbo_plazo_entrega.setEditText(self.plazo_entrega_actual)

    def obtener_notas(self) -> str:
        """Retorna las notas ingresadas."""
        return self.text_notas.toPlainText().strip()

    def obtener_forma_pago(self) -> str:
        """Retorna la forma de pago seleccionada."""
        texto = self.cbo_forma_pago.currentText()
        if texto == "OTRO (ESPECIFICAR)":
            personalizado = self.edit_forma_pago_personalizada.toPlainText().strip()
            return personalizado if personalizado else texto
        return texto

    def obtener_descuento(self) -> float:
        """NUEVO: Retorna el porcentaje de descuento capturado por el usuario."""
        return float(self.sp_descuento.value())

    def obtener_plazo_entrega(self) -> str:
        """Retorna el plazo de entrega seleccionado."""
        texto = self.cbo_plazo_entrega.currentText()
        if texto == "FECHA ESPECÍFICA":
            return f"ENTREGA EL DÍA {self.date_fecha_entrega.date().toString('dd/MM/yyyy')}"
        return texto