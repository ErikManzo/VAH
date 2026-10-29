# -*- coding: utf-8 -*-
"""
imprimir.py — Módulo de impresión para Paquete Herrajes
Soporta: Pantalla, PDF, Impresora
Reportes: General y Desglosado
"""
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QComboBox, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QTreeWidget,
    QTreeWidgetItem, QFileDialog, QMessageBox, QWidget, QApplication, QProgressDialog
)
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrinterInfo

from common.pdf_utils import get_pdf_path
from common.logger_config import get_logger
logger = get_logger('paquetes.herrajes.imprimir')


class ReportGenerationWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, db_factory, server, database, tipo, destino):
        super().__init__()
        self.db_factory = db_factory
        self.server = server
        self.database = database
        self.tipo = tipo
        self.destino = destino

    def run(self):
        try:
            db = self.db_factory(server=self.server, database=self.database)
            if self.tipo == "General":
                paquetes = db.paquetes_listar()
                payload = {
                    "tipo": self.tipo,
                    "destino": self.destino,
                    "data": paquetes,
                    "html": _build_html_general(paquetes),
                }
            else:
                data = db.paquetes_y_items()
                payload = {
                    "tipo": self.tipo,
                    "destino": self.destino,
                    "data": data,
                    "html": _build_html_desglosado(data),
                }
            self.finished.emit(payload)
        except Exception as e:
            self.error.emit(str(e))


