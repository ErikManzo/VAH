# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/ui/dialogs/enviar_correo_dialog.py
DIÁLOGO PARA ENVÍO DE CORREO - Método Semi-Automático con Outlook
Envía automáticamente sin mostrar la ventana de Outlook.
Requiere desactivar Object Model Guard (ver instrucciones abajo).
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import sys
import os
import re
import winreg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from presupuestos.core.constants import ICON_PATH


def validar_email(email: str) -> bool:
    if not email or not email.strip():
        return False
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email.strip()) is not None


def desactivar_object_model_guard():
    """
    Desactiva la alerta de seguridad de Outlook (Object Model Guard).
    Requiere permisos de administrador.
    """
    try:
        # Ruta del registro para Outlook
        reg_path = r"SOFTWARE\Microsoft\Office\16.0\Outlook\Security"

        # Abrir la clave del registro
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)

        # Establecer ObjectModelGuard a 2 (desactivado)
        winreg.SetValueEx(key, "ObjectModelGuard", 0, winreg.REG_DWORD, 2)

        # Establecer PromptOOMSend a 2 (no mostrar alerta)
        winreg.SetValueEx(key, "PromptOOMSend", 0, winreg.REG_DWORD, 2)

        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error desactivando Object Model Guard: {e}")
        return False


