# -*- coding: utf-8 -*-
"""
Pantalla principal del Concentrador de Materiales
"""
from __future__ import annotations
import sys
import os
from datetime import datetime
from typing import Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (

    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QMessageBox, QFileDialog
)


from common.estilos import QSS_BASE
from common.app_paths import get_app_root, get_resource_path
from common.focus_utils import apply_tab_order, install_select_all_on_focus
from common.logger_config import get_logger
from common.pdf_utils import get_pdf_dir
logger = get_logger('concentrador.ui.pantalla')

from concentrador_materiales.services.concentrador_service import ConcentradorService
from concentrador_materiales.models.concentrado import ReporteConcentrado, MaterialConcentrado
from concentrador_materiales.ui.recursos import ESTILO_CONCENTRADOR
from concentrador_materiales.ui.widgets.tabla_materiales import TablaMateriales
from concentrador_materiales.ui.widgets.barra_estado import BarraEstado
from concentrador_materiales.ui.dialogs.filtros_dialog import FiltrosDialog
from concentrador_materiales.ui.dialogs.advertencias_dialog import AdvertenciasDialog
from concentrador_materiales.ui.dialogs.detalle_material_dialog import DetalleMaterialDialog
from concentrador_materiales.ui.dialogs.progreso_dialog import ProgresoDialog

# Importar reportes
from concentrador_materiales.reports import ExcelGenerator, PDFGenerator

# ============================================================================
# RUTAS DE EXPORTACIÓN CONFIGURADAS
# ============================================================================
RUTA_EXPORTACION_EXCEL = os.path.join(get_app_root(), "pdfs", "Concentrador", "Excel")
RUTA_EXPORTACION_PDF = get_pdf_dir("Concentrador")

