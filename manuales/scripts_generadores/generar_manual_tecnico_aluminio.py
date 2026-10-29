# D:\vah\manuales\scripts_generadores\generar_manual_tecnico_aluminio.py
# -*- coding: utf-8 -*-
"""
Generador de Manual Técnico - Módulo Materiales Aluminio VAH
============================================================
"""

import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Paragraph, Spacer, Image, PageBreak, Table, TableStyle, ListFlowable, ListItem

# ==================== CONFIGURACIÓN ====================
MODULO = "Aluminio"
TIPO_MANUAL = "Técnico"
RUTA_BASE = r"D:\vah\manuales"
RUTA_IMAGENES = os.path.join(RUTA_BASE, "imagenes", "aluminio")
RUTA_COMUNES = os.path.join(RUTA_BASE, "imagenes", "comunes")
RUTA_PDF = os.path.join(RUTA_BASE, "pdf", "técnico")
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

# ==================== ESTILOS ====================
estilos = getSampleStyleSheet()

estilo_normal = ParagraphStyle(
    'Normal',
    parent=estilos['Normal'],
    fontName='Helvetica',
    fontSize=10,
    leading=14,
    textColor=COLOR_GRIS_TEXTO,
    alignment=TA_JUSTIFY,
    spaceAfter=4 * mm,
)

