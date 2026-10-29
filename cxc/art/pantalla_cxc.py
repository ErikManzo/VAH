# -*- coding: utf-8 -*-
"""
VENTANA PRINCIPAL DEL MÓDULO CXC - VAH v1.0 Core
Arquitectura ERP Profesional - UI limpia, lógica encapsulada
"""
import os
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QTabWidget, QGroupBox, QMessageBox, QHeaderView,
    QAbstractItemView, QDialog, QMenu
)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common.app_paths import get_resource_path
from common.estilos import QSS_BASE, aplicar_estilo
from common.manuales import abrir_manual_pdf
from cxc.services.cxc_service import CxcService
from cxc.repositories.cxc_repository import CxcRepository
from cxc.repositories.pago_repository import PagoRepository
from cxc.art.dialogs.nuevo_cxc_dialog import NuevoCxcDialog
from cxc.art.dialogs.registrar_pago_dialog import RegistrarPagoDialog
from cxc.art.dialogs.cxc_reportes import CxcReportes
from cxc.data.db import get_connection


class PantallaCxc(QMainWindow):
    def __init__(self):
        super().__init__()
        aplicar_estilo(self)
        self.setWindowTitle("CXC - CUENTAS POR COBRAR")
        
        for icon_name in ("logo.jpg", "logo.png", "logo_00001.ico"):
            logo_path = get_resource_path(icon_name)
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
                break

        self.setGeometry(0, 0, 1400, 800)
        self.showMaximized()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        self._crear_menu_erp()
        self._setup_resumen(main_layout)
        self._setup_tabs(main_layout)

        self.statusBar().showMessage("LISTO")
        self.cargar_resumen()
        self.cargar_tabla_todos()
        self.cargar_listado_general()

    def _crear_menu_erp(self):
        menubar = self.menuBar()
        menu_archivo = menubar.addMenu("&Archivo")
        accion_nuevo = QAction("NUEVO CXC (DESDE PRESUPUESTO)", self)
        accion_nuevo.triggered.connect(self.abrir_nuevo_cxc)
        menu_archivo.addAction(accion_nuevo)
        accion_abono = QAction("REGISTRAR ABONO/FINIQUITO", self)
        accion_abono.triggered.connect(self.registrar_abono_desde_menu)
        menu_archivo.addAction(accion_abono)
        menu_archivo.addSeparator()
        accion_salir = QAction("SALIR", self)
        accion_salir.triggered.connect(self.close)
        menu_archivo.addAction(accion_salir)

        menu_movimientos = menubar.addMenu("&Movimientos")
        accion_eliminar = QAction("ELIMINAR CXC SELECCIONADO", self)
        accion_eliminar.triggered.connect(self.eliminar_cxc_actual)
        menu_movimientos.addAction(accion_eliminar)
        accion_actualizar = QAction("ACTUALIZAR", self)
        accion_actualizar.triggered.connect(self.cargar_tabla_todos)
        menu_movimientos.addAction(accion_actualizar)

        menu_reportes = menubar.addMenu("&Reportes")
        submenu_listado = QMenu("Listado General", self)
        accion_listado_pdf = QAction("Imprimir PDF", self)
        accion_listado_pdf.triggered.connect(lambda: self._exportar_reporte("listado_general", "pdf"))
        accion_listado_excel = QAction("Exportar Excel", self)
        accion_listado_excel.triggered.connect(lambda: self._exportar_reporte("listado_general", "excel"))
        submenu_listado.addAction(accion_listado_pdf)
        submenu_listado.addAction(accion_listado_excel)
        menu_reportes.addMenu(submenu_listado)

        submenu_estado = QMenu("Estado por Cliente", self)
        accion_estado_pdf = QAction("Imprimir PDF", self)
        accion_estado_pdf.triggered.connect(lambda: self._exportar_reporte("estado_cliente", "pdf"))
        accion_estado_excel = QAction("Exportar Excel", self)
        accion_estado_excel.triggered.connect(lambda: self._exportar_reporte("estado_cliente", "excel"))
        submenu_estado.addAction(accion_estado_pdf)
        submenu_estado.addAction(accion_estado_excel)
        menu_reportes.addMenu(submenu_estado)

        submenu_mov = QMenu("Todos los Movimientos", self)
        accion_mov_pdf = QAction("Imprimir PDF", self)
        accion_mov_pdf.triggered.connect(lambda: self._exportar_reporte("movimientos", "pdf"))
        accion_mov_excel = QAction("Exportar Excel", self)
        accion_mov_excel.triggered.connect(lambda: self._exportar_reporte("movimientos", "excel"))
        submenu_mov.addAction(accion_mov_pdf)
        submenu_mov.addAction(accion_mov_excel)
        menu_reportes.addMenu(submenu_mov)

        menu_ayuda = menubar.addMenu("&Ayuda")
        accion_manual_operativo = QAction("Manual Operativo", self)
        accion_manual_operativo.triggered.connect(lambda: abrir_manual_pdf("CXC", "operativo", self))
        menu_ayuda.addAction(accion_manual_operativo)
        accion_manual_tecnico = QAction("Manual Tecnico", self)
        accion_manual_tecnico.triggered.connect(lambda: abrir_manual_pdf("CXC", "tecnico", self))
        menu_ayuda.addAction(accion_manual_tecnico)
        menu_ayuda.addSeparator()
        accion_acerca = QAction("Acerca de", self)
        accion_acerca.triggered.connect(self._acerca_de)
        menu_ayuda.addAction(accion_acerca)

    def _exportar_reporte(self, tipo: str, formato: str):
        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            ruta = None
            if tipo == "listado_general":
                if formato == "pdf":
                    ruta = CxcReportes.generar_listado_general_pdf()
                else:
                    ruta = CxcReportes.generar_listado_general_excel()
            elif tipo == "estado_cliente":
                if hasattr(self, 'cmb_cliente_detalle'):
                    cliente_id = self.cmb_cliente_detalle.currentData()
                    cliente_nombre = self.cmb_cliente_detalle.currentText()
                    if cliente_id and cliente_id != 0:
                        if formato == "pdf":
                            ruta = CxcReportes.generar_estado_cliente_pdf(cliente_id, cliente_nombre)
                        else:
                            ruta = CxcReportes.generar_estado_cliente_excel(cliente_id, cliente_nombre)
                    else:
                        QMessageBox.warning(self, "ADVERTENCIA",
                                            "SELECCIONE UN CLIENTE EN LA PESTAÑA 'DETALLE POR CLIENTE'")
            elif tipo == "movimientos":
                filtros = self._obtener_filtros()
                if formato == "pdf":
                    ruta = CxcReportes.generar_movimientos_pdf(filtros)
                else:
                    ruta = CxcReportes.generar_movimientos_excel(filtros)

            if ruta:
                QMessageBox.information(self, "ÉXITO", f"ARCHIVO GENERADO:\n{ruta}")
            elif ruta is not None:
                QMessageBox.warning(self, "SIN DATOS", "NO HAY DATOS PARA EXPORTAR")
        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"ERROR GENERANDO REPORTE:\n{str(e)}")
        finally:
            QApplication.restoreOverrideCursor()

    def _setup_resumen(self, layout):
        resumen_group = QGroupBox("RESUMEN DE SALDOS")
        resumen_layout = QHBoxLayout(resumen_group)
        resumen_layout.setContentsMargins(8, 8, 8, 8)
        resumen_layout.setSpacing(12)
        self.lbl_saldo_total = QLabel("$0.00")
        self.lbl_en_curso = QLabel("0")
        self.lbl_liquidados = QLabel("0")
        self.lbl_clientes_activos = QLabel("0")
        for lbl, w in [("SALDO TOTAL PENDIENTE:", self.lbl_saldo_total),
                       ("EN CURSO:", self.lbl_en_curso),
                       ("LIQUIDADOS:", self.lbl_liquidados),
                       ("CLIENTES ACTIVOS:", self.lbl_clientes_activos)]:
            resumen_layout.addWidget(QLabel(lbl))
            resumen_layout.addWidget(w)
            resumen_layout.addStretch()
        layout.addWidget(resumen_group)

    def _setup_tabs(self, layout):
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.tab_general = QWidget()
        self.tabs.addTab(self.tab_general, "LISTADO GENERAL (CLIENTES)")
        self._setup_tab_general()
        self.tab_detalle_cliente = QWidget()
        self.tabs.addTab(self.tab_detalle_cliente, "DETALLE POR CLIENTE")
        self._setup_tab_detalle_cliente()
        self.tab_todos = QWidget()
        self.tabs.addTab(self.tab_todos, "TODOS LOS MOVIMIENTOS CXC")
        self._setup_tab_todos()

    def _setup_tab_general(self):
        layout = QVBoxLayout(self.tab_general)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table_general = QTableWidget()
        self.table_general.setColumnCount(5)
        self.table_general.setHorizontalHeaderLabels(
            ["ID CLIENTE", "CLIENTE", "TOTAL FACTURADO", "TOTAL ABONADO", "SALDO"])
        self.table_general.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_general.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_general.doubleClicked.connect(self.on_cliente_double_click)
        layout.addWidget(self.table_general, 1)

    def _setup_tab_detalle_cliente(self):
        layout = QVBoxLayout(self.tab_detalle_cliente)
        layout.setContentsMargins(4, 4, 4, 4)
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("SELECCIONAR CLIENTE:"))
        self.cmb_cliente_detalle = QComboBox()
        self.cmb_cliente_detalle.addItem("-- SELECCIONE --", 0)
        top_layout.addWidget(self.cmb_cliente_detalle)
        self.btn_cargar_detalle = QPushButton("MOSTRAR DETALLE")
        self.btn_cargar_detalle.clicked.connect(self.cargar_detalle_por_cliente)
        top_layout.addWidget(self.btn_cargar_detalle)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        self.table_detalle = QTableWidget()
        self.table_detalle.setColumnCount(8)
        self.table_detalle.setHorizontalHeaderLabels(
            ["ID CXC", "FOLIO", "PRESUPUESTO", "OBRA", "FECHA", "TOTAL", "ABONADO", "SALDO"])
        self.table_detalle.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_detalle.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table_detalle, 1)
        self.cargar_clientes_combobox()

    def _setup_tab_todos(self):
        layout = QVBoxLayout(self.tab_todos)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table_todos = QTableWidget()
        self.table_todos.setColumnCount(10)
        self.table_todos.setHorizontalHeaderLabels([
            "ID", "FOLIO", "CLIENTE", "PRESUPUESTO", "OBRA", "FECHA EMISIÓN",
            "TOTAL", "SALDO", "ESTADO", "TIPO"
        ])
        self.table_todos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_todos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_todos.doubleClicked.connect(self.on_cxc_double_click)
        layout.addWidget(self.table_todos, 1)

    def cargar_resumen(self):
        try:
            resumen = CxcService.obtener_resumen_general()
            self.lbl_saldo_total.setText(f"${resumen['saldo_total']:,.2f}")
            self.lbl_en_curso.setText(str(resumen['en_curso']))
            self.lbl_liquidados.setText(str(resumen['liquidados']))
            self.lbl_clientes_activos.setText(str(resumen['clientes_activos']))
        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"NO SE PUDO CARGAR EL RESUMEN:\n{str(e)}")

    def cargar_listado_general(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.id AS cliente_id,
                    c.Nombre AS cliente_nombre,
                    ISNULL(SUM(cc.total), 0) AS total_facturado,
                    ISNULL(SUM(p.monto), 0) AS total_abonado,
                    ISNULL(SUM(cc.saldo_pendiente), 0) AS saldo
                FROM [clientes].[dbo].[Clientes] c
                LEFT JOIN [cxc].[dbo].[cuentas_por_cobrar] cc ON c.id = cc.cliente_id
                LEFT JOIN [cxc].[dbo].[pagos_recibidos] p ON cc.id = p.cxc_id
                GROUP BY c.id, c.Nombre
                ORDER BY c.Nombre
            """)
            rows = cursor.fetchall()
            conn.close()

            self.table_general.setRowCount(0)
            for row_idx, row in enumerate(rows):
                self.table_general.insertRow(row_idx)
                self.table_general.setItem(row_idx, 0, QTableWidgetItem(str(row[0])))
                self.table_general.setItem(row_idx, 1, QTableWidgetItem((row[1] or "").upper()))
                self.table_general.setItem(row_idx, 2, QTableWidgetItem(f"${float(row[2] or 0):,.2f}"))
                self.table_general.setItem(row_idx, 3, QTableWidgetItem(f"${float(row[3] or 0):,.2f}"))
                self.table_general.setItem(row_idx, 4, QTableWidgetItem(f"${float(row[4] or 0):,.2f}"))
        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"ERROR AL CARGAR LISTADO GENERAL:\n{str(e)}")

    def cargar_tabla_todos(self):
        try:
            filtros = self._obtener_filtros()
            datos = CxcRepository.get_all_with_client_and_presupuesto(filtros)
            self.table_todos.setRowCount(len(datos))
            for i, row in enumerate(datos):
                self.table_todos.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                self.table_todos.setItem(i, 1, QTableWidgetItem(row['folio'].upper()))
                self.table_todos.setItem(i, 2, QTableWidgetItem(row['cliente_nombre'].upper()))
                self.table_todos.setItem(i, 3, QTableWidgetItem(
                    str(row['presupuesto_numero']) if row['presupuesto_numero'] else " "))
                self.table_todos.setItem(i, 4, QTableWidgetItem(row['obra'].upper() if row['obra'] else " "))
                self.table_todos.setItem(i, 5, QTableWidgetItem(row['fecha_emision'].strftime("%d/%m/%Y")))
                self.table_todos.setItem(i, 6, QTableWidgetItem(f"${row['total']:,.2f}"))
                self.table_todos.setItem(i, 7, QTableWidgetItem(f"${row['saldo_pendiente']:,.2f}"))
                self.table_todos.setItem(i, 8, QTableWidgetItem(row['estado']))
                self.table_todos.setItem(i, 9, QTableWidgetItem(row['tipo_operacion']))
            self.statusBar().showMessage(f"SE ENCONTRARON {len(datos)} MOVIMIENTOS", 3000)
            self.cargar_listado_general()
        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"ERROR AL CARGAR MOVIMIENTOS:\n{str(e)}")

    def cargar_clientes_combobox(self):
        try:
            datos = CxcRepository.get_saldos_por_cliente()
            self.cmb_cliente_detalle.clear()
            self.cmb_cliente_detalle.addItem("-- SELECCIONE --", 0)
            for cli in datos:
                self.cmb_cliente_detalle.addItem(cli['cliente_nombre'].upper(), cli['cliente_id'])
        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"ERROR AL CARGAR CLIENTES:\n{str(e)}")

    def cargar_detalle_por_cliente(self):
        cliente_id = self.cmb_cliente_detalle.currentData()
        if not cliente_id or cliente_id == 0:
            QMessageBox.warning(self, "ADVERTENCIA", "SELECCIONE UN CLIENTE VÁLIDO")
            return
        try:
            datos = CxcRepository.get_detalle_por_cliente(cliente_id)
            self.table_detalle.setRowCount(len(datos))
            for i, row in enumerate(datos):
                self.table_detalle.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                self.table_detalle.setItem(i, 1, QTableWidgetItem(row['folio'].upper()))
                self.table_detalle.setItem(i, 2, QTableWidgetItem(str(row['presupuesto_numero'])))
                self.table_detalle.setItem(i, 3, QTableWidgetItem(row['obra'].upper() if row['obra'] else " "))
                self.table_detalle.setItem(i, 4, QTableWidgetItem(row['fecha_emision'].strftime("%d/%m/%Y")))
                self.table_detalle.setItem(i, 5, QTableWidgetItem(f"${row['total']:,.2f}"))
                self.table_detalle.setItem(i, 6, QTableWidgetItem(f"${row['abonado']:,.2f}"))
                self.table_detalle.setItem(i, 7, QTableWidgetItem(f"${row['saldo']:,.2f}"))
        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"ERROR AL CARGAR DETALLE:\n{str(e)}")

    def _obtener_filtros(self):
        return {}

    def abrir_nuevo_cxc(self):
        dialogo = NuevoCxcDialog(self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_tabla_todos()
            self.cargar_resumen()
            self.cargar_listado_general()
            QMessageBox.information(self, "CXC CREADO", "EL NUEVO CXC SE HA REGISTRADO CORRECTAMENTE")

    def registrar_abono_desde_menu(self):
        tabla_actual = self.tabs.currentWidget()
        cxc_id = None
        if tabla_actual == self.tab_todos:
            fila = self.table_todos.currentRow()
            if fila >= 0: cxc_id = int(self.table_todos.item(fila, 0).text())
        elif tabla_actual == self.tab_detalle_cliente:
            fila = self.table_detalle.currentRow()
            if fila >= 0: cxc_id = int(self.table_detalle.item(fila, 0).text())
        if not cxc_id:
            QMessageBox.warning(self, "ADVERTENCIA", "SELECCIONE UN CXC EN LA TABLA PRIMERO")
            return
        dialogo = RegistrarPagoDialog(cxc_id, self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cargar_tabla_todos()
            self.cargar_resumen()
            self.cargar_listado_general()

    def eliminar_cxc_actual(self):
        tabla_actual = self.tabs.currentWidget()
        cxc_id = None
        if tabla_actual == self.tab_todos:
            fila = self.table_todos.currentRow()
            if fila >= 0: cxc_id = int(self.table_todos.item(fila, 0).text())
        elif tabla_actual == self.tab_detalle_cliente:
            fila = self.table_detalle.currentRow()
            if fila >= 0: cxc_id = int(self.table_detalle.item(fila, 0).text())
        if not cxc_id:
            QMessageBox.warning(self, "ADVERTENCIA", "SELECCIONE UN CXC EN LA TABLA PRIMERO")
            return
        pagos = PagoRepository.get_by_cxc_id(cxc_id)
        if pagos:
            resp = QMessageBox.question(self, "CONFIRMAR ELIMINACIÓN",
                                        f"EL CXC TIENE {len(pagos)} PAGO(S) REGISTRADOS.\n¿ELIMINAR TODO (CXC Y PAGOS)?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp != QMessageBox.StandardButton.Yes: return
        else:
            resp = QMessageBox.question(self, "CONFIRMAR ELIMINACIÓN", "¿ELIMINAR ESTE CXC?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp != QMessageBox.StandardButton.Yes: return
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cxc_detalle WHERE cxc_id = ?", (cxc_id,))
            cursor.execute("DELETE FROM pagos_recibidos WHERE cxc_id = ?", (cxc_id,))
            cursor.execute("DELETE FROM cuentas_por_cobrar WHERE id = ?", (cxc_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "ELIMINADO", "CXC ELIMINADO CORRECTAMENTE")
            self.cargar_tabla_todos()
            self.cargar_resumen()
            self.cargar_listado_general()
        except Exception as e:
            QMessageBox.critical(self, "ERROR", f"NO SE PUDO ELIMINAR:\n{str(e)}")

    def on_cliente_double_click(self, index):
        row = index.row()
        cliente_nombre = self.table_general.item(row, 1).text()
        idx = self.cmb_cliente_detalle.findText(cliente_nombre)
        if idx >= 0:
            self.cmb_cliente_detalle.setCurrentIndex(idx)
            self.tabs.setCurrentIndex(1)
            self.cargar_detalle_por_cliente()

    def on_cxc_double_click(self, index):
        row = index.row()
        cxc_id = int(self.table_todos.item(row, 0).text())
        opcion = QMessageBox.question(self, "CXC SELECCIONADO",
                                      f"¿QUÉ DESEA HACER?\n\nCXC ID: {cxc_id}\n\n- SÍ: REGISTRAR PAGO\n- NO: VER PDF",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
        if opcion == QMessageBox.StandardButton.Yes:
            dialogo = RegistrarPagoDialog(cxc_id, self)
            if dialogo.exec() == QDialog.DialogCode.Accepted:
                self.cargar_tabla_todos()
                self.cargar_resumen()
                self.cargar_listado_general()

    def _acerca_de(self):
        QMessageBox.information(self, "Acerca de VAH CXC",
                                "VAH v1.0 Core - Módulo CXC\n\nSistema de Cuentas por Cobrar\nERP Industrial/Comercial")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS_BASE + """
    QLabel, QPushButton, QTabBar::tab, QTableWidget, QHeaderView::section {
    text-transform: uppercase;
    font-weight: bold;
    }
    """)
    ventana = PantallaCxc()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
