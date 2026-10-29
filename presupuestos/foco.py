

# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/foco.py — Gestión de foco y navegación entre campos

CORRECCIONES APLICADAS:
1.2 - Campo Fecha: Navegación automática dd/mm/aaaa
2.2 - Flujo Color: Si "Varios" → foco en color(partida), else → $/kg
3.1 - Paquete aluminio: Flujo Ancho → Alto → Piezas → Tipo
3.2 - Herrería: Flujo Cant. Ancho → Ancho → Cant. Alto → Alto → Piezas → Tipo
3.3 - Vidrio: Flujo Ancho → Alto → Piezas → Tipo

Última actualización: 2026
"""

from PyQt6.QtCore import Qt, QObject, QEvent
from PyQt6.QtWidgets import QComboBox, QDoubleSpinBox, QSpinBox, QLineEdit


# ============================================================================
# FILTRO GLOBAL DE TECLAS
# ============================================================================

class GlobalKeyFilter(QObject):
    """Filtro global para manejar teclas especiales (Enter, Tab, etc.)."""
    
    def __init__(self, window):
        super().__init__()
        self.window = window
        self._navigation_cache = {}
        self.refresh_navigation_cache()
    
    def refresh_navigation_cache(self):
        """Actualiza el caché de navegación según el estado actual."""
        color_global = (self.window.cbo_color_global.currentText() or "").strip().upper()
        self._navigation_cache['color_global'] = color_global
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                return self._handle_enter_key(obj)
        return super().eventFilter(obj, event)
    
    def _handle_enter_key(self, obj):
        """Maneja la tecla Enter según el widget que tiene el foco."""
        # Si es un campo de búsqueda, no hacer nada especial
        if obj == getattr(self.window, 'le_filtro', None):
            return False
        if obj == getattr(self.window, 'le_cliente', None):
            return False
        
        # Navegación normal con Tab
        return False


def install_global_key_filter(window):
    """Instala el filtro global de teclas en la ventana."""
    keyfilter = GlobalKeyFilter(window)
    window.installEventFilter(keyfilter)
    return keyfilter


# ============================================================================
# CONEXIÓN DE FLUJOS DE FOCO
# ============================================================================

def connect_focus_flows(window, keyfilter):
    """
    CORRECCIÓN 2.2: Conecta los flujos de foco entre campos.
    Si color = "Varios" → foco en color(partida) después de f.v.
    Si color ≠ "Varios" → salto directo a $/kg
    """
    
    # ------------------------------------------------------------------------
    # Flujo: f.v. (%) → color (partida) o $/kg dependiendo de color_global
    # ------------------------------------------------------------------------
    def on_fv_pct_enter():
        """Maneja el Enter en el campo de F.V. (%)"""
        color_global = (window.cbo_color_global.currentText() or "").strip().upper()
        
        if color_global == "VARIOS":
            # Si es Varios, el foco va a color (partida)
            window.cbo_color.setFocus()
            if window.cbo_color.lineEdit():
                window.cbo_color.lineEdit().selectAll()
        else:
            # Si no es Varios, saltamos color (partida) y vamos a $/kg
            window.sp_precio_kg.setFocus()
            window.sp_precio_kg.selectAll()
    
    # Conectar el evento Enter de f.v. (%)
    if hasattr(window, 'sb_fv_pct'):
        window.sb_fv_pct.returnPressed.connect(on_fv_pct_enter)
    
    # ------------------------------------------------------------------------
    # Flujo: $/kg → Ancho
    # ------------------------------------------------------------------------
    if hasattr(window, 'sp_precio_kg'):
        window.sp_precio_kg.returnPressed.connect(lambda: (
            window.sp_ancho.setFocus(),
            window.sp_ancho.selectAll()
        ))
    
    # ------------------------------------------------------------------------
    # Flujo: Ancho → Alto
    # ------------------------------------------------------------------------
    if hasattr(window, 'sp_ancho'):
        window.sp_ancho.returnPressed.connect(lambda: (
            window.sp_alto.setFocus(),
            window.sp_alto.selectAll()
        ))
    
    # ------------------------------------------------------------------------
    # Flujo: Alto → Piezas (o Tipo según configuración)
    # ------------------------------------------------------------------------
    if hasattr(window, 'sp_alto'):
        window.sp_alto.returnPressed.connect(lambda: (
            window.sb_pzas_global.setFocus(),
            window.sb_pzas_global.selectAll()
        ))
    
    # ------------------------------------------------------------------------
    # Flujo: Color Global → sincronizar regla de color
    # ------------------------------------------------------------------------
    if hasattr(window, 'cbo_color_global'):
        window.cbo_color_global.currentTextChanged.connect(
            lambda _: _sync_color_rule(window)
        )
    
    # ------------------------------------------------------------------------
    # CORRECCIÓN 3.1-3.3: Flujos específicos por Tipo de material
    # ------------------------------------------------------------------------
    if hasattr(window, 'cbo_tipo'):
        window.cbo_tipo.currentTextChanged.connect(
            lambda _: _on_tipo_changed(window)
        )


def _sync_color_rule(window):
    """
    CORRECCIÓN 2.2: Sincroniza la regla de color.
    Delega a la implementación ÚNICA de la ventana (modulo_presupuestos.py)
    para evitar duplicidad de lógica.
    """
    if hasattr(window, '_sync_color_rule'):
        window._sync_color_rule(from_user=False)



def _on_tipo_changed(window):
    """
    CORRECCIÓN 3.1-3.3: Maneja el cambio de Tipo de material.
    Configura el flujo de foco según el tipo seleccionado.
    """
    tipo = (window.cbo_tipo.currentText() or "").strip().upper()
    
    # Limpiar conexiones anteriores
    _clear_focus_connections(window)
    
    # Configurar flujo según tipo
    if "PAQUETE" in tipo and "ALUMINIO" in tipo:
        _setup_paquete_aluminio_flow(window)
    elif "HERRERIA" in tipo or "HERRERÍA" in tipo:
        _setup_herreria_flow(window)
    elif "VIDRIO" in tipo:
        _setup_vidrio_flow(window)
    elif "ALUMINIO" in tipo:
        _setup_aluminio_flow(window)
    elif "HERRAJES" in tipo:
        _setup_herrajes_flow(window)
    else:
        _setup_default_flow(window)


def _clear_focus_connections(window):
    """Limpia las conexiones de foco anteriores."""
    # Nota: En PyQt6 no hay forma directa de desconectar lambdas
    # Se maneja creando nuevas conexiones que sobrescriben las anteriores
    pass


def _setup_paquete_aluminio_flow(window):
    """
    CORRECCIÓN 3.1: Flujo para Paquete Aluminio.
    Foco: Ancho → Alto → Piezas → Tipo
    """
    if hasattr(window, 'sp_ancho'):
        window.sp_ancho.returnPressed.connect(lambda: (
            window.sp_alto.setFocus(),
            window.sp_alto.selectAll()
        ))
    
    if hasattr(window, 'sp_alto'):
        window.sp_alto.returnPressed.connect(lambda: (
            window.sb_pzas_global.setFocus(),
            window.sb_pzas_global.selectAll()
        ))


def _setup_herreria_flow(window):
    """
    CORRECCIÓN 3.2: Flujo para Herrería.
    Foco: Cant. Ancho → Ancho → Cant. Alto → Alto → Piezas → Tipo
    """
    # En herrería, el flujo se maneja en la tabla tbl_he
    # Las columnas son: H_CA, H_ANCHO, H_CH, H_ALTO, H_PZAS
    pass


def _setup_vidrio_flow(window):
    """
    CORRECCIÓN 3.3: Flujo para Vidrio.
    Foco: Ancho → Alto → Piezas → Tipo
    """
    if hasattr(window, 'sp_ancho'):
        window.sp_ancho.returnPressed.connect(lambda: (
            window.sp_alto.setFocus(),
            window.sp_alto.selectAll()
        ))
    
    if hasattr(window, 'sp_alto'):
        window.sp_alto.returnPressed.connect(lambda: (
            window.sb_pzas_global.setFocus(),
            window.sb_pzas_global.selectAll()
        ))


def _setup_aluminio_flow(window):
    """Flujo para Aluminio estándar."""
    _setup_default_flow(window)


def _setup_herrajes_flow(window):
    """Flujo para Herrajes."""
    _setup_default_flow(window)


def _setup_default_flow(window):
    """Flujo de foco por defecto."""
    if hasattr(window, 'sp_ancho'):
        window.sp_ancho.returnPressed.connect(lambda: (
            window.sp_alto.setFocus(),
            window.sp_alto.selectAll()
        ))
    
    if hasattr(window, 'sp_alto'):
        window.sp_alto.returnPressed.connect(lambda: (
            window.sb_pzas_global.setFocus(),
            window.sb_pzas_global.selectAll()
        ))


# ============================================================================
# FUNCIONES DE FOCO POR COLUMNA
# ============================================================================

def focus_col(table, row, col):
    """
    Establece el foco en una celda específica de la tabla.
    
    Args:
        table: QTableWidget donde establecer el foco
        row: Índice de la fila
        col: Índice de la columna
    """
    if table is None or row < 0 or col < 0:
        return
    
    table.setFocus()
    table.setCurrentCell(row, col)
    item = table.item(row, col)
    if item is not None:
        table.editItem(item)


def focus_after_add(window, table, row, tipo):
    """
    Establece el foco después de agregar una fila a la tabla.
    
    Args:
        window: Ventana principal
        table: QTableWidget donde se agregó la fila
        row: Índice de la fila agregada
        tipo: Tipo de material (para determinar la columna)
    """
    if table is None or row < 0:
        return
    
    # Determinar columna de foco según tipo
    col = _get_focus_column_for_tipo(tipo, table)
    focus_col(table, row, col)


def _get_focus_column_for_tipo(tipo, table):
    """
    Obtiene la columna de foco según el tipo de material.
    
    Args:
        tipo: Tipo de material
        table: QTableWidget para obtener las constantes de columna
    
    Returns:
        int: Índice de la columna
    """
    tipo_up = (tipo or "").upper()
    
    # Columnas para tabla estándar (tbl)
    if hasattr(table, 'window') and hasattr(table.window(), 'C_ANCHO'):
        if "ALUMINIO" in tipo_up:
            if "PAQUETE" in tipo_up:
                return table.window().C_ANCHO
            return table.window().C_CA
        elif "VIDRIO" in tipo_up:
            return table.window().C_ANCHO
        elif "HERRAJES" in tipo_up:
            return table.window().C_PZAS
        else:
            return table.window().C_PZAS
    
    # Default
    return 4  # Columna Ancho por defecto


def force_focus_on_pzas(window):
    """
    Fuerza el foco al campo de Piezas.
    
    Args:
        window: Ventana principal
    """
    if hasattr(window, 'sb_pzas_global'):
        window.sb_pzas_global.setFocus()
        window.sb_pzas_global.selectAll()


# ============================================================================
# NAVEGACIÓN DE FECHA (CORRECCIÓN 1.2)
# ============================================================================

def setup_date_navigation(window):
    """
    CORRECCIÓN 1.2: Configura la navegación automática en el campo de fecha.
    El inputMask "99/99/9999" ya maneja las barras automáticamente.
    
    Args:
        window: Ventana principal
    """
    if not hasattr(window, 'le_fecha'):
        return
    
    # El inputMask ya inserta las / automáticamente
    # Solo conectamos para asegurar el comportamiento
    window.le_fecha.textChanged.connect(lambda: _on_date_text_changed(window))


def _on_date_text_changed(window):
    """
    Maneja el cambio de texto en el campo de fecha.
    
    Args:
        window: Ventana principal
    """
    if not hasattr(window, 'le_fecha') or not window.le_fecha:
        return
    
    text = window.le_fecha.text()
    cursor_pos = window.le_fecha.cursorPosition()
    
    # El inputMask "99/99/9999" ya maneja las barras automáticamente
    # No necesitamos hacer nada especial
    pass


# ============================================================================
# UTILIDADES DE NAVEGACIÓN
# ============================================================================

def select_all_on_focus(widget):
    """
    Selecciona todo el texto cuando un widget recibe el foco.
    
    Args:
        widget: Widget al que aplicar el comportamiento
    """
    if widget is None:
        return
    
    if isinstance(widget, (QLineEdit, QComboBox)):
        if hasattr(widget, 'lineEdit') and widget.lineEdit():
            widget.lineEdit().focusInEvent = lambda event: (
                widget.lineEdit().selectAll(),
                QLineEdit.focusInEvent(widget.lineEdit(), event)
            )
    elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
        widget.focusInEvent = lambda event: (
            widget.selectAll(),
            QSpinBox.focusInEvent(widget, event) if isinstance(widget, QSpinBox)
            else QDoubleSpinBox.focusInEvent(widget, event)
        )


def connect_upper_lineedit(lineedit):
    """
    Conecta un QLineEdit para convertir texto a mayúsculas.
    
    Args:
        lineedit: QLineEdit a conectar
    """
    if lineedit is None:
        return
    
    def to_upper():
        text = lineedit.text()
        if text:
            lineedit.setText(text.upper())
    
    lineedit.textEdited.connect(lambda _: to_upper())


def connect_upper_combobox(combobox):
    """
    Conecta un QComboBox para convertir texto a mayúsculas.
    
    Args:
        combobox: QComboBox a conectar
    """
    if combobox is None:
        return
    
    def to_upper():
        text = combobox.currentText()
        if text:
            combobox.setCurrentText(text.upper())
    
    combobox.currentTextChanged.connect(lambda _: to_upper())