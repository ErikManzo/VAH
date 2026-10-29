# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/core/__init__.py

Módulo core del sistema de presupuestos.
Contiene las clases y constantes fundamentales del sistema.

Este módulo será importado como:
    from presupuestos.core import constants, utils
"""

from . import constants
from . import utils

# Re-exportar las constantes principales para acceso directo
from .constants import (
    # Índices de columnas
    C_TIPO, C_COLOR, C_CLAVE, C_DESC, C_CA, C_ANCHO, C_CH, C_ALTO, C_PZAS, C_PU, C_IMP,
    H_TIPO, H_CLAVE, H_DESC, H_CA, H_ANCHO, H_CH, H_ALTO, H_METROS, H_KG_M, H_KGS,
    H_PKG, H_PZAS, H_PU, H_IMP,
    P_TIPO, P_CLAVE, P_DESC, P_ANCHO, P_ALTO, P_PZAS,
    A_TIPO, A_COLOR, A_CLAVE, A_DESC, A_CA, A_ANCHO, A_CH, A_ALTO, A_PZAS, A_PU, A_IMP,

    # Reglas y configuraciones
    EDITABILIDAD,
    ICON_PATH, WINDOW_TITLE,

    # Funciones de utilidad (re-exportadas desde constants)
    es_tipo_paquete as es_tipo_paquete_const,
    obtener_regla_editabilidad as obtener_regla_editabilidad_const,
    es_campo_editable as es_campo_editable_const
)

# Re-exportar funciones principales de utils
from .utils import (
    # Funciones de conversión
    to_float, to_int, format_money, to_bool,

    # Alias de compatibilidad
    _f, _i, _money,

    # Funciones de UI
    connect_upper_lineedit, connect_upper_textedit, connect_upper_combobox,
    make_readonly_display,

    # Alias de compatibilidad para UI
    _connect_upper_lineedit, _connect_upper_textedit, _connect_upper_combobox,

    # Funciones matemáticas
    round_up_to_005, ajustar_medidas_industriales,
    calcular_porcentaje, aplicar_desperdicio, aplicar_factor_venta, calcular_iva,

    # Alias de compatibilidad para funciones matemáticas
    _round_up_to_005, _ajustar_medidas_industriales,

    # Funciones de validación
    limpiar_texto, es_numerico, es_texto_valido, normalizar_clave,

    # Funciones para tablas
    safe_table_text, set_table_item_text, set_table_money,

    # Funciones para manejo de paquetes
    es_tipo_paquete, obtener_regla_editabilidad, es_campo_editable,

    # Funciones de inicialización
    initialize_module
)

__all__ = [
    # Módulos
    'constants',
    'utils',

    # Constantes de columnas
    'C_TIPO', 'C_COLOR', 'C_CLAVE', 'C_DESC', 'C_CA', 'C_ANCHO',
    'C_CH', 'C_ALTO', 'C_PZAS', 'C_PU', 'C_IMP',
    'H_TIPO', 'H_CLAVE', 'H_DESC', 'H_CA', 'H_ANCHO', 'H_CH',
    'H_ALTO', 'H_METROS', 'H_KG_M', 'H_KGS', 'H_PKG', 'H_PZAS',
    'H_PU', 'H_IMP',
    'P_TIPO', 'P_CLAVE', 'P_DESC', 'P_ANCHO', 'P_ALTO', 'P_PZAS',
    'A_TIPO', 'A_COLOR', 'A_CLAVE', 'A_DESC', 'A_CA', 'A_ANCHO',
    'A_CH', 'A_ALTO', 'A_PZAS', 'A_PU', 'A_IMP',

    # Reglas y configuraciones
    'EDITABILIDAD',
    'ICON_PATH', 'WINDOW_TITLE',

    # Funciones de utils
    'to_float', 'to_int', 'format_money', 'to_bool',
    '_f', '_i', '_money',
    'connect_upper_lineedit', 'connect_upper_textedit', 'connect_upper_combobox',
    'make_readonly_display',
    '_connect_upper_lineedit', '_connect_upper_textedit', '_connect_upper_combobox',
    'round_up_to_005', 'ajustar_medidas_industriales',
    'calcular_porcentaje', 'aplicar_desperdicio', 'aplicar_factor_venta', 'calcular_iva',
    '_round_up_to_005', '_ajustar_medidas_industriales',
    'limpiar_texto', 'es_numerico', 'es_texto_valido', 'normalizar_clave',
    'safe_table_text', 'set_table_item_text', 'set_table_money',
    'es_tipo_paquete', 'obtener_regla_editabilidad', 'es_campo_editable',
    'initialize_module',

    # Funciones de constants (para compatibilidad)
    'es_tipo_paquete_const', 'obtener_regla_editabilidad_const', 'es_campo_editable_const'
]