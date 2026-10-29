# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/ui/dialogs/abrir_presupuesto_dialog.py
Diálogo para buscar y seleccionar un presupuesto existente.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from typing import Optional


class AbrirPresupuestoDialog(QDialog):
    def __init__(self, parent, service):
        super().__init__(parent)
        self.service = service
        self.presupuesto_seleccionado = None

        self.setWindowTitle("Abrir Presupuesto")
        self.setModal(True)
        self.resize(900, 600)
        
        layout = QVBoxLayout(self)

        # Panel de filtros
        filtros_layout = QGridLayout()
        fila = 0
        
        filtros_layout.addWidget(QLabel("Número:"), fila, 0)
        self.numero_edit = QLineEdit()
        self.numero_edit.setPlaceholderText("Número exacto")
        filtros_layout.addWidget(self.numero_edit, fila, 1)
        
        filtros_layout.addWidget(QLabel("Cliente:"), fila, 2)
        self.cliente_edit = QLineEdit()
        self.cliente_edit.setPlaceholderText("Nombre del cliente")
        filtros_layout.addWidget(self.cliente_edit, fila, 3)
        
        fila += 1
        filtros_layout.addWidget(QLabel("Obra:"), fila, 0)
        self.obra_edit = QLineEdit()
        self.obra_edit.setPlaceholderText("Obra")
        filtros_layout.addWidget(self.obra_edit, fila, 1)
        
        filtros_layout.addWidget(QLabel("Fecha desde:"), fila, 2)
        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDate(QDate(2000, 1, 1))
        filtros_layout.addWidget(self.fecha_desde, fila, 3)
        
        fila += 1
        filtros_layout.addWidget(QLabel("Fecha hasta:"), fila, 2)
        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDate(QDate.currentDate())
        filtros_layout.addWidget(self.fecha_hasta, fila, 3)
        
        layout.addLayout(filtros_layout)

        # Botón buscar
        btn_buscar = QPushButton("🔍 Buscar")
        btn_buscar.clicked.connect(self.buscar)
        layout.addWidget(btn_buscar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Tabla de resultados
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Número", "Cliente", "Obra", "Fecha"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        self.tabla.doubleClicked.connect(self.aceptar_seleccion)
        self.tabla.itemActivated.connect(self.aceptar_seleccion)
        
        layout.addWidget(self.tabla)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_aceptar = QPushButton("Abrir")
        self.btn_aceptar.clicked.connect(self.aceptar_seleccion)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_aceptar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

        self.buscar()

    def buscar(self):
        filtros = {}
        
        if self.numero_edit.text().strip():
            try:
                filtros['numero'] = int(self.numero_edit.text().strip())
            except ValueError:
                pass
        
        if self.cliente_edit.text().strip():
            filtros['cliente'] = self.cliente_edit.text().strip()
        
        if self.obra_edit.text().strip():
            filtros['obra'] = self.obra_edit.text().strip()
        
        if self.fecha_desde.date().toString("yyyy-MM-dd") != "2000-01-01":
            filtros['fecha_inicio'] = self.fecha_desde.date().toString("yyyy-MM-dd")
        
        filtros['fecha_fin'] = self.fecha_hasta.date().toString("yyyy-MM-dd")
        
        try:
            resultados = self.service.buscar_presupuestos(filtros)
        except Exception as e:
            resultados = []
            self.tabla.setRowCount(1)
            self.tabla.setItem(0, 0, QTableWidgetItem(f"Error: {str(e)}"))
            return
        
        self.tabla.setRowCount(len(resultados))
        
        for i, p in enumerate(resultados):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(p['id'])))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(p['presupuesto'])))
            self.tabla.setItem(i, 2, QTableWidgetItem(p['cliente_nombre']))
            self.tabla.setItem(i, 3, QTableWidgetItem(p['obra']))
            
            fecha = p['fecha']
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime("%d/%m/%Y")
            else:
                fecha = str(fecha)
            self.tabla.setItem(i, 4, QTableWidgetItem(fecha))

    def aceptar_seleccion(self):
        current = self.tabla.currentRow()
        if current >= 0:
            id_item = self.tabla.item(current, 0)
            if id_item:
                try:
                    self.presupuesto_seleccionado = int(id_item.text())
                    self.accept()
                except ValueError:
                    QMessageBox.warning(
                        self,
                        "Selección inválida",
                        "Por favor seleccione un presupuesto válido de la tabla."
                    )

    def get_selected_id(self) -> Optional[int]:
        return self.presupuesto_seleccionado
