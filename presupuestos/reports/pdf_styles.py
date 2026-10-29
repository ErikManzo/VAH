# -*- coding: utf-8 -*-
r"""
D:\vah\presupuestos\reports\pdf_styles.py
Estilos y configuración visual para el PDF de presupuesto
VERSIÓN COMPLETA - Con todos los estilos necesarios
"""

from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


class PDFStyles:
    """Configuración centralizada de estilos para el PDF"""

    # Configuración de página
    PAGE_SIZE = (215.9 * mm, 279.4 * mm)  # Tamaño carta / Letter
    TOP_MARGIN = 25 * mm
    BOTTOM_MARGIN = 20 * mm
    LEFT_MARGIN = 15 * mm
    RIGHT_MARGIN = 15 * mm

    # Fuentes estándar de ReportLab (siempre disponibles)
    FONT_FAMILY_NORMAL = 'Helvetica'
    FONT_FAMILY_BOLD = 'Helvetica-Bold'
    FONT_FAMILY_ITALIC = 'Helvetica-Oblique'
    FONT_FAMILY_BOLD_ITALIC = 'Helvetica-BoldOblique'

    # Tamaños de fuente
    FONT_SIZE_TITLE = 20
    FONT_SIZE_SUBTITLE = 16
    FONT_SIZE_HEADER_CONTACT = 8
    FONT_SIZE_DATOS = 10
    FONT_SIZE_SALUDO = 10
    FONT_SIZE_PARTIDA_NUM = 11
    FONT_SIZE_PARTIDA_TITULO = 11
    FONT_SIZE_PARTIDA_DESC = 9
    FONT_SIZE_VALORES = 10
    FONT_SIZE_TOTALES = 10
    FONT_SIZE_FOOTER = 8
    FONT_SIZE_FORMA_PAGO = 10
    FONT_SIZE_FIRMA = 10

    # Colores
    COLOR_BLACK = colors.black
    COLOR_GRAY = colors.gray
    COLOR_DARK_GRAY = colors.Color(0.2, 0.2, 0.2)
    COLOR_LIGHT_GRAY = colors.Color(0.8, 0.8, 0.8)
    COLOR_WHITE = colors.white
    COLOR_BLUE = colors.Color(0, 0, 0.5)

    # Espaciados
    LINE_HEIGHT_TITLE = 25
    LINE_HEIGHT_NORMAL = 12
    LINE_HEIGHT_SMALL = 10
    LINE_HEIGHT_PARTIDA = 30

    # Márgenes para elementos específicos
    MARGIN_PARTIDA_LEFT = 5 * mm
    MARGIN_DESC_LEFT = 10 * mm
    MARGIN_VALORES_RIGHT = 5 * mm

    @classmethod
    def get_watermark_config(cls):
        """Configuración para la marca de agua"""
        from common.app_paths import get_resource_path
        # Buscar el logo dinámicamente
        logo_path = ""
        for relative_path in [("logo.png",), ("logo.jpg",), ("logo_principal.jpg",)]:
            path = get_resource_path(*relative_path)
            if os.path.exists(path):
                logo_path = path
                break
        
        return {
            'image_path': logo_path,
            'opacity': 0.07,  # 7% de opacidad
            'width': 100 * mm,
            'height': 100 * mm
        }

    @classmethod
    def get_header_data(cls):
        """Datos del encabezado completo"""
        return {
            'empresa': "VENTANAS DE ALUMINIO Y HERRERIA",
            'dueno': "EDGAR MANZO RUIZ",
            'direccion': "VOLCÁN COFRE DEL PEROTE No.1813 EL COLLI C.P. 45070",
            'email': "E-mail: ventanasdealuminioyherreria@hotmail.com",
            'telefonos': "TELS: 33 3620-9293 - 33 3620-0269",
            'ciudad': "ZAPOPAN, JALISCO",
            'facebook': "Facebook: Ventanas de Aluminio y Herrería"
        }

    @classmethod
    def get_footer_data(cls):
        """Datos del pie de página completo (sin FAX)"""
        return {
            'linea1': "VOLCÁN COFRE DEL PEROTE No.1813 EL COLLI C.P. 45070",
            'linea2': "E-mail: ventanasdealuminioyherreria@hotmail.com",
            'linea3': "TELS: 33 3620-9293 - 33 3620-0269 ZAPOPAN, JALISCO",
            'linea4': "Facebook: Ventanas de Aluminio y Herrería"
        }

    @classmethod
    def get_forma_pago_data(cls):
        """Datos de forma de pago"""
        return {
            'titulo': "FORMA DE PAGO:",
            'lineas': [
                "60% AL ACEPTAR EL PRESUPUESTO",
                "40% AL TERMINAR"
            ]
        }

    @classmethod
    def get_plazo_entrega_data(cls):
        """Datos de plazo de entrega"""
        return {
            'titulo': "PLAZO DE ENTREGA:",
            'texto': "SERÁ DE COMÚN ACUERDO."
        }

    @classmethod
    def get_despedida_data(cls):
        """Texto de despedida"""
        return "Esperando que nuestro presupuesto merezca su aprobación y en espera de sus noticias y gratas órdenes, quedamos a sus órdenes para cualquier duda o aclaración."

    @classmethod
    def get_firma_data(cls):
        """Datos de firma"""
        return {
            'atentamente': "A T E N T A M E N T E",
            'nombre': "EDGAR MANZO RUIZ",
            'aceptacion': "PRESUPUESTO ACEPTADO",
            'linea_firma': "_________________________"
        }


class FormatoNumeros:
    """Utilidades para formateo de números en moneda"""

    @staticmethod
    def formato_moneda(valor: float) -> str:
        """Formatea un número como moneda mexicana"""
        if valor is None:
            return "$ 0.00"
        try:
            valor_redondeado = round(valor, 2)
            entero = int(valor_redondeado)
            decimal = int(round((valor_redondeado - entero) * 100))
            entero_str = f"{entero:,}"
            decimal_str = f"{decimal:02d}"
            signo = "-" if valor < 0 else ""
            return f"{signo}$ {entero_str}.{decimal_str}"
        except Exception:
            return "$ 0.00"

    @staticmethod
    def formato_numero(valor: float, decimales: int = 2) -> str:
        """Formatea un número con separadores de miles"""
        if valor is None:
            return "0"
        try:
            return f"{valor:,.{decimales}f}"
        except Exception:
            return "0"

    @staticmethod
    def formato_entero(valor: int) -> str:
        """Formatea un entero con separadores de miles"""
        if valor is None:
            return "0"
        try:
            return f"{valor:,}"
        except Exception:
            return str(valor)

    @staticmethod
    def formato_porcentaje(valor: float, decimales: int = 1) -> str:
        """Formatea un número como porcentaje"""
        if valor is None:
            return "0%"
        try:
            return f"{valor:.{decimales}f}%"
        except Exception:
            return "0%"

    @staticmethod
    def limpiar_moneda(texto: str) -> float:
        """Limpia un string de moneda y lo convierte a float"""
        if not texto:
            return 0.0
        try:
            limpio = texto.replace('$', '').replace(' ', '').replace(',', '')
            return float(limpio)
        except Exception:
            return 0.0


COLORES_TOTALES = {
    'subtotal': colors.Color(0, 0, 0),
    'iva': colors.Color(0.4, 0.4, 0.4),
    'total': colors.Color(0, 0, 0)
}

COLORES_PARTIDA = {
    'numero': colors.Color(0, 0, 0),
    'titulo': colors.Color(0, 0, 0),
    'descripcion': colors.Color(0.2, 0.2, 0.2),
    'valores': colors.Color(0, 0, 0)
}
