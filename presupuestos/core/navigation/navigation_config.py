# -*- coding: utf-8 -*-
from PyQt6.QtCore import Qt

# Configuración de FOCUS_FLOW extraída de foco.py
DEFAULT_FOCUS_FLOW = [
    "le_cliente", "le_obra", "le_fecha", "cbo_color_global",
    "le_titulo", "te_desc", "sb_desperdicio", "sb_fv_pct",
    "cbo_color", "sp_precio_kg", "sp_ancho", "sp_alto",
    "sp_mo", "sp_acc", "sb_pzas_global", "cbo_tipo",
    "cbo_buscar", "le_filtro",
]

# Configuración de tablas
DEFAULT_TABLE_CONFIGS = [
    ("tbl", "C_TIPO", [
        ("CA", "C_CA"), ("ANCHO", "C_ANCHO"), ("CH", "C_CH"), ("ALTO", "C_ALTO"), ("PZAS", "C_PZAS"),
    ]),
    ("tbl_he", "H_TIPO", [
        ("CA", "H_CA"), ("ANCHO", "H_ANCHO"), ("CH", "H_CH"), ("ALTO", "H_ALTO"), ("PZAS", "H_PZAS"),
    ]),
    ("tbl_paquetes", "P_TIPO", [
        ("ANCHO", "P_ANCHO"), ("ALTO", "P_ALTO"), ("PZAS", "P_PZAS"),
    ]),
]

# Flujos de columnas por tipo
COLUMN_FLOWS = {
    "ALUMINIO": ["CA", "ANCHO", "CH", "ALTO", "PZAS"],
    "PAQUETE ALUMINIO": ["ANCHO", "ALTO", "PZAS"],
    "HERRERIA": ["CA", "ANCHO", "CH", "ALTO", "PZAS"],
    "VIDRIO": ["ANCHO", "ALTO", "PZAS"],
    "PLASTICOS": ["PZAS"],
    "HERRAJES": ["PZAS"],
    "OTROS": ["PZAS"],
    "PAQUETE HERRAJES": ["PZAS"],
}