estilo_heading1 = ParagraphStyle(
    'Heading1',
    parent=estilos['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=20,
    textColor=COLOR_AZUL,
    spaceBefore=12 * mm,
    spaceAfter=6 * mm,
)

estilo_heading2 = ParagraphStyle(
    'Heading2',
    parent=estilos['Heading2'],
    fontName='Helvetica-Bold',
    fontSize=16,
    textColor=COLOR_AZUL_OSCURO,
    spaceBefore=10 * mm,
    spaceAfter=4 * mm,
)

estilo_heading3 = ParagraphStyle(
    'Heading3',
    parent=estilos['Heading3'],
    fontName='Helvetica-Bold',
    fontSize=13,
    textColor=COLOR_GRIS_TEXTO,
    spaceBefore=8 * mm,
    spaceAfter=3 * mm,
)

estilo_codigo = ParagraphStyle(
    'Code',
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

estilo_pie = ParagraphStyle(
    'Pie',
    fontName='Helvetica',
    fontSize=7,
    textColor=HexColor("#9ca3af"),
    alignment=TA_CENTER,
)

estilo_indice_link = ParagraphStyle(
    'IndiceLink',
    parent=estilo_normal,
    textColor=COLOR_AZUL,
    underline=True,
)

estilo_bullet = ParagraphStyle(
    'Bullet',
    parent=estilo_normal,
    bulletIndent=10 * mm,
    leftIndent=20 * mm,
    spaceBefore=1 * mm,
    spaceAfter=1 * mm,
)

estilo_ancla = ParagraphStyle('Ancla', fontSize=0, leading=0)


# ==================== FUNCIONES AUXILIARES ====================

def _imagen(nombre_archivo, ancho=None, alto=None):
    ruta = os.path.join(RUTA_IMAGENES, nombre_archivo)
    if os.path.exists(ruta):
        if ancho and alto:
            return Image(ruta, width=ancho, height=alto)
        elif ancho:
            return Image(ruta, width=ancho, height=ancho * 0.5625)
        else:
            return Image(ruta, width=150 * mm, height=100 * mm)
    else:
        return Paragraph(f"<i>[Imagen pendiente: {nombre_archivo}]</i>", estilo_normal)


def _tabla(datos, anchos=None, encabezado=True):
    estilo_tabla = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_AZUL if encabezado else (1, 1, 1)),
        ('TEXTCOLOR', (0, 0), (-1, 0), (1, 1, 1) if encabezado else (0, 0, 0)),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#cfd8e3")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#ffffff"), COLOR_GRIS_CLARO]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ])
    t = Table(datos, colWidths=anchos)
    t.setStyle(estilo_tabla)
    return t


def _lista(items):
    return ListFlowable(
        [ListItem(Paragraph(item, estilo_bullet)) for item in items],
        bulletType='bullet',
        start='•',
        bulletFontName='Helvetica',
        bulletFontSize=10,
        bulletOffsetY=-1,
    )


def _codigo(texto):
    return Paragraph(texto.replace('\n', '<br/>').replace(' ', '&nbsp;'), estilo_codigo)


def _ancla(nombre):
    return Paragraph(f'<a name="{nombre}"/>', estilo_ancla)


# ==================== PLANTILLA DE PÁGINA ====================

class PlantillaPagina:
    def __init__(self, parent_doc, tipo_manual, modulo, logo_path):
        self.tipo_manual = tipo_manual
        self.modulo = modulo
        self.logo_path = logo_path

    def beforeDrawPage(self, canv, doc):
        canv.saveState()
        if os.path.exists(self.logo_path):
            try:
                logo_w = 120 * mm
                logo_h = 120 * mm
                x_centro = (ANCHO - logo_w) / 2
                y_centro = (ALTO - logo_h) / 2
                canv.setFillAlpha(0.07)
                canv.drawImage(self.logo_path, x_centro, y_centro, width=logo_w, height=logo_h, mask='auto')
                canv.setFillAlpha(1.0)
            except Exception:
                pass
        canv.setFont('Helvetica-Bold', 8)
        canv.setFillColor(COLOR_AZUL)
        canv.drawString(MARGEN_IZQ, ALTO - 12 * mm, f"VAH - Manual {self.tipo_manual} - {self.modulo}")
        canv.setStrokeColor(COLOR_AZUL)
        canv.setLineWidth(1)
        canv.line(MARGEN_IZQ, ALTO - 14 * mm, ANCHO - MARGEN_DER, ALTO - 14 * mm)
        canv.setFont('Helvetica', 7)
        canv.setFillColor(HexColor("#9ca3af"))
        n_pagina = canv.getPageNumber()
        canv.drawCentredString(ANCHO / 2, 12 * mm, f"Página {n_pagina}")
        canv.drawString(MARGEN_IZQ, 12 * mm, f"Versión {VERSION}")
        canv.drawRightString(ANCHO - MARGEN_DER, 12 * mm, FECHA_GENERACION)
        canv.setStrokeColor(HexColor("#cfd8e3"))
        canv.setLineWidth(0.5)
        canv.line(MARGEN_IZQ, 18 * mm, ANCHO - MARGEN_DER, 18 * mm)
        canv.restoreState()


# ==================== DOCUMENTO PRINCIPAL ====================

class DocManual:
    def __init__(self, filename, tipo_manual, modulo, logo_path):
        self.filename = filename
        self.tipo_manual = tipo_manual
        self.modulo = modulo
        self.logo_path = logo_path

    def build(self, story):
        from reportlab.platypus import SimpleDocTemplate
        from reportlab.platypus.doctemplate import PageTemplate
        from reportlab.platypus.frames import Frame

        doc = SimpleDocTemplate(
            self.filename,
            pagesize=TAMANO_PAGINA,
            title=f"VAH Manual {self.tipo_manual} - {self.modulo}",
            author="VAH ERP",
            subject=f"Manual {self.tipo_manual} del módulo {self.modulo}",
        )

        frame = Frame(MARGEN_IZQ, MARGEN_INF, ANCHO - MARGEN_IZQ - MARGEN_DER, ALTO - MARGEN_SUP - MARGEN_INF,
                      id='normal')

        def _beforeDraw(canv, _):
            plantilla = PlantillaPagina(doc, self.tipo_manual, self.modulo, self.logo_path)
            plantilla.beforeDrawPage(canv, doc)

        doc.build(story, onFirstPage=_beforeDraw, onLaterPages=_beforeDraw)


# ==================== CONTENIDO ====================

def generar_manual_tecnico():
    os.makedirs(RUTA_PDF, exist_ok=True)
    ruta_salida = os.path.join(RUTA_PDF, f"VAH_Manual_Tecnico_{MODULO}.pdf")
    doc = DocManual(ruta_salida, TIPO_MANUAL, MODULO, RUTA_LOGO)
    historia = []

    # PORTADA
    historia.append(Spacer(1, 40 * mm))
    if os.path.exists(RUTA_LOGO):
        historia.append(Image(RUTA_LOGO, width=60 * mm, height=60 * mm))
        historia.append(Spacer(1, 10 * mm))
    historia.append(Paragraph(f"Manual {TIPO_MANUAL}<br/>Módulo {MODULO}",
                              ParagraphStyle('TituloPortada', parent=estilos['Title'], fontSize=26,
                                             textColor=COLOR_AZUL, alignment=TA_CENTER)))
    historia.append(Spacer(1, 8 * mm))
    historia.append(Paragraph(f"Versión {VERSION} | {FECHA_GENERACION}",
                              ParagraphStyle('InfoPortada', parent=estilo_normal, fontSize=12,
                                             textColor=COLOR_GRIS_TEXTO, alignment=TA_CENTER)))
    historia.append(Spacer(1, 10 * mm))
    historia.append(
        Paragraph("Documentación técnica para desarrolladores y administradores del sistema.", estilo_normal))
    historia.append(PageBreak())

    # ÍNDICE
    historia.append(Paragraph("Índice de Contenido", estilo_heading1))
    historia.append(Spacer(1, 5 * mm))

    secciones = [
        ("1.", "Arquitectura del Sistema", "arquitectura"),
        ("2.", "Estructura de Archivos", "estructura"),
        ("3.", "Base de Datos", "basedatos"),
        ("  3.1", "Esquema de la Tabla", "bd-esquema"),
        ("  3.2", "Campos de Precio", "bd-campos"),
        ("  3.3", "Relaciones", "bd-relaciones"),
        ("4.", "Dependencias", "dependencias"),
        ("5.", "Módulos y Clases Principales", "modulos"),
        ("  5.1", "DBManager", "modulo-dbmanager"),
        ("  5.2", "PantallaMaterialesAluminio", "modulo-pantalla"),
        ("  5.3", "Parsers", "modulo-parsers"),
        ("6.", "Flujo de Datos", "flujo"),
        ("  6.1", "Guardado Manual", "flujo-guardar"),
        ("  6.2", "Importación", "flujo-importar"),
        ("  6.3", "Edición", "flujo-editar"),
        ("7.", "Manejo de Errores", "errores"),
        ("8.", "Logging y Depuración", "logging"),
        ("9.", "Configuración", "configuracion"),
        ("10.", "Formatos de Importación", "formatos"),
    ]

    datos_indice = [["#", "Sección"]]
    for num, titulo, ancla in secciones:
        datos_indice.append([num, Paragraph(f'<a href="#{ancla}" color="#1f6feb">{titulo}</a>', estilo_indice_link)])
    historia.append(_tabla(datos_indice, anchos=[15 * mm, 141 * mm]))
    historia.append(PageBreak())

    # 1. ARQUITECTURA
    historia.append(_ancla("arquitectura"))
    historia.append(Paragraph("1. Arquitectura del Sistema", estilo_heading1))
    historia.append(Paragraph("El Módulo de Aluminio sigue una arquitectura de tres capas:", estilo_normal))
    datos_arq = [["Capa", "Tecnología", "Responsabilidad"],
                 ["Presentación", "PyQt6", "Interfaz gráfica (PantallaMaterialesAluminio)"],
                 ["Lógica de Negocio", "Python 3.12", "DBManager, validaciones, reglas de importación"],
                 ["Acceso a Datos", "pyodbc + SQL Server", "CRUD sobre materiales_aluminio"],
                 ["Almacenamiento", "SQL Server", "Base de datos 'aluminio', tabla materiales_aluminio"]]
    historia.append(_tabla(datos_arq, anchos=[35 * mm, 35 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_imagen("arquitectura_sistema.png", ancho=160 * mm))
    historia.append(PageBreak())

    # 2. ESTRUCTURA DE ARCHIVOS
    historia.append(_ancla("estructura"))
    historia.append(Paragraph("2. Estructura de Archivos", estilo_heading1))
    datos_files = [
        ["Archivo", "Descripción"],
        ["pantalla_materiales_aluminio.py", "UI principal, modos de operación, eventos"],
        ["db_manager.py", "CRUD, conexión BD, merge_max, listar_todos"],
        ["db.py", "OBSOLETO - No utilizado (mantener por compatibilidad)"],
        ["imprimir.py", "Generación de PDF con reportlab"],
        ["utils.py", "Funciones: dec2, merge_max, ordenar_registros_asc, CAMPOS_PRECIO_BD"],
        ["restricciones.py", "Reglas de negocio: is_title_like, desc_bloqueada, registro_todo_ceros"],
        ["parsers/parse_excel.py", "Importación desde Excel (formato Profilo)"],
        ["parsers/parse_pdf.py", "Importación desde PDF (formato Mateco)"],
        ["parsers/parse_csv.py", "Importación desde CSV genérico"],
    ]
    historia.append(_tabla(datos_files, anchos=[60 * mm, 96 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_imagen("estructura_modulos.png", ancho=160 * mm))
    historia.append(PageBreak())

    # 3. BASE DE DATOS
    historia.append(_ancla("basedatos"))
    historia.append(Paragraph("3. Base de Datos", estilo_heading1))
    historia.append(_ancla("bd-esquema"))
    historia.append(Paragraph("3.1 Esquema de la Tabla", estilo_heading2))

    datos_esq = [
        ["Columna", "Tipo", "Nulo", "Descripción"],
        ["clave", "varchar(10)", "NO", "PK - Clave única del perfil"],
        ["descripcion", "varchar(100)", "NO", "Nombre comercial"],
        ["largo", "decimal(4,2)", "NO", "Largo en metros (6.10, 5.50, etc.)"],
        ["sa", "decimal(10,2)", "YES", "Precio S/A (Sin acabado)"],
        ["nat", "decimal(10,2)", "YES", "Precio NAT (Natural)"],
        ["bmo", "decimal(10,2)", "YES", "Precio BMO (Bronce mate)"],
        ["e100", "decimal(10,2)", "YES", "Precio E-100"],
        ["e200", "decimal(10,2)", "YES", "Precio E-200"],
        ["e400", "decimal(10,2)", "YES", "Precio E-400"],
        ["bco", "decimal(10,2)", "YES", "Precio BCO (Blanco)"],
        ["hue", "decimal(10,2)", "YES", "Precio HUESO"],
        ["np", "decimal(10,2)", "YES", "Precio NP (Negro punta)"],
        ["gris", "decimal(10,2)", "YES", "Precio GRIS"],
        ["cho", "decimal(10,2)", "YES", "Precio CHO (Chocolate)"],
        ["ace", "decimal(10,2)", "YES", "Precio ACE (Acero)"],
        ["madl", "decimal(10,2)", "YES", "Precio MAD L (Madera línea)"],
        ["madt", "decimal(10,2)", "YES", "Precio MAD T (Madera textura)"],
    ]
    historia.append(_tabla(datos_esq, anchos=[30 * mm, 30 * mm, 15 * mm, 81 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_imagen("diagrama_bd.png", ancho=160 * mm))

    historia.append(_ancla("bd-campos"))
    historia.append(Paragraph("3.2 Campos de Precio", estilo_heading2))
    historia.append(_codigo(
        "# Constante en utils.py\n"
        "CAMPOS_PRECIO_BD = [\n"
        '    "sa", "nat", "bmo",\n'
        '    "e100", "e200", "e400",\n'
        '    "bco", "hue", "np",\n'
        '    "gris", "cho", "ace",\n'
        '    "madl", "madt"\n'
        "]"
    ))

    historia.append(_ancla("bd-relaciones"))
    historia.append(Paragraph("3.3 Relaciones", estilo_heading2))
    historia.append(_lista([
        "La tabla NO tiene claves foráneas explícitas.",
        "La clave primaria es 'clave' (única).",
        "No hay relaciones con otras tablas (independiente).",
        "La integridad se maneja a nivel de aplicación."
    ]))
    historia.append(PageBreak())

    # 4. DEPENDENCIAS
    historia.append(_ancla("dependencias"))
    historia.append(Paragraph("4. Dependencias", estilo_heading1))
    datos_deps = [
        ["Librería", "Versión", "Uso"],
        ["PyQt6", "6.5+", "Interfaz gráfica completa"],
        ["pyodbc", "4.0+", "Conexión ODBC a SQL Server"],
        ["openpyxl", "3.0+", "Lectura de archivos Excel (Profilo)"],
        ["pdfplumber", "0.9+", "Extracción de texto desde PDF (Mateco)"],
        ["reportlab", "3.6+", "Generación de PDF para impresión"],
        ["win32print", "pywin32", "Impresión directa a impresora física"],
        ["Python", "3.10+", "Lenguaje base"],
    ]
    historia.append(_tabla(datos_deps, anchos=[40 * mm, 30 * mm, 86 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_codigo(
        "pip install PyQt6 pyodbc openpyxl pdfplumber reportlab pywin32"
    ))
    historia.append(PageBreak())

    # 5. MÓDULOS Y CLASES PRINCIPALES
    historia.append(_ancla("modulos"))
    historia.append(Paragraph("5. Módulos y Clases Principales", estilo_heading1))

    historia.append(_ancla("modulo-dbmanager"))
    historia.append(Paragraph("5.1 DBManager (db_manager.py)", estilo_heading2))
    historia.append(_lista([
        "listar_todos() → List[Dict] - Obtiene todos los materiales",
        "obtener_por_clave(clave) → Dict - Busca por clave",
        "existe_clave(clave) → bool - Verifica existencia",
        "insertar_o_actualizar(material, use_merge=False) → Dict - Guarda material",
        "eliminar_por_clave(clave) → None - Elimina material",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_codigo(
        "# Ejemplo de uso\n"
        "db = DBManager(db_name=\"aluminio\")\n"
        "material = {\n"
        '    "clave": "7821C",\n'
        '    "descripcion": "PERFIL VENTANA",\n'
        '    "largo": Decimal("6.10"),\n'
        '    "sa": Decimal("125.50"),\n'
        "    ...\n"
        "}\n"
        "db.insertar_o_actualizar(material, use_merge=False)"
    ))

    historia.append(_ancla("modulo-pantalla"))
    historia.append(Paragraph("5.2 PantallaMaterialesAluminio (pantalla_materiales_aluminio.py)", estilo_heading2))
    historia.append(_lista([
        "_on_guardar() - Guarda material (modo nuevo o edición)",
        "_modo_editar() - Activa modo edición, habilita búsqueda",
        "_modo_eliminar() - Activa modo eliminación",
        "Inicio() - Limpia todos los campos y tabla",
        "_buscar_dinamico() - Filtra tabla mientras escribe",
        "_on_imprimir() - Diálogo de impresión (Pantalla/PDF/Impresora)",
        "_on_importar() - Importa desde archivo externo",
        "eventFilter() - Valida clave duplicada al perder foco",
        "_llenar_tabla() - Carga datos en QTableWidget",
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_codigo(
        "# Atajos de teclado definidos\n"
        "Ctrl+S → _on_guardar\n"
        "Ctrl+F → focus búsqueda\n"
        "Ctrl+P → _on_imprimir\n"
        "Delete → _modo_eliminar\n"
        "F5 → _on_refresh\n"
        "Esc → _on_salir"
    ))

    historia.append(_ancla("modulo-parsers"))
    historia.append(Paragraph("5.3 Parsers (parsers/)", estilo_heading2))
    historia.append(Paragraph("<b>parse_excel.py</b>", estilo_heading3))
    historia.append(_lista([
        "parse_excel_profilo(filename) → List[Dict] - Extrae materiales de Excel",
        "Mapea encabezados (SA → sa, NAT → nat, ELE → e100/e200/e400)",
        "Aplica reglas de negocio (ignora títulos, claves C1150/C1200)",
        "Aplica EXCEPCIONES_LARGO para claves específicas",
    ]))
    historia.append(Paragraph("<b>parse_pdf.py</b>", estilo_heading3))
    historia.append(_lista([
        "parse_pdf_mateco(pdf_path) → List[Dict] - Extrae materiales de PDF Mateco",
        "Reconoce largos válidos: 6.10, 5.50, 5.00, 4.60, 3.66",
        "Asigna precios en orden: SA, NAT, BMO, ELE, BCO, HUESO, NP, GRIS, MADL, MADT",
        "ELE se distribuye a e100, e200, e400",
    ]))
    historia.append(Paragraph("<b>parse_csv.py</b>", estilo_heading3))
    historia.append(_lista([
        "parse_csv_generico(filename) → List[Dict] - Importa desde CSV",
        "Espera encabezados: CLAVE, DESCRIPCION, SA, NAT, ...",
        "Aplica mismas restricciones que Excel/PDF",
    ]))
    historia.append(PageBreak())

    # 6. FLUJO DE DATOS
    historia.append(_ancla("flujo"))
    historia.append(Paragraph("6. Flujo de Datos", estilo_heading1))

    historia.append(_ancla("flujo-guardar"))
    historia.append(Paragraph("6.1 Guardado Manual", estilo_heading2))
    historia.append(_lista([
        "1. Usuario completa campos (Clave, Descripción, Largo, Precios)",
        "2. Usuario presiona Guardar (Ctrl+S)",
        "3. UI valida campos obligatorios (Clave no vacía, Descripción no vacía)",
        "4. UI llama a DBManager.insertar_o_actualizar(use_merge=False)",
        "5. DBManager verifica si la clave existe con SELECT",
        "6. Si existe → UPDATE, si no → INSERT",
        "7. UI limpia pantalla (Inicio())"
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen("flujo_datos.png", ancho=160 * mm))

    historia.append(_ancla("flujo-importar"))
    historia.append(Paragraph("6.2 Importación desde Archivo", estilo_heading2))
    historia.append(_lista([
        "1. Usuario selecciona Importar y elige archivo (.xlsx, .pdf, .csv)",
        "2. UI llama al parser correspondiente (parse_excel_profilo, etc.)",
        "3. Parser extrae registros aplicando reglas de negocio",
        "4. Para cada registro, DBManager.insertar_o_actualizar(use_merge=True)",
        "5. DBManager aplica merge_max (conserva precio más alto entre existente y nuevo)",
        "6. UI muestra mensaje con número de registros importados"
    ]))

    historia.append(_ancla("flujo-editar"))
    historia.append(Paragraph("6.3 Edición", estilo_heading2))
    historia.append(_lista([
        "1. Usuario presiona Editar",
        "2. UI activa barra de búsqueda y limpia tabla",
        "3. Usuario escribe texto en búsqueda",
        "4. UI filtra y muestra resultados",
        "5. Usuario hace doble clic en registro deseado",
        "6. UI carga datos (Clave, Descripción deshabilitadas, Precios habilitados)",
        "7. Usuario modifica precios o largo",
        "8. Usuario presiona Guardar → UPDATE en BD",
        "9. UI limpia pantalla"
    ]))
    historia.append(PageBreak())

    # 7. MANEJO DE ERRORES
    historia.append(_ancla("errores"))
    historia.append(Paragraph("7. Manejo de Errores", estilo_heading1))
    datos_err = [
        ["Nivel", "Mecanismo", "Ejemplo"],
        ["Validación UI", "Comprobaciones en _on_guardar()", "Clave vacía → mensaje"],
        ["Clave duplicada", "eventFilter() + QMessageBox.question", "Pregunta si editar"],
        ["Conexión BD", "try/except en DBManager", "Logging + raise"],
        ["Importación", "try/except por registro", "Logging + continúa"],
        ["Impresión", "try/except en imprimir_pdf_guardar", "QMessageBox.critical"],
    ]
    historia.append(_tabla(datos_err, anchos=[35 * mm, 50 * mm, 71 * mm]))
    historia.append(Spacer(1, 5 * mm))
    historia.append(_codigo(
        "# Ejemplo de manejo de errores en db_manager.py\n"
        "with pyodbc.connect(self.conn_str) as cn:\n"
        "    try:\n"
        "        cur = cn.cursor()\n"
        "        cur.execute(sql, vals)\n"
        "        cn.commit()\n"
        "    except pyodbc.Error as e:\n"
        "        logger.error(f\"Error SQL: {e}\")\n"
        "        raise"
    ))
    historia.append(PageBreak())

    # 8. LOGGING
    historia.append(_ancla("logging"))
    historia.append(Paragraph("8. Logging y Depuración", estilo_heading1))
    historia.append(_lista([
        "Archivo de log: D:\\vah\\materiales\\aluminio\\aluminio_db.log",
        "Tamaño máximo: 1 MB",
        "Backup: 3 archivos rotativos",
        "Encoding: UTF-8",
        "Nivel: DEBUG (registra errores de conexión y operaciones)"
    ]))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_codigo(
        "# Configuración en db.py (obsoleto) y db_manager.py\n"
        "logger = logging.getLogger(\"aluminio_db\")\n"
        "logger.setLevel(logging.DEBUG)\n"
        "handler = RotatingFileHandler(\n"
        '    "aluminio_db.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"\n'
        ")\n"
        "logger.addHandler(handler)"
    ))
    historia.append(Spacer(1, 3 * mm))
    historia.append(_nota_manual(
        "El log principal del módulo se encuentra en aluminio_db.log. "
        "Revise este archivo ante errores de conexión o importación."
    ))
    historia.append(PageBreak())

    # 9. CONFIGURACIÓN
    historia.append(_ancla("configuracion"))
    historia.append(Paragraph("9. Configuración", estilo_heading1))
    historia.append(Paragraph("Cadena de conexión a SQL Server (db_manager.py):", estilo_normal))
    historia.append(_codigo(
        'self.conn_str = (\n'
        '    "Driver={ODBC Driver 18 for SQL Server};"\n'
        '    "Server=DESKTOP-AE60PIU\\\\SQLEXPRESS;"\n'
        '    f"Database={db_name};"\n'
        '    "Trusted_Connection=yes;"\n'
        '    "Encrypt=no;"\n'
        ")"
    ))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph("Configuración de largos disponibles:", estilo_normal))
    historia.append(_codigo(
        "# pantalla_materiales_aluminio.py\n"
        'self.largo_input.addItems(["6.10 MTS.", "5.50 MTS.", "5.00 MTS.", "4.60 MTS.", "3.66 MTS."])'
    ))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph("Reglas de excepción de largo (parse_excel.py):", estilo_normal))
    historia.append(_codigo(
        "EXCEPCIONES_LARGO = {\n"
        '    "7821C": 4.60,\n'
        '    "9955C": 4.60,\n'
        "    ...\n"
        "}"
    ))
    historia.append(PageBreak())

    # 10. FORMATOS DE IMPORTACIÓN
    historia.append(_ancla("formatos"))
    historia.append(Paragraph("10. Formatos de Importación", estilo_heading1))

    historia.append(Paragraph("10.1 Excel (Profilo)", estilo_heading2))
    historia.append(_lista([
        "Formato esperado: fila 11 = encabezados",
        "Encabezados: CLAVE, DESCRIPCION, SA, NAT, BMO, E1, E2, E4, BL, HU, NP, GR, CH, AC, NO, MA",
        "Datos desde fila 12",
        "Largo por defecto: 6.10 m, excepto claves en EXCEPCIONES_LARGO",
        "E1/E2/E4 → e100/e200/e400",
    ]))

    historia.append(Paragraph("10.2 PDF (Mateco)", estilo_heading2))
    historia.append(_lista([
        "Formato esperado: líneas con clave, descripción, largo y precios",
        "Largos válidos: 6.10, 5.50, 5.00, 4.60, 3.66",
        "Orden de precios: SA, NAT, BMO, ELE, BCO, HUESO, NP, GRIS, MADL, MADT",
        "ELE se distribuye a e100/e200/e400",
        "Ignora líneas que comienzan con * o contienen meses (ENE, FEB, ...)"
    ]))

    historia.append(Paragraph("10.3 CSV", estilo_heading2))
    historia.append(_lista([
        "Formato esperado: encabezados en primera fila",
        "Columnas: CLAVE, DESCRIPCION, SA, NAT, BMO, E100, E200, E400, BCO, HUESO, NP, GRIS, CHO, ACE, MADL, MADT",
        "Delimitador: coma (,)",
        "Encoding: UTF-8",
    ]))
    historia.append(PageBreak())

    # CIERRE
    historia.append(Paragraph("— Fin del Manual Técnico —",
                              ParagraphStyle('Cierre', parent=estilo_normal, alignment=TA_CENTER, textColor=COLOR_AZUL,
                                             fontSize=12)))
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph(f"Documento generado el {FECHA_GENERACION} | Versión {VERSION}", estilo_pie))
    historia.append(Paragraph("VAH ERP © Todos los derechos reservados", estilo_pie))

    doc.build(historia)
    print(f"✅ Manual Técnico de {MODULO} generado: {ruta_salida}")


def _nota_manual(texto):
    """Nota para manual técnico."""
    estilo_nota = ParagraphStyle(
        'NotaTecnica',
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
    return Paragraph(f"💡 <b>Nota:</b> {texto}", estilo_nota)


if __name__ == "__main__":
    generar_manual_tecnico()