# ---------------------- Diálogos de opciones ----------------------
class ReportTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tipo de reporte")
        self.setModal(True)
        self.resize(420, 130)
        lay = QVBoxLayout(self)

        grid = QGridLayout()
        lay.addLayout(grid)

        grid.addWidget(QLabel("Reporte:"), 0, 0)
        self.cmb_tipo = QComboBox() 
        self.cmb_tipo.addItems(["General", "Desglosado"])
        grid.addWidget(self.cmb_tipo, 0, 1, 1, 2)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("Aceptar")
        lay.addWidget(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

    def selected_report_type(self):
        return self.cmb_tipo.currentText()


class PrintOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Destino de salida")
        self.setModal(True)
        self.resize(420, 130)
        lay = QVBoxLayout(self)

        grid = QGridLayout()
        lay.addLayout(grid)

        grid.addWidget(QLabel("Destino:"), 0, 0)
        self.cmb_destino = QComboBox()
        self.cmb_destino.addItems(["Pantalla", "PDF", "Impresora"])
        grid.addWidget(self.cmb_destino, 0, 1, 1, 2)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("Aceptar")
        lay.addWidget(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

    def selected_destination(self):
        return self.cmb_destino.currentText()


# ---------------------- Pantalla ----------------------
class ScreenReportGeneral(QDialog):
    def __init__(self, paquetes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reporte: Pantalla / General")
        self.resize(700, 500)
        lay = QVBoxLayout(self)
        tbl = QTableWidget(0, 2, self)
        tbl.setHorizontalHeaderLabels(["CLAVE", "DESCRIPCIÓN"])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        lay.addWidget(tbl)
        for r in sorted(paquetes, key=lambda x: x.get("clave", "")):
            i = tbl.rowCount()
            tbl.insertRow(i)
            tbl.setItem(i, 0, QTableWidgetItem(r.get("clave", "")))
            tbl.setItem(i, 1, QTableWidgetItem(r.get("descripcion", "")))
        lbl = QLabel("Vista informativa. No afecta ninguna otra parte.")
        lbl.setStyleSheet("color: #555;")
        lay.addWidget(lbl)


class ScreenReportDesglosado(QDialog): 
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reporte: Pantalla / Desglosado")
        self.resize(900, 600)
        lay = QVBoxLayout(self)
        tree = QTreeWidget(self)
        tree.setColumnCount(5)
        tree.setHeaderLabels(["CLAVE PAQ.", "DESCRIPCIÓN PAQ.", "CLAVE HERRAJE", "DESCRIPCIÓN HERRAJE", "CANT."])
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        tree.header().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(tree)
        for p in sorted(data, key=lambda x: x.get("clave", "")):
            parent_item = QTreeWidgetItem([p.get("clave", ""), p.get("descripcion", ""), "", "", ""])
            tree.addTopLevelItem(parent_item)
            for it in sorted(p.get("items", []), key=lambda x: x.get("clave", "")):
                child = QTreeWidgetItem(["", "", it.get("clave", ""), it.get("descripcion", ""), str(it.get("cantidad", 0))])
                parent_item.addChild(child)
        tree.expandAll()


# ---------------------- HTML builders ----------------------
def _build_html_general(paquetes):
    rows = "\n".join(
        f"<tr><td>{p.get('clave', '')}</td><td>{p.get('descripcion', '')}</td></tr>"
        for p in sorted(paquetes, key=lambda x: x.get('clave', ''))
    )
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Paquetes (General)</title>
    <style>
        body {{ font-family: Segoe UI, Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    <h1>Paquetes (General)</h1>
    <table>
        <thead>
            <tr>
                <th>CLAVE</th>
                <th>DESCRIPCIÓN</th>
            </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
    </table>
</body>
</html>
""".strip()


def _build_html_desglosado(data):
    parts = ["<!DOCTYPE html>\n<html>\n<head>\n    <meta charset=\"utf-8\">\n    <title>Paquetes (Desglosado)</title>\n    <style>\n        body { font-family: Segoe UI, Arial, sans-serif; margin: 20px; }\n        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }\n        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n        th { background-color: #f2f2f2; }\n        h2 { color: #333; margin-top: 30px; }\n    </style>\n</head>\n<body>\n    <h1>Paquetes (Desglosado)</h1>"]
    for p in sorted(data, key=lambda x: x.get("clave", "")):
        parts.append(f"<h2>Paquete: {p.get('clave', '')} – {p.get('descripcion', '')}</h2>")
        if not p.get("items"):
            parts.append("<p>Sin items</p>")
            continue
        parts.append("<table><thead><tr><th>CLAVE HERRAJE</th><th>DESCRIPCIÓN HERRAJE</th><th>CANT.</th></tr></thead><tbody>")
        for it in sorted(p.get("items", []), key=lambda x: x.get("clave", "")):
            parts.append(f"<tr><td>{it.get('clave', '')}</td><td>{it.get('descripcion', '')}</td><td>{it.get('cantidad', 0)}</td></tr>")
        parts.append("</tbody></table>")
    parts.append("</body>\n</html>")
    return "".join(parts)


def _export_html_to_pdf(parent, html, suggested_name):
    path = get_pdf_path("Paquetes_Herrajes", suggested_name)
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(path)
    doc = QTextDocument()
    doc.setHtml(html)
    doc.print(printer)
    QMessageBox.information(parent, "PDF", f"PDF generado:\n{path}")
    logger.info("PDF de paquetes de herrajes generado: %s", path)


# --- Utilidad: filtrar impresoras virtuales (PDF/XPS/OneNote/Fax, etc.) ---
def _filtrar_impresoras_fisicas(printers):
    virtual_keywords = [
        "microsoft print to pdf",
        "microsoft xps document writer",
        "onenote",
        "fax",
        "cutepdf",
        "novapdf",
        "dopdf",
        "pdfcreator",
        "bullzip",
        "snagit",
        "foxit reader",
    ]
    fisicas = []
    for p in printers:
        name = p.printerName().lower().strip()
        if any(name == k for k in virtual_keywords):
            continue
        fisicas.append(p)
    return fisicas


def _print_to_physical(parent, html, titulo):
    try:
        printers = QPrinterInfo.availablePrinters()
    except Exception:
        printers = []
        logger.warning("No se pudieron consultar impresoras disponibles")

    printers_fisicas = _filtrar_impresoras_fisicas(printers)

    if not printers_fisicas:
        QMessageBox.warning(parent, "Impresora", "No hay equipo conectado")
        return

    try:
        def_name = ""
        try:
            def_name = QPrinterInfo.defaultPrinterName()
        except Exception:
            try:
                def_name = QPrinterInfo.defaultPrinter().printerName()
            except Exception:
                def_name = ""
        nombres_fisicos = [p.printerName() for p in printers_fisicas]
        if def_name in nombres_fisicos:
            name = def_name
        else:
            name = nombres_fisicos[0]
    except Exception:
        name = printers_fisicas[0].printerName()

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setPrinterName(name)
    doc = QTextDocument()
    doc.setHtml(html)
    doc.print(printer)
    QMessageBox.information(parent, "Impresora", f"Enviado a la impresora: {name}")
    logger.info("Reporte de paquetes de herrajes enviado a impresora: %s", name)


# ---------------------- API pública ----------------------
def imprimir(parent, db):
    logger.info("Iniciando proceso de impresión")
    tipo_dialog = ReportTypeDialog(parent)
    if tipo_dialog.exec() != QDialog.DialogCode.Accepted:
        logger.info("Usuario canceló la selección de tipo de reporte")
        return
    tipo = tipo_dialog.selected_report_type()
    logger.info(f"Tipo de reporte seleccionado: {tipo}")

    destino_dialog = PrintOptionsDialog(parent)
    if destino_dialog.exec() != QDialog.DialogCode.Accepted:
        logger.info("Usuario canceló la selección de destino")
        return
    destino = destino_dialog.selected_destination()
    logger.info(f"Destino seleccionado: {destino}")

    if getattr(parent, "_print_job_thread", None) is not None:
        QMessageBox.information(parent, "Imprimir", "Ya hay una generacion de reporte en proceso.")
        return

    progress = QProgressDialog("Generando reporte...", None, 0, 100, parent)
    progress.setWindowTitle("Imprimir")
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(500)
    progress.setAutoClose(True)
    progress.setAutoReset(True)
    progress.setCancelButton(None)
    progress.setValue(0)
    progress.show()
    QApplication.processEvents()

    # Crear diccionario con info de conexión usando getattr para acceso seguro
    conn_info = {
        "db_factory": lambda server=None, database=None: type(db)(server=server, database=database),
        "server": getattr(db, 'server', ''),
        "database": getattr(db, 'database', '')
    }

    thread = QThread(parent)
    worker = ReportGenerationWorker(
        conn_info["db_factory"],
        conn_info["server"],
        conn_info["database"],
        tipo,
        destino
    )
    worker.moveToThread(thread)

    def cleanup_ui():
        try:
            if progress is not None:
                progress.close()
                progress.deleteLater()
        except Exception as e:
            logger.exception(f"Error cerrando progress dialog: {e}")
        parent._print_job_thread = None
        parent._print_job_worker = None
        parent._print_job_progress = None

    def handle_success(payload):
        try:
            logger.info(f"Reporte generado exitosamente: {payload.get('tipo')} -> {payload.get('destino')}")
            if payload["tipo"] == "General":
                if payload["destino"] == "Pantalla":
                    ScreenReportGeneral(payload["data"], parent).exec()
                elif payload["destino"] == "PDF":
                    _export_html_to_pdf(parent, payload["html"], "Paquetes_General.pdf")
                else:
                    _print_to_physical(parent, payload["html"], "Paquetes (General)")
            else:
                if payload["destino"] == "Pantalla":
                    ScreenReportDesglosado(payload["data"], parent).exec()
                elif payload["destino"] == "PDF":
                    _export_html_to_pdf(parent, payload["html"], "Paquetes_Desglosado.pdf")
                else:
                    _print_to_physical(parent, payload["html"], "Paquetes (Desglosado)")
        except Exception as e:
            QMessageBox.critical(parent, "Imprimir", f"No fue posible obtener datos o imprimir:\n{e}")
            logger.exception("Error generando o imprimiendo reporte de paquetes de herrajes")
        finally:
            cleanup_ui()

    def handle_error(message):
        try:
            logger.error(f"Error en hilo de impresión: {message}")
            QMessageBox.critical(parent, "Imprimir", f"No fue posible generar el reporte:\n{message}")
        except Exception as e:
            logger.exception(f"Error manejando error del hilo: {e}")
        finally:
            cleanup_ui()

    thread.started.connect(worker.run)
    worker.finished.connect(handle_success)
    worker.error.connect(handle_error)
    worker.finished.connect(thread.quit)
    worker.error.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    worker.error.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    parent._print_job_thread = thread
    parent._print_job_worker = worker
    parent._print_job_progress = progress
    thread.start()