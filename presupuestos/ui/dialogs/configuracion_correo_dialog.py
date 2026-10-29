# -*- coding: utf-8 -*-
import os
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QDialogButtonBox, QMessageBox, QInputDialog
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from presupuestos.service import Service
from presupuestos.core.constants import ICON_PATH


class ConfiguracionCorreoDialog(QDialog):
    def __init__(self, svc: Service, parent=None):
        super().__init__(parent)
        self.svc = svc
        self.setWindowTitle("Configuracion de Correo")
        self.setModal(True)
        self.setMinimumWidth(420)

        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        if not self._solicitar_clave_admin():
            QTimer.singleShot(0, self.reject)
            return

        self._build_ui()
        self._cargar_parametros()

    def _solicitar_clave_admin(self) -> bool:
        clave_real = self.svc.obtener_clave_admin()
        if not clave_real:
            QMessageBox.warning(
                self,
                "Configuracion requerida",
                "No hay clave de administrador configurada en config.json.",
            )
            return False
        texto, ok = QInputDialog.getText(
            self,
            "Seguridad",
            "Ingrese la clave de administrador:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return False
        if texto != clave_real:
            QMessageBox.critical(self, "Acceso Denegado", "La clave ingresada es incorrecta.")
            return False
        return True

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.edit_correo = QLineEdit()
        self.edit_correo.setPlaceholderText("ventanasdealuminioyherreria@hotmail.com")
        form_layout.addRow("Correo remitente:", self.edit_correo)

        self.edit_contrasena = QLineEdit()
        self.edit_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_contrasena.setPlaceholderText("Contrasena del correo")
        form_layout.addRow("Contrasena:", self.edit_contrasena)

        self.edit_servidor = QLineEdit()
        self.edit_servidor.setPlaceholderText("smtp.office365.com")
        form_layout.addRow("Servidor SMTP:", self.edit_servidor)

        self.sp_puerto = QSpinBox()
        self.sp_puerto.setRange(1, 65535)
        self.sp_puerto.setValue(587)
        form_layout.addRow("Puerto SMTP:", self.sp_puerto)

        main_layout.addLayout(form_layout)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        button_box.accepted.connect(self._guardar)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _cargar_parametros(self):
        params = self.svc.obtener_configuracion_correo() or {}
        self.edit_correo.setText(
            params.get("correo_remitente", "ventanasdealuminioyherreria@hotmail.com")
        )
        self.edit_contrasena.setText(params.get("contrasena_correo", ""))
        self.edit_servidor.setText(params.get("servidor_smtp", "smtp.office365.com"))
        self.sp_puerto.setValue(int(params.get("puerto_smtp", 587) or 587))

    def _guardar(self):
        parametros = {
            "correo_remitente": self.edit_correo.text().strip(),
            "contrasena_correo": self.edit_contrasena.text(),
            "servidor_smtp": self.edit_servidor.text().strip(),
            "puerto_smtp": self.sp_puerto.value(),
        }

        if self.svc.guardar_configuracion_correo(parametros):
            QMessageBox.information(self, "Exito", "Configuracion de correo guardada correctamente.")
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "No se pudo guardar la configuracion de correo.\n"
                "Verifique que correo, contrasena, servidor y puerto sean validos.",
            )
