# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/core/utils.py

UTILIDADES GENERALES DEL SISTEMA DE PRESUPUESTOS

Este archivo centraliza funciones helper, conversores y utilidades generales
que son utilizadas en múltiples partes del sistema.

USO:
    from presupuestos.core.utils import (
        to_float, to_int, format_money,
        connect_upper_lineedit, connect_upper_textedit,
        round_up_to_005, ajustar_medidas_industriales,
        safe_table_text, set_table_item_text, set_table_money,
        limpiar_texto, es_numerico, normalizar_clave
    )

FUNCIONES INCLUIDAS:
    1. Conversión de datos: to_float(), to_int(), format_money()
    2. Utilidades de UI: connect_upper_*() para convertir a mayúsculas
    3. Utilidades matemáticas: round_up_to_005(), ajustar_medidas_industriales()
    4. Validación y limpieza: limpiar_texto(), es_numerico()
    5. Utilidades para tablas: safe_table_text(), set_table_item_text()
    6. Funciones de compatibilidad: _f, _i, _money (alias)

MANTENIMIENTO:
    - Agregar nuevas funciones helper aquí
    - Mantener compatibilidad con código existente
    - Documentar bien cada función
"""

import re
import math
import sys
import os
from typing import Any, Optional, Tuple, Dict, List, Callable

from PyQt6.QtWidgets import QLineEdit, QTextEdit, QComboBox, QTableWidget, QTableWidgetItem, QDoubleSpinBox
from PyQt6.QtCore import Qt, QTimer

# Importar dimensioning para ajuste industrial
try:
    from ..calculators.dimensioning import adjust_dimension
except ImportError:
    # Función de respaldo si dimensioning no está disponible
    def adjust_dimension(value: float, step: float = 0.05) -> float:
        """Función de respaldo si dimensioning.py no está disponible."""
        if value <= 0:
            return 0.0
        # Lógica simplificada: subir al siguiente múltiplo de step
        return math.ceil(value / step) * step


# ============================================================================
# FUNCIONES DE INICIALIZACIÓN Y COMPATIBILIDAD
# ============================================================================

def initialize_module() -> bool:
    """
    Función de inicialización para resolver problemas de importación circular.
    Llama a esta función al inicio de modulo_presupuestos.py si hay problemas.

    Returns:
        bool: True si la inicialización fue exitosa
    """
    # Añadir el directorio actual al path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)

    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    return True


# ============================================================================
# CONVERSIÓN DE DATOS (FUNCIONES FUNDAMENTALES)
# ============================================================================

def to_float(x: Any, default: float = 0.0) -> float:
    """
    Convierte cualquier valor a float de forma segura.

    Args:
        x: Valor a convertir (str, int, float, etc.)
        default: Valor por defecto si la conversión falla

    Returns:
        Valor convertido a float o el valor por defecto

    Ejemplos:
        >>> to_float("123.45")
        123.45
        >>> to_float("ABC", 0.0)
        0.0
        >>> to_float(None, 10.0)
        10.0
    """
    try:
        if isinstance(x, str):
            # Eliminar caracteres no numéricos excepto punto decimal y signo negativo
            x_clean = re.sub(r"[^0-9\.\-]", "", x)
            if not x_clean or x_clean == "-":
                return default
            return float(x_clean)
        elif x is None:
            return default
        return float(x)
    except (ValueError, TypeError, AttributeError):
        return default


def to_int(x: Any, default: int = 0) -> int:
    """
    Convierte cualquier valor a int de forma segura.

    Args:
        x: Valor a convertir
        default: Valor por defecto si la conversión falla

    Returns:
        Valor convertido a int o el valor por defecto

    Ejemplos:
        >>> to_int("123")
        123
        >>> to_int("123.45")  # Se trunca a 123
        123
        >>> to_int("ABC", 0)
        0
    """
    try:
        return int(to_float(x, default))
    except (ValueError, TypeError, AttributeError):
        return default


def format_money(value: Any) -> str:
    """
    Formatea un valor como moneda con 2 decimales y separadores de miles.

    Args:
        value: Valor a formatear (str, int, float)

    Returns:
        String formateado como moneda

    Ejemplos:
        >>> format_money(1234.56)
        '1,234.56'
        >>> format_money("1234.56")
        '1,234.56'
        >>> format_money("ABC")
        '0.00'
    """
    try:
        return f"{to_float(value):,.2f}"
    except (ValueError, TypeError, AttributeError):
        return "0.00"


def to_bool(x: Any, default: bool = False) -> bool:
    """
    Convierte cualquier valor a booleano de forma segura.

    Args:
        x: Valor a convertir
        default: Valor por defecto si la conversión falla

    Returns:
        Valor booleano

    Ejemplos:
        >>> to_bool("true")
        True
        >>> to_bool(1)
        True
        >>> to_bool("no")
        False
    """
    if isinstance(x, str):
        x_lower = x.strip().lower()
        if x_lower in ("true", "yes", "si", "sí", "1", "on", "verdadero", "t"):
            return True
        elif x_lower in ("false", "no", "0", "off", "falso", "f"):
            return False

    try:
        return bool(x)
    except (ValueError, TypeError):
        return default


# ============================================================================
# UTILIDADES DE INTERFAZ DE USUARIO (UI)
# ============================================================================

def connect_upper_lineedit(line_edit: QLineEdit) -> None:
    """
    Convierte automáticamente el texto a mayúsculas en un QLineEdit.

    Args:
        line_edit: Instancia de QLineEdit a configurar

    Notas:
        - Mantiene la posición del cursor
        - No afecta texto ingresado por programa (blockSignals)
        - Aplica a medida que el usuario escribe
    """
    if not line_edit:
        return

    def on_text_edited(text: str):
        if text is None:
            return
        text_upper = text.upper()
        if text_upper != text:
            # Guardar posición del cursor
            pos = line_edit.cursorPosition()

            # Cambiar texto sin disparar señales recursivas
            line_edit.blockSignals(True)
            line_edit.setText(text_upper)
            line_edit.blockSignals(False)

            # Restaurar posición del cursor
            line_edit.setCursorPosition(pos)

    # Conectar la señal de texto editado (no changed, para no loops infinitos)
    line_edit.textEdited.connect(on_text_edited)


def connect_upper_textedit(text_edit: QTextEdit) -> None:
    """
    Convierte automáticamente el texto a mayúsculas en un QTextEdit.

    Args:
        text_edit: Instancia de QTextEdit a configurar

    Notas:
        - Mantiene la posición del cursor
        - Aplica a todo el contenido del widget
    """
    if not text_edit:
        return

    def on_text_changed():
        doc = text_edit.toPlainText()
        doc_upper = doc.upper()
        if doc_upper != doc:
            # Guardar posición del cursor
            cursor = text_edit.textCursor()
            pos = cursor.position()

            # Cambiar texto sin disparar señales recursivas
            text_edit.blockSignals(True)
            text_edit.setPlainText(doc_upper)
            text_edit.blockSignals(False)

            # Restaurar posición del cursor
            cursor.setPosition(min(pos, len(doc_upper)))
            text_edit.setTextCursor(cursor)

    text_edit.textChanged.connect(on_text_changed)


def connect_upper_combobox(combo_box: QComboBox) -> None:
    """
    Convierte automáticamente el texto a mayúsculas en un QComboBox editable.

    Args:
        combo_box: Instancia de QComboBox a configurar

    Notas:
        - Solo aplica a combobox editables
        - Usa connect_upper_lineedit en el lineEdit interno
    """
    if not combo_box:
        return

    if combo_box.isEditable():
        line_edit = combo_box.lineEdit()
        if line_edit is not None:
            connect_upper_lineedit(line_edit)


def make_readonly_display(parent=None, decimals: int = 2,
                          minimum: float = 0.0, maximum: float = 9999999999.99) -> QDoubleSpinBox:
    """
    Crea un widget de visualización de solo lectura.

    Args:
        parent: Widget padre
        decimals: Número de decimales a mostrar
        minimum: Valor mínimo permitido
        maximum: Valor máximo permitido

    Returns:
        QDoubleSpinBox configurado como display de solo lectura
    """
    widget = QDoubleSpinBox(parent)
    widget.setDecimals(decimals)
    widget.setMinimum(minimum)
    widget.setMaximum(maximum)
    widget.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    widget.setReadOnly(True)
    widget.setAlignment(Qt.AlignmentFlag.AlignRight)
    widget.setEnabled(False)

    # Estilo adicional para indicar que es solo lectura
    widget.setStyleSheet("""
        QDoubleSpinBox:disabled {
            background-color: #f0f0f0;
            color: #666666;
            border: 1px solid #cccccc;
        }
    """)

    return widget


# ============================================================================
# UTILIDADES MATEMÁTICAS Y DE CÁLCULO
# ============================================================================

def round_up_to_005(value: float) -> float:
    """
    DEPRECADO: Reemplazado por adjust_dimension de dimensioning.py
    Mantenido por compatibilidad con código existente.

    Redondea un valor hacia arriba al múltiplo de 0.05 más cercano.

    Args:
        value: Valor a redondear

    Returns:
        Valor redondeado al múltiplo de 0.05 más cercano hacia arriba
    """
    # Delegar a adjust_dimension para consistencia
    return adjust_dimension(value, 0.05)


def ajustar_medidas_industriales(ancho: float, alto: float) -> Tuple[float, float]:
    """
    Aplica ajuste industrial a medidas usando dimensioning.py.
    SOLO para cálculos internos, NO para mostrar en interfaz.

    Args:
        ancho: Valor original de ancho
        alto: Valor original de alto

    Returns:
        Tuple[ancho_ajustado, alto_ajustado] según estándar industrial

    Notas:
        - Usa adjust_dimension con paso de 0.05
        - Los valores se redondean hacia arriba
        - Para debug, activar con ajustar_medidas_industriales.debug = True
    """
    try:
        # Usar adjust_dimension para ajuste industrial consistente
        ancho_ajustado = adjust_dimension(ancho, 0.05)
        alto_ajustado = adjust_dimension(alto, 0.05)

        # Debug log (puede activarse con flag)
        if hasattr(ajustar_medidas_industriales, 'debug') and ajustar_medidas_industriales.debug:
            print(f"[DEBUG] Ajuste industrial: {ancho:.3f}→{ancho_ajustado:.3f}, {alto:.3f}→{alto_ajustado:.3f}")

        return ancho_ajustado, alto_ajustado
    except Exception as e:
        # En caso de error, mantener valores originales
        print(f"[WARN] Error en ajuste industrial: {e}. Usando valores originales.")
        return ancho, alto


# Activar debug para ajuste industrial (cambiar a True si necesario)
ajustar_medidas_industriales.debug = False


def calcular_porcentaje(base: float, porcentaje: float) -> float:
    """
    Calcula el porcentaje de un valor base.

    Args:
        base: Valor base
        porcentaje: Porcentaje a calcular (ej: 25 para 25%)

    Returns:
        Valor del porcentaje calculado
    """
    return base * (porcentaje / 100.0)


def aplicar_desperdicio(valor: float, porcentaje_desperdicio: float) -> float:
    """
    Aplica porcentaje de desperdicio a un valor.

    Args:
        valor: Valor base
        porcentaje_desperdicio: Porcentaje de desperdicio (ej: 2 para 2%)

    Returns:
        Valor con desperdicio aplicado
    """
    return valor + calcular_porcentaje(valor, porcentaje_desperdicio)


def aplicar_factor_venta(valor: float, porcentaje_fv: float) -> float:
    """
    Aplica factor de venta a un valor.

    Args:
        valor: Valor base
        porcentaje_fv: Porcentaje de factor de venta (ej: 25 para 25%)

    Returns:
        Valor con factor de venta aplicado
    """
    return valor + calcular_porcentaje(valor, porcentaje_fv)


def calcular_iva(valor: float, porcentaje_iva: float = 16.0) -> float:
    """
    Calcula el IVA de un valor.

    Args:
        valor: Valor base
        porcentaje_iva: Porcentaje de IVA (default: 16%)

    Returns:
        Valor del IVA calculado
    """
    return calcular_porcentaje(valor, porcentaje_iva)


def calcular_precio_unitario(importe: float, cantidad: float) -> float:
    """
    Calcula el precio unitario basado en importe y cantidad.

    Args:
        importe: Importe total
        cantidad: Cantidad de unidades

    Returns:
        Precio unitario (importe / cantidad)
    """
    if cantidad == 0:
        return 0.0
    return importe / cantidad


# ============================================================================
# VALIDACIÓN Y LIMPIEZA DE DATOS
# ============================================================================

def limpiar_texto(texto: str) -> str:
    """
    Limpia un texto eliminando espacios extra y normalizando.

    Args:
        texto: Texto a limpiar

    Returns:
        Texto limpio (sin espacios extra, trimmed)
    """
    if not texto:
        return ""
    return " ".join(texto.strip().split())


def es_numerico(valor: Any) -> bool:
    """
    Verifica si un valor puede convertirse a número.

    Args:
        valor: Valor a verificar

    Returns:
        True si es numérico, False en caso contrario
    """
    try:
        float(valor)
        return True
    except (ValueError, TypeError):
        return False


def es_texto_valido(texto: str, min_len: int = 1, max_len: int = 255) -> bool:
    """
    Verifica si un texto cumple con los criterios de validez.

    Args:
        texto: Texto a verificar
        min_len: Longitud mínima permitida
        max_len: Longitud máxima permitida

    Returns:
        True si el texto es válido, False en caso contrario
    """
    if not isinstance(texto, str):
        return False

    texto_limpio = limpiar_texto(texto)
    return min_len <= len(texto_limpio) <= max_len


def normalizar_clave(clave: str) -> str:
    """
    Normaliza una clave eliminando espacios y convirtiendo a mayúsculas.

    Args:
        clave: Clave a normalizar

    Returns:
        Clave normalizada
    """
    if not clave:
        return ""
    return clave.strip().upper()


def validar_medida(medida: float, min_val: float = 0.0, max_val: float = 9999.99) -> bool:
    """
    Valida que una medida esté dentro de rangos aceptables.

    Args:
        medida: Valor de la medida a validar
        min_val: Valor mínimo permitido
        max_val: Valor máximo permitido

    Returns:
        True si la medida es válida, False en caso contrario
    """
    return min_val <= medida <= max_val


# ============================================================================
# UTILIDADES PARA TABLAS
# ============================================================================

def safe_table_text(table: QTableWidget, row: int, col: int, default: str = "") -> str:
    """
    Obtiene el texto de una celda de tabla de forma segura.

    Args:
        table: Widget de tabla (QTableWidget)
        row: Fila de la celda
        col: Columna de la celda
        default: Valor por defecto si la celda no existe

    Returns:
        Texto de la celda o valor por defecto
    """
    if not table or row < 0 or col < 0:
        return default

    try:
        item = table.item(row, col)
        return item.text() if item else default
    except (IndexError, AttributeError):
        return default


def set_table_item_text(table: QTableWidget, row: int, col: int,
                        text: str, editable: bool = True,
                        alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft) -> None:
    """
    Establece o actualiza el texto de una celda de tabla.

    Args:
        table: Widget de tabla (QTableWidget)
        row: Fila de la celda
        col: Columna de la celda
        text: Texto a establecer
        editable: Si la celda debe ser editable
        alignment: Alineación del texto en la celda
    """
    if not table or row < 0 or col < 0:
        return

    try:
        item = table.item(row, col)
        if item is None:
            item = QTableWidgetItem("")
            table.setItem(row, col, item)

        item.setText(text)
        item.setTextAlignment(alignment)

        flags = item.flags()
        item.setFlags(
            (flags | Qt.ItemFlag.ItemIsEditable) if editable
            else (flags & ~Qt.ItemFlag.ItemIsEditable)
        )
    except (IndexError, AttributeError):
        pass


def set_table_money(table: QTableWidget, row: int, col: int, value: float) -> None:
    """
    Establece un valor monetario formateado en una celda de tabla.

    Args:
        table: Widget de tabla (QTableWidget)
        row: Fila de la celda
        col: Columna de la celda
        value: Valor monetario a establecer
    """
    set_table_item_text(table, row, col, format_money(value),
                        editable=False, alignment=Qt.AlignmentFlag.AlignRight)


def set_table_number(table: QTableWidget, row: int, col: int,
                     value: float, decimals: int = 2) -> None:
    """
    Establece un valor numérico formateado en una celda de tabla.

    Args:
        table: Widget de tabla (QTableWidget)
        row: Fila de la celda
        col: Columna de la celda
        value: Valor numérico a establecer
        decimals: Número de decimales a mostrar
    """
    format_str = f"{value:.{decimals}f}"
    set_table_item_text(table, row, col, format_str,
                        editable=False, alignment=Qt.AlignmentFlag.AlignRight)


def clear_table(table: QTableWidget) -> None:
    """
    Limpia completamente una tabla (elimina todas las filas).

    Args:
        table: Widget de tabla a limpiar
    """
    table.setRowCount(0)


def get_table_row_count(table: QTableWidget) -> int:
    """
    Obtiene el número de filas de una tabla de forma segura.

    Args:
        table: Widget de tabla

    Returns:
        Número de filas, 0 si la tabla es None
    """
    if not table:
        return 0
    return table.rowCount()


# ============================================================================
# FUNCIONES PARA MANEJO DE PAQUETES (ESPECÍFICAS PARA EL SISTEMA)
# ============================================================================

def es_tipo_paquete(tipo: str) -> bool:
    """
    Determina si un tipo de material es un paquete.

    Args:
        tipo: Tipo de material en mayúsculas

    Returns:
        True si es un paquete, False en caso contrario
    """
    from .constants import TIPOS_PAQUETE  # Importación diferida para evitar circularidad

    if not tipo:
        return False

    tipo_normalizado = tipo.strip().upper()
    return tipo_normalizado in TIPOS_PAQUETE


def obtener_regla_editabilidad(tipo: str) -> Dict[str, bool]:
    """
    Obtiene las reglas de editabilidad para un tipo de material.

    Args:
        tipo: Tipo de material en mayúsculas

    Returns:
        Diccionario con reglas de editabilidad
    """
    from .constants import EDITABILIDAD  # Importación diferida

    tipo_normalizado = tipo.strip().upper()
    return EDITABILIDAD.get(tipo_normalizado, EDITABILIDAD.get("OTROS", {}))


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


def calcular_componentes_paquete(componentes_base: List[Dict],
                                 piezas_paquete: int,
                                 ancho_paquete: float,
                                 alto_paquete: float) -> List[Dict]:
    """
    Calcula las cantidades finales de los componentes de un paquete.

    Args:
        componentes_base: Lista de componentes base del paquete
        piezas_paquete: Número de piezas del paquete
        ancho_paquete: Ancho del paquete
        alto_paquete: Alto del paquete

    Returns:
        Lista de componentes con cantidades calculadas
    """
    resultados = []

    for comp in componentes_base:
        comp_calculado = comp.copy()

        # Multiplicar cantidad base por piezas del paquete
        cantidad_base = comp.get("cantidad_base", 1)
        cantidad_final = cantidad_base * piezas_paquete

        comp_calculado["cantidad_final"] = cantidad_final
        comp_calculado["ancho_final"] = ancho_paquete
        comp_calculado["alto_final"] = alto_paquete

        resultados.append(comp_calculado)

    return resultados


# ============================================================================
# FUNCIONES DE COMPATIBILIDAD (alias para código existente)
# ============================================================================

# Alias para mantener compatibilidad con código existente
_f = to_float
_i = to_int
_money = format_money
_connect_upper_lineedit = connect_upper_lineedit
_connect_upper_textedit = connect_upper_textedit
_connect_upper_combobox = connect_upper_combobox
_round_up_to_005 = round_up_to_005
_ajustar_medidas_industriales = ajustar_medidas_industriales

# ============================================================================
# EXPORTACIÓN DE FUNCIONES
# ============================================================================

__all__ = [
    # Funciones de inicialización
    'initialize_module',

    # Funciones de conversión
    'to_float', 'to_int', 'format_money', 'to_bool',

    # Alias de compatibilidad
    '_f', '_i', '_money',

    # Funciones de UI
    'connect_upper_lineedit', 'connect_upper_textedit', 'connect_upper_combobox',
    'make_readonly_display',

    # Alias de compatibilidad para UI
    '_connect_upper_lineedit', '_connect_upper_textedit', '_connect_upper_combobox',

    # Funciones matemáticas
    'round_up_to_005', 'ajustar_medidas_industriales',
    'calcular_porcentaje', 'aplicar_desperdicio', 'aplicar_factor_venta',
    'calcular_iva', 'calcular_precio_unitario',

    # Alias de compatibilidad para funciones matemáticas
    '_round_up_to_005', '_ajustar_medidas_industriales',

    # Funciones de validación
    'limpiar_texto', 'es_numerico', 'es_texto_valido', 'normalizar_clave',
    'validar_medida',

    # Funciones para tablas
    'safe_table_text', 'set_table_item_text', 'set_table_money',
    'set_table_number', 'clear_table', 'get_table_row_count',

    # Funciones para manejo de paquetes
    'es_tipo_paquete', 'obtener_regla_editabilidad', 'es_campo_editable',
    'calcular_componentes_paquete',

    # Constante de debug
    'ajustar_medidas_industriales',
]