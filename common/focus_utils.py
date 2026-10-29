# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Callable, Iterable, Optional
from PyQt6.QtCore import QObject, QEvent, Qt, QTimer
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QDateEdit,
    QLineEdit,
    QPlainTextEdit,
    QTextEdit,
    QWidget,
)

def _iter_valid_widgets(widgets: Iterable[Optional[QWidget]]) -> list[QWidget]:
    return [widget for widget in widgets if widget is not None]

def _select_all_if_possible(widget: QWidget) -> None:
    if isinstance(widget, QLineEdit):
        widget.selectAll()
        return
    if isinstance(widget, (QTextEdit, QPlainTextEdit)):
        widget.selectAll()
        return
    if isinstance(widget, QComboBox) and widget.isEditable() and widget.lineEdit():
        widget.lineEdit().selectAll()
        return
    if isinstance(widget, (QAbstractSpinBox, QDateEdit)) and widget.lineEdit():
        widget.lineEdit().selectAll()

def _resolve_select_all_target(widget: QWidget) -> Optional[QWidget]:
    if isinstance(widget, (QLineEdit, QTextEdit, QPlainTextEdit)):
        return widget
    if isinstance(widget, QComboBox) and widget.isEditable() and widget.lineEdit():
        return widget.lineEdit()
    if isinstance(widget, (QAbstractSpinBox, QDateEdit)) and widget.lineEdit():
        return widget.lineEdit()
    return None

def _collect_select_all_widgets(
    container: QWidget,
    widgets: Optional[Iterable[Optional[QWidget]]] = None,
) -> list[QWidget]:
    if widgets is None:
        candidates: list[QWidget] = [container, *container.findChildren(QWidget)]
    else:
        candidates = _iter_valid_widgets(widgets)
    targets: list[QWidget] = []
    seen: set[int] = set()
    for candidate in candidates:
        target = _resolve_select_all_target(candidate)
        if target is None:
            continue
        target_id = id(target)
        if target_id in seen:
            continue
        seen.add(target_id)
        targets.append(target)
    return targets

def _resolve_combo_popup_target(widget: QWidget) -> Optional[QComboBox]:
    if isinstance(widget, QComboBox):
        return widget
    parent = widget.parentWidget()
    if isinstance(parent, QComboBox):
        return parent
    return None

def _collect_combo_popup_targets(
    container: QWidget,
    widgets: Optional[Iterable[Optional[QWidget]]] = None,
) -> list[QComboBox]:
    if widgets is None:
        candidates: list[QWidget] = [container, *container.findChildren(QWidget)]
    else:
        candidates = _iter_valid_widgets(widgets)
    targets: list[QComboBox] = []
    seen: set[int] = set()
    for candidate in candidates:
        combo = _resolve_combo_popup_target(candidate)
        if combo is None:
            continue
        combo_id = id(combo)
        if combo_id in seen:
            continue
        seen.add(combo_id)
        targets.append(combo)
    return targets

def apply_tab_order(container: QWidget, widgets: Iterable[Optional[QWidget]]) -> list[QWidget]:
    """
    Aplica un orden explícito de tabulación sobre los widgets visibles del formulario.
    """
    ordered_widgets = _iter_valid_widgets(widgets)
    for previous, current in zip(ordered_widgets, ordered_widgets[1:]):
        container.setTabOrder(previous, current)
    return ordered_widgets

