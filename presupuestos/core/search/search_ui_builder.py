# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtCore import Qt
from typing import Dict, Any
from common.search_utils import format_key_description

class SearchUIBuilder:
    @staticmethod
    def format_cliente_for_list(rec: Dict[str, Any]) -> str:
        cliente_id = str(rec.get("id", "") or "").strip()
        partes = [str(rec.get(k)).strip() for k in ["titulo", "nombre", "a_paterno", "a_materno"] if rec.get(k)]
        nombre = " ".join(partes).upper() or "(SIN NOMBRE)"
        return format_key_description(cliente_id, nombre) if cliente_id else nombre

    @staticmethod
    def build_material_item(rec: Dict[str, Any]) -> QListWidgetItem:
        clave = str(rec.get("clave", "")).strip()
        desc = str(rec.get("descripcion", "")).strip()
        item = QListWidgetItem(format_key_description(clave, desc))
        item.setData(Qt.ItemDataRole.UserRole, rec)
        return item

    @staticmethod
    def build_cliente_item(rec: Dict[str, Any]) -> QListWidgetItem:
        texto = SearchUIBuilder.format_cliente_for_list(rec)
        item = QListWidgetItem(texto)
        item.setData(Qt.ItemDataRole.UserRole, rec)
        return item
