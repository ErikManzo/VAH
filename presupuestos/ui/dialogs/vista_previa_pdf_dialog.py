# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/ui/dialogs/vista_previa_pdf_dialog.py
Diálogo de Vista Previa de Impresión con QPdfView (Qt 6.3+)
CORREGIDO: Ahora muestra TODAS las páginas del PDF con scroll vertical
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QLabel
)
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtCore import Qt
import os
import sys


class VistaPreviaPDFDialog(QDialog):
    """
    Diálogo de Vista Previa que muestra el PDF generado.
    Muestra TODAS las páginas con scroll vertical.
    """

    def __init__(self, ruta_pdf: str, parent=None, service=None,
                 presupuesto_num: int = 0, cliente: str = "",
                 presupuesto_id: int = None):
        """
        Args:
            ruta_pdf: Ruta completa del archivo PDF
            parent: Widget padre
            service: Instancia del Service
            presupuesto_num: Número del presupuesto (ej. 6923)
            cliente: Nombre del cliente
            presupuesto_id: ID interno del presupuesto
        """
        super().__init__(parent)
        self.ruta_pdf = ruta_pdf
        self.svc = service
        self.presupuesto_num = presupuesto_num
        self.cliente = cliente
        self.presupuesto_id = presupuesto_id
        self.setWindowTitle("Vista Previa de Impresión")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
        self._build_ui()
        self._cargar_pdf()

    def _build_ui(self):
        """Construye la interfaz del diálogo."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Vista del PDF - CORREGIDO: MultiPage para mostrar todas las páginas
        self.pdf_view = QPdfView(self)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)  # ← CLAVE: Mostrar todas las páginas
        layout.addWidget(self.pdf_view, 1)

        # Información del archivo
        info_layout = QHBoxLayout()
        info_label = f"📄 Archivo: {os.path.basename(self.ruta_pdf)}"
        lbl_info = QLabel(info_label)
        lbl_info.setStyleSheet("QLabel { color: #666; font-size: 9px; }")
        info_layout.addWidget(lbl_info)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_imprimir = QPushButton("🖨️ Imprimir")
        self.btn_imprimir.setMinimumHeight(35)
        self.btn_imprimir.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.btn_imprimir.clicked.connect(self._on_imprimir)
        btn_layout.addWidget(self.btn_imprimir)

        self.btn_email = QPushButton("📧 Enviar por Email")
        self.btn_email.setMinimumHeight(35)
        self.btn_email.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #0b7dda; }
        """)
        self.btn_email.clicked.connect(self._on_enviar_email)
        btn_layout.addWidget(self.btn_email)

        btn_layout.addStretch()

        self.btn_cerrar = QPushButton("❌ Cerrar")
        self.btn_cerrar.setMinimumHeight(35)
        self.btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        self.btn_cerrar.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_cerrar)

        layout.addLayout(btn_layout)

    def _cargar_pdf(self):
        """Carga el PDF en el visor."""
        try:
            if os.path.exists(self.ruta_pdf):
                doc = QPdfDocument(self)
                doc.load(self.ruta_pdf)
                self.pdf_view.setDocument(doc)
            else:
                QMessageBox.warning(self, "Error", f"No se encontró el PDF:\n{self.ruta_pdf}")
        except Exception as e:
            QMessageBox.critical(self, "Error al cargar PDF", f"No se pudo cargar:\n{str(e)}")

    def _on_imprimir(self):
        """Envía el PDF a la impresora."""
        try:
            if sys.platform == 'win32':
                os.startfile(self.ruta_pdf, "print")
                QMessageBox.information(self, "Imprimir", "PDF enviado a la impresora.")
            else:
                import subprocess
                subprocess.run(['lp', self.ruta_pdf], check=True)
        except Exception as e:
            QMessageBox.critical(self, "Error al imprimir", f"No se pudo imprimir:\n{str(e)}")

    def _on_enviar_email(self):
        """Abre el diálogo de envío de email."""
        try:
            from presupuestos.ui.dialogs.enviar_correo_dialog import EnviarCorreoDialog

            # Obtener el correo del cliente si está disponible
            destinatario = ""
            if self.presupuesto_id and self.svc:
                try:
                    sql = """
                        SELECT c.Correo 
                        FROM [presupuestos].dbo.presupuestos p
                        LEFT JOIN [clientes].dbo.Clientes c ON p.cliente_id = c.id
                        WHERE p.id = ?
                    """
                    row = self.svc.db.fetchone(sql, [self.presupuesto_id])
                    if row and row[0]:
                        destinatario = row[0]
                except Exception:
                    pass

            dlg = EnviarCorreoDialog(
                parent=self,
                service=self.svc,
                destinatario=destinatario,
                presupuesto_num=self.presupuesto_num,
                cliente=self.cliente,
                ruta_pdf=self.ruta_pdf
            )

            if dlg.exec():
                QMessageBox.information(self, "Email", "Correo enviado exitosamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error al enviar email", f"No se pudo abrir:\n{str(e)}")