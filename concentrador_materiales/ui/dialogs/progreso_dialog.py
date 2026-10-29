# -*- coding: utf-8 -*-
"""
Diálogo de progreso para procesamiento asíncrono
"""
from PyQt6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer


from common.logger_config import get_logger
logger = get_logger('concentrador.ui.dialogs.progreso')

class ConcentradorThread(QThread):
    """
    Thread para ejecutar el concentrador sin bloquear la UI.
    """
    progress = pyqtSignal(int, str)
    finished_signal = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, service, filtros):
        super().__init__()
        self.service = service
        self.filtros = filtros
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            resultado = self.service.ejecutar_concentracion(
                fecha_desde=self.filtros.get("fecha_desde"),
                fecha_hasta=self.filtros.get("fecha_hasta"),
                almacenes_filtro=self.filtros.get("almacenes") if self.filtros.get("almacenes") else None,
                cxc_id=self.filtros.get("cxc_id")  # ← NUEVO PARÁMETRO: ID del CXC específico
            )

            if not self._is_cancelled:
                self.finished_signal.emit(resultado)
            else:
                self.error.emit("Proceso cancelado por el usuario")

        except Exception as e:
            self.error.emit(str(e))

class ProgresoDialog(QDialog):
    """
    Diálogo que muestra el progreso durante la concentración.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Procesando...")
        self.setModal(True)
        self.setFixedSize(400, 150)

        self.thread = None
        self._progreso = 0
        self.timer = None

        self.setup_ui()

    def setup_ui(self):
        """Construye la interfaz del diálogo."""
        layout = QVBoxLayout(self)

        self.lbl_estado = QLabel("Iniciando concentración...")
        layout.addWidget(self.lbl_estado)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.cancelar)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

    def iniciar(self, service, filtros):
        """Inicia el proceso de concentración en un thread."""
        self.thread = ConcentradorThread(service, filtros)
        self.thread.progress.connect(self.actualizar_progreso)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.error.connect(self.on_error)
        self.thread.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self._simular_progreso)
        self.timer.start(100)
        self._progreso = 0

    def _simular_progreso(self):
        if self._progreso < 90:
            self._progreso += 2
            self.progress_bar.setValue(self._progreso)

    def actualizar_progreso(self, valor, mensaje):
        self.progress_bar.setValue(valor)
        self.lbl_estado.setText(mensaje)

    def on_finished(self, resultado):
        if self.timer:
            self.timer.stop()
        self.progress_bar.setValue(100)
        self.lbl_estado.setText("Proceso completado")

        # Llamar al método del padre si existe
        parent = self.parent()
        if parent and hasattr(parent, 'mostrar_resultado'):
            parent.mostrar_resultado(resultado)

        self.accept()

    def on_error(self, mensaje):
        if self.timer:
            self.timer.stop()
        self.lbl_estado.setText(f"Error: {mensaje}")
        QMessageBox.critical(self, "Error", mensaje)
        self.reject()

    def cancelar(self):
        if self.thread:
            self.thread.cancel()
        self.lbl_estado.setText("Cancelando...")
        self.btn_cancelar.setEnabled(False)