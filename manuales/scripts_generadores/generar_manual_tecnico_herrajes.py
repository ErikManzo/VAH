# D:\vah\manuales\scripts_generadores\generar_manual_tecnico_herrajes.py
# -*- coding: utf-8 -*-
"""
Generador de Manual Técnico - Módulo Herrajes VAH
==================================================
Genera un PDF profesional con:
  - Arquitectura del módulo
  - Esquema de base de datos
  - Diagramas de flujo
  - Documentación de código
  - Dependencias y configuración
"""

import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    Paragraph, Spacer, Image, PageBreak,
    Table, TableStyle, ListFlowable, ListItem,
)

# ==================== CONFIGURACIÓN ====================
MODULO = "Herrajes"
TIPO_MANUAL = "Técnico"
RUTA_BASE = r"D:\vah\manuales"
RUTA_IMAGENES = os.path.join(RUTA_BASE, "imagenes", "herrajes")
RUTA_COMUNES = os.path.join(RUTA_BASE, "imagenes", "comunes")
RUTA_PDF = os.path.join(RUTA_BASE, "pdf")
RUTA_LOGO = os.path.join(RUTA_COMUNES, "logo_vah.png")

COLOR_AZUL = HexColor("#1f6feb")
COLOR_AZUL_OSCURO = HexColor("#1557b0")
COLOR_GRIS_CLARO = HexColor("#f0f4f8")
COLOR_GRIS_TEXTO = HexColor("#374151")

TAMANO_PAGINA = letter
ANCHO, ALTO = TAMANO_PAGINA
MARGEN_IZQ = 20 * mm
MARGEN_DER = 20 * mm
MARGEN_SUP = 25 * mm
MARGEN_INF = 25 * mm

FECHA_GENERACION = datetime.datetime.now().strftime("%d/%m/%Y")
VERSION = "1.0"

# ==================== IMPORTAR CLASES BASE ====================
import sys

sys.path.insert(0, os.path.dirname(__file__))

from generar_manual_operativo_herrajes import (
    PlantillaPagina, DocManual,
    _imagen, _tabla, _lista, _nota, _codigo, _ancla,
)

# ==================== ESTILOS ====================
estilos = getSampleStyleSheet()

estilo_titulo_principal = ParagraphStyle(
    'TituloPrincipalTec',
    parent=estilos['Title'],
    fontName='Helvetica-Bold',
    fontSize=26,
    textColor=COLOR_AZUL,
    spaceAfter=6 * mm,
    alignment=TA_LEFT,
)

