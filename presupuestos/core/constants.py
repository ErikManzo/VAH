# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/core/constants.py

CONSTANTES GLOBALES DEL MÓDULO DE PRESUPUESTOS

Este archivo centraliza todas las constantes utilizadas en el sistema de presupuestos.
Extraído de modulo_presupuestos.py para mejorar la mantenibilidad y evitar
duplicación de código.

USO:
    from presupuestos.core.constants import (
        C_TIPO, C_COLOR, EDITABILIDAD,
        COLOR_EDITABLE, SPLITTER_LEFT_RATIO
    )

MANTENIMIENTO:
    - Actualizar aquí cualquier cambio en índices de columnas
    - Modificar reglas de editabilidad en un solo lugar
    - Ajustar valores por defecto globalmente
"""

import os
from common.app_paths import get_app_root, get_resource_path
from common.pdf_utils import get_pdf_dir
from typing import Dict, Any

# ============================================================================
# ÍNDICES DE COLUMNAS PARA TABLAS
# ============================================================================

# ----------------------------------------------------------------------------
# TABLA ESTÁNDAR (Materiales) - 11 columnas
# ----------------------------------------------------------------------------
C_TIPO = 0  # Tipo de material (ALUMINIO, HERRAJES, VIDRIO, etc.)
C_COLOR = 1  # Color del material
C_CLAVE = 2  # Clave/ID del material
C_DESC = 3  # Descripción del material
C_CA = 4  # Cantidad en Ancho (multiplicador horizontal)
C_ANCHO = 5  # Ancho del material (valor visible original)
C_CH = 6  # Cantidad en Alto (multiplicador vertical)
C_ALTO = 7  # Alto del material (valor visible original)
C_PZAS = 8  # Piezas (cantidad de unidades)
C_PU = 9  # Precio Unitario (calculado)
C_IMP = 10  # Importe total (PU * Piezas)

# Crear tupla para fácil desempacado
STD_COLUMNS = (C_TIPO, C_COLOR, C_CLAVE, C_DESC, C_CA, C_ANCHO, C_CH, C_ALTO, C_PZAS, C_PU, C_IMP)

# ----------------------------------------------------------------------------
# TABLA DE HERRERÍA - 14 columnas
# ----------------------------------------------------------------------------
H_TIPO = 0  # Tipo (siempre "HERRERÍA")
H_CLAVE = 1  # Clave del perfil de herrería
H_DESC = 2  # Descripción del perfil
H_CA = 3  # Cantidad en Ancho
H_ANCHO = 4  # Ancho del perfil (valor visible original)
H_CH = 5  # Cantidad en Alto
H_ALTO = 6  # Alto del perfil (valor visible original)
H_METROS = 7  # Metros totales (calculado)
H_KG_M = 8  # Kilogramos por metro
H_KGS = 9  # Kilogramos totales (calculado)
H_PKG = 10  # Precio por kilogramo
H_PZAS = 11  # Piezas
H_PU = 12  # Precio Unitario (calculado)
H_IMP = 13  # Importe total

# Tupla para herrería
HERRERIA_COLUMNS = (H_TIPO, H_CLAVE, H_DESC, H_CA, H_ANCHO, H_CH, H_ALTO, H_METROS,
                    H_KG_M, H_KGS, H_PKG, H_PZAS, H_PU, H_IMP)

# ----------------------------------------------------------------------------
# TABLA DE PAQUETES - 8 columnas (ACTUALIZADO - AGREGADAS P_PU y P_IMP)
# ----------------------------------------------------------------------------
P_TIPO = 0  # Tipo de paquete (PAQUETE ALUMINIO, PAQUETE HERRAJES)
P_CLAVE = 1  # Clave del paquete
P_DESC = 2  # Descripción del paquete
P_ANCHO = 3  # Ancho del paquete (EDITABLE para paquetes madre)
P_ALTO = 4  # Alto del paquete (EDITABLE para paquetes madre)
P_PZAS = 5  # Piezas del paquete (EDITABLE - dispara multiplicación)
P_PU = 6   # Precio Unitario del paquete (calculado - AGREGADO)
P_IMP = 7  # Importe total del paquete (calculado - AGREGADO)

# Tupla para paquetes (ACTUALIZADA)
PAQUETES_COLUMNS = (P_TIPO, P_CLAVE, P_DESC, P_ANCHO, P_ALTO, P_PZAS, P_PU, P_IMP)

# ----------------------------------------------------------------------------
# TABLA ANIDADA - 11 columnas (igual que tabla estándar, solo visualización)
# ----------------------------------------------------------------------------
A_TIPO = 0  # Tipo del componente anidado
A_COLOR = 1  # Color del componente
A_CLAVE = 2  # Clave del componente
A_DESC = 3  # Descripción del componente
A_CA = 4  # Cantidad en Ancho (del componente)
A_ANCHO = 5  # Ancho del componente (valor original)
A_CH = 6  # Cantidad en Alto (del componente)
A_ALTO = 7  # Alto del componente (valor original)
A_PZAS = 8  # Piezas del componente (SIN multiplicar por paquete madre)
A_PU = 9  # Precio Unitario (calculado)
A_IMP = 10  # Importe total (calculado)

# Tupla para anidada
ANIDADA_COLUMNS = (A_TIPO, A_COLOR, A_CLAVE, A_DESC, A_CA, A_ANCHO, A_CH,
                   A_ALTO, A_PZAS, A_PU, A_IMP)

# ============================================================================
# REGLAS DE EDITABILIDAD POR TIPO DE MATERIAL
# ============================================================================
"""
Define qué campos son editables para cada tipo de material.
Claves: Tipo de material en mayúsculas
Valores: Dict con booleanos para cada campo editable
"""
EDITABILIDAD: Dict[str, Dict[str, bool]] = {
    # ALUMINIO: Todos los campos de medidas editables
    "ALUMINIO": dict(CA=True, CH=True, ANCHO=True, ALTO=True, PZAS=True),

    # HERRAJES: Solo piezas editable (componentes fijos)
    "HERRAJES": dict(CA=False, CH=False, ANCHO=False, ALTO=False, PZAS=True),

    # VIDRIO: Ancho, Alto y Piezas editables
    "VIDRIO": dict(CA=False, CH=False, ANCHO=True, ALTO=True, PZAS=True),

    # PAQUETES DE ALUMINIO (variaciones de nombre)
    "PAQUETE ALUMINIO": dict(CA=False, CH=False, ANCHO=True, ALTO=True, PZAS=True),
    "PAQUETE ALUMIO": dict(CA=False, CH=False, ANCHO=True, ALTO=True, PZAS=True),
    "PAQ-AL": dict(CA=False, CH=False, ANCHO=True, ALTO=True, PZAS=True),
    "PAQ AL": dict(CA=False, CH=False, ANCHO=True, ALTO=True, PZAS=True),

    # HERRERÍA (con y sin acento)
    "HERRERÍA": dict(CA=False, CH=False, ANCHO=False, ALTO=False, PZAS=True),
    "HERRERIA": dict(CA=False, CH=False, ANCHO=False, ALTO=False, PZAS=True),

    # PLÁSTICOS (con y sin acento)
    "PLÁSTICOS": dict(CA=False, CH=False, ANCHO=False, ALTO=False, PZAS=True),
    "PLASTICOS": dict(CA=False, CH=False, ANCHO=False, ALTO=False, PZAS=True),

    # OTROS MATERIALES
    "OTROS": dict(CA=False, CH=False, ANCHO=False, ALTO=False, PZAS=True),

    # PAQUETES DE HERRAJES
    "PAQUETE HERRAJES": dict(CA=False, CH=False, ANCHO=False, ALTO=False, PZAS=True),
    "PAQUETE HERRAJE": dict(CA=False, CH=False, ANCHO=False, ALTO=False, PZAS=True),

    # TIPOS ESPECIALES PARA COMPONENTES INTERNOS
    "AL": dict(CA=True, CH=True, ANCHO=True, ALTO=True, PZAS=True),  # Componente aluminio
    "PH": dict(CA=False, CH=False, ANCHO=False, ALTO=False, PZAS=True),  # Paquete herrajes (anidado)
    "HR": dict(CA=False, CH=False, ANCHO=False, ALTO=False, PZAS=True),  # Componente herrajes
}

# ============================================================================
# VALORES POR DEFECTO DEL SISTEMA
# ============================================================================

# RUTAS DEL SISTEMA
VAH_ROOT = get_app_root()
PDFS_BASE_DIR = os.path.join(VAH_ROOT, "pdfs")
PRESUPUESTOS_PDF_DIR = get_pdf_dir("Presupuestos")
ICON_PATH = get_resource_path("logo_00001.ico")
WINDOW_TITLE = "VAH — Módulo Presupuestos"

# VALORES INICIALES
DEFAULT_DESPERDICIO = 2  # 2% de desperdicio por defecto
DEFAULT_FV_PCT = 25  # 25% de Factor de Venta
DEFAULT_COLOR_GLOBAL = "VARIOS"
DEFAULT_PRESUPUESTO_NUM = 1
DEFAULT_PARTIDA_NUM = 1
DEFAULT_PIEZAS_GLOBAL = 1

# CONFIGURACIÓN DE INTERFAZ
SPLITTER_LEFT_RATIO = 0.20  # 20% para panel izquierdo
SPLITTER_RIGHT_RATIO = 0.80  # 80% para panel derecho
SPLITTER_HANDLE_WIDTH = 6  # Ancho del divisor

# COLORES PARA INTERFAZ (usados en estilos CSS)
COLOR_EDITABLE = "yellow"  # Fondo para celdas editables
COLOR_READONLY = "lightGray"  # Fondo para celdas de solo lectura
COLOR_FOCUS_BORDER = "#0a84ff"  # Borde azul para elementos con foco
COLOR_TABLE_READONLY_BG = "#f0f0f0"  # Fondo para items no editables
COLOR_TABLE_READONLY_TEXT = "#666"  # Texto para items no editables
COLOR_ANIDADA_BG = "#e8f4fd"  # Fondo para grupo tabla anidada
COLOR_ANIDADA_BORDER = "#0a84ff"  # Borde para grupo tabla anidada

# CONFIGURACIÓN DE TABLAS
TABLE_HEADER_RESIZE_MODE = "Stretch"  # Modo de redimensionamiento de columnas
TABLE_VERTICAL_HEADER_VISIBLE = False  # Ocultar encabezados verticales

# TIEMPOS Y DELAYS
SEARCH_DELAY_MS = 160  # Delay para búsqueda (ms)
FOCUS_DELAY_MS = 100  # Delay para establecer foco (ms)
INIT_DELAY_MS = 0  # Delay para inicialización

# ============================================================================
# TIPOS DE MATERIAL DISPONIBLES EN COMBOBOX
# ============================================================================

TIPOS_MATERIAL = [
    "ALUMINIO",
    "PAQUETE ALUMINIO",
    "HERRERÍA",
    "VIDRIO",
    "PLÁSTICOS",
    "HERRAJES",
    "PAQUETE HERRAJES",
    "OTROS"
]

TIPOS_BUSQUEDA = ["CLAVE", "DESCRIPCIÓN"]

COLORES_GLOBAL = [
    "VARIOS", "NATURAL", "BLANCO", "E-100", "E-200", "E-400",
    "BRONCE", "HUESO", "GRIS", "CHOCOLATE", "N.P.", "ACERO",
    "MADERA LISA", "MADERA TEXTURIZADA"
]

COLORES_PARTIDA = [
    "NATURAL", "BLANCO", "E-100", "E-200", "E-400", "BRONCE",
    "HUESO", "GRIS", "CHOCOLATE", "N.P.", "ACERO",
    "MADERA LISA", "MADERA TEXTURIZADA"
]

# ============================================================================
# CONFIGURACIÓN DE AJUSTE INDUSTRIAL
# ============================================================================

# Paso de redondeo para medidas industriales
INDUSTRIAL_STEP = 0.05  # Redondeo a múltiplos de 0.05

# Debug para ajuste industrial (False en producción)
DEBUG_AJUSTE_INDUSTRIAL = False

# ============================================================================
# CONFIGURACIÓN DE PAQUETES
# ============================================================================

# Tipos que se consideran paquetes
TIPOS_PAQUETE = [
    "PAQUETE ALUMINIO",
    "PAQUETE ALUMIO",
    "PAQ-AL",
    "PAQ AL",
    "PAQUETE HERRAJES",
    "PAQUETE HERRAJE",
    "PAQ-HR"
]

# Tipos internos para componentes
TIPO_COMPONENTE_AL = "AL"  # Componente de aluminio
TIPO_COMPONENTE_PH = "PH"  # Paquete de herrajes (anidado)
TIPO_COMPONENTE_HR = "HR"  # Componente de herrajes

# ============================================================================
# CONFIGURACIÓN DE ESTILOS CSS
# ============================================================================

STYLESHEET = f'''
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, 
QSpinBox:focus, QDoubleSpinBox:focus {{ 
    border: 2px solid {COLOR_FOCUS_BORDER}; 
}}
QGroupBox {{ 
    font-weight: bold; 
    margin-top: 10px; 
}}
QGroupBox::title {{ 
    subcontrol-origin: margin; 
    left: 10px; 
    padding: 0 5px 0 5px; 
}}
QTableWidget::item:!editable {{ 
    background-color: {COLOR_TABLE_READONLY_BG}; 
    color: {COLOR_TABLE_READONLY_TEXT}; 
}}
QTableWidget::item[readonly="true"] {{ 
    background-color: #f5f5f5; 
    color: #999; 
}}
QGroupBox#gb_tabla_anidada {{ 
    background-color: {COLOR_ANIDADA_BG}; 
    border: 2px solid {COLOR_ANIDADA_BORDER}; 
}}
'''

# ============================================================================
# CONFIGURACIÓN DE MENÚ
# ============================================================================

# Estructura básica del menú (para menu_builder.py)
MENU_STRUCTURE = {
    "Archivo": {
        "items": [
            ("&Nuevo Presupuesto", "Ctrl+N", "_on_nuevo_presupuesto"),
            ("&Abrir Presupuesto", "Ctrl+O", "_on_abrir_presupuesto"),
            ("---", None, None),
            ("&Guardar Presupuesto", "Ctrl+S", "_on_guardar_presupuesto"),
            ("&Guardar Como...", "Ctrl+Shift+S", "_on_guardar_como_presupuesto"),
            ("---", None, None),
            ("&Imprimir", "Ctrl+P", "_on_imprimir"),
            ("Vista &Previa de Impresión", None, "_on_vista_previa"),
            ("---", None, None),
            ("Exportar a E&xcel", "Ctrl+E", "_on_exportar_excel"),
            ("Exportar a &PDF", "Ctrl+D", "_on_exportar_pdf"),
            ("---", None, None),
            ("&Configuración", None, "_on_configuracion"),
            ("---", None, None),
            ("&Salir", "Ctrl+Q", "close")
        ]
    },
    "Edición": {
        "items": [
            ("Cor&tar", "Ctrl+X", "_on_cortar"),
            ("&Copiar", "Ctrl+C", "_on_copiar"),
            ("&Pegar", "Ctrl+V", "_on_pegar"),
            ("---", None, None),
            ("&Seleccionar Todo", "Ctrl+A", "_on_seleccionar_todo"),
            ("---", None, None),
            ("&Deshacer", "Ctrl+Z", "_on_deshacer"),
            ("&Rehacer", "Ctrl+Y", "_on_rehacer"),
            ("---", None, None),
            ("&Buscar", "Ctrl+F", "_on_buscar"),
            ("&Reemplazar", "Ctrl+H", "_on_reemplazar")
        ]
    },
    "Presupuesto": {
        "items": [
            ("Nueva &Partida", "Ctrl+T", "_on_nueva_partida"),
            ("&Duplicar Partida", None, "_on_duplicar_partida"),
            ("&Eliminar Partida", "Del", "_on_eliminar_partida"),
            ("---", None, None),
            ("&Recalcular Todo", "F5", "_on_recalcular_todo"),
            ("---", None, None),
            ("&Validar Presupuesto", None, "_on_validar_presupuesto"),
            ("Verificar &Precios", None, "_on_verificar_precios")
        ]
    },
    "Mantenimiento": {
        "items": [
            ("&Catálogo de Materiales", None, "_on_catalogo_materiales"),
            ("Catálogo de &Clientes", None, "_on_catalogo_clientes"),
            ("---", None, None),
            ("Definir &Paquetes", None, "_on_definir_paquetes"),
            ("Configurar &Herrajes", None, "_on_configurar_herrajes"),
            ("&Parámetros del Sistema", None, "_on_parametros_sistema")
        ]
    },
    "Reportes": {
        "items": [
            ("&Reporte de Presupuesto", None, "_on_reporte_presupuesto"),
            ("Análisis de &Costos", None, "_on_analisis_costos"),
            ("&Lista de Materiales", None, "_on_lista_materiales"),
            ("---", None, None),
            ("Reporte de &Ventas", None, "_on_reporte_ventas"),
            ("Reporte de &Inventario", None, "_on_reporte_inventario")
        ]
    },
    "Ventana": {
        "items": [
            ("&Nueva Ventana", None, "_on_nueva_ventana"),
            ("&Cerrar Ventana", None, "_on_cerrar_ventana"),
            ("---", None, None),
            ("&Cascada", None, "_on_cascada"),
            ("Mosaico &Horizontal", None, "_on_mosaico_horizontal"),
            ("Mosaico &Vertical", None, "_on_mosaico_vertical"),
            ("---", None, None),
            ("&Siguiente Ventana", "Ctrl+Tab", "_on_siguiente_ventana"),
            ("Ventana &Anterior", "Ctrl+Shift+Tab", "_on_ventana_anterior")
        ]
    },
    "Ayuda": {
        "items": [
            ("&Contenido de Ayuda", "F1", "_on_contenido_ayuda"),
            ("&Tutoriales", None, "_on_tutoriales"),
            ("---", None, None),
            ("&Acerca de VAH", None, "_on_acerca_de"),
            ("Verificar &Actualizaciones", None, "_on_verificar_actualizaciones")
        ]
    }
}


# ============================================================================
# FUNCIONES DE UTILIDAD PARA CONSTANTES
# ============================================================================

def es_tipo_paquete(tipo: str) -> bool:
    """
    Determina si un tipo de material es un paquete.

    Args:
        tipo: Tipo de material en mayúsculas

    Returns:
        True si es un paquete, False en caso contrario
    """
    return tipo.strip().upper() in TIPOS_PAQUETE


def obtener_regla_editabilidad(tipo: str) -> Dict[str, bool]:
    """
    Obtiene las reglas de editabilidad para un tipo de material.

    Args:
        tipo: Tipo de material en mayúsculas

    Returns:
        Diccionario con reglas de editabilidad
    """
    tipo_normalizado = tipo.strip().upper()
    return EDITABILIDAD.get(tipo_normalizado, EDITABILIDAD["OTROS"])


def es_campo_editable(tipo: str, campo: str) -> bool:
    """
    Verifica si un campo específico es editable para un tipo de material.

    Args:
        tipo: Tipo de material en mayúsculas
        campo: Nombre del campo (CA, CH, ANCHO, ALTO, PZAS)

    Returns:
        True si el campo es editable, False en caso contrario
    """
    reglas = obtener_regla_editabilidad(tipo)
    return reglas.get(campo, False)


# ============================================================================
# EXPORTACIÓN DE CONSTANTES
# ============================================================================

# Para importación directa de todas las constantes principales
__all__ = [
    # Índices de columnas
    'C_TIPO', 'C_COLOR', 'C_CLAVE', 'C_DESC', 'C_CA', 'C_ANCHO',
    'C_CH', 'C_ALTO', 'C_PZAS', 'C_PU', 'C_IMP',
    'H_TIPO', 'H_CLAVE', 'H_DESC', 'H_CA', 'H_ANCHO', 'H_CH',
    'H_ALTO', 'H_METROS', 'H_KG_M', 'H_KGS', 'H_PKG', 'H_PZAS',
    'H_PU', 'H_IMP',
    'P_TIPO', 'P_CLAVE', 'P_DESC', 'P_ANCHO', 'P_ALTO', 'P_PZAS',
    'P_PU', 'P_IMP',  # AGREGADOS
    'A_TIPO', 'A_COLOR', 'A_CLAVE', 'A_DESC', 'A_CA', 'A_ANCHO',
    'A_CH', 'A_ALTO', 'A_PZAS', 'A_PU', 'A_IMP',

    # Tuplas de columnas
    'STD_COLUMNS', 'HERRERIA_COLUMNS', 'PAQUETES_COLUMNS', 'ANIDADA_COLUMNS',

    # Reglas y configuraciones
    'EDITABILIDAD',
    'ICON_PATH', 'WINDOW_TITLE',
    'DEFAULT_DESPERDICIO', 'DEFAULT_FV_PCT', 'DEFAULT_COLOR_GLOBAL',
    'DEFAULT_PRESUPUESTO_NUM', 'DEFAULT_PARTIDA_NUM', 'DEFAULT_PIEZAS_GLOBAL',
    'SPLITTER_LEFT_RATIO', 'SPLITTER_RIGHT_RATIO', 'SPLITTER_HANDLE_WIDTH',
    'COLOR_EDITABLE', 'COLOR_READONLY', 'COLOR_FOCUS_BORDER',
    'COLOR_TABLE_READONLY_BG', 'COLOR_TABLE_READONLY_TEXT',
    'COLOR_ANIDADA_BG', 'COLOR_ANIDADA_BORDER',
    'TABLE_HEADER_RESIZE_MODE', 'TABLE_VERTICAL_HEADER_VISIBLE',
    'SEARCH_DELAY_MS', 'FOCUS_DELAY_MS', 'INIT_DELAY_MS',

    # Listas de opciones
    'TIPOS_MATERIAL', 'TIPOS_BUSQUEDA', 'COLORES_GLOBAL', 'COLORES_PARTIDA',

    # Ajuste industrial
    'INDUSTRIAL_STEP', 'DEBUG_AJUSTE_INDUSTRIAL',

    # Configuración de paquetes
    'TIPOS_PAQUETE', 'TIPO_COMPONENTE_AL', 'TIPO_COMPONENTE_PH', 'TIPO_COMPONENTE_HR',

    # Estilos
    'STYLESHEET',

    # Estructura de menú
    'MENU_STRUCTURE',

    # Funciones de utilidad
    'es_tipo_paquete', 'obtener_regla_editabilidad', 'es_campo_editable'
]
