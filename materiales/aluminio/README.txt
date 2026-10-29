=====================================================
 VAH - Módulo de Materiales de Aluminio
=====================================================

Este módulo está dividido en varios archivos .py para mayor control
y facilidad de mantenimiento. Cada archivo tiene una responsabilidad clara.

-----------------------------------------------------
 ESTRUCTURA
-----------------------------------------------------

D:\vah\materiales\aluminio\
│
├── pantalla_materiales_aluminio.py   # Pantalla principal (PyQt6 GUI)
├── db_manager.py                     # Conexión y operaciones con SQL Server
├── imprimir.py                       # Generación de PDF
├── restricciones.py                  # Validaciones de negocio (títulos, bolsas, todo en 0.00)
├── utils.py                          # Funciones generales y utilidades
│
└── parsers\
    ├── __init__.py                   # (vacío, marca carpeta como paquete Python)
    ├── parse_excel.py                # Parser de Excel
    ├── parse_pdf.py                  # Parser de PDF
    └── parse_csv.py                  # Parser CSV (si se usa en el futuro)

-----------------------------------------------------
 EJECUCIÓN DE LA PANTALLA
-----------------------------------------------------

Para abrir la pantalla principal (PyQt6 GUI):

    cd D:\vah\materiales\aluminio
    python pantalla_materiales_aluminio.py

-----------------------------------------------------
 PRUEBAS AISLADAS DE LOS PARSERS
-----------------------------------------------------

1) Probar parser de Excel:
    cd D:\vah\materiales\aluminio
    python -i
    >>> from parsers.parse_excel import parse_excel_profilo
    >>> regs = parse_excel_profilo("archivo.xlsx")
    >>> len(regs), regs[0]

2) Probar parser de PDF:
    cd D:\vah\materiales\aluminio
    python -i
    >>> from parsers.parse_pdf import parse_pdf_mateco
    >>> regs = parse_pdf_mateco("archivo.pdf")
    >>> len(regs), regs[0]

3) Probar impresión a PDF (sin abrir GUI):
    cd D:\vah\materiales\aluminio
    python -i
    >>> from imprimir import imprimir_pdf_guardar
    >>> from parsers.parse_excel import parse_excel_profilo
    >>> regs = parse_excel_profilo("archivo.xlsx")
    >>> imprimir_pdf_guardar(regs, None, "prueba.pdf")

-----------------------------------------------------
 BASE DE DATOS
-----------------------------------------------------

- La clase DBManager (db_manager.py) se conecta a SQL Server
  usando ODBC Driver 18.
- Ajustar SERVER y DATABASE según sea necesario en:
    db_manager.py → DBManager._get_conn()

- La tabla usada es: materiales_aluminio
  con campos:
    clave (PK), descripcion, largo,
    sa, nat, bmo, e100, e200, e400,
    bco, hue, np, gris, cho, ace, madl, madt

-----------------------------------------------------
 NOTAS
-----------------------------------------------------

- Todas las validaciones de negocio (ej. FISARMONICA, BOLSA DE 2")
  están centralizadas en restricciones.py.
- La lista de campos de precios está en utils.py (CAMPOS_PRECIO_BD).
- Siempre se conserva el valor mayor al consolidar datos de Excel o PDF.
- La tabla en pantalla y el PDF se muestran en orden ascendente por clave.
