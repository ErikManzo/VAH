# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QMessageBox, QListWidgetItem
from common.search_utils import configure_list_widget_for_search_results, format_key_description

from presupuestos.core.utils import es_tipo_paquete

class SearchController:
    def __init__(self, window, svc):
        self.window = window
        self.svc = svc
        self.search_service = svc.material_service
        self.cliente_service = svc.cliente_service
        self.ui_builder = svc.ui_builder if hasattr(svc, 'ui_builder') else None

    def on_list_accepted(self, list_w, list_type):
        item = list_w.currentItem()
        if not item: return
        
        if list_type == "cliente":
            self.on_cliente_picked(item)
        else:
            self.on_material_picked(item)

    def on_cliente_picked(self, item):
        if not item: return
        rec = item.data(Qt.ItemDataRole.UserRole)
        if not rec: return
        
        # Lógica original de pick_cliente
        self.window.le_cliente.setText(self.ui_builder.format_cliente_for_list(rec))
        self.window.cliente_actual_id = rec.get("id")
        self.window.lst_clientes.setVisible(False)
        self.window.le_obra.setFocus()

    def do_material_search(self):
        filtro = (self.window.le_filtro.text() or "").strip()
        if not filtro:
            self.window.lst_result.clear()
            self.window.lst_result.setVisible(False)
            return

        tipo = (self.window.cbo_tipo.currentText() or "").strip()
        buscar_por = (self.window.cbo_buscar.currentText() or "").strip()
        
        try:
            rows = self.search_service.do_material_search(tipo, buscar_por, filtro)
            self.window.lst_result.clear()
            if not rows:
                it = QListWidgetItem("— SIN RESULTADOS —")
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                self.window.lst_result.addItem(it)
            else:
                for r in rows:
                    it = self.ui_builder.build_material_item(r)
                    self.window.lst_result.addItem(it)
            self.window.lst_result.setVisible(True)
            self.window.lst_result.setCurrentRow(0)
        except Exception as e:
            print(f"Error en búsqueda: {e}")

    def on_material_picked(self, item):
        if item is None:
            return
        rec = item.data(Qt.ItemDataRole.UserRole) or {}
        if not rec:
            QMessageBox.warning(self.window, "Advertencia", "El elemento seleccionado no contiene datos válidos.")
            return

        tipo = (self.window.cbo_tipo.currentText() or "").strip()
        color = (self.window.cbo_color.currentText() or "").strip()

        clave = str(rec.get("clave", "")).strip()
        desc = str(rec.get("descripcion", "")).strip()
        texto_filtro = format_key_description(clave, desc)

        if es_tipo_paquete(tipo):
            self.window._on_pick_result_paquete(item)
            self.window.le_filtro.setText(texto_filtro)
            self.window.lst_result.clear()
            self.window.lst_result.setVisible(False)
            QTimer.singleShot(100, lambda: self.window.le_filtro.clear())
            return

        try:
            ancho = float(self.window.sp_ancho.value())
        except Exception:
            ancho = 0.0
        try:
            alto = float(self.window.sp_alto.value())
        except Exception:
            alto = 0.0

        t_up = (tipo or "").upper()
        tnorm = (t_up.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U"))

        if tnorm.startswith("HERRERIA"):
            self.window._add_he(rec, tipo, color, ancho, alto, 1)
            target_tbl = self.window.tbl_he
            row = target_tbl.rowCount() - 1
            focus_col = self.window.H_CA
        else:
            self.window._add_std(rec, tipo, color, ancho, alto, 1)
            target_tbl = self.window.tbl
            row = target_tbl.rowCount() - 1
            if tnorm.startswith("ALUMINIO"):
                if "PAQUETE" not in t_up:
                    focus_col = self.window.C_CA
                else:
                    focus_col = self.window.C_ANCHO
            elif tnorm.startswith("VIDRIO"):
                focus_col = self.window.C_ANCHO
            elif tnorm.startswith("HERRAJES"):
                focus_col = self.window.C_PZAS
            else:
                focus_col = self.window.C_PZAS

        self.window.le_filtro.setText(texto_filtro)
        self.window.lst_result.clear()
        self.window.lst_result.setVisible(False)
        QTimer.singleShot(100, lambda: self.window.le_filtro.clear())

        def _focus_new_row():
            try:
                target_tbl.setFocus()
                target_tbl.setCurrentCell(row, focus_col)
                it = target_tbl.item(row, focus_col)
                if it is not None:
                    target_tbl.editItem(it)
            except Exception:
                pass

        QTimer.singleShot(0, _focus_new_row)

    def do_cliente_search(self, text):
        if not text:
            self.window.lst_clientes.clear()
            self.window.lst_clientes.setVisible(False)
            return

        rows = self.search_service.do_cliente_search(text)
        self.window.lst_clientes.clear()
        if not rows:
            it = QListWidgetItem("— SIN RESULTADOS —")
            it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.window.lst_clientes.addItem(it)
        else:
            for r in rows:
                it = self.ui_builder.build_cliente_item(r)
                self.window.lst_clientes.addItem(it)
        configure_list_widget_for_search_results(self.window.lst_clientes)
        self.window.lst_clientes.setVisible(True)
        self.window.lst_clientes.setCurrentRow(0)
