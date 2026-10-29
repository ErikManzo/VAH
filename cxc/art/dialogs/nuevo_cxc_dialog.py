# -*- coding: utf-8 -*-
"""
Diálogo para crear nuevo CXC desde un presupuesto.
CORREGIDO: Edición de columna CANTIDAD funcionando con clic, doble clic y teclado.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox,
    QDoubleSpinBox, QTextEdit, QPushButton, QMessageBox, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
from decimal import Decimal
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.focus_utils import setup_form_navigation
from cxc.services.cxc_service import CxcService
from cxc.repositories.cxc_repository import CxcRepository
from cxc.repositories.configuracion_repository import ConfiguracionRepository
from cxc.utils.mayusculas import aplicar_mayusculas
from cxc.data.db import get_connection


class NuevoCxcDialog(QDialog):
    COL_SEL = 0
    COL_PARTIDA = 1
    COL_TITULO = 2
    COL_DESCRIPCION = 3
    COL_CANTIDAD = 4
    COL_PRECIO = 5
    COL_IMPORTE = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NUEVO CXC - DESDE PRESUPUESTO")
        if parent:
            self.setWindowIcon(parent.windowIcon())
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setModal(True)

        # Variables de estado
        self.presupuesto_seleccionado = None
        self.partidas_seleccionadas = []
        self._actualizando_tabla = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # ============================================
        # SELECCIÓN DE PRESUPUESTO
        # ============================================
        group_presupuesto = QGroupBox("SELECCIONAR PRESUPUESTO")
        form_presupuesto = QFormLayout()

        self.cmb_presupuesto = QComboBox()
        self.cmb_presupuesto.setMinimumWidth(400)
        self.cmb_presupuesto.addItem("-- SELECCIONE UN PRESUPUESTO --", None)
        self.cmb_presupuesto.currentIndexChanged.connect(self.on_presupuesto_seleccionado)
        form_presupuesto.addRow("Presupuesto:", self.cmb_presupuesto)

        self.lbl_info_presupuesto = QLabel("Información del presupuesto seleccionado")
        self.lbl_info_presupuesto.setStyleSheet("color: #555; font-style: italic;")
        form_presupuesto.addRow(self.lbl_info_presupuesto)

        group_presupuesto.setLayout(form_presupuesto)
        layout.addWidget(group_presupuesto)

        # ============================================
        # TABLA DE PARTIDAS
        # ============================================
        group_partidas = QGroupBox("PARTIDAS DEL PRESUPUESTO (Seleccione las que aplican)")
        layout_partidas = QVBoxLayout()

        self.table_partidas = QTableWidget()
        self.table_partidas.setColumnCount(7)
        self.table_partidas.setHorizontalHeaderLabels([
            "SEL", "PARTIDA", "TÍTULO", "DESCRIPCIÓN", "CANTIDAD", "P. UNITARIO", "IMPORTE"
        ])
        self.table_partidas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Configuración de edición: múltiples triggers para facilitar la edición
        self.table_partidas.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.AnyKeyPressed
            | QAbstractItemView.EditTrigger.CurrentChanged
        )
        self.table_partidas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_partidas.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.table_partidas.setMinimumHeight(200)

        # Conectar eventos
        self.table_partidas.itemChanged.connect(self.on_item_changed)
        self.table_partidas.cellClicked.connect(self._on_cell_clicked)
        self.table_partidas.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table_partidas.currentCellChanged.connect(self._on_current_cell_changed)

        layout_partidas.addWidget(self.table_partidas)

        group_partidas.setLayout(layout_partidas)
        layout.addWidget(group_partidas, 1)

        # ============================================
        # CONFIGURACIÓN DE CXC
        # ============================================
        group_config = QGroupBox("CONFIGURACIÓN DE CXC")
        form_config = QFormLayout()

        self.tipo_operacion = QComboBox()
        self.tipo_operacion.addItems(["FACTURADO", "SIN FACTURAR"])
        form_config.addRow("Tipo de Operación:", self.tipo_operacion)

        self.descuento_porcentaje = QDoubleSpinBox()
        self.descuento_porcentaje.setRange(0, 100)
        self.descuento_porcentaje.setSuffix(" %")
        self.descuento_porcentaje.setValue(0)
        form_config.addRow("Descuento (%):", self.descuento_porcentaje)

        self.descuento_monto = QDoubleSpinBox()
        self.descuento_monto.setPrefix("$ ")
        self.descuento_monto.setRange(0, 9999999.99)
        self.descuento_monto.setValue(0)
        form_config.addRow("Descuento (Monto):", self.descuento_monto)

        self.lbl_subtotal = QLabel("$ 0.00")
        self.lbl_subtotal.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_config.addRow("Subtotal:", self.lbl_subtotal)

        self.lbl_total_cxc = QLabel("$ 0.00")
        self.lbl_total_cxc.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_total_cxc.setStyleSheet("font-weight: bold; color: #1f6feb;")
        form_config.addRow("Total estimado:", self.lbl_total_cxc)

        self.notas = QTextEdit()
        self.notas.setMaximumHeight(60)
        self.notas.setPlaceholderText("Notas adicionales...")
        aplicar_mayusculas(self.notas)
        form_config.addRow("Notas:", self.notas)

        self.tipo_operacion.currentTextChanged.connect(self.recalcular_total_general)
        self.descuento_porcentaje.valueChanged.connect(self.recalcular_total_general)
        self.descuento_monto.valueChanged.connect(self.recalcular_total_general)

        group_config.setLayout(form_config)
        layout.addWidget(group_config)

        # ============================================
        # BOTONES
        # ============================================
        btn_layout = QHBoxLayout()
        self.btn_cargar = QPushButton("CARGAR PRESUPUESTOS")
        self.btn_cargar.clicked.connect(self.cargar_presupuestos)

        self.btn_guardar = QPushButton("CREAR CXC")
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.clicked.connect(self.guardar)

        self.btn_cancelar = QPushButton("CANCELAR")
        self.btn_cancelar.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_cargar)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

        # Configurar navegación con Tab y Enter
        self._focus_navigation = setup_form_navigation(
            self,
            tab_widgets=[
                self.cmb_presupuesto,
                self.table_partidas,
                self.tipo_operacion,
                self.descuento_porcentaje,
                self.descuento_monto,
                self.notas,
                self.btn_cargar,
                self.btn_guardar,
                self.btn_cancelar,
            ],
            enter_widgets=[
                self.cmb_presupuesto,
                self.tipo_operacion,
                self.descuento_porcentaje,
                self.descuento_monto,
            ],
            submit_callback=self.btn_guardar.click,
        )

        # Cargar presupuestos al iniciar
        self.cargar_presupuestos()
        self.recalcular_total_general()

    # ========================================================================
    # CARGA DE DATOS
    # ========================================================================

    def cargar_presupuestos(self):
        """Carga la lista de presupuestos desde la base de datos."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.presupuesto, p.obra, c.Nombre as cliente
                FROM [presupuestos].[dbo].[presupuestos] p
                LEFT JOIN [clientes].[dbo].[Clientes] c ON p.cliente_id = c.id
                ORDER BY p.presupuesto DESC
            """)
            rows = cursor.fetchall()
            conn.close()

            self.cmb_presupuesto.clear()
            self.cmb_presupuesto.addItem("-- SELECCIONE UN PRESUPUESTO --", None)

            for row in rows:
                presupuesto_id = row[0]
                numero = row[1]
                obra = row[2] or "SIN OBRA"
                cliente = row[3] or "SIN CLIENTE"
                display = f"{numero} - {cliente} - {obra}"
                self.cmb_presupuesto.addItem(display, presupuesto_id)

            if len(rows) == 0:
                QMessageBox.warning(self, "SIN DATOS", "No existen presupuestos en la base de datos.")

        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"Error cargando presupuestos:\n{str(e)}")

    def on_presupuesto_seleccionado(self, index):
        """Cuando se selecciona un presupuesto, carga sus partidas."""
        presupuesto_id = self.cmb_presupuesto.currentData()

        if not presupuesto_id:
            self.presupuesto_seleccionado = None
            self.table_partidas.setRowCount(0)
            self.btn_guardar.setEnabled(False)
            self.lbl_info_presupuesto.setText("Ningún presupuesto seleccionado")
            self.recalcular_total_general()
            return

        self.presupuesto_seleccionado = presupuesto_id
        self.cargar_partidas(presupuesto_id)
        QTimer.singleShot(0, self._enfocar_primera_cantidad)

    def cargar_partidas(self, presupuesto_id: int):
        """Carga las partidas del presupuesto seleccionado."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pa.id, pa.partida, pa.titulo, pa.descripcion,
                       pa.piezas, pa.precio_unitario, pa.total_partida
                FROM [presupuestos].[dbo].[partidas] pa
                WHERE pa.presupuesto_id = ?
                ORDER BY pa.partida
            """, (presupuesto_id,))
            rows = cursor.fetchall()
            conn.close()

            self._actualizando_tabla = True
            self.table_partidas.setRowCount(len(rows))
            self.partidas_seleccionadas = []

            for i, row in enumerate(rows):
                partida_id = row[0]
                numero_partida = row[1]
                titulo = row[2]
                descripcion = row[3] or ""
                cantidad_raw = row[4]
                precio = float(row[5] or 0)
                total = float(row[6] or 0)
                cantidad = int(float(cantidad_raw or 0))
                if cantidad < 1 and precio > 0 and total > 0:
                    cantidad = int(round(total / precio))
                if cantidad < 1:
                    cantidad = 1
                if precio <= 0 and cantidad > 0 and total > 0:
                    precio = total / cantidad
                if total <= 0:
                    total = cantidad * precio

                # Checkbox de selección
                check_item = QTableWidgetItem()
                check_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                check_item.setCheckState(Qt.CheckState.Checked)
                self.table_partidas.setItem(i, self.COL_SEL, check_item)

                partida_item = QTableWidgetItem(str(numero_partida))
                partida_item.setFlags(partida_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_partidas.setItem(i, self.COL_PARTIDA, partida_item)

                titulo_item = QTableWidgetItem(titulo or "")
                titulo_item.setFlags(titulo_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_partidas.setItem(i, self.COL_TITULO, titulo_item)

                descripcion_item = QTableWidgetItem(descripcion[:80])
                descripcion_item.setFlags(descripcion_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_partidas.setItem(i, self.COL_DESCRIPCION, descripcion_item)

                cantidad_item = QTableWidgetItem(str(cantidad))
                cantidad_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cantidad_item.setFlags(cantidad_item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table_partidas.setItem(i, self.COL_CANTIDAD, cantidad_item)

                precio_item = QTableWidgetItem(self._format_money(precio))
                precio_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                precio_item.setFlags(precio_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_partidas.setItem(i, self.COL_PRECIO, precio_item)

                importe_item = QTableWidgetItem(self._format_money(total))
                importe_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                importe_item.setFlags(importe_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table_partidas.setItem(i, self.COL_IMPORTE, importe_item)

                # Guardar datos completos para uso posterior
                self.table_partidas.item(i, self.COL_SEL).setData(Qt.ItemDataRole.UserRole, {
                    'partida_id': partida_id,
                    'precio_unitario': float(precio),
                    'cantidad_original': int(cantidad),
                    'cantidad_facturada': int(cantidad),
                    'importe': float(total)
                })

            self.btn_guardar.setEnabled(True)
            self.lbl_info_presupuesto.setText(f"Presupuesto #{presupuesto_id} cargado - {len(rows)} partidas")
            self.recalcular_total_general()

        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"Error cargando partidas:\n{str(e)}")
        finally:
            self._actualizando_tabla = False

    # ========================================================================
    # MANEJO DE FOCO Y EDICIÓN DE CANTIDAD
    # ========================================================================

    def _enfocar_primera_cantidad(self):
        """Enfoca la primera celda de cantidad de la tabla."""
        if self.table_partidas.rowCount() <= 0:
            return
        self._enfocar_cantidad_fila(0)

    def _enfocar_cantidad_fila(self, row: int):
        """Coloca el foco en la celda de cantidad de la fila indicada."""
        if row < 0 or row >= self.table_partidas.rowCount():
            return
        cantidad_item = self.table_partidas.item(row, self.COL_CANTIDAD)
        if cantidad_item is None:
            return
        self.table_partidas.setCurrentCell(row, self.COL_CANTIDAD)
        self.table_partidas.scrollToItem(cantidad_item)
        self.table_partidas.setFocus()

    def _abrir_editor_cantidad(self, row: int):
        """Fuerza la apertura del editor en la celda de cantidad de la fila dada."""
        if row < 0 or row >= self.table_partidas.rowCount():
            return
        item = self.table_partidas.item(row, self.COL_CANTIDAD)
        if item is not None:
            self.table_partidas.setCurrentCell(row, self.COL_CANTIDAD)
            self.table_partidas.editItem(item)

    # ========================================================================
    # EVENTOS DE LA TABLA
    # ========================================================================

    def _on_cell_clicked(self, row: int, column: int):
        """Al hacer clic en la columna CANTIDAD, abrir editor inmediatamente."""
        if column == self.COL_CANTIDAD:
            QTimer.singleShot(0, lambda r=row: self._abrir_editor_cantidad(r))
        else:
            # Si se hace clic en otra columna, enfocar la cantidad pero sin abrir editor
            self._enfocar_cantidad_fila(row)

    def _on_cell_double_clicked(self, row: int, column: int):
        """Al hacer doble clic en cualquier celda, abrir editor en cantidad."""
        QTimer.singleShot(0, lambda r=row: self._abrir_editor_cantidad(r))

    def _on_current_cell_changed(self, current_row: int, current_col: int, previous_row: int, previous_col: int):
        """Cuando se cambia la celda actual, si es la columna cantidad, abrir editor."""
        if current_col == self.COL_CANTIDAD and current_row >= 0:
            QTimer.singleShot(0, lambda r=current_row: self._abrir_editor_cantidad(r))

    # ========================================================================
    # CÁLCULOS Y ACTUALIZACIÓN DE DATOS
    # ========================================================================

    def _format_money(self, value: float) -> str:
        return f"$ {float(value):,.2f}"

    def _obtener_datos_fila(self, row: int):
        item = self.table_partidas.item(row, self.COL_SEL)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _guardar_datos_fila(self, row: int, datos: dict):
        item = self.table_partidas.item(row, self.COL_SEL)
        if item:
            item.setData(Qt.ItemDataRole.UserRole, datos)

    def _obtener_iva_porcentaje(self) -> float:
        try:
            config = ConfiguracionRepository.get_config()
            if config and config.iva_default is not None:
                return float(config.iva_default)
        except Exception:
            pass
        return 16.0

    def on_item_changed(self, item: QTableWidgetItem):
        """Cuando cambia el contenido de una celda, recalcula importe y totales."""
        if self._actualizando_tabla or item is None:
            return

        row = item.row()
        col = item.column()

        if col == self.COL_CANTIDAD:
            datos = self._obtener_datos_fila(row)
            if not datos:
                return

            cantidad_anterior = int(datos.get("cantidad_facturada") or 1)
            texto = (item.text() or "").strip()
            try:
                cantidad_nueva = int(float(texto))
                if cantidad_nueva < 1:
                    raise ValueError()
            except Exception:
                cantidad_nueva = cantidad_anterior

            importe_nuevo = float(cantidad_nueva) * float(datos.get("precio_unitario") or 0.0)
            datos["cantidad_facturada"] = cantidad_nueva
            datos["importe"] = importe_nuevo

            self._actualizando_tabla = True
            try:
                item.setText(str(cantidad_nueva))
                importe_item = self.table_partidas.item(row, self.COL_IMPORTE)
                if importe_item is None:
                    importe_item = QTableWidgetItem()
                    importe_item.setFlags(importe_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table_partidas.setItem(row, self.COL_IMPORTE, importe_item)
                importe_item.setText(self._format_money(importe_nuevo))
                importe_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._guardar_datos_fila(row, datos)
            finally:
                self._actualizando_tabla = False

        if col in (self.COL_SEL, self.COL_CANTIDAD):
            self.recalcular_total_general()

    def recalcular_total_general(self):
        """Recalcula el subtotal y total general del CXC."""
        subtotal = 0.0
        for i in range(self.table_partidas.rowCount()):
            check_item = self.table_partidas.item(i, self.COL_SEL)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                datos = check_item.data(Qt.ItemDataRole.UserRole) or {}
                subtotal += float(datos.get("importe") or 0.0)

        if self.descuento_monto.value() > 0:
            descuento = float(self.descuento_monto.value())
        elif self.descuento_porcentaje.value() > 0:
            descuento = subtotal * (float(self.descuento_porcentaje.value()) / 100.0)
        else:
            descuento = 0.0

        subtotal_con_descuento = max(subtotal - descuento, 0.0)
        if self.tipo_operacion.currentText() == "FACTURADO":
            total = subtotal_con_descuento * (1.0 + (self._obtener_iva_porcentaje() / 100.0))
        else:
            total = subtotal_con_descuento

        self.lbl_subtotal.setText(self._format_money(subtotal))
        self.lbl_total_cxc.setText(self._format_money(total))

    def obtener_partidas_seleccionadas(self):
        """Obtiene las partidas marcadas por el usuario."""
        partidas = []
        for i in range(self.table_partidas.rowCount()):
            check_item = self.table_partidas.item(i, self.COL_SEL)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                datos = check_item.data(Qt.ItemDataRole.UserRole)
                if datos:
                    partidas.append({
                        'partida_id': datos['partida_id'],
                        'cantidad_facturada': int(datos.get('cantidad_facturada') or 1),
                        'precio_unitario': float(datos.get('precio_unitario') or 0.0),
                        'importe': float(datos.get('importe') or 0.0),
                    })
        return partidas

    def guardar(self):
        """Lógica real de creación de CXC."""
        # Validaciones
        if not self.presupuesto_seleccionado:
            QMessageBox.warning(self, "ERROR", "Debe seleccionar un presupuesto.")
            return

        partidas = self.obtener_partidas_seleccionadas()
        if not partidas:
            QMessageBox.warning(self, "ERROR", "Debe seleccionar al menos una partida.")
            return

        # Confirmación
        resp = QMessageBox.question(
            self,
            "CONFIRMAR CREACIÓN",
            f"¿Crear CXC desde el presupuesto #{self.presupuesto_seleccionado}?\n\n"
            f"Partidas seleccionadas: {len(partidas)}\n"
            f"Tipo: {self.tipo_operacion.currentText()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            cxc_id = CxcService.crear_cxc_desde_presupuesto(
                presupuesto_id=self.presupuesto_seleccionado,
                tipo_operacion=self.tipo_operacion.currentText(),
                partidas_seleccionadas=partidas,
                descuento_porcentaje=self.descuento_porcentaje.value(),
                descuento_monto=self.descuento_monto.value(),
                notas=self.notas.toPlainText(),
                aceptar_presupuesto=True
            )

            QMessageBox.information(
                self,
                "ÉXITO",
                f"CXC creado correctamente.\nID: {cxc_id}"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "ERROR",
                f"Error creando CXC:\n{str(e)}"
            )