class EnviarCorreoDialog(QDialog):
    def __init__(self, parent=None, service=None, destinatario: str = "",
                 presupuesto_num: int = 0, cliente: str = "",
                 cliente_id: int = None, ruta_pdf: str = ""):
        super().__init__(parent)
        self.service = service
        self.cliente_id = cliente_id
        self.ruta_pdf = ruta_pdf
        self.destinatario_inicial = destinatario
        self.presupuesto_num = presupuesto_num
        self.cliente = cliente

        self.setWindowTitle("Enviar presupuesto por correo")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        if ICON_PATH and os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self._build_ui()
        self._cargar_valores()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        info_label = QLabel(
            "📧 El correo se enviará automáticamente.\n"
            "No se mostrará la ventana de Outlook."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("QLabel { color: #0066cc; font-size: 10px; background-color: #e6f3ff; padding: 5px; }")
        main_layout.addWidget(info_label)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.edit_para = QLineEdit()
        self.edit_para.setPlaceholderText("correo@cliente.com")
        self.edit_para.textChanged.connect(self._on_para_changed)
        form_layout.addRow("Para:", self.edit_para)

        self.lbl_correo_valid = QLabel()
        self.lbl_correo_valid.setVisible(False)
        form_layout.addRow("", self.lbl_correo_valid)

        self.btn_editar_cliente = QPushButton("✏️ Agregar/Editar correo del cliente")
        self.btn_editar_cliente.setVisible(not bool(self.destinatario_inicial))
        self.btn_editar_cliente.clicked.connect(self._editar_correo_cliente)
        form_layout.addRow("", self.btn_editar_cliente)

        self.edit_asunto = QLineEdit()
        self.edit_asunto.setPlaceholderText("Asunto del correo")
        form_layout.addRow("Asunto:", self.edit_asunto)

        self.text_mensaje = QTextEdit()
        self.text_mensaje.setMinimumHeight(150)
        form_layout.addRow("Mensaje:", self.text_mensaje)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()

        self.btn_enviar = QPushButton("📧 Enviar Correo")
        self.btn_enviar.setMinimumWidth(150)
        self.btn_enviar.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_enviar.clicked.connect(self._enviar_correo)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.btn_enviar)
        button_layout.addWidget(self.btn_cancelar)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

    def _cargar_valores(self):
        if self.destinatario_inicial:
            self.edit_para.setText(self.destinatario_inicial)
            self._on_para_changed(self.destinatario_inicial)

        asunto_default = f"Presupuesto VAH #{self.presupuesto_num}"
        if self.cliente:
            asunto_default += f" - {self.cliente}"
        self.edit_asunto.setText(asunto_default)

        mensaje_default = f"""Estimado(a) {self.cliente if self.cliente else 'cliente'},

Adjunto encontrará el presupuesto #{self.presupuesto_num} solicitado.

Quedamos a sus órdenes para cualquier aclaración.

Saludos cordiales.

VENTANAS DE ALUMINIO Y HERRERIA
EDGAR MANZO RUIZ
Tel: 33 3620-9293 - 33 3620-0269
ventanasdealuminioyherreria@hotmail.com"""
        self.text_mensaje.setPlainText(mensaje_default)

    def _on_para_changed(self, texto: str):
        email = texto.strip()
        if not email:
            self.lbl_correo_valid.setVisible(False)
            return

        es_valido = validar_email(email)
        if es_valido:
            self.lbl_correo_valid.setText("✓ Correo válido")
            self.lbl_correo_valid.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            self.lbl_correo_valid.setVisible(True)
        else:
            self.lbl_correo_valid.setText("✗ Correo no válido")
            self.lbl_correo_valid.setStyleSheet("QLabel { color: red; }")
            self.lbl_correo_valid.setVisible(True)

    def _editar_correo_cliente(self):
        from presupuestos.ui.dialogs.editar_correo_cliente_dialog import EditarCorreoClienteDialog
        dialog = EditarCorreoClienteDialog(self, self.service, self.cliente_id, self.destinatario_inicial)
        if dialog.exec():
            nuevo_correo = dialog.get_correo()
            if nuevo_correo:
                self.edit_para.setText(nuevo_correo)
                self.btn_editar_cliente.setVisible(False)

    def _enviar_correo(self):
        """Envía el correo automáticamente usando Outlook COM."""
        para = self.edit_para.text().strip()
        if not para:
            QMessageBox.warning(self, "Validación", "El destinatario es obligatorio.")
            return

        if not validar_email(para):
            QMessageBox.warning(self, "Validación", "El formato del correo no es válido.")
            return

        asunto = self.edit_asunto.text().strip()
        if not asunto:
            QMessageBox.warning(self, "Validación", "El asunto es obligatorio.")
            return

        if not os.path.exists(self.ruta_pdf):
            QMessageBox.critical(self, "Error", f"No se encuentra el PDF:\n{self.ruta_pdf}")
            return

        # Desactivar Object Model Guard
        if not desactivar_object_model_guard():
            QMessageBox.warning(
                self,
                "Advertencia",
                "No se pudo desactivar la alerta de seguridad de Outlook.\n"
                "Es posible que aparezca una alerta de seguridad.\n\n"
                "Si aparece, haz clic en 'Permitir'."
            )

        try:
            import win32com.client

            outlook = win32com.client.Dispatch('outlook.application')

            cuenta_windows = None
            for account in outlook.Session.Accounts:
                if 'ventanasdealuminioyherreria' in account.SmtpAddress.lower():
                    cuenta_windows = account
                    break

            mail = outlook.CreateItem(0)

            if cuenta_windows:
                mail.SendUsingAccount = cuenta_windows

            mail.To = para
            mail.Subject = asunto
            mail.Body = self.text_mensaje.toPlainText()

            mail.Attachments.Add(self.ruta_pdf)

            # ENVIAR AUTOMÁTICAMENTE (no mostrar ventana)
            mail.Send()

            QMessageBox.information(
                self,
                "✓ Correo Enviado",
                f"El correo se envió exitosamente.\n\n"
                f"Destinatario: {para}\n"
                f"Asunto: {asunto}\n"
                f"Adjunto: {os.path.basename(self.ruta_pdf)}\n\n"
                f"Verifica en 'Elementos enviados' de Outlook."
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al enviar correo",
                f"No se pudo enviar el correo:\n\n{str(e)}\n\n"
                f"Verifica que Outlook esté configurado correctamente."
            )