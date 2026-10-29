# -*- coding: utf-8 -*-
"""
Diálogo para registrar pagos/abonos en el módulo CXC.
Mejora UX: Auto-selección de contenido al recibir foco en campos editables.
"""
from datetime import date
from decimal import Decimal
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QDoubleSpinBox,
    QDateEdit, QLineEdit, QTextEdit, QPushButton, QHBoxLayout, QMessageBox,
    QLabel
)
from PyQt6.QtCore import QDate, QEvent, Qt
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.focus_utils import setup_form_navigation
from common.logger_config import get_logger
from cxc.services.cxc_service import CxcService
from cxc.repositories.cxc_repository import CxcRepository
from cxc.utils.mayusculas import aplicar_mayusculas

logger = get_logger("cxc.art.dialogs.registrar_pago")


class RegistrarPagoDialog(QDialog):
    def __init__(self, cxc_id: int, parent=None):
        super().__init__(parent)
        self.cxc_id = cxc_id
        self.setWindowTitle("REGISTRAR PAGO - CXC")
        if parent:
            self.setWindowIcon(parent.windowIcon())
        self.setMinimumWidth(450)
        self.setModal(True)

        # Instalar filtro de eventos para auto-selección (Mejora UX)
        self.installEventFilter(self)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # === CAMPO MONTO ===
        self.monto = QDoubleSpinBox()
        self.monto.setRange(0.01, 9999999.99)
        self.monto.setPrefix("$ ")
        self.monto.setDecimals(2)
        self.monto.setSingleStep(10.0)
        self.monto.setAlignment(Qt.AlignmentFlag.AlignRight)
        # Auto-selección
        self.monto.installEventFilter(self)

        # === CAMPO FECHA ===
        self.fecha = QDateEdit()
        self.fecha.setDate(QDate.currentDate())
        self.fecha.setCalendarPopup(True)
        self.fecha.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Auto-selección
        self.fecha.installEventFilter(self)

        # === COMBOS (NO REQUIEREN AUTO-SELECCIÓN) ===
        self.metodo = QComboBox()
        self.metodo.addItems(["EFECTIVO", "TRANSFERENCIA", "TARJETA", "CHEQUE"])

        self.concepto = QComboBox()
        self.concepto.addItems(["ANTICIPO", "ESTIMACIÓN", "FINIQUITO", "PAGO", "COMPLEMENTO ANTICIPO"])

        self.cuenta_destino = QComboBox()
        self.cuenta_destino.addItems(["EMPRESARIAL", "PERSONAL", "EFECTIVO", "SIN CUENTA"])

        # === CAMPO REFERENCIA ===
        self.referencia = QLineEdit()
        self.referencia.setPlaceholderText("OPCIONAL (NÚMERO DE REFERENCIA)")
        aplicar_mayusculas(self.referencia)
        # Auto-selección
        self.referencia.installEventFilter(self)

        # === NOTAS (NO REQUIERE AUTO-SELECCIÓN) ===
        self.notas = QTextEdit()
        self.notas.setMaximumHeight(80)
        self.notas.setPlaceholderText("OBSERVACIONES ADICIONALES...")
        aplicar_mayusculas(self.notas)

        # Agregar al formulario
        form.addRow(QLabel("MONTO:"), self.monto)
        form.addRow(QLabel("FECHA:"), self.fecha)
        form.addRow(QLabel("MÉTODO:"), self.metodo)
        form.addRow(QLabel("CONCEPTO:"), self.concepto)
        form.addRow(QLabel("CUENTA DESTINO:"), self.cuenta_destino)
        form.addRow(QLabel("REFERENCIA:"), self.referencia)
        form.addRow(QLabel("NOTAS:"), self.notas)
        layout.addLayout(form)

        # === BOTONES ===
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("REGISTRAR PAGO")
        self.btn_guardar.setDefault(True)
        self.btn_cancelar = QPushButton("CANCELAR")

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

        self.btn_guardar.clicked.connect(self.guardar)
        self.btn_cancelar.clicked.connect(self.reject)
        self._focus_navigation = setup_form_navigation(
            self,
            tab_widgets=[
                self.monto,
                self.fecha,
                self.metodo,
                self.concepto,
                self.cuenta_destino,
                self.referencia,
                self.btn_guardar,
                self.btn_cancelar,
            ],
            enter_widgets=[
                self.monto,
                self.fecha,
                self.metodo,
                self.concepto,
                self.cuenta_destino,
                self.referencia,
            ],
            submit_callback=self.btn_guardar.click,
        )

        # === INICIALIZACIÓN DE DATOS ===
        try:
            cxc = CxcRepository.get_by_id(cxc_id)
            if cxc:
                # Mostrar saldo actual en título
                self.setWindowTitle(f"REGISTRAR PAGO - SALDO: ${cxc.saldo_pendiente:,.2f}")
                # Ajustar máximo al saldo actual para evitar errores
                self.monto.setMaximum(float(cxc.saldo_pendiente))
                # Poner el foco inicial en el monto
                self.monto.setFocus()
                self.monto.selectAll()  # Seleccionar monto al inicio
        except Exception as e:
            print(f"Error cargando saldo para diálogo: {e}")
            logger.exception("Error cargando saldo para el dialogo de registro de pago")

    def eventFilter(self, obj, event):
        """
        Filtro de eventos para implementar Auto-Selección.
        Cuando un campo editable recibe foco, selecciona todo su contenido.
        """
        if event.type() == QEvent.Type.FocusIn:
            # Lógica para SpinBox y DateEdit
            if hasattr(obj, 'selectAll'):
                obj.selectAll()
            # Lógica específica para QLineEdit
            if isinstance(obj, QLineEdit):
                obj.selectAll()
            # Lógica específica para DateEdit (seleccionar el texto de fecha)
            elif isinstance(obj, QDateEdit):
                line_edit = obj.lineEdit()
                if line_edit:
                    line_edit.selectAll()

        return super().eventFilter(obj, event)

    def guardar(self):
        """Lógica para guardar el pago."""
        if self.monto.value() <= 0:
            QMessageBox.warning(self, "ERROR", "EL MONTO DEBE SER MAYOR A CERO")
            return

        try:
            # Convertir a Decimal para precisión
            monto_decimal = Decimal(str(self.monto.value())).quantize(Decimal('0.01'))

            CxcService.registrar_pago(
                cxc_id=self.cxc_id,
                monto=monto_decimal,
                fecha_pago=self.fecha.date().toPyDate(),
                metodo_pago=self.metodo.currentText(),
                concepto=self.concepto.currentText(),
                cuenta_destino=self.cuenta_destino.currentText(),
                referencia=self.referencia.text(),
                notas=self.notas.toPlainText()
            )

            QMessageBox.information(self, "ÉXITO", "PAGO REGISTRADO CORRECTAMENTE")
            self.accept()

        except Exception as e:
            logger.exception("Error registrando pago en CXC")
            QMessageBox.critical(self, "ERROR", str(e))
