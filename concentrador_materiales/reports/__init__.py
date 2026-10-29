# -*- coding: utf-8 -*-
"""
Reportes del Módulo Concentrador de Materiales

Componentes:
- ExcelGenerator: Generación de archivos Excel
- PDFGenerator: Generación de archivos PDF
"""

from concentrador_materiales.reports.excel_generator import ExcelGenerator
from concentrador_materiales.reports.pdf_generator import PDFGenerator

__all__ = ["ExcelGenerator", "PDFGenerator"]