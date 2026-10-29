# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/ui/dialogs/editar_correo_cliente_dialog.py

DIÁLOGO PARA EDITAR EL CORREO DEL CLIENTE
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QDialogButtonBox, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from presupuestos.core.constants import ICON_PATH


class EditarCorreoClienteDialog(QDialog):
    """
    Diálogo para editar el correo electrónico de un cliente.
    """

    def __init__(self, parent=None, service=None, cliente_id: int = None, correo_actual: str = ""):
        super().__init__(parent)
        self.service = service
        self.cliente_id = cliente_id
        self.correo_actual = correo_actual

        self.setWindowTitle("Correo del cliente")
        self.setModal(True)
        self.setMinimumWidth(400)

        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self._build_ui()
        self._cargar_valores()

    def _build_ui(self):
        """Construye la interfaz."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Información
        info_label = QLabel(
            "Ingrese el correo electrónico del cliente.\n"
            "Este correo se guardará en la base de datos para futuros envíos."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("QLabel { color: #666; }")
        main_layout.addWidget(info_label)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.edit_correo = QLineEdit()
        self.edit_correo.setPlaceholderText("cliente@empresa.com")
        self.edit_correo.textChanged.connect(self._validar_correo)
        form_layout.addRow("Correo electrónico:", self.edit_correo)

        self.lbl_validacion = QLabel()
        self.lbl_validacion.setVisible(False)
        form_layout.addRow("", self.lbl_validacion)

        main_layout.addLayout(form_layout)

        # Botones
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._guardar)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _cargar_valores(self):
        """Carga el correo actual."""
        if self.correo_actual:
            self.edit_correo.setText(self.correo_actual)
            self._validar_correo(self.correo_actual)

    def _validar_correo(self, correo: str):
        """Valida el formato del correo."""
        if not correo:
            self.lbl_validacion.setVisible(False)
            return

        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        es_valido = re.match(patron, correo) is not None

        if es_valido:
            self.lbl_validacion.setText("✓ Correo válido")
            self.lbl_validacion.setStyleSheet("QLabel { color: green; }")
            self.lbl_validacion.setVisible(True)
        else:
            self.lbl_validacion.setText("✗ Correo no válido")
            self.lbl_validacion.setStyleSheet("QLabel { color: red; }")
            self.lbl_validacion.setVisible(True)

        return es_valido

    def _guardar(self):
        """Guarda el correo en la base de datos."""
        correo = self.edit_correo.text().strip()

        if not correo:
            QMessageBox.warning(self, "Validación", "El correo electrónico no puede estar vacío.")
            return

        if not self._validar_correo(correo):
            QMessageBox.warning(self, "Validación", "El formato del correo no es válido.")
            return

        if not self.service or not self.cliente_id:
            QMessageBox.warning(self, "Error", "No se pudo guardar el correo en la base de datos.")
            return

        try:
            with self.service.cursor() as cur:
                cur.execute("""
                    UPDATE [clientes].dbo.clientes
                    SET correo = ?
                    WHERE id = ?
                """, (correo, self.cliente_id))
                cur.commit()

            QMessageBox.information(self, "Éxito", "Correo guardado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el correo: {str(e)}")

    def get_correo(self) -> str:
        return self.edit_correo.text().strip()