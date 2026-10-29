# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/ui/dialogs/navegar_partidas_dialog.py
Diálogo para navegar entre partidas de un presupuesto.
CORREGIDO: Uso de QColor en lugar de Qt.GlobalColor.lightYellow (inexistente en PyQt6)
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor  # ← AGREGADO: Import necesario para el color


class NavegarPartidasDialog(QDialog):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.partida_seleccionada_indice = -1
        
        self.setWindowTitle("Navegar entre Partidas")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Instrucciones
        lbl = QLabel("Seleccione una partida para navegar:")
        lbl.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(lbl)
        
        # Lista de partidas
        self.lista_partidas = QListWidget()
        self.lista_partidas.itemDoubleClicked.connect(self.aceptar_seleccion)
        layout.addWidget(self.lista_partidas)
        
        # Botones
        btn_layout = QHBoxLayout()
        self.btn_ir = QPushButton("Ir a Partida")
        self.btn_ir.clicked.connect(self.aceptar_seleccion)
        self.btn_ir.setEnabled(False)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_ir)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)
        
        # Cargar partidas
        self.cargar_partidas()
        
        # Conexión para habilitar botón
        self.lista_partidas.currentRowChanged.connect(
            lambda idx: self.btn_ir.setEnabled(idx >= 0)
        )
    
    def cargar_partidas(self):
        """Carga la lista de partidas del presupuesto actual."""
        self.lista_partidas.clear()
        if not self.controller._partidas_cache:
            self.lista_partidas.addItem("No hay partidas en este presupuesto")
            return
        for i, partida in enumerate(self.controller._partidas_cache):
            num = partida.get('partida', 0)
            titulo = partida.get('titulo', '') or 'Sin título'
            if len(titulo) > 50:
                titulo = titulo[:47] + '...'
            texto = f"Partida {num}: {titulo}"
            item = QListWidgetItem(texto)
            item.setData(Qt.ItemDataRole.UserRole, i)
            self.lista_partidas.addItem(item)
            # Marcar la partida actual
            if i == self.controller._indice_partida_actual:
                # CORREGIDO: Usar QColor en lugar de Qt.GlobalColor.lightYellow
                item.setBackground(QColor("lightyellow"))
                self.lista_partidas.setCurrentItem(item)
    
    def aceptar_seleccion(self):
        """Acepta la partida seleccionada y navega a ella."""
        item = self.lista_partidas.currentItem()
        if item:
            indice = item.data(Qt.ItemDataRole.UserRole)
            if indice is not None:
                self.partida_seleccionada_indice = indice
                self.accept()
    
    def get_indice_seleccionado(self):
        """Retorna el índice de la partida seleccionada."""
        return self.partida_seleccionada_indice