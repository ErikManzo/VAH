# -*- coding: utf-8 -*-
"""
Diálogo de filtros para el concentrador de materiales
PERMITE SELECCIONAR INSTANCIAS ESPECÍFICAS DE CXC
"""
from typing import Optional
from datetime import date
from PyQt6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QDateEdit, QCheckBox, QGroupBox, QPushButton,
    QLineEdit, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, QDate

from common.focus_utils import install_enter_navigation, setup_form_navigation
from concentrador_materiales.ui.recursos import ESTILO_CONCENTRADOR
from concentrador_materiales.repositories.cxc_repository import CXCRepository


from common.logger_config import get_logger
logger = get_logger('concentrador.ui.dialogs.filtros')

class FiltrosDialog(QDialog):
    """
    Diálogo para configurar filtros de concentración.
    Permite seleccionar instancias específicas de CXC para explosión de materiales.
    """

    ALMACENES = ["ALUMINIO", "VIDRIO", "HERRERIA", "HERRAJES", "PLASTICOS", "OTROS"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros - Concentrador de Materiales")
        self.setModal(True)
        self.setMinimumWidth(550)
        self.setStyleSheet(ESTILO_CONCENTRADOR)

        # Repositorio CXC para cargar instancias
        self.cxc_repo = CXCRepository()

        self.setup_ui()
        self.cargar_valores_por_defecto()

    def setup_ui(self):
        """Construye la interfaz del diálogo."""
        layout = QVBoxLayout(self)

        # ====================================================================
        # GRUPO DE FECHAS
        # ====================================================================
        gb_fechas = QGroupBox("Rango de fechas (aceptación CXC)")
        grid_fechas = QGridLayout(gb_fechas)

        self.chk_fecha_desde = QCheckBox("Desde:")
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDisplayFormat("dd/MM/yyyy")

        self.chk_fecha_hasta = QCheckBox("Hasta:")
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDisplayFormat("dd/MM/yyyy")

        self.chk_fecha_desde.stateChanged.connect(self._toggle_fecha_desde)
        self.chk_fecha_hasta.stateChanged.connect(self._toggle_fecha_hasta)

        grid_fechas.addWidget(self.chk_fecha_desde, 0, 0)
        grid_fechas.addWidget(self.date_desde, 0, 1)
        grid_fechas.addWidget(self.chk_fecha_hasta, 1, 0)
        grid_fechas.addWidget(self.date_hasta, 1, 1)

        layout.addWidget(gb_fechas)

        # ====================================================================
        # GRUPO DE ALMACENES
        # ====================================================================
        gb_almacenes = QGroupBox("Almacenes a incluir")
        grid_almacenes = QGridLayout(gb_almacenes)

        self.checkboxes_almacen = {}
        for i, almacen in enumerate(self.ALMACENES):
            cb = QCheckBox(almacen)
            cb.setChecked(True)
            self.checkboxes_almacen[almacen] = cb
            row = i // 3
            col = i % 3
            grid_almacenes.addWidget(cb, row, col)

        layout.addWidget(gb_almacenes)

        # ====================================================================
        # GRUPO DE BÚSQUEDA AVANZADA (CON SELECCIÓN DE INSTANCIA CXC)
        # ====================================================================
        gb_avanzado = QGroupBox("Búsqueda avanzada")
        gb_avanzado.setCheckable(True)
        gb_avanzado.setChecked(False)
        grid_avanzado = QGridLayout(gb_avanzado)

        # Campo Presupuesto ID (opcional, para filtrar instancias)
        grid_avanzado.addWidget(QLabel("Presupuesto ID:"), 0, 0)
        self.spin_presupuesto = QLineEdit()
        self.spin_presupuesto.setPlaceholderText("Opcional (filtra instancias)")
        grid_avanzado.addWidget(self.spin_presupuesto, 0, 1)

        # Botón para cargar instancias
        self.btn_cargar_instancias = QPushButton("🔍 Cargar instancias")
        self.btn_cargar_instancias.setToolTip(
            "Carga las instancias CXC disponibles para el presupuesto indicado"
        )
        self.btn_cargar_instancias.clicked.connect(self._cargar_instancias)
        grid_avanzado.addWidget(self.btn_cargar_instancias, 0, 2)

        # ComboBox de instancias CXC (reemplaza el campo CXC ID anterior)
        grid_avanzado.addWidget(QLabel("Instancia CXC:"), 1, 0)
        self.cmb_instancia_cxc = QComboBox()
        self.cmb_instancia_cxc.setToolTip(
            "Selecciona la instancia específica de CXC a explotar. "
            "Si dejas 'Todas las instancias activas', se procesarán todas."
        )
        # Item por defecto: todas las instancias
        self.cmb_instancia_cxc.addItem("🔄 Todas las instancias activas", None)
        grid_avanzado.addWidget(self.cmb_instancia_cxc, 1, 1, 1, 2)

        # Etiqueta informativa
        lbl_info = QLabel(
            "💡 Tip: Escribe el # de presupuesto y haz clic en 'Cargar instancias' "
            "para ver las aceptaciones de ese presupuesto."
        )
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("QLabel { color: #666; font-size: 9px; font-style: italic; }")
        grid_avanzado.addWidget(lbl_info, 2, 0, 1, 3)

        layout.addWidget(gb_avanzado)

        # ====================================================================
        # BOTONES
        # ====================================================================
        botones_layout = QHBoxLayout()
        btn_aplicar = QPushButton("Aplicar filtros")
        btn_aplicar.clicked.connect(self.accept)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.clicked.connect(self.cargar_valores_por_defecto)

        botones_layout.addWidget(btn_limpiar)
        botones_layout.addStretch()
        botones_layout.addWidget(btn_cancelar)
        botones_layout.addWidget(btn_aplicar)

        layout.addLayout(botones_layout)
        self.btn_aplicar = btn_aplicar
        self.btn_cancelar = btn_cancelar
        self.btn_limpiar = btn_limpiar
        self._focus_navigation = setup_form_navigation(
            self,
            tab_widgets=[
                self.chk_fecha_desde,
                self.date_desde,
                self.chk_fecha_hasta,
                self.date_hasta,
                self.spin_presupuesto,
                self.btn_cargar_instancias,
                self.cmb_instancia_cxc,
                self.btn_limpiar,
                self.btn_cancelar,
                self.btn_aplicar,
            ],
            enter_widgets=[
                self.date_desde,
                self.date_hasta,
                self.cmb_instancia_cxc,
            ],
            submit_callback=self.btn_aplicar.click,
        )
        self._instancias_enter_navigation = install_enter_navigation(
            self,
            [self.spin_presupuesto],
            submit_callback=self.btn_cargar_instancias.click,
        )

    def _toggle_fecha_desde(self, state):
        self.date_desde.setEnabled(state == Qt.CheckState.Checked.value)

    def _toggle_fecha_hasta(self, state):
        self.date_hasta.setEnabled(state == Qt.CheckState.Checked.value)

    def cargar_valores_por_defecto(self):
        """Restablece los filtros a sus valores por defecto."""
        self.chk_fecha_desde.setChecked(False)
        self.chk_fecha_hasta.setChecked(False)
        self.date_desde.setDate(QDate.currentDate().addMonths(-1))
        self.date_hasta.setDate(QDate.currentDate())
        self.date_desde.setEnabled(False)
        self.date_hasta.setEnabled(False)

        for cb in self.checkboxes_almacen.values():
            cb.setChecked(True)

        self.spin_presupuesto.clear()

        # Resetear ComboBox de instancias
        self.cmb_instancia_cxc.clear()
        self.cmb_instancia_cxc.addItem("🔄 Todas las instancias activas", None)

    def _cargar_instancias(self):
        """
        Carga las instancias CXC disponibles en el ComboBox.
        Si se especificó un presupuesto_id, filtra por ese presupuesto.
        Si no, carga todas las instancias activas.
        """
        # Leer presupuesto_id (opcional)
        presupuesto_id = None
        texto_presupuesto = self.spin_presupuesto.text().strip()
        if texto_presupuesto:
            try:
                presupuesto_id = int(texto_presupuesto)
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Presupuesto ID inválido",
                    "El Presupuesto ID debe ser un número entero."
                )
                return

        try:
            # Mostrar cursor de espera
            self.setCursor(Qt.CursorShape.WaitCursor)
            self.btn_cargar_instancias.setEnabled(False)
            self.btn_cargar_instancias.setText("⏳ Cargando...")

            # Obtener instancias del repositorio
            instancias = self.cxc_repo.obtener_instancias_cxc_por_presupuesto(presupuesto_id)

            # Limpiar ComboBox
            self.cmb_instancia_cxc.clear()

            # Agregar item "Todas las instancias"
            if presupuesto_id is not None:
                self.cmb_instancia_cxc.addItem(
                    f"🔄 Todas las instancias del presupuesto {presupuesto_id}",
                    None
                )
            else:
                self.cmb_instancia_cxc.addItem("🔄 Todas las instancias activas", None)

            # Agregar cada instancia
            if not instancias:
                QMessageBox.information(
                    self,
                    "Sin instancias",
                    "No se encontraron instancias CXC activas" +
                    (f" para el presupuesto {presupuesto_id}" if presupuesto_id else "") +
                    ".\n\nVerifica que el presupuesto tenga presupuesto_aceptado = 1 en CXC."
                )
            else:
                for instancia in instancias:
                    # Formatear fecha
                    fecha = instancia.get("fecha_aceptacion")
                    if fecha:
                        if hasattr(fecha, 'strftime'):
                            fecha_str = fecha.strftime("%d/%m/%Y")
                        else:
                            fecha_str = str(fecha)
                    else:
                        fecha_str = "S/F"

                    # Formato: FOLIO | FECHA | N_PARTIDAS | TOTAL
                    folio = instancia.get("folio", "S/F")
                    num_partidas = instancia.get("num_partidas", 0)
                    total_cxc = instancia.get("total_cxc", 0.0)
                    presupuesto = instancia.get("presupuesto_id", 0)

                    display = (
                        f"{folio} | {fecha_str} | "
                        f"{num_partidas} partidas | "
                        f"Presp. {presupuesto} | ${total_cxc:,.2f}"
                    )

                    self.cmb_instancia_cxc.addItem(
                        display,
                        instancia["cxc_id"]
                    )

                # Seleccionar la primera instancia específica (no "Todas")
                if self.cmb_instancia_cxc.count() > 1:
                    self.cmb_instancia_cxc.setCurrentIndex(1)

                QMessageBox.information(
                    self,
                    "Instancias cargadas",
                    f"Se encontraron {len(instancias)} instancia(s) CXC activa(s)."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al cargar instancias",
                f"No fue posible cargar las instancias CXC:\n\n{str(e)}"
            )
        finally:
            self.unsetCursor()
            self.btn_cargar_instancias.setEnabled(True)
            self.btn_cargar_instancias.setText(" Cargar instancias")

    def obtener_filtros(self) -> dict:
        """
        Retorna los filtros seleccionados.
        Incluye cxc_id si se seleccionó una instancia específica.
        """
        filtros = {
            "fecha_desde": None,
            "fecha_hasta": None,
            "almacenes": [],
            "presupuesto_id": None,
            "cxc_id": None  # NUEVO: ID de la instancia CXC seleccionada
        }

        if self.chk_fecha_desde.isChecked():
            filtros["fecha_desde"] = self.date_desde.date().toPyDate()

        if self.chk_fecha_hasta.isChecked():
            filtros["fecha_hasta"] = self.date_hasta.date().toPyDate()

        for almacen, cb in self.checkboxes_almacen.items():
            if cb.isChecked():
                filtros["almacenes"].append(almacen)

        # Presupuesto ID (texto)
        if self.spin_presupuesto.text().strip():
            try:
                filtros["presupuesto_id"] = int(self.spin_presupuesto.text())
            except ValueError:
                pass

        # CXC ID (de la instancia seleccionada en el ComboBox)
        cxc_id = self.cmb_instancia_cxc.currentData()
        if cxc_id is not None:
            filtros["cxc_id"] = int(cxc_id)

        return filtros
