# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/core/navigation/focus_manager.py
Gestor de foco - VERSIÓN CORREGIDA (sin search_controller)
"""
from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtWidgets import QApplication, QTableWidget, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QAbstractItemDelegate
from .navigation_config import DEFAULT_FOCUS_FLOW, DEFAULT_TABLE_CONFIGS, COLUMN_FLOWS

class FocusManager(QObject):
    def __init__(self, window, config=None):
        super().__init__(window)
        self.window = window
        self.focus_flow = config.get('flow', DEFAULT_FOCUS_FLOW) if config else DEFAULT_FOCUS_FLOW
        self.table_configs = config.get('tables', DEFAULT_TABLE_CONFIGS) if config else DEFAULT_TABLE_CONFIGS
        self._init_table_data()
    
    def _init_table_data(self):
        self._table_data = {}
        for table_attr, tipo_attr, cols in self.table_configs:
            table = getattr(self.window, table_attr, None)
            if table:
                tipo_col = getattr(self.window, tipo_attr, -1)
                col_map = {logical: getattr(self.window, const, -1) for logical, const in cols}
                self._table_data[table_attr] = {"table": table, "tipo_col": tipo_col, "col_map": col_map}
    
    def eventFilter(self, obj, event):
        if event.type() != QEvent.Type.KeyPress:
            return False
        key = event.key()
        modifiers = event.modifiers()
        
        # 1. LISTAS VISIBLES
        if obj is self.window.lst_clientes and self.window.lst_clientes.isVisible():
            return self._handle_list_event(obj, "cliente", key, modifiers)
        if obj is self.window.le_cliente and self.window.lst_clientes.isVisible():
            return self._handle_list_event(self.window.lst_clientes, "cliente", key, modifiers)
        if obj is self.window.lst_result and self.window.lst_result.isVisible():
            return self._handle_list_event(obj, "filtro", key, modifiers)
        if obj is self.window.le_filtro and self.window.lst_result.isVisible():
            return self._handle_list_event(self.window.lst_result, "filtro", key, modifiers)
        
        # 2. DENTRO DE UNA TABLA
        table, row, col, flow = self._get_table_context(obj)
        if table is not None and row >= 0 and col >= 0:
            if key == Qt.Key.Key_Delete:
                self.window._delete_table_row(table, row)
                return True
            if key in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._commit_table_editor(table)
                direction = -1 if modifiers & Qt.KeyboardModifier.ShiftModifier and key == Qt.Key.Key_Tab else 1
                self._move_in_table(direction, table, row, col, flow)
                return True
        
        # 3. NAVEGACIÓN GLOBAL
        norm = self._normalize_to_global_widget(obj)
        if norm:
            if norm is self.window.sb_fv_pct and key in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                direction = -1 if modifiers & Qt.KeyboardModifier.ShiftModifier else 1
                self._move_focus_from_fv(direction)
                return True
            if key == Qt.Key.Key_Tab:
                direction = -1 if modifiers & Qt.KeyboardModifier.ShiftModifier else 1
                self._move_focus_global(direction, norm)
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._move_focus_global(1, norm)
                return True
        return False
    
    def _move_focus_from_fv(self, direction):
        if direction == -1:
            self.window.sb_desperdicio.setFocus()
            self.window.sb_desperdicio.selectAll()
            return
        color_global = (self.window.cbo_color_global.currentText() or "").strip().upper()
        if color_global == "VARIOS":
            self.window.cbo_color.setFocus()
            self.window.cbo_color.showPopup()
        else:
            self.window.sp_precio_kg.setFocus()
            self.window.sp_precio_kg.selectAll()
    
    def _get_table_context(self, widget):
        p = widget
        while p:
            if isinstance(p, QTableWidget):
                for attr, data in self._table_data.items():
                    if p is data["table"]:
                        r, c = p.currentRow(), p.currentColumn()
                        if r >= 0 and c >= 0:
                            tipo = self.window._safe_text(p, r, data["tipo_col"], "").strip().upper()
                            tnorm = tipo.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
                            flow = COLUMN_FLOWS.get(tnorm, COLUMN_FLOWS.get("OTROS", ["PZAS"]))
                            indices = [data["col_map"][l] for l in flow if l in data["col_map"]]
                            return p, r, c, indices
            p = p.parent()
        return None, -1, -1, []
    
    def _normalize_to_global_widget(self, widget):
        for name in self.focus_flow:
            if getattr(self.window, name, None) is widget: return widget
        p = widget.parent()
        while p:
            for name in self.focus_flow:
                if getattr(self.window, name, None) is p: return p
            p = p.parent()
        return None
    
    def _move_focus_global(self, direction, current):
        try:
            idx = -1
            for i, name in enumerate(self.focus_flow):
                if getattr(self.window, name, None) is current:
                    idx = i; break
            if idx == -1: next_idx = 0
            else:
                next_idx = (idx + direction) % len(self.focus_flow)
            next_w = getattr(self.window, self.focus_flow[next_idx], None)
            if next_w:
                next_w.setFocus()
                if isinstance(next_w, (QLineEdit, QSpinBox, QDoubleSpinBox)): next_w.selectAll()
        except: pass
    
    def _move_in_table(self, direction, table, row, col, flow):
        if not flow: return
        try:
            pos = flow.index(col) if col in flow else -1
            next_pos = pos + direction
            if 0 <= next_pos < len(flow):
                table.setCurrentCell(row, flow[next_pos])
                it = table.item(row, flow[next_pos])
                if it: table.editItem(it)
            else:
                if direction == 1:
                    self._exit_table_forward()
                else:
                    self._exit_table_backward()
        except: pass
    
    def _exit_table_forward(self):
        if hasattr(self.window, "cbo_tipo"):
            self.window.cbo_tipo.setFocus()
    
    def _exit_table_backward(self):
        if hasattr(self.window, "le_filtro"):
            self.window.le_filtro.setFocus()
            self.window.le_filtro.selectAll()
    
    def _commit_table_editor(self, table):
        idx = table.currentIndex()
        if idx.isValid():
            editor = table.indexWidget(idx)
            if isinstance(editor, QLineEdit):
                table.commitData(editor)
                table.closeEditor(editor, QAbstractItemDelegate.EndEditHint.SubmitModelCache)
    
    def _handle_list_event(self, list_w, list_type, key, mods):
        """CORREGIDO: Maneja eventos de lista directamente sin search_controller."""
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current_item = list_w.currentItem()
            if current_item:
                if list_type == "cliente":
                    from presupuestos import busquedas
                    busquedas.pick_cliente(self.window, current_item)
                elif list_type == "filtro":
                    if hasattr(self.window, '_es_tipo_paquete') and self.window._es_tipo_paquete():
                        self.window._on_pick_result_paquete(current_item)
                    else:
                        from presupuestos import busquedas
                        busquedas.on_pick_result(self.window, current_item)
            return True
        if key == Qt.Key.Key_Escape:
            list_w.setVisible(False)
            return True
        if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            curr = list_w.currentRow()
            if key == Qt.Key.Key_Down: list_w.setCurrentRow(min(list_w.count()-1, curr+1))
            else: list_w.setCurrentRow(max(0, curr-1))
            return True
        return False

def install_focus_manager(window):
    fm = FocusManager(window)
    QApplication.instance().installEventFilter(fm)
    return fm