estilo_heading1 = ParagraphStyle(
    'Heading1Tec',
    parent=estilos['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=20,
    textColor=COLOR_AZUL,
    spaceBefore=12 * mm,
    spaceAfter=6 * mm,
)

estilo_heading2 = ParagraphStyle(
    'Heading2Tec',
    parent=estilos['Heading2'],
    fontName='Helvetica-Bold',
    fontSize=16,
    textColor=COLOR_AZUL_OSCURO,
    spaceBefore=10 * mm,
    spaceAfter=4 * mm,
)

estilo_heading3 = ParagraphStyle(
    'Heading3Tec',
    parent=estilos['Heading3'],
    fontName='Helvetica-Bold',
    fontSize=13,
    textColor=COLOR_GRIS_TEXTO,
    spaceBefore=8 * mm,
    spaceAfter=3 * mm,
)

estilo_normal = ParagraphStyle(
    'NormalTec',
    parent=estilos['Normal'],
    fontName='Helvetica',
    fontSize=10,
    leading=14,
    textColor=COLOR_GRIS_TEXTO,
    alignment=TA_JUSTIFY,
    spaceAfter=4 * mm,
)

estilo_codigo = ParagraphStyle(
    'CodigoTec',
    parent=estilos['Code'],
    fontName='Courier',
    fontSize=8,
    leading=10,
    backColor=COLOR_GRIS_CLARO,
    borderColor=HexColor("#cfd8e3"),
    borderWidth=0.5,
    borderPadding=6,
    leftIndent=5 * mm,
    rightIndent=5 * mm,
)

estilo_nota = ParagraphStyle(
    'NotaTec',
    parent=estilo_normal,
    fontName='Helvetica-Oblique',
    fontSize=9,
    textColor=HexColor("#6b7280"),
    leftIndent=5 * mm,
    rightIndent=5 * mm,
    borderColor=HexColor("#cfd8e3"),
    borderWidth=0.5,
    borderPadding=8,
    backColor=COLOR_GRIS_CLARO,
)

estilo_pie = ParagraphStyle(
    'PiePaginaTec',
    fontName='Helvetica',
    fontSize=7,
    textColor=HexColor("#9ca3af"),
    alignment=TA_CENTER,
)

estilo_indice_link = ParagraphStyle(
    'IndiceLinkTec',
    parent=estilo_normal,
    textColor=COLOR_AZUL,
    underline=True,
)


def generar_manual_tecnico():
    """Genera el PDF del manual técnico."""

    os.makedirs(RUTA_PDF, exist_ok=True)
    ruta_salida = os.path.join(RUTA_PDF, f"VAH_Manual_Tecnico_{MODULO}.pdf")

    doc = DocManual(ruta_salida, TIPO_MANUAL, MODULO, RUTA_LOGO)
    historia = []

    # ============== PORTADA ==============
    historia.append(Spacer(1, 40 * mm))

    if os.path.exists(RUTA_LOGO):
        historia.append(Image(RUTA_LOGO, width=60 * mm, height=60 * mm))
        historia.append(Spacer(1, 10 * mm))

    historia.append(Paragraph(
        f"Manual {TIPO_MANUAL}<br/>Módulo {MODULO}",
        estilo_titulo_principal
    ))
    historia.append(Spacer(1, 8 * mm))
    historia.append(Paragraph(
        f"Versión {VERSION} | {FECHA_GENERACION}",
        ParagraphStyle('InfoPortadaTec', parent=estilo_normal, fontSize=12, textColor=COLOR_GRIS_TEXTO)
    ))
    historia.append(Spacer(1, 10 * mm))
    historia.append(Paragraph(
        "Documentación técnica para desarrolladores y administradores del sistema.<br/>"
        "Arquitectura, base de datos, dependencias y procesos internos.",
        estilo_normal
    ))
    historia.append(PageBreak())

    # ============== ÍNDICE ==============
    historia.append(Paragraph("Índice de Contenido", estilo_heading1))
    historia.append(Spacer(1, 5 * mm))

    secciones_indice = [
        ("1.", "Arquitectura del Sistema", "arquitectura"),
        ("2.", "Estructura de Archivos", "estructura"),
        ("3.", "Base de Datos", "basedatos"),
        ("  3.1", "Esquema de la Tabla", "bd-esquema"),
        ("  3.2", "Procedimientos SQL", "bd-sql"),
        ("4.", "Dependencias", "dependencias"),
        ("5.", "Módulos y Clases Principales", "modulos"),
        ("  5.1", "pantalla_herrajes.py", "mod-pantalla"),
        ("  5.2", "db_manager.py", "mod-db"),
        ("  5.3", "Parsers de Importación", "mod-parsers"),
        ("  5.4", "ventana_divisora.py", "mod-divisora"),
        ("  5.5", "imprimir.py", "mod-imprimir"),
        ("  5.6", "utils.py", "mod-utils"),
        ("6.", "Flujo de Importación", "flujo"),
        ("7.", "Hilos y Concurrencia", "hilos"),
        ("8.", "Manejo de Errores", "errores"),
        ("9.", "Configuración y Personalización", "configuracion"),
    ]

    datos_indice = [["#", "Sección"]]
    for num, titulo, ancla in secciones_indice:
        datos_indice.append([
            num,
            Paragraph(f'<a href="#{ancla}" color="#1f6feb">{titulo}</a>', estilo_indice_link),
        ])

    historia.append(_tabla(datos_indice, anchos=[15 * mm, 141 * mm]))
    historia.append(PageBreak())

    # ============== 1. ARQUITECTURA ==============
    historia.append(_ancla("arquitectura"))
    historia.append(Paragraph("1. Arquitectura del Sistema", estilo_heading1))
    historia.append(Paragraph(
        "El Módulo de Herrajes sigue una arquitectura de <b>tres capas</b> dentro del ecosistema ERP VAH:",
        estilo_normal
    ))
    historia.append(_imagen("arquitectura_sistema.png", ancho=160 * mm))
    historia.append(Spacer(1, 5 * mm))

    datos_arquitectura = [
        ["Capa", "Tecnología", "Responsabilidad"],
        ["Presentación", "PyQt6", "Interfaz gráfica, validación de entrada, UX"],
        ["Lógica de Negocio", "Python 3.12", "Parsers, cálculos de precios, workers, PDFs"],
        ["Acceso a Datos", "pyodbc + SQL Server", "ODBC, CRUD, MERGE masivo, transacciones"],
        ["Almacenamiento", "SQL Server", "Tabla materiales_herraje"],
    ]
    historia.append(_tabla(datos_arquitectura, anchos=[35 * mm, 35 * mm, 86 * mm]))
    historia.append(PageBreak())

    # ============== 2. ESTRUCTURA DE ARCHIVOS ==============
    historia.append(_ancla("estructura"))
    historia.append(Paragraph("2. Estructura de Archivos", estilo_heading1))
    historia.append(_imagen("estructura_modulos.png", ancho=140 * mm))
    historia.append(Spacer(1, 5 * mm))

    datos_archivos = [
        ["Archivo", "Tipo", "Descripción"],
        ["pantalla_herrajes.py", "Principal", "UI principal, worker de importación, diálogos"],
        ["db_manager.py", "Datos", "DBManager: conexión, CRUD, bulk upsert con MERGE"],
        ["imprimir.py", "Utilidad", "PDF con ReportLab (catálogo de materiales)"],
        ["utils.py", "Utilidad", "dec2, detección columnas, ordenamiento"],
        ["ventana_divisora.py", "Interfaz", "Diálogo para cantidad divisora en importación"],
        ["parsers/__init__.py", "Paquete", "Re-exporta parsers"],
        ["parsers/parse_csv.py", "Parser", "CSV genérico"],
        ["parsers/parse_excel_herralum.py", "Parser", "Herralum: detección, precio unitario, factor RL"],
        ["parsers/parse_excel_profilo.py", "Parser", "Profilo: columnas fijas, limpieza precios"],
    ]
    historia.append(_tabla(datos_archivos, anchos=[50 * mm, 20 * mm, 86 * mm]))
    historia.append(PageBreak())

    # ============== 3. BASE DE DATOS ==============
    historia.append(_ancla("basedatos"))
    historia.append(Paragraph("3. Base de Datos", estilo_heading1))

    historia.append(_ancla("bd-esquema"))
    historia.append(Paragraph("3.1 Esquema de la Tabla", estilo_heading2))
    historia.append(_imagen("diagrama_bd.png", ancho=140 * mm))
    historia.append(Spacer(1, 5 * mm))

    datos_esquema = [
        ["Columna", "Tipo", "Restricciones", "Descripción"],
        ["Clave", "VARCHAR(20)", "PK, NOT NULL", "Código único del producto"],
        ["Descripcion", "VARCHAR(100)", "NULL", "Nombre del herraje"],
        ["Precio", "DECIMAL(10,2)", "NULL", "Precio unitario (2 decimales)"],
    ]
    historia.append(_tabla(datos_esquema, anchos=[30 * mm, 28 * mm, 30 * mm, 68 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_codigo(
        "CREATE TABLE dbo.materiales_herraje (\n"
        "    Clave       VARCHAR(20)   NOT NULL PRIMARY KEY,\n"
        "    Descripcion VARCHAR(100)  NULL,\n"
        "    Precio      DECIMAL(10,2) NULL\n"
        ");"
    ))

    historia.append(_ancla("bd-sql"))
    historia.append(Paragraph("3.2 Procedimientos SQL Principales", estilo_heading2))
    historia.append(Paragraph(
        "El módulo usa SQL dinámico desde Python vía pyodbc. "
        "Operación principal: <b>MERGE masivo</b> con tabla temporal:",
        estilo_normal
    ))
    historia.append(_codigo(
        "MERGE dbo.materiales_herraje AS T\n"
        "USING #imp2 AS S ON T.Clave = S.Clave\n"
        "WHEN MATCHED THEN\n"
        "  UPDATE SET\n"
        "    T.Descripcion = CASE WHEN S.Descripcion IS NOT NULL\n"
        "      THEN S.Descripcion ELSE T.Descripcion END,\n"
        "    T.Precio = CASE\n"
        "      WHEN T.Precio IS NULL THEN S.Precio\n"
        "      WHEN S.Precio > T.Precio THEN S.Precio\n"
        "      ELSE T.Precio END\n"
        "WHEN NOT MATCHED BY TARGET THEN\n"
        "  INSERT (Clave, Descripcion, Precio)\n"
        "  VALUES (S.Clave, S.Descripcion, S.Precio);"
    ))
    historia.append(PageBreak())

    # ============== 4. DEPENDENCIAS ==============
    historia.append(_ancla("dependencias"))
    historia.append(Paragraph("4. Dependencias", estilo_heading1))

    datos_deps = [
        ["Librería", "Versión", "Uso"],
        ["PyQt6", "6.5+", "Interfaz gráfica (widgets, hilos, señales)"],
        ["pandas", "1.5+", "Lectura/procesamiento Excel/CSV"],
        ["pyodbc", "4.0+", "Conexión ODBC a SQL Server"],
        ["openpyxl", "3.0+", "Motor lectura .xlsx"],
        ["reportlab", "3.6+", "Generación PDFs"],
        ["Python", "3.10+", "Lenguaje base"],
    ]
    historia.append(_tabla(datos_deps, anchos=[35 * mm, 25 * mm, 96 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_codigo("pip install PyQt6 pandas pyodbc openpyxl reportlab"))
    historia.append(PageBreak())

    # ============== 5. MÓDULOS PRINCIPALES ==============
    historia.append(_ancla("modulos"))
    historia.append(Paragraph("5. Módulos y Clases Principales", estilo_heading1))

    # 5.1 pantalla_herrajes.py
    historia.append(_ancla("mod-pantalla"))
    historia.append(Paragraph("5.1 pantalla_herrajes.py", estilo_heading2))

    datos_clases = [
        ["Clase", "Tipo", "Descripción"],
        ["PantallaHerrajes", "QMainWindow", "Ventana principal, lógica UI"],
        ["ImportDialog", "QDialog", "Configuración importación (hojas, mapeo)"],
        ["ImportWorker", "QObject", "Worker asíncrono en QThread"],
        ["UpperLineEdit", "QLineEdit", "Fuerza mayúsculas"],
        ["NavLineEdit", "UpperLineEdit", "Enter = Tab"],
    ]
    historia.append(_tabla(datos_clases, anchos=[40 * mm, 25 * mm, 91 * mm]))

    # 5.2 db_manager.py
    historia.append(_ancla("mod-db"))
    historia.append(Paragraph("5.2 db_manager.py", estilo_heading2))
    historia.append(_lista([
        "<b>listar_todos()</b> → SELECT * ORDER BY Clave",
        "<b>buscar(texto)</b> → LIKE en Clave y Descripcion",
        "<b>insertar_o_actualizar(reg)</b> → UPSERT simple",
        "<b>bulk_upsert_max_precio(lista)</b> → MERGE masivo con tabla temporal",
    ]))

    # 5.3 Parsers
    historia.append(_ancla("mod-parsers"))
    historia.append(Paragraph("5.3 Parsers de Importación", estilo_heading2))

    datos_parsers = [
        ["Parser", "Proveedor", "Características"],
        ["parse_excel_herralum.py", "Herralum", "Auto-detección encabezados, mapeo configurable, "
                                                "cálculo precio unitario (PZ,CJ,CT,ML,RL), extracción factor RL"],
        ["parse_excel_profilo.py", "Profilo", "Columnas fijas (2,3,5), limpieza precios ($, comas)"],
        ["parse_csv.py", "Genérico", "CSV: clave, descripcion, precio"],
    ]
    historia.append(_tabla(datos_parsers, anchos=[45 * mm, 25 * mm, 86 * mm]))

    # 5.4 ventana_divisora.py
    historia.append(_ancla("mod-divisora"))
    historia.append(Paragraph("5.4 ventana_divisora.py", estilo_heading2))
    historia.append(Paragraph(
        "QDialog que se abre durante la importación para registros con precio_invalido_o_cero. "
        "Fórmula: <b>Precio Unitario = Precio Original / Cantidad Divisora</b>",
        estilo_normal
    ))

    # 5.5 imprimir.py
    historia.append(_ancla("mod-imprimir"))
    historia.append(Paragraph("5.5 imprimir.py", estilo_heading2))
    historia.append(Paragraph(
        "Usa <b>ReportLab</b> para generar PDF tamaño Carta con encabezados repetidos, "
        "columnas CLAVE/DESCRIPCIÓN/PRECIO y pie numerado.",
        estilo_normal
    ))

    # 5.6 utils.py
    historia.append(_ancla("mod-utils"))
    historia.append(Paragraph("5.6 utils.py", estilo_heading2))
    historia.append(_lista([
        "<b>dec2(valor)</b> → Decimal con 2 decimales",
        "<b>detectar_columnas_excel(df, headers)</b> → Auto-detección por nombre y scores de contenido",
    ]))
    historia.append(PageBreak())

    # ============== 6. FLUJO DE IMPORTACIÓN ==============
    historia.append(_ancla("flujo"))
    historia.append(Paragraph("6. Flujo de Importación", estilo_heading1))
    historia.append(_imagen("flujo_importacion.png", ancho=160 * mm))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph("<b>Secuencia:</b>", estilo_normal))
    historia.append(_lista([
        "1. Usuario selecciona archivo (QFileDialog)",
        "2. Si Excel → ImportDialog (hojas + mapeo columnas)",
        "3. Se crea ImportWorker → QThread",
        "4. Sniff proveedor por valores UM",
        "5. Parser → (validos, rechazados)",
        "6. Deduplicación origen (Counter, colapso precio máx)",
        "7. bulk_upsert_max_precio() → MERGE SQL",
        "8. Si rechazados precio_invalido_o_cero → VentanaDivisora",
        "9. Resultados ventana → insertar_o_actualizar()",
        "10. Mensaje final con resumen + RL pendientes",
    ]))
    historia.append(PageBreak())

    # ============== 7. HILOS Y CONCURRENCIA ==============
    historia.append(_ancla("hilos"))
    historia.append(Paragraph("7. Hilos y Concurrencia", estilo_heading1))
    historia.append(_codigo(
        "self._import_thread = QThread(self)\n"
        "self._import_worker = ImportWorker(...)\n"
        "self._import_worker.moveToThread(self._import_thread)\n"
        "\n"
        "self._import_thread.started.connect(self._import_worker.run)\n"
        "self._import_worker.progress.connect(progress.setValue)\n"
        "self._import_worker.status.connect(progress.setLabelText)\n"
        "self._import_worker.finished.connect(_ok)\n"
        "self._import_worker.error.connect(_fail)\n"
        "\n"
        "self._import_thread.start()"
    ))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph(
        "La UI se bloquea con <b>_set_controles_habilitados(False)</b> y se libera en <b>_cleanup()</b>.",
        estilo_normal
    ))
    historia.append(PageBreak())

    # ============== 8. MANEJO DE ERRORES ==============
    historia.append(_ancla("errores"))
    historia.append(Paragraph("8. Manejo de Errores", estilo_heading1))

    datos_errores = [
        ["Nivel", "Mecanismo", "Ejemplo"],
        ["Validación UI", "QDoubleValidator, comprobaciones", "Precio inválido → QMessageBox.warning"],
        ["Parsers", "try/except por registro", "precio_invalido_o_cero, clave_larga"],
        ["BD", "try/except operaciones", "Error conexión → QMessageBox.critical"],
        ["Worker", "error.emit(str)", "Excepción en hilo → UI"],
        ["Logs", "CSV rechazados", "D:\\vah\\logs\\rechazados_*.csv"],
    ]
    historia.append(_tabla(datos_errores, anchos=[30 * mm, 50 * mm, 76 * mm]))
    historia.append(PageBreak())

    # ============== 9. CONFIGURACIÓN ==============
    historia.append(_ancla("configuracion"))
    historia.append(Paragraph("9. Configuración y Personalización", estilo_heading1))
    historia.append(Paragraph("<b>Conexión (db_manager.py):</b>", estilo_normal))
    historia.append(_codigo(
        'server = r"DESKTOP-AE60PIU\\SQLEXPRESS"\n'
        'database = "herrajes"\n'
        'table = "dbo.materiales_herraje"\n'
        'DRIVER={ODBC Driver 18 for SQL Server};\n'
        'Trusted_Connection=yes;'
    ))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph("<b>Mapeo columnas persistente:</b>", estilo_normal))
    historia.append(_codigo(
        "# D:\\vah\\logs\\herrajes_column_mapping.json\n"
        '{\n'
        '  "archivo.xlsx": {\n'
        '    "sheets": ["Hoja1"],\n'
        '    "mapping": {"clave":"Parte","descripcion":"Descripción",...}\n'
        '  }\n'
        '}'
    ))
    historia.append(Spacer(1, 10 * mm))

    # Cierre
    historia.append(Paragraph(
        "— Fin del Manual Técnico —",
        ParagraphStyle('CierreTec', parent=estilo_normal, alignment=TA_CENTER,
                       textColor=COLOR_AZUL, fontSize=12)
    ))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph(
        f"Documento generado el {FECHA_GENERACION} | Versión {VERSION}",
        estilo_pie
    ))
    historia.append(Paragraph(
        "VAH ERP © Todos los derechos reservados",
        estilo_pie
    ))

    # ==================== CONSTRUIR PDF ====================
    doc.build(historia)
    print(f"✅ Manual Técnico generado: {ruta_salida}")
    return ruta_salida


if __name__ == "__main__":
    generar_manual_tecnico()