class PantallaConcentrador(QMainWindow):
    """
    Ventana principal del módulo Concentrador de Materiales.
    """
    COLUMNAS_ALUMINIO = [
        {"titulo": "Clave", "campo": "clave", "formato": "text", "ancho": 120},
        {"titulo": "Descripción", "campo": "descripcion", "formato": "text", "ancho": 250},
        {"titulo": "Metros Totales", "campo": "metros_totales", "formato": "decimal_2", "unidad": "m", "ancho": 100},
        {"titulo": "Largo Tramo", "campo": "largo_tramo", "formato": "decimal_2", "unidad": "m", "ancho": 80},
        {"titulo": "TRAMOS", "campo": "tramos_calculados", "formato": "int", "unidad": "tr", "ancho": 100, "negrita": True},
        {"titulo": "Origen", "campo": "origen", "formato": "text", "ancho": 100},
    ]

    COLUMNAS_VIDRIO = [
        {"titulo": "Clave", "campo": "clave", "formato": "text", "ancho": 120},
        {"titulo": "Descripción", "campo": "descripcion", "formato": "text", "ancho": 250},
        {"titulo": "Dimensiones", "campo": "dimensiones", "formato": "text", "ancho": 120},
        {"titulo": "m² Totales", "campo": "m2_totales", "formato": "decimal_2", "unidad": "m²", "ancho": 100},
        {"titulo": "HOJAS", "campo": "hojas_calculadas", "formato": "int", "unidad": "hj", "ancho": 100, "negrita": True},
    ]

    COLUMNAS_HERRERIA = [
        {"titulo": "Clave", "campo": "clave", "formato": "text", "ancho": 120},
        {"titulo": "Descripción", "campo": "descripcion", "formato": "text", "ancho": 250},
        {"titulo": "Metros Totales", "campo": "metros_totales", "formato": "decimal_2", "unidad": "m", "ancho": 100},
        {"titulo": "TRAMOS 6m", "campo": "tramos_calculados", "formato": "int", "unidad": "tr", "ancho": 100, "negrita": True},
        {"titulo": "Origen", "campo": "origen", "formato": "text", "ancho": 100},
    ]

    COLUMNAS_HERRAJES = [
        {"titulo": "Clave", "campo": "clave", "formato": "text", "ancho": 120},
        {"titulo": "Descripción", "campo": "descripcion", "formato": "text", "ancho": 250},
        {"titulo": "CANTIDAD", "campo": "cantidad", "formato": "int", "unidad": "pz", "ancho": 120, "negrita": True},
        {"titulo": "Origen", "campo": "origen", "formato": "text", "ancho": 100},
    ]

    COLUMNAS_PLASTICOS = [
        {"titulo": "Clave", "campo": "clave", "formato": "text", "ancho": 120},
        {"titulo": "Descripción", "campo": "descripcion", "formato": "text", "ancho": 300},
        {"titulo": "CANTIDAD", "campo": "cantidad", "formato": "int", "unidad": "pz", "ancho": 120, "negrita": True},
    ]

    COLUMNAS_OTROS = [
        {"titulo": "Clave", "campo": "clave", "formato": "text", "ancho": 120},
        {"titulo": "Descripción", "campo": "descripcion", "formato": "text", "ancho": 300},
        {"titulo": "CANTIDAD", "campo": "cantidad", "formato": "int", "unidad": "pz", "ancho": 120, "negrita": True},
    ]

    ALMACENES = [
        ("ALUMINIO", COLUMNAS_ALUMINIO),
        ("VIDRIO", COLUMNAS_VIDRIO),
        ("HERRERIA", COLUMNAS_HERRERIA),
        ("HERRAJES", COLUMNAS_HERRAJES),
        ("PLÁSTICOS", COLUMNAS_PLASTICOS),
        ("OTROS", COLUMNAS_OTROS),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VAH — Concentrador de Materiales")

        for relative_path in (
            ("logo.jpg",),
            ("logo.png",),
            ("logo_00001.ico",),
            ("principal", "pantalla_principal.ico"),
        ):
            logo_path = get_resource_path(*relative_path)
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
                break

        self.service = ConcentradorService()
        self.reporte_actual: Optional[ReporteConcentrado] = None
        self.filtros_actuales = {}

        self.setup_ui()
        self.setStyleSheet(QSS_BASE + "\n" + ESTILO_CONCENTRADOR)

        self._aplicar_sin_datos()

        # CORRECCIÓN: Maximizar después de que la ventana esté completamente inicializada
        # QTimer.singleShot(0, ...) ejecuta la función después de que el bucle de eventos
        # termine de procesar todos los eventos pendientes, asegurando que la ventana esté lista
        QTimer.singleShot(0, self._maximizar_ventana)

    def _maximizar_ventana(self):
        """
        Maximiza la ventana después de que esté completamente inicializada.
        Este método se llama vía QTimer.singleShot para evitar problemas de timing.
        """
        # Establecer el estado de ventana a maximizado
        self.setWindowState(Qt.WindowState.WindowMaximized)
        # Mostrar la ventana maximizada
        self.showMaximized()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        toolbar = QHBoxLayout()

        self.btn_filtros = QPushButton(" Filtros")
        self.btn_filtros.setToolTip("Configurar filtros de fecha y almacén")
        self.btn_filtros.clicked.connect(self._abrir_filtros)

        self.btn_generar = QPushButton("🔄 Generar Concentrado")
        self.btn_generar.setToolTip("Ejecutar concentración de materiales")
        self.btn_generar.clicked.connect(self._generar_concentrado)

        self.btn_excel = QPushButton("📊 Exportar Excel")
        self.btn_excel.setToolTip("Exportar a archivo Excel")
        self.btn_excel.setEnabled(False)
        self.btn_excel.clicked.connect(self._exportar_excel)

        self.btn_pdf = QPushButton("📄 Exportar PDF")
        self.btn_pdf.setToolTip("Exportar a archivo PDF")
        self.btn_pdf.setEnabled(False)
        self.btn_pdf.clicked.connect(self._exportar_pdf)

        toolbar.addWidget(self.btn_filtros)
        toolbar.addWidget(self.btn_generar)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_excel)
        toolbar.addWidget(self.btn_pdf)

        layout.addLayout(toolbar)

        self.tab_widget = QTabWidget()

        self.tablas = {}
        for nombre, columnas in self.ALMACENES:
            tabla = TablaMateriales()
            tabla.fila_doble_clic.connect(self._mostrar_detalle)
            tabla.columnas_actuales = columnas
            self.tablas[nombre] = tabla
            self.tab_widget.addTab(tabla, nombre)

        layout.addWidget(self.tab_widget)

        self.status = BarraEstado()
        self.setStatusBar(self.status)
        self.status.conectar_advertencias(self._mostrar_advertencias)
        apply_tab_order(
            self,
            [
                self.btn_filtros,
                self.btn_generar,
                self.btn_excel,
                self.btn_pdf,
                self.tab_widget,
            ],
        )
        self._focus_selection = install_select_all_on_focus(self)

    def _aplicar_sin_datos(self):
        for tabla in self.tablas.values():
            tabla.setRowCount(0)
        self.btn_excel.setEnabled(False)
        self.btn_pdf.setEnabled(False)
        self.status.set_mensaje("Presione 'Generar Concentrado' para comenzar")

    def _abrir_filtros(self):
        dialog = FiltrosDialog(self)
        if dialog.exec():
            self.filtros_actuales = dialog.obtener_filtros()
            self._generar_concentrado()

    def _generar_concentrado(self):
        self.progreso_dialog = ProgresoDialog(self)
        self.progreso_dialog.iniciar(self.service, self.filtros_actuales)
        self.progreso_dialog.exec()

    def mostrar_resultado(self, reporte: ReporteConcentrado):
        self.reporte_actual = reporte

        for tabla in self.tablas.values():
            tabla.setRowCount(0)

        for almacen, materiales in reporte.materiales_por_almacen.items():
            if almacen in self.tablas:
                columnas = None
                for nombre, cols in self.ALMACENES:
                    if nombre == almacen:
                        columnas = cols
                        break

                if columnas:
                    # Enriquecer datos para ALUMINIO
                    if almacen == "ALUMINIO":
                        for m in materiales:
                            if m.largo_tramo is None:
                                m.largo_tramo = 6.10

                    self.tablas[almacen].cargar_materiales(materiales, columnas)

        total_materiales = reporte.total_materiales
        total_advertencias = len(reporte.advertencias)
        total_errores = len(reporte.errores)

        self.status.actualizar_contadores(total_materiales, total_advertencias, total_errores)
        self.status.set_timestamp(f"✅ Procesado el {reporte.fecha_generacion.strftime('%d/%m/%Y %H:%M:%S')}")

        self.btn_excel.setEnabled(total_materiales > 0)
        self.btn_pdf.setEnabled(total_materiales > 0)

        if total_materiales > 0:
            self.status.set_mensaje(f"Concentrado generado: {total_materiales} materiales")
        else:
            self.status.set_mensaje("No se encontraron materiales para concentrar")

    def _mostrar_detalle(self, material: MaterialConcentrado):
        dialog = DetalleMaterialDialog(material, self)
        dialog.exec()

    def _mostrar_advertencias(self):
        if not self.reporte_actual:
            QMessageBox.information(self, "Información", "No hay advertencias para mostrar")
            return

        dialog = AdvertenciasDialog(
            self.reporte_actual.advertencias,
            self.reporte_actual.errores,
            self
        )
        dialog.exec()

    # ========================================================================
    # EXPORTACIÓN A EXCEL - RUTA AUTOMÁTICA
    # ========================================================================
    def _exportar_excel(self):
        """
        Exporta el concentrado actual a Excel en la ruta configurada.
        Ruta: <raiz_app>\\pdfs\\Concentrador\\Excel
        """
        if not self.reporte_actual:
            QMessageBox.warning(self, "Exportar", "No hay datos para exportar")
            return

        try:
            # Crear carpeta si no existe
            os.makedirs(RUTA_EXPORTACION_EXCEL, exist_ok=True)

            # Generar nombre de archivo con timestamp
            fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"Concentrador_Materiales_{fecha_str}.xlsx"
            ruta_completa = os.path.join(RUTA_EXPORTACION_EXCEL, nombre_archivo)

            # Generar el archivo Excel
            ExcelGenerator.generar(self.reporte_actual, ruta_completa)

            # Mostrar mensaje de éxito
            QMessageBox.information(
                self,
                "✅ Exportación Exitosa",
                f"Archivo Excel generado correctamente:\n\n{ruta_completa}"
            )

            # Actualizar status bar
            self.status.set_mensaje(f"Excel exportado: {nombre_archivo}")

        except ImportError as e:
            QMessageBox.warning(
                self,
                "Librería faltante",
                f"Para exportar a Excel necesitas instalar openpyxl:\n\n"
                f"pip install openpyxl\n\n"
                f"Error: {str(e)}"
            )
        except PermissionError as e:
            QMessageBox.critical(
                self,
                "Error de permisos",
                f"No se pudo guardar el archivo. Verifica que no esté abierto en otro programa:\n\n"
                f"{ruta_completa}\n\n"
                f"Error: {str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al exportar",
                f"No se pudo generar el archivo Excel:\n\n{str(e)}"
            )

    # ========================================================================
    # EXPORTACIÓN A PDF - RUTA AUTOMÁTICA
    # ========================================================================
    def _exportar_pdf(self):
        """
        Exporta el concentrado actual a PDF en la ruta configurada.
        Ruta: <raiz_app>\\pdfs\\Concentrador
        """
        if not self.reporte_actual:
            QMessageBox.warning(self, "Exportar", "No hay datos para exportar")
            return

        try:
            # Crear carpeta si no existe
            os.makedirs(RUTA_EXPORTACION_PDF, exist_ok=True)

            # Generar nombre de archivo con timestamp
            fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"Concentrador_Materiales_{fecha_str}.pdf"
            ruta_completa = os.path.join(RUTA_EXPORTACION_PDF, nombre_archivo)

            # Generar el archivo PDF
            PDFGenerator.generar(self.reporte_actual, ruta_completa)

            # Mostrar mensaje de éxito
            QMessageBox.information(
                self,
                "✅ Exportación Exitosa",
                f"Archivo PDF generado correctamente:\n\n{ruta_completa}"
            )

            # Actualizar status bar
            self.status.set_mensaje(f"PDF exportado: {nombre_archivo}")

        except ImportError as e:
            QMessageBox.warning(
                self,
                "Librería faltante",
                f"Para exportar a PDF necesitas instalar reportlab:\n\n"
                f"pip install reportlab\n\n"
                f"Error: {str(e)}"
            )
        except PermissionError as e:
            QMessageBox.critical(
                self,
                "Error de permisos",
                f"No se pudo guardar el archivo. Verifica que no esté abierto en otro programa:\n\n"
                f"{ruta_completa}\n\n"
                f"Error: {str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al exportar",
                f"No se pudo generar el archivo PDF:\n\n{str(e)}"
            )

# ============================================================================
# PUNTO DE ENTRADA DE LA APLICACIÓN
# ============================================================================
def main() -> int:
    """Función principal de arranque del módulo Concentrador."""
    # Asegurar que la raíz del proyecto esté en el path
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    # Inicializar aplicación PyQt6
    app = QApplication(sys.argv)

    # Instanciar y mostrar la ventana
    win = PantallaConcentrador()
    win.show()
    win.raise_()
    win.activateWindow()

    # Ejecutar bucle de eventos
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
