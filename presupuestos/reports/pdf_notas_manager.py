# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/reports/pdf_notas_manager.py
Gestor de notas aclaratorias para presupuestos
Responsabilidad:
Antes de imprimir, preguntar si hay notas
Almacenar las notas ingresadas por el usuario
Renderizar las notas después de totales y antes de "FORMA DE PAGO"
NUEVO: gestiona también el DESCUENTO (%) modificable por el usuario.
"""
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import QMessageBox
from reportlab.pdfgen import canvas
from presupuestos.ui.dialogs.notas_presupuesto_dialog import NotasPresupuestoDialog

class NotasManager:
    """Gestor de notas aclaratorias para presupuestos"""

    def __init__(self, parent=None, service=None):
        """
        Args:
            parent: Widget padre (normalmente la ventana principal)
            service: Instancia de Service para guardar/cargar notas
        """
        self.parent = parent
        self.svc = service
        self.presupuesto_id = None
        self.notas = ""
        self.forma_pago = ""
        self.plazo_entrega = ""
        self.descuento = 0.0
        self._cargadas = False

    def cargar_desde_bd(self, presupuesto_id: int):
        """Carga las notas (y el descuento) desde la base de datos."""
        self.presupuesto_id = presupuesto_id
        if self.svc and presupuesto_id:
            config = self.svc.obtener_configuracion_presupuesto(presupuesto_id)
            self.notas = config.get('notas', '')
            self.forma_pago = config.get('forma_pago', '60% AL ACEPTAR EL PRESUPUESTO / 40% AL TERMINAR')
            self.plazo_entrega = config.get('plazo_entrega', 'SERÁ DE COMÚN ACUERDO')
            try:
                self.descuento = float(config.get('descuento_porcentaje', 0.0) or 0.0)
            except (TypeError, ValueError):
                self.descuento = 0.0
            self._cargadas = True

    def preguntar_notas(self, presupuesto_id: int) -> tuple:
        """
        Pregunta al usuario si desea agregar/editar notas, forma de pago,
        descuento y plazo de entrega.
        Returns:
            tuple: (notas: str, forma_pago: str, plazo_entrega: str, descuento: float)
        """
        if not self.parent or not self.svc:
            return (self.notas, self.forma_pago, self.plazo_entrega, self.descuento)
        # Cargar desde BD si no se ha hecho
        if not self._cargadas and presupuesto_id:
            self.cargar_desde_bd(presupuesto_id)
        # Preguntar si desea configurar
        respuesta = QMessageBox.question(
            self.parent,
            "Configuración del presupuesto",
            "¿Desea configurar notas aclaratorias, forma de pago, descuento y plazo de entrega?\n\n"
            "Las notas aparecerán después del total general y antes de la forma de pago.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return (self.notas, self.forma_pago, self.plazo_entrega, self.descuento)
        # Mostrar diálogo (con el descuento precargado y editable)
        dialog = NotasPresupuestoDialog(
            self.parent,
            notas_actual=self.notas,
            forma_pago_actual=self.forma_pago,
            plazo_entrega_actual=self.plazo_entrega,
            descuento_actual=self.descuento
        )
        if dialog.exec() == NotasPresupuestoDialog.DialogCode.Accepted:
            self.notas = dialog.obtener_notas()
            self.forma_pago = dialog.obtener_forma_pago()
            self.plazo_entrega = dialog.obtener_plazo_entrega()
            self.descuento = dialog.obtener_descuento()
            # Guardar en BD (incluye descuento)
            if self.svc and presupuesto_id:
                self.svc.guardar_configuracion_presupuesto(
                    presupuesto_id, self.notas, self.forma_pago,
                    self.plazo_entrega, self.descuento
                )
        return (self.notas, self.forma_pago, self.plazo_entrega, self.descuento)

    def tiene_notas(self) -> bool:
        """Verifica si hay notas almacenadas."""
        return len(self.notas.strip()) > 0

    def get_forma_pago(self) -> str:
        """Retorna la forma de pago."""
        return self.forma_pago if self.forma_pago else "60% AL ACEPTAR EL PRESUPUESTO / 40% AL TERMINAR"

    def get_plazo_entrega(self) -> str:
        """Retorna el plazo de entrega."""
        return self.plazo_entrega if self.plazo_entrega else "SERÁ DE COMÚN ACUERDO"

    def dibujar_notas(self, c: canvas.Canvas, y: float, left: float, width: float, generador) -> float:
        """
        Dibuja las notas en el PDF.
        """
        if not self.tiene_notas():
            return y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left, y, "NOTAS:")
        y -= 15
        c.setFont("Helvetica", 9)
        lineas = self.notas.split('\n')
        for nota in lineas:
            nota = nota.strip()
            if nota:
                y = generador._texto_multilinea(c, nota, left + 10, y, width - 10, 10)
                y -= 5
        y -= 10
        return y