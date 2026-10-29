# -*- coding: utf-8 -*-
"""
Barra de estado personalizada para el concentrador de materiales.
Muestra contadores, advertencias, errores y mensajes temporales.
Corregido para evitar RuntimeError al cerrar la ventana antes de que expire el timer.
"""

from PyQt6.QtWidgets import QStatusBar, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer

from common.logger_config import get_logger

logger = get_logger('concentrador.ui.widgets.barra_estado')


class BarraEstado(QStatusBar):
    """
    Barra de estado con contadores de materiales, advertencias y errores.
    Incluye un mensaje temporal que se restablece después de 3 segundos,
    con manejo seguro del ciclo de vida de los widgets.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Configura los elementos de la barra de estado."""
        # Contador de materiales
        self.lbl_materiales = QLabel("Materiales: 0")
        self.lbl_materiales.setMinimumWidth(150)

        # Contador de advertencias (clickeable)
        self.btn_advertencias = QPushButton("⚠️ 0 advertencias")
        self.btn_advertencias.setFlat(True)
        self.btn_advertencias.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_advertencias.setStyleSheet("QPushButton { text-align: left; }")

        # Contador de errores
        self.lbl_errores = QLabel("❌ 0 errores")
        self.lbl_errores.setMinimumWidth(100)

        # Timestamp
        self.lbl_timestamp = QLabel("")
        self.lbl_timestamp.setMinimumWidth(200)
        self.lbl_timestamp.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Mensaje temporal (se restablece a "Listo" tras 3 segundos)
        self.lbl_mensaje = QLabel("Listo")
        self.lbl_mensaje.setMinimumWidth(300)

        # Agregar widgets a la barra
        self.addPermanentWidget(self.lbl_materiales)
        self.addPermanentWidget(self.btn_advertencias)
        self.addPermanentWidget(self.lbl_errores)
        self.addPermanentWidget(self.lbl_mensaje, 1)
        self.addPermanentWidget(self.lbl_timestamp)

        # Timer para restablecer el mensaje (no se inicia hasta que se use set_mensaje)
        self._reset_timer = None

    def actualizar_contadores(self, total_materiales: int, advertencias: int, errores: int):
        """
        Actualiza los contadores de materiales, advertencias y errores.
        Verifica que los widgets existan antes de modificarlos.
        """
        if not self._widgets_validos():
            return

        self.lbl_materiales.setText(f"Materiales: {total_materiales}")
        self.btn_advertencias.setText(f"⚠️ {advertencias} advertencias")
        self.lbl_errores.setText(f"❌ {errores} errores")

        if advertencias > 0:
            self.btn_advertencias.setStyleSheet("QPushButton { color: #e67e22; text-align: left; }")
        else:
            self.btn_advertencias.setStyleSheet("QPushButton { text-align: left; }")

    def set_mensaje(self, mensaje: str, temporal: bool = True):
        """
        Establece un mensaje en la barra de estado.
        Si temporal es True, se restablece a "Listo" después de 3 segundos,
        con manejo seguro para evitar acceder a widgets eliminados.
        """
        if not self._widgets_validos():
            return

        self.lbl_mensaje.setText(mensaje)

        if temporal:
            # Cancelar cualquier timer anterior que aún esté pendiente
            if self._reset_timer and self._reset_timer.isActive():
                self._reset_timer.stop()

            # Crear un nuevo timer que ejecute el restablecimiento seguro
            self._reset_timer = QTimer(self)
            self._reset_timer.setSingleShot(True)
            self._reset_timer.timeout.connect(self._restablecer_mensaje_seguro)
            self._reset_timer.start(3000)

    def _restablecer_mensaje_seguro(self):
        """
        Restablece el mensaje a "Listo" solo si el QLabel aún existe.
        Captura cualquier RuntimeError para evitar crashes al cerrar la ventana.
        """
        try:
            # Verificar que el objeto aún esté vivo y accesible
            if self.lbl_mensaje is not None:
                # En PyQt6, intentar acceder a un widget eliminado lanza RuntimeError
                self.lbl_mensaje.setText("Listo")
        except RuntimeError:
            # El widget ya fue eliminado (ventana cerrada), ignorar
            logger.debug("Intento de restablecer mensaje en barra de estado ya destruida")

    def set_timestamp(self, texto: str):
        """Establece el timestamp de la última ejecución."""
        if self._widgets_validos():
            self.lbl_timestamp.setText(texto)

    def conectar_advertencias(self, callback):
        """Conecta el botón de advertencias a un callback."""
        if self._widgets_validos():
            self.btn_advertencias.clicked.connect(callback)

    def _widgets_validos(self) -> bool:
        """
        Verifica que los widgets principales sigan existiendo.
        Retorna False si alguno ha sido eliminado (ventana cerrada).
        """
        try:
            # Comprobar un widget representativo
            _ = self.lbl_mensaje.text()
            return True
        except RuntimeError:
            return False

    def closeEvent(self, event):
        """Al cerrar la barra (o la ventana padre), detener el timer si está activo."""
        if self._reset_timer and self._reset_timer.isActive():
            self._reset_timer.stop()
        super().closeEvent(event)