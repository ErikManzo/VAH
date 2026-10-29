# -*- coding: utf-8 -*-
"""
Diálogo para unificar proveedores duplicados
Muestra una vista previa y permite seleccionar qué registros conservar
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QGroupBox, QRadioButton, QButtonGroup,
    QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt


class UnificarProveedoresDialog(QDialog):
    """
    Diálogo que muestra proveedores duplicados y permite seleccionar
    cuál conservar y cuáles eliminar.
    """

    def __init__(self, duplicados, parent=None):
        super().__init__(parent)
        self.duplicados = duplicados
        self.seleccionado_id = None
        self.ids_a_eliminar = []
        self.radio_buttons = []
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Unificar Proveedores Duplicados")
        self.setMinimumSize(950, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Instrucciones
        lbl_info = QLabel(
            "Se encontraron múltiples registros que podrían ser duplicados.\n"
            "Seleccione el registro que desea CONSERVAR (se mantendrá en la base de datos).\n"
            "Los registros NO seleccionados serán ELIMINADOS después de la unificación."
        )
        lbl_info.setStyleSheet("background-color: #FFF3CD; padding: 8px; border-radius: 4px;")
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        # Grupo de registros duplicados
        group = QGroupBox("Registros encontrados")
        group_layout = QVBoxLayout(group)

        # Tabla de registros
        self.tabla = QTableWidget()
        self._configurar_tabla()
        group_layout.addWidget(self.tabla)

        layout.addWidget(group)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_unificar = QPushButton("Unificar seleccionados")
        self.btn_unificar.setEnabled(False)
        self.btn_unificar.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px;")
        self.btn_unificar.clicked.connect(self.unificar)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("padding: 8px;")
        self.btn_cancelar.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_unificar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

        self._llenar_tabla()

    def _configurar_tabla(self):
        columnas = [
            "Conservar", "ID", "Empresa", "Tipo", "Agente",
            "RFC", "Teléfono", "Correo", "Dirección"
        ]
        self.tabla.setColumnCount(len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)

        self.tabla.setColumnWidth(0, 85)
        self.tabla.setColumnWidth(1, 50)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(self.tabla.SelectionBehavior.SelectRows)

    def _llenar_tabla(self):
        self.tabla.setRowCount(0)
        self.radio_buttons = []
        grupo_radio = QButtonGroup(self)

        for i, proveedor in enumerate(self.duplicados):
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)

            id_proveedor = proveedor.get("id")
            if isinstance(id_proveedor, dict):
                id_proveedor = id_proveedor.get("id") or id_proveedor.get("id_proveedor")

            radio = QRadioButton()
            radio.setProperty("fila", i)
            radio.setProperty("id_proveedor", id_proveedor)
            radio.toggled.connect(lambda checked, idx=i: self._on_seleccion_cambiado(checked, idx))

            grupo_radio.addButton(radio)
            self.radio_buttons.append(radio)

            if i == 0:
                radio.setChecked(True)
                self.seleccionado_id = id_proveedor

            self.tabla.setCellWidget(fila, 0, radio)

            self.tabla.setItem(fila, 1, QTableWidgetItem(str(id_proveedor) if id_proveedor else ""))
            self.tabla.setItem(fila, 2, QTableWidgetItem(proveedor.get("empresa", "")))
            self.tabla.setItem(fila, 3, QTableWidgetItem(proveedor.get("tipo_proveedor", "")))
            self.tabla.setItem(fila, 4, QTableWidgetItem(proveedor.get("nombre_agente", "")))
            self.tabla.setItem(fila, 5, QTableWidgetItem(proveedor.get("rfc", "")))
            self.tabla.setItem(fila, 6, QTableWidgetItem(proveedor.get("telefono", "")))
            self.tabla.setItem(fila, 7, QTableWidgetItem(proveedor.get("correo", "")))
            self.tabla.setItem(fila, 8, QTableWidgetItem(proveedor.get("direccion", "")))

            for col in range(2, self.tabla.columnCount()):
                item = self.tabla.item(fila, col)
                if item and not item.text().strip():
                    item.setBackground(Qt.GlobalColor.lightGray)

        self.tabla.resizeRowsToContents()

        if self.duplicados:
            self.btn_unificar.setEnabled(True)

    def _on_seleccion_cambiado(self, checked, indice):
        if checked:
            self.btn_unificar.setEnabled(True)
            radio = self.radio_buttons[indice] if indice < len(self.radio_buttons) else None
            if radio:
                self.seleccionado_id = radio.property("id_proveedor")

            self.ids_a_eliminar = []
            for i, radio_btn in enumerate(self.radio_buttons):
                if i != indice:
                    pid = radio_btn.property("id_proveedor")
                    if pid:
                        self.ids_a_eliminar.append(pid)

    def unificar(self):
        if not self.seleccionado_id:
            QMessageBox.warning(self, "Advertencia", "Debe seleccionar un registro para conservar.")
            return

        if not self.ids_a_eliminar:
            for i, radio in enumerate(self.radio_buttons):
                pid = radio.property("id_proveedor")
                if pid and pid != self.seleccionado_id:
                    self.ids_a_eliminar.append(pid)

        if not self.ids_a_eliminar:
            QMessageBox.warning(self, "Advertencia", "No hay registros para eliminar.")
            return

        mensaje = (
            f"Se conservará el registro ID: {self.seleccionado_id}\n"
            f"Se eliminarán {len(self.ids_a_eliminar)} registro(s) duplicado(s).\n\n"
            "¿Está seguro de continuar? Esta acción NO se puede deshacer."
        )

        respuesta = QMessageBox.question(
            self, "Confirmar unificación", mensaje,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.accept()

    def get_seleccionado_id(self):
        return self.seleccionado_id

    def get_ids_a_eliminar(self):
        return self.ids_a_eliminar