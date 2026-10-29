# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/reports/pdf_partida_manager.py
Gestor de saltos de página inteligentes para partidas

Responsabilidad:
- Calcular altura de cada partida ANTES de dibujarla
- Decidir si cabe en la página actual o debe pasar a la siguiente
- Garantizar que UNA PARTIDA NUNCA SE DIVIDA ENTRE PÁGINAS
"""

from reportlab.pdfgen import canvas


class PartidaManager:
    """Gestor de posicionamiento y saltos de página para partidas"""

    def __init__(self, generador):
        """
        Args:
            generador: Instancia de GeneradorPresupuestoPDF
        """
        self.generador = generador
        self._margen_seguridad = 60  # Margen desde el fondo de página

    def calcular_altura_partida(self, c: canvas.Canvas, partida, left: float, width: float) -> float:
        """
        Calcula la altura TOTAL que ocupará una partida completa.
        """
        altura = 0

        # "PARTIDA X"
        altura += 15

        # Título de la partida
        if partida.titulo and partida.titulo.strip():
            lineas = self.generador._contar_lineas_texto(c, partida.titulo, width - 10, 12, bold=True)
            altura += lineas * 12

        # Descripción de la partida
        if partida.descripcion and partida.descripcion.strip():
            lineas = self.generador._contar_lineas_texto(c, partida.descripcion, width - 15, 10, bold=False)
            altura += lineas * 10

        # Línea de valores (precio, piezas, importe)
        altura += 25

        # Espacio entre partidas
        altura += 10

        return altura

    def cabe_en_pagina(self, c: canvas.Canvas, y_actual: float, partida, left: float, width: float) -> bool:
        """
        Verifica si la partida COMPLETA cabe en la página actual.

        Args:
            c: Canvas de ReportLab
            y_actual: Posición Y actual en la página
            partida: Objeto PartidaPresupuesto
            left: Margen izquierdo
            width: Ancho disponible

        Returns:
            True si cabe, False si no cabe
        """
        altura_necesaria = self.calcular_altura_partida(c, partida, left, width)

        # Verificar si hay espacio suficiente (considerando margen de seguridad)
        return y_actual - altura_necesaria > self._margen_seguridad

    def necesita_nueva_pagina(self, c: canvas.Canvas, y_actual: float, partida, left: float, width: float) -> bool:
        """
        Determina si la partida necesita una nueva página.
        """
        return not self.cabe_en_pagina(c, y_actual, partida, left, width)