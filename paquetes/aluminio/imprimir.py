# -*- coding: utf-8 -*-
"""
imprimir.py — Módulo de impresión para Paquete Aluminio
Soporta: Pantalla, PDF, Impresora
Reportes: General y Desglosado
"""
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QComboBox, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QMessageBox, QApplication, QProgressDialog
)
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrinterInfo

from common.pdf_utils import get_pdf_path
from common.logger_config import get_logger
logger = get_logger('paquetes.aluminio.imprimir')


class ReportGenerationWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, db_factory, server, db_al, db_hr, db_he, db_vi, db_pl, db_ot, tipo, destino):
        super().__init__()
        self.db_factory = db_factory
        self.server = server
        self.db_al = db_al
        self.db_hr = db_hr
        self.db_he = db_he
        self.db_vi = db_vi
        self.db_pl = db_pl
        self.db_ot = db_ot
        self.tipo = tipo
        self.destino = destino

    def run(self):
        try:
            db = self.db_factory(
                server=self.server,
                db_al=self.db_al,
                db_hr=self.db_hr,
                db_he=self.db_he,
                db_vi=self.db_vi,
                db_pl=self.db_pl,
                db_ot=self.db_ot,
            )
            if self.tipo == "General":
                paquetes = db.paquetes_al_listar()
                payload = {
                    "tipo": self.tipo,
                    "destino": self.destino,
                    "data": paquetes,
                    "html": _build_html_general(paquetes),
                }
            else:
                data = db.paquetes_al_y_items()
                payload = {
                    "tipo": self.tipo,
                    "destino": self.destino,
                    "data": data,
                    "html": _build_html_desglosado(data),
                }
            self.finished.emit(payload)
        except Exception as e:
            self.error.emit(str(e))


# -------- Diálogos de opciones --------
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


# -------- Vistas en pantalla --------
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


class ScreenReportDesglosado(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reporte: Pantalla / Desglosado")
        self.resize(950, 600)
        lay = QVBoxLayout(self)
        tbl = QTableWidget(0, 6, self)
        tbl.setHorizontalHeaderLabels(["CLAVE PAQ.", "DESCRIPCIÓN PAQ.", "TIPO", "CLAVE", "DESCRIPCIÓN", "H/V/CANT"])
        for i in range(6):
            mode = QHeaderView.ResizeMode.Stretch if i in (1, 4) else QHeaderView.ResizeMode.ResizeToContents
            tbl.horizontalHeader().setSectionResizeMode(i, mode)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        lay.addWidget(tbl)
        for p in sorted(data, key=lambda x: x.get("clave", "")):
            if not p.get("items"):
                i = tbl.rowCount()
                tbl.insertRow(i)
                tbl.setItem(i, 0, QTableWidgetItem(p.get("clave", "")))
                tbl.setItem(i, 1, QTableWidgetItem(p.get("descripcion", "")))
                tbl.setItem(i, 2, QTableWidgetItem(""))
                tbl.setItem(i, 3, QTableWidgetItem(""))
                tbl.setItem(i, 4, QTableWidgetItem(""))
                tbl.setItem(i, 5, QTableWidgetItem(""))
            else:
                for it in sorted(p["items"], key=lambda x: (x.get("tipo", ""), x.get("clave", ""))):
                    i = tbl.rowCount()
                    tbl.insertRow(i)
                    tbl.setItem(i, 0, QTableWidgetItem(p.get("clave", "")))
                    tbl.setItem(i, 1, QTableWidgetItem(p.get("descripcion", "")))
                    tbl.setItem(i, 2, QTableWidgetItem(it.get("tipo", "")))
                    tbl.setItem(i, 3, QTableWidgetItem(it.get("clave", "")))
                    tbl.setItem(i, 4, QTableWidgetItem(it.get("descripcion", "")))
                    if it.get("tipo") == "AL":
                        hv = f"H:{it.get('horizontal', 0)}  V:{it.get('vertical', 0)}"
                    else:
                        hv = f"CANT:{it.get('cantidad', 0)}"
                    tbl.setItem(i, 5, QTableWidgetItem(hv))


# -------- HTML helpers --------
def _build_html_general(paquetes):
    rows = "\n".join(
        f"<tr><td>{p.get('clave', '')}</td><td>{p.get('descripcion', '')}</td></tr>"
        for p in sorted(paquetes, key=lambda x: x.get('clave', ''))
    )
    return f"""
<html>
<head><title>Paquetes de Aluminio (General)</title></head>
<body>
<h2>Paquetes de Aluminio (General)</h2>
<table border="1">
<tr><th>CLAVE</th><th>DESCRIPCIÓN</th></tr>
{rows}
</table>
</body>
</html>
""".strip()


def _build_html_desglosado(data):
    parts = ["<html><head><title>Paquetes de Aluminio (Desglosado)</title></head><body>"]
    parts.append("<h2>Paquetes de Aluminio (Desglosado)</h2>")
    for p in sorted(data, key=lambda x: x.get("clave", "")):
        parts.append(f"<h3>Paquete: {p.get('clave', '')} – {p.get('descripcion', '')}</h3>")
        if not p.get("items"):
            parts.append("<p>Sin items</p>")
            continue
        parts.append("<table border='1'><tr><th>TIPO</th><th>CLAVE</th><th>DESCRIPCIÓN</th><th>H</th><th>V</th><th>CANT</th></tr>")
        for it in sorted(p.get("items", []), key=lambda x: (x.get("tipo", ""), x.get("clave", ""))):
            if it.get("tipo") == "AL":
                hv = f"{it.get('horizontal', 0)} / {it.get('vertical', 0)}"
            else:
                hv = f"{it.get('cantidad', 0)}"
            parts.append(f"<tr><td>{it.get('tipo', '')}</td><td>{it.get('clave', '')}</td><td>{it.get('descripcion', '')}</td><td colspan='3'>{hv}</td></tr>")
        parts.append("</table>")
    parts.append("</body></html>")
    return "".join(parts)


def _export_html_to_pdf(parent, html, suggested_name):
    path = get_pdf_path("Paquetes_Aluminio", suggested_name)
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(path)
    doc = QTextDocument()
    doc.setHtml(html)
    doc.print(printer)
    QMessageBox.information(parent, "PDF", f"PDF generado:\n{path}")


def _filtrar_impresoras_fisicas(printers):
    virtual = ["pdf", "xps", "onenote", "fax", "writer", "microsoft print to pdf",
               "cutepdf", "novapdf", "dopdf", "pdfcreator", "bullzip", "snagit", "foxit"]
    fis = []
    for p in printers:
        name = p.printerName().lower()
        if any(k in name for k in virtual):
            continue
        fis.append(p)
    return fis


def _print_to_physical(parent, html, titulo):
    try:
        printers = QPrinterInfo.availablePrinters()
    except Exception:
        printers = []
    fis = _filtrar_impresoras_fisicas(printers)
    if not fis:
        QMessageBox.warning(parent, "Impresora", "No hay equipo conectado")
        try:
            if hasattr(parent, "Inicio"):
                parent.Inicio()
        except Exception:
            pass
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
        nombres = [p.printerName() for p in fis]
        name = def_name if def_name in nombres else nombres[0]
    except Exception:
        name = fis[0].printerName()

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setPrinterName(name)
    doc = QTextDocument()
    doc.setHtml(html)
    doc.print(printer)
    QMessageBox.information(parent, "Impresora", f"Enviado a la impresora: {name}")


# -------- API pública --------
def imprimir(parent, db):
    tipo_dialog = ReportTypeDialog(parent)
    if tipo_dialog.exec() != QDialog.DialogCode.Accepted:
        return
    tipo = tipo_dialog.selected_report_type()

    destino_dialog = PrintOptionsDialog(parent)
    if destino_dialog.exec() != QDialog.DialogCode.Accepted:
        return
    destino = destino_dialog.selected_destination()

    if getattr(parent, "_print_job_thread", None) is not None:
        QMessageBox.information(parent, "Imprimir", "Ya hay una generación de reporte en proceso.")
        return

    progress = QProgressDialog("Generando reporte...", None, 0, 0, parent)
    progress.setWindowTitle("Imprimir")
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setAutoClose(False)
    progress.setAutoReset(False)
    progress.setCancelButton(None)
    progress.setValue(0)
    progress.show()
    QApplication.processEvents()

    thread = QThread(parent)
    worker = ReportGenerationWorker(
        db.__class__, db.server, db.db_al, db.db_hr, db.db_he, db.db_vi, db.db_pl, db.db_ot, tipo, destino
    )
    worker.moveToThread(thread)

    def cleanup_ui():
        try:
            progress.close()
            progress.deleteLater()
        except Exception:
            pass
        parent._print_job_thread = None
        parent._print_job_worker = None
        parent._print_job_progress = None

    def handle_success(payload):
        try:
            if payload["tipo"] == "General":
                if payload["destino"] == "Pantalla":
                    ScreenReportGeneral(payload["data"], parent).exec()
                elif payload["destino"] == "PDF":
                    _export_html_to_pdf(parent, payload["html"], "Paquetes_Aluminio_General.pdf")
                else:
                    _print_to_physical(parent, payload["html"], "Paquetes de Aluminio (General)")
            else:
                if payload["destino"] == "Pantalla":
                    ScreenReportDesglosado(payload["data"], parent).exec()
                elif payload["destino"] == "PDF":
                    _export_html_to_pdf(parent, payload["html"], "Paquetes_Aluminio_Desglosado.pdf")
                else:
                    _print_to_physical(parent, payload["html"], "Paquetes de Aluminio (Desglosado)")
        except Exception as e:
            QMessageBox.critical(parent, "Imprimir", f"No fue posible obtener datos o imprimir:\n{e}")
        finally:
            cleanup_ui()

    def handle_error(message):
        try:
            QMessageBox.critical(parent, "Imprimir", f"No fue posible obtener datos o imprimir:\n{message}")
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