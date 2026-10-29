# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Iterable, Optional, Sequence
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QAbstractItemView, QCompleter, QHeaderView, QListWidget, QTableView

DEFAULT_MIN_VISIBLE_ITEMS = 15
DEFAULT_MAX_VISIBLE_ITEMS = 20
COMBINED_TEXT_COLUMN = 2


def format_key_description(clave: object, descripcion: object, separator: str = " - ") -> str:
    clave_text = str(clave or "").strip()
    desc_text = str(descripcion or "").strip()
    if clave_text and desc_text:
        return f"{clave_text}{separator}{desc_text}"
    return clave_text or desc_text


class ContainsAnywhereProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None, *, search_columns: Sequence[int] = (0, 1, COMBINED_TEXT_COLUMN)) -> None:
        super().__init__(parent)
        self._search_columns = tuple(search_columns)
        self._search_text = ""

    def set_search_text(self, text: str) -> None:
        normalized = (text or "").strip().casefold()
        if normalized == self._search_text:
            return
        self._search_text = normalized
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        if not self._search_text:
            return True
        model = self.sourceModel()
        if model is None:
            return True
        for column in self._search_columns:
            index = model.index(source_row, column, source_parent)
            value = str(model.data(index) or "").casefold()
            if self._search_text in value:
                return True
        return False


class MultiColumnSearchCompleter(QCompleter):
    def __init__(
        self,
        source_model: QStandardItemModel,
        *,
        display_column: int,
        parent=None,
        search_columns: Sequence[int] = (0, 1, COMBINED_TEXT_COLUMN),
    ) -> None:
        self._proxy = ContainsAnywhereProxyModel(parent, search_columns=search_columns)
        self._proxy.setSourceModel(source_model)
        super().__init__(self._proxy, parent)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompletionColumn(display_column)
        self.setMaxVisibleItems(DEFAULT_MIN_VISIBLE_ITEMS)

    def splitPath(self, path: str) -> list[str]:
        self._proxy.set_search_text(path)
        return [""]


def create_key_description_model(parent=None) -> QStandardItemModel:
    model = QStandardItemModel(0, 3, parent)
    model.setHorizontalHeaderLabels(["CLAVE", "DESCRIPCION", "BUSQUEDA"])
    return model


def populate_key_description_model(
    model: QStandardItemModel,
    rows: Iterable[dict],
    *,
    key_field: str = "clave",
    description_field: str = "descripcion",
) -> None:
    model.setRowCount(0)
    for row in rows:
        clave = str(row.get(key_field, "") or "").strip()
        descripcion = str(row.get(description_field, "") or "").strip()
        combined = format_key_description(clave, descripcion)
        model.appendRow(
            [
                QStandardItem(clave),
                QStandardItem(descripcion),
                QStandardItem(combined),
            ]
        )


def configure_two_column_completer(
    model: QStandardItemModel,
    *,
    display_column: int,
    parent=None,
    min_visible_items: int = DEFAULT_MIN_VISIBLE_ITEMS,
) -> MultiColumnSearchCompleter:
    completer = MultiColumnSearchCompleter(model, display_column=display_column, parent=parent)
    completer.setMaxVisibleItems(min_visible_items)
    popup = QTableView()
    popup.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    popup.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    popup.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    popup.setShowGrid(False)
    popup.verticalHeader().setVisible(False)
    popup.horizontalHeader().setStretchLastSection(True)
    popup.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    popup.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    popup.setColumnHidden(COMBINED_TEXT_COLUMN, True)
    completer.setPopup(popup)
    return completer


def get_key_description_from_index(index) -> tuple[str, str]:
    if not index.isValid():
        return "", ""
    clave = str(index.siblingAtColumn(0).data() or "").strip()
    descripcion = str(index.siblingAtColumn(1).data() or "").strip()
    return clave, descripcion


def configure_list_widget_for_search_results(
    list_widget: QListWidget,
    *,
    min_visible_rows: int = DEFAULT_MIN_VISIBLE_ITEMS,
    max_visible_rows: int = DEFAULT_MAX_VISIBLE_ITEMS,
) -> None:
    row_height = list_widget.sizeHintForRow(0)
    if row_height <= 0:
        row_height = max(list_widget.fontMetrics().height() + 10, 28)
    visible_rows = list_widget.count() if list_widget.count() > 0 else min_visible_rows
    visible_rows = max(min_visible_rows, min(max_visible_rows, visible_rows))
    frame = list_widget.frameWidth() * 2
    list_widget.setMinimumHeight((row_height * min_visible_rows) + frame + 4)
    list_widget.setMaximumHeight((row_height * visible_rows) + frame + 4)
    list_widget.setUniformItemSizes(True)


def popup_height_for_list_widget(
    list_widget: QListWidget,
    *,
    min_visible_rows: int = DEFAULT_MIN_VISIBLE_ITEMS,
    max_visible_rows: int = DEFAULT_MAX_VISIBLE_ITEMS,
    extra_padding: int = 10,
) -> int:
    row_height = list_widget.sizeHintForRow(0)
    if row_height <= 0:
        row_height = max(list_widget.fontMetrics().height() + 10, 28)
    visible_rows = list_widget.count() if list_widget.count() > 0 else min_visible_rows
    visible_rows = max(min_visible_rows, min(max_visible_rows, visible_rows))
    return (row_height * visible_rows) + extra_padding