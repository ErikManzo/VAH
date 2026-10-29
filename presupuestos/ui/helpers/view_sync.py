# -*- coding: utf-8 -*-
from datetime import datetime


def actualizar_combo_partidas(window, lista: list):
    """Actualiza el ComboBox con la lista de partidas."""
    window._actualizando_combo = True
    try:
        window.cbo_partida_rapida.blockSignals(True)
        window.cbo_partida_rapida.clear()
        if lista:
            window.cbo_partida_rapida.addItems(lista)
            indice = window.presupuesto_ctrl.obtener_indice_actual()
            if indice >= 0 and indice < len(lista):
                window.cbo_partida_rapida.setCurrentIndex(indice)
        else:
            window.cbo_partida_rapida.addItem("-- Sin partidas --")
        window.cbo_partida_rapida.blockSignals(False)
    finally:
        window._actualizando_combo = False


def on_partida_rapida_seleccionada(window, index: int):
    """Se ejecuta cuando se selecciona una partida del ComboBox."""
    if index < 0 or window._actualizando_combo:
        return
    window.presupuesto_ctrl.cargar_partida_por_indice(index)


def sync_color_rule(window, from_user: bool = False) -> None:
    g = (window.cbo_color_global.currentText() or "").strip().upper()
    if g == "VARIOS":
        window.cbo_color.setEnabled(True)
    else:
        window.cbo_color.setCurrentText(g)
        window.cbo_color.setEnabled(False)
    actualizar_color_en_tabla_materiales(window)
    actualizar_color_en_tabla_anidada(window)


def actualizar_color_en_tabla_materiales(window):
    color = window._get_color_partida_o_global()
    for r in range(window.tbl.rowCount()):
        item = window.tbl.item(r, window.C_COLOR)
        if item:
            item.setText(color)


def actualizar_color_en_tabla_anidada(window):
    color = window._get_color_partida_o_global()
    for r in range(window.tbl_anidada.rowCount()):
        item = window.tbl_anidada.item(r, window.A_COLOR)
        if item:
            item.setText(color)


def set_fecha_hoy(window) -> None:
    if hasattr(window, "le_fecha") and window.le_fecha:
        window.le_fecha.setText(datetime.now().strftime("%d/%m/%Y"))


def on_fecha_editado(window, text: str):
    cursor_pos = window.le_fecha.cursorPosition()
    if cursor_pos == 2 and len(text) >= 2:
        window.le_fecha.setCursorPosition(3)
    elif cursor_pos == 5 and len(text) >= 5:
        window.le_fecha.setCursorPosition(6)


def after_choose_filtro(window):
    try:
        window.le_filtro.clear()
        window.lst_result.clear()
        window.lst_result.setVisible(False)
        window.le_filtro.setFocus()
    except Exception:
        pass
