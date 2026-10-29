# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/reports/pdf_generator.py
Generador profesional de presupuestos en PDF
VERSION CORREGIDA v12 - Paginación correcta del bloque final + DESCUENTO
CORRECCIÓN v12:
- _dibujar_totales(): colocación dinámica concepto/valor con separación
  mínima garantizada; elimina el encime de "DESCUENTO (x%)" con su cantidad.
CORRECCIÓN v11:
- Nuevo helper _asegurar_espacio(): verifica espacio antes de cada bloque
  (totales, notas, forma de pago/plazo/despedida/firmas) y crea página nueva
  con pie, marca de agua y encabezado cuando no cabe.
- El bloque de cierre se mide completo y nunca se dibuja sobre el pie.
- Notas largas paganizan línea por línea.
- Línea DESCUENTO (p%) bajo SUBTOTAL; I.V.A. y TOTAL calculados sobre el
  subtotal descontado desde TotalesPresupuesto.
- MARGIN_BOTTOM = 60: el contenido nunca invade la zona del pie de página.
"""
import os
from datetime import datetime
from typing import List, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm, cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from common.app_paths import get_resource_path
from presupuestos.reports.pdf_models import DatosPresupuesto, PartidaPresupuesto, TotalesPresupuesto
from presupuestos.reports.pdf_partida_manager import PartidaManager

class GeneradorPresupuestoPDF:
    # Margen inferior seguro: el contenido nunca baja de esta coordenada
    # (el pie de página se dibuja en y=30/38).
    MARGIN_BOTTOM = 60

    def __init__(self, parent=None):
        self._watermark_image = None
        self._current_page = 1
        self._primera_pagina = True
        self.parent = parent
        self.partida_manager = PartidaManager(self)
        self._cargar_marca_agua()

    def _cargar_marca_agua(self):
        try:
            for relative_path in (
                ("logo.png",),
                ("logo.jpg",),
                ("logo_principal.jpg",),
                ("logo_principal_pagina.jpg",),
            ):
                logo_path = get_resource_path(*relative_path)
                if os.path.exists(logo_path):
                    self._watermark_image = ImageReader(logo_path)
                    print(f"Marca de agua cargada desde {logo_path}")
                    return
            print("No se encontro un logo empaquetado para la marca de agua")
        except Exception as e:
            print(f"Error marca de agua: {e}")

    def _dibujar_marca_agua(self, c: canvas.Canvas, width: float, height: float):
        if self._watermark_image is None:
            return
        try:
            c.saveState()
            c.setFillAlpha(0.07)
            c.setStrokeAlpha(0.07)
            watermark_width = 120 * mm
            watermark_height = 120 * mm
            x = (width - watermark_width) / 2
            y = (height - watermark_height) / 2
            c.drawImage(self._watermark_image, x, y, watermark_width, watermark_height, mask='auto')
            c.restoreState()
        except Exception as e:
            print(f"Error dibujando marca de agua: {e}")

    def generar_pdf(self, datos: DatosPresupuesto, output_path: str) -> bool:
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            c = canvas.Canvas(output_path, pagesize=letter)
            self._current_page = 1
            self._primera_pagina = True
            self._dibujar_presupuesto_completo(c, datos)
            c.save()
            print(f"PDF generado: {output_path} - {len(datos.partidas)} partidas")
            return True
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    # ==================================================================
    # NUEVO (v11): gestión centralizada de saltos de página
    # ==================================================================
    def _nueva_pagina(self, c: canvas.Canvas, datos: DatosPresupuesto) -> float:
        """Cierra la página actual con su pie y abre una nueva con marca de
        agua y encabezado (sin saludo). Retorna la nueva coordenada y."""
        page_width, page_height = letter
        self._dibujar_pie_pagina(c)
        c.showPage()
        self._current_page += 1
        self._dibujar_marca_agua(c, page_width, page_height)
        return self._dibujar_encabezado(c, 750, datos, incluir_saludo=False)

    def _asegurar_espacio(self, c: canvas.Canvas, y: float, necesario: float,
                          datos: DatosPresupuesto) -> float:
        """Si no hay espacio suficiente para 'necesario' puntos por encima del
        margen inferior seguro, crea página nueva."""
        if y - necesario <= self.MARGIN_BOTTOM:
            return self._nueva_pagina(c, datos)
        return y

    def _altura_notas(self, c: canvas.Canvas, notas: str, width: float) -> float:
        """Altura estimada del bloque de notas completo."""
        total = 15 + 10  # "NOTAS:" + separador final
        for nota in notas.split('\n'):
            nota = nota.strip()
            if nota:
                total += self._contar_lineas_texto(c, nota, width - 10, 10) * 10 + 5
        return total

    def _altura_cierre(self, c: canvas.Canvas, datos: DatosPresupuesto, width: float) -> float:
        """Altura estimada del bloque de cierre completo:
        FORMA DE PAGO + PLAZO + DESPEDIDA + FIRMAS."""
        despedida = ("Esperando que nuestro presupuesto merezca su aprobacion y en espera de sus "
                     "noticias y gratas ordenes, quedamos a sus ordenes para cualquier duda o aclaracion.")
        lineas_pago = datos.forma_pago.split('\n')
        altura = 15 + len(lineas_pago) * 15            # FORMA DE PAGO
        altura += 15 + 15 + 20                         # PLAZO DE ENTREGA
        # Despedida: se cuenta con ancho reducido y línea de 14 para holgura
        altura += self._contar_lineas_texto(c, despedida, width - 40, 12) * 14 + 20
        altura += 15 + 15 + 25 + 15 + 15 + 15 + 20    # FIRMAS
        return altura

    def _dibujar_encabezado_tabla(self, c: canvas.Canvas, y: float, datos: DatosPresupuesto) -> float:
        """Dibuja la tabla de encabezado (como 6888.pdf)."""
        page_width, page_height = letter
        right_x = page_width - 40
        c.setFont("Helvetica", 9)
        line_height = 14
        datos_tabla = [
            f"ATENCION: {datos.cliente}",
            f"NUM. PPTO: {datos.num_presupuesto:,}",
            f"OBRA: {datos.obra}",
            f"FECHA: {datos.fecha}",
            f"ANODIZADO: {datos.anodizado}",
            f"PAGINA: {self._current_page}"
        ]
        for linea in datos_tabla:
            c.drawRightString(right_x, y, linea)
            y -= line_height
        return y

    def _dibujar_encabezado(self, c: canvas.Canvas, y: float, datos: DatosPresupuesto,
                            incluir_saludo: bool = True) -> float:
        left = 40
        width = 500
        page_width, page_height = letter
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(page_width / 2, y, "VENTANAS DE ALUMINIO Y HERRERIA")
        y -= 20
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(page_width / 2, y, "EDGAR MANZO RUIZ")
        y -= 25
        c.line(left, y, page_width - left, y)
        y -= 20
        y = self._dibujar_encabezado_tabla(c, y, datos)
        y -= 10
        if incluir_saludo:
            c.setFont("Helvetica", 10)
            c.drawString(left, y, datos.cliente)
            y -= 15
            c.drawString(left, y, "Muy senores nuestros:")
            y -= 15
            intro = ("De acuerdo con sus deseos y con la base de datos que tuvieron la gentileza de "
                     "proporcionarnos, nos es grato dar a su consideracion nuestro presupuesto que se "
                     "detalla a continuacion en:")
            y = self._texto_multilinea(c, intro, left, y, width, 12)
            y -= 10
            c.setFont("Helvetica-Bold", 10)
            c.drawString(left, y, datos.anodizado)
            y -= 20
            c.setFont("Helvetica", 10)
        else:
            y -= 20
        return y

    def _dibujar_pie_pagina(self, c: canvas.Canvas):
        page_width, page_height = letter
        y = 30
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        linea1 = "VOLCAN COFRE DEL PEROTE No.1813 EL COLLI C.P. 45070 E-mail: ventanasdealuminioyherreria@hotmail.com"
        c.drawCentredString(page_width / 2, y + 8, linea1)
        linea2 = "TELS: 33 3620-9293 - 33 3620-0269 ZAPOPAN, JALISCO Facebook: Ventanas de Aluminio y Herreria"
        c.drawCentredString(page_width / 2, y, linea2)
        c.setFillColorRGB(0, 0, 0)

    def _dibujar_partida(self, c: canvas.Canvas, y: float, partida: PartidaPresupuesto, left: float,
                         width: float) -> float:
        """Dibuja una partida completa con valores alineados a la derecha y separación uniforme."""
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left, y, f"PARTIDA {partida.numero}")
        y -= 15
        if partida.titulo and partida.titulo.strip():
            c.setFont("Helvetica-Bold", 10)
            y = self._texto_multilinea(c, partida.titulo, left + 10, y, width - 10, 12)
        if partida.descripcion and partida.descripcion.strip():
            c.setFont("Helvetica", 9)
            y = self._texto_multilinea(c, partida.descripcion, left + 15, y, width - 15, 10)
        c.setFont("Helvetica", 10)
        precio_formateado = f"{partida.precio_unitario:,.2f}"
        piezas_str = f"{partida.piezas} PZA"
        importe_formateado = f"{partida.importe:,.2f}"
        texto_precio = f"$ {precio_formateado}"
        texto_importe = f"$ {importe_formateado}"
        ancho_precio = c.stringWidth(texto_precio, "Helvetica", 10)
        ancho_piezas = c.stringWidth(piezas_str, "Helvetica", 10)
        ancho_importe = c.stringWidth(texto_importe, "Helvetica", 10)
        margen_izquierdo = left + 200
        ancho_disponible = (left + width) - margen_izquierdo
        ancho_total_elementos = ancho_precio + ancho_piezas + ancho_importe
        if ancho_total_elementos < ancho_disponible:
            espacio_n = (ancho_disponible - ancho_total_elementos) // 2
        else:
            espacio_n = 30
        pos_importe = (left + width) - 30
        pos_piezas = pos_importe - ancho_importe - espacio_n
        pos_precio = pos_piezas - ancho_piezas - espacio_n
        c.drawRightString(pos_importe, y - 5, texto_importe)
        c.drawString(pos_piezas, y - 5, piezas_str)
        c.drawString(pos_precio, y - 5, texto_precio)
        y -= 25
        return y

    def _dibujar_totales(self, c: canvas.Canvas, y: float, left: float, width: float,
                         totales: TotalesPresupuesto) -> float:
        """
        Dibuja la tabla de totales alineada a la derecha, con la línea de
        DESCUENTO debajo de SUBTOTAL cuando el porcentaje es mayor a 0.
        CORREGIDO (v12): colocación dinámica concepto/valor; si el concepto no
        cabe con separación mínima de 10 pt respecto al valor, se desplaza a
        la izquierda. Elimina el encime de "DESCUENTO (x%)" con su cantidad.
        """
        c.setFont("Helvetica", 10)
        etiqueta_x = left + width - 150
        valor_x = left + width - 30
        gap = 10

        def dibujar_linea(label: str, valor_texto: str, base_x: float) -> None:
            nonlocal y
            ancho_label = c.stringWidth(label, c._fontname, c._fontsize)
            ancho_valor = c.stringWidth(valor_texto, c._fontname, c._fontsize)
            label_x = min(base_x, valor_x - ancho_valor - gap - ancho_label)
            c.drawString(label_x, y, label)
            c.drawRightString(valor_x, y, valor_texto)
            y -= 15

        dibujar_linea("SUBTOTAL", f"$ {totales.subtotal:,.2f}", etiqueta_x)
        if totales.descuento_porcentaje > 0:
            dibujar_linea(
                f"DESCUENTO ({totales.descuento_porcentaje:.2f}%)",
                f"-$ {totales.descuento_monto:,.2f}",
                etiqueta_x
            )
        dibujar_linea("I.V.A. (16%)", f"$ {totales.iva_monto:,.2f}", etiqueta_x)
        c.setFont("Helvetica-Bold", 11)
        dibujar_linea("TOTAL", f"$ {totales.total:,.2f}", etiqueta_x + 5)
        y -= 10
        c.setFont("Helvetica", 10)
        return y

    def _dibujar_notas(self, c: canvas.Canvas, y: float, left: float, width: float,
                       notas: str, datos: Optional[DatosPresupuesto] = None) -> float:
        if not notas or not notas.strip():
            return y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left, y, "NOTAS:")
        y -= 15
        c.setFont("Helvetica", 9)
        for nota in notas.split('\n'):
            nota = nota.strip()
            if nota:
                if datos is not None:
                    alto_nota = self._contar_lineas_texto(c, nota, width - 10, 10) * 10 + 5
                    y = self._asegurar_espacio(c, y, alto_nota, datos)
                    c.setFont("Helvetica", 9)
                y = self._texto_multilinea(c, nota, left + 10, y, width - 10, 10)
                y -= 5
        y -= 10
        return y

    def _dibujar_presupuesto_completo(self, c: canvas.Canvas, datos: DatosPresupuesto):
        left = 40
        width = 500
        top = 750
        page_width, page_height = letter
        self._dibujar_marca_agua(c, page_width, page_height)
        y = self._dibujar_encabezado(c, top, datos, incluir_saludo=True)
        idx = 0
        while idx < len(datos.partidas):
            partida = datos.partidas[idx]
            if self.partida_manager.necesita_nueva_pagina(c, y, partida, left, width):
                y = self._nueva_pagina(c, datos)
                continue
            y = self._dibujar_partida(c, y, partida, left, width)
            y -= 10
            idx += 1
        # TOTALES: se verifica espacio antes de dibujar (con línea de descuento si aplica)
        if datos.totales:
            necesario_totales = 90 + (15 if datos.totales.descuento_porcentaje > 0 else 0)
            y = self._asegurar_espacio(c, y, necesario_totales, datos)
            y -= 15
            y = self._dibujar_totales(c, y, left, width, datos.totales)
        # NOTAS: se verifica el bloque completo y pagina línea por línea
        if datos.notas and datos.notas.strip():
            y = self._asegurar_espacio(c, y, self._altura_notas(c, datos.notas, width), datos)
            y = self._dibujar_notas(c, y, left, width, datos.notas, datos)
        # BLOQUE DE CIERRE: se mide COMPLETO; si no cabe, pasa íntegro a página nueva
        y = self._asegurar_espacio(c, y, self._altura_cierre(c, datos, width), datos)
        # FORMA DE PAGO
        c.drawString(left, y, "FORMA DE PAGO:")
        y -= 15
        lineas_pago = datos.forma_pago.split('\n')
        for linea in lineas_pago:
            c.drawString(left + 10, y, linea.strip())
            y -= 15
        # PLAZO DE ENTREGA
        c.drawString(left, y, "PLAZO DE ENTREGA:")
        y -= 15
        c.drawString(left + 10, y, datos.plazo_entrega)
        y -= 20
        # DESPEDIDA
        despedida = ("Esperando que nuestro presupuesto merezca su aprobacion y en espera de sus "
                     "noticias y gratas ordenes, quedamos a sus ordenes para cualquier duda o aclaracion.")
        c.setFont("Helvetica", 10)
        y = self._texto_multilinea(c, despedida, left, y, width, 12)
        y -= 20
        # FIRMAS
        c.setFont("Helvetica", 10)
        c.drawCentredString(page_width / 2, y, "A T E N T A M E N T E")
        y -= 15
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(page_width / 2, y, "EDGAR MANZO RUIZ")
        y -= 25
        c.setFont("Helvetica", 10)
        c.drawCentredString(page_width / 2, y, "PRESUPUESTO ACEPTADO")
        y -= 15
        c.drawCentredString(page_width / 2, y, "_________________________")
        y -= 15
        c.drawCentredString(page_width / 2, y, datos.cliente)
        y -= 20
        self._dibujar_pie_pagina(c)

    def _contar_lineas_texto(self, c: canvas.Canvas, texto: str, ancho_maximo: float, line_height: float,
                             bold: bool = False) -> int:
        if not texto:
            return 0
        if bold:
            c.setFont("Helvetica-Bold", 10)
        else:
            c.setFont("Helvetica", 9)
        palabras = texto.split()
        lineas = 0
        ancho_actual = 0
        for palabra in palabras:
            ancho_palabra = c.stringWidth(palabra + " ", c._fontname, c._fontsize)
            if ancho_actual + ancho_palabra <= ancho_maximo:
                ancho_actual += ancho_palabra
            else:
                lineas += 1
                ancho_actual = ancho_palabra
        if ancho_actual > 0:
            lineas += 1
        c.setFont("Helvetica", 10)
        return lineas

    def _texto_multilinea(self, c: canvas.Canvas, texto: str, x: float, y: float,
                          ancho_maximo: float, line_height: float) -> float:
        if not texto:
            return y
        palabras = texto.split()
        lineas = []
        linea_actual = []
        ancho_actual = 0
        for palabra in palabras:
            ancho_palabra = c.stringWidth(palabra + " ", c._fontname, c._fontsize)
            if ancho_actual + ancho_palabra <= ancho_maximo:
                linea_actual.append(palabra)
                ancho_actual += ancho_palabra
            else:
                if linea_actual:
                    lineas.append(" ".join(linea_actual))
                linea_actual = [palabra]
                ancho_actual = ancho_palabra
        if linea_actual:
            lineas.append(" ".join(linea_actual))
        for i, linea in enumerate(lineas):
            c.drawString(x, y - (i * line_height), linea)
        return y - (len(lineas) * line_height)

def generar_presupuesto_pdf(datos: DatosPresupuesto, ruta_salida: str, parent=None) -> bool:
    generador = GeneradorPresupuestoPDF(parent=parent)
    return generador.generar_pdf(datos, ruta_salida)