class EnterNavigationFilter(QObject):
    """
    Convierte Enter en "siguiente campo" para formularios simples y dispara una
    acción final opcional en el último control gestionado.
    """
    def __init__(
        self,
        parent: QWidget,
        widgets: Iterable[Optional[QWidget]],
        submit_callback: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self._widgets = _iter_valid_widgets(widgets)
        self._submit_callback = submit_callback

    def eventFilter(self, obj, event):  # type: ignore[override]
        if event.type() != QEvent.Type.KeyPress:
            return super().eventFilter(obj, event)
        if event.key() not in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return super().eventFilter(obj, event)
        if event.modifiers() & (
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.AltModifier
            | Qt.KeyboardModifier.MetaModifier
        ):
            return super().eventFilter(obj, event)
        widget = self._resolve_widget(obj)
        if widget is None:
            return super().eventFilter(obj, event)
        # CASO ESPECIAL: QComboBox con popup visible
        if isinstance(widget, QComboBox):
            view = widget.view()
            if view is not None and view.isVisible():
                # Permitir que Qt procese la selección del item
                result = super().eventFilter(obj, event)
                # Programar el avance del foco DESPUÉS de que Qt termine
                QTimer.singleShot(50, lambda: self._advance_after_combo(widget))
                return result
        # CASO NORMAL: navegación estándar
        if not self._should_handle_enter(widget):
            return super().eventFilter(obj, event)
        try:
            index = self._widgets.index(widget)
        except ValueError:
            return super().eventFilter(obj, event)
        if index == len(self._widgets) - 1:
            if self._submit_callback:
                self._submit_callback()
                return True
            return super().eventFilter(obj, event)
        next_widget = self._widgets[index + 1]
        next_widget.setFocus()
        _select_all_if_possible(next_widget)
        return True

    def _advance_after_combo(self, combo: QComboBox) -> None:
        """
        Avanza el foco al siguiente widget después de seleccionar un item en un QComboBox.
        Se llama con QTimer.singleShot para asegurar que el popup se haya cerrado completamente.
        """
        try:
            index = self._widgets.index(combo)
            if index < len(self._widgets) - 1:
                next_widget = self._widgets[index + 1]
                # Cerrar el popup explícitamente si está abierto
                if combo.view() and combo.view().isVisible():
                    combo.hidePopup()
                # Mover el foco al siguiente widget
                next_widget.setFocus()
                _select_all_if_possible(next_widget)
        except ValueError:
            pass

    def _resolve_widget(self, obj) -> Optional[QWidget]:
        for widget in self._widgets:
            if obj is widget:
                return widget
            if isinstance(widget, QComboBox) and widget.lineEdit() is obj:
                return widget
            if isinstance(widget, (QAbstractSpinBox, QDateEdit)) and widget.lineEdit() is obj:
                return widget
        return None

    @staticmethod
    def _should_handle_enter(widget: QWidget) -> bool:
        if isinstance(widget, (QTextEdit, QPlainTextEdit)):
            return False
        if isinstance(widget, QComboBox):
            view = widget.view()
            if view is not None and view.isVisible():
                return False
        return True

class SelectAllOnFocusFilter(QObject):
    """
    Selecciona todo el contenido del campo editable cuando recibe foco.
    """
    def __init__(self, parent: QWidget, widgets: Iterable[QWidget]) -> None:
        super().__init__(parent)
        self._widgets = list(widgets)

    def eventFilter(self, obj, event):  # type: ignore[override]
        if event.type() == QEvent.Type.FocusIn and isinstance(obj, QWidget):
            QTimer.singleShot(0, lambda widget=obj: _select_all_if_possible(widget))
        return super().eventFilter(obj, event)

class AutoPopupComboBoxFilter(QObject):
    """
    Despliega automáticamente la lista de un QComboBox al recibir foco.
    """
    def __init__(self, parent: QWidget, combos: Iterable[QComboBox]) -> None:
        super().__init__(parent)
        self._combos = list(combos)

    def eventFilter(self, obj, event):  # type: ignore[override]
        if event.type() == QEvent.Type.FocusIn and isinstance(obj, QWidget):
            combo = _resolve_combo_popup_target(obj)
            if combo is not None and combo.isEnabled() and combo.isVisible():
                QTimer.singleShot(0, lambda current_combo=combo: self._show_popup(current_combo))
        return super().eventFilter(obj, event)

    @staticmethod
    def _show_popup(combo: QComboBox) -> None:
        view = combo.view()
        if view is not None and view.isVisible():
            return
        combo.showPopup()

def install_select_all_on_focus(
    container: QWidget,
    widgets: Optional[Iterable[Optional[QWidget]]] = None,
) -> SelectAllOnFocusFilter:
    """
    Instala auto-selección del contenido al recibir foco en widgets editables.
    """
    targets = _collect_select_all_widgets(container, widgets)
    filter_obj = SelectAllOnFocusFilter(container, targets)
    for widget in targets:
        widget.installEventFilter(filter_obj)
    return filter_obj

def install_auto_popup_on_focus(
    container: QWidget,
    widgets: Optional[Iterable[Optional[QWidget]]] = None,
) -> AutoPopupComboBoxFilter:
    """
    Instala auto-despliegue de la lista en QComboBox al recibir foco.
    """
    combos = _collect_combo_popup_targets(container, widgets)
    filter_obj = AutoPopupComboBoxFilter(container, combos)
    for combo in combos:
        combo.installEventFilter(filter_obj)
        if combo.isEditable() and combo.lineEdit():
            combo.lineEdit().installEventFilter(filter_obj)
    return filter_obj

def install_enter_navigation(
    container: QWidget,
    widgets: Iterable[Optional[QWidget]],
    submit_callback: Optional[Callable[[], None]] = None,
) -> EnterNavigationFilter:
    """
    Instala navegación con Enter sobre los widgets recibidos.
    """
    filter_obj = EnterNavigationFilter(container, widgets, submit_callback=submit_callback)
    for widget in filter_obj._widgets:
        widget.installEventFilter(filter_obj)
        if isinstance(widget, QComboBox) and widget.lineEdit():
            widget.lineEdit().installEventFilter(filter_obj)
        if isinstance(widget, (QAbstractSpinBox, QDateEdit)) and widget.lineEdit():
            widget.lineEdit().installEventFilter(filter_obj)
    return filter_obj

def setup_form_navigation(
    container: QWidget,
    *,
    tab_widgets: Iterable[Optional[QWidget]],
    enter_widgets: Optional[Iterable[Optional[QWidget]]] = None,
    submit_callback: Optional[Callable[[], None]] = None,
) -> EnterNavigationFilter:
    """
    Configura orden de tabulación y navegación con Enter en una sola llamada.
    """
    ordered_tab_widgets = apply_tab_order(container, tab_widgets)
    select_all_filter = install_select_all_on_focus(container, ordered_tab_widgets)
    combo_popup_filter = install_auto_popup_on_focus(container, ordered_tab_widgets)
    effective_enter_widgets = enter_widgets if enter_widgets is not None else tab_widgets
    enter_filter = install_enter_navigation(container, effective_enter_widgets, submit_callback=submit_callback)
    enter_filter._select_all_filter = select_all_filter
    enter_filter._combo_popup_filter = combo_popup_filter
    return enter_filter