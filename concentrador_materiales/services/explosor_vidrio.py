# -*- coding: utf-8 -*-
"""
Explosor de materiales de vidrio.
REGLAS DE CONSOLIDACIÓN:
- NO calcular hojas todavía
- Consolidar m2_totales
- Las hojas se calcularán después en concentrador_service
"""
from typing import List, Dict, Any, Optional
from concentrador_materiales.services.explosor_base import ExplosorBase
from concentrador_materiales.services.calculos import area_vidrio
from concentrador_materiales.models.concentrado import MaterialConcentrado
from concentrador_materiales.models.tipos import OrigenMaterial


from common.logger_config import get_logger
logger = get_logger('concentrador.services.explosor_vidrio')

class ExplosorVidrio(ExplosorBase):
    """
    Explosor para materiales de vidrio.
    IMPORTANTE: Este explosor NO calcula hojas todavía.
    Solo calcula m2_totales para que el concentrador
    pueda consolidar m² y luego recalcular hojas.
    """

    def explotar(
            self,
            item: Dict[str, Any],
            cantidad_cxc: float,
            context: Optional[Dict[str, Any]] = None
    ) -> List[MaterialConcentrado]:
        """
        Explota un material de vidrio.
        Retorna MaterialConcentrado con m2_totales (NO hojas).
        """
        if cantidad_cxc <= 0:
            self._registrar_advertencia(
                "CANTIDAD_CERO",
                f"Cantidad CXC = 0, material omitido",
                {"clave": item.get("clave"), "partida_id": item.get("partida_id")}
            )
            return []

        clave = item.get("clave", "")
        if not clave:
            self._registrar_advertencia(
                "CLAVE_VACIA",
                "Item sin clave, omitido",
                {"partida_id": item.get("partida_id")}
            )
            return []

        material = self.materiales_repo.obtener_material_vidrio(clave)

        if material is None:
            self._registrar_advertencia(
                "CLAVE_HUERFANA",
                f"Clave {clave} no encontrada en catálogo de vidrio",
                {"clave": clave, "partida_id": item.get("partida_id")}
            )
            return []

        ancho = float(item.get("ancho", 0.0))
        alto = float(item.get("alto", 0.0))
        piezas = int(item.get("piezas", 1))  # ← CORRECCIÓN: Obtener piezas

        if ancho <= 0 or alto <= 0:
            self._registrar_advertencia(
                "DIMENSIONES_INVALIDAS",
                f"Dimensiones inválidas para vidrio {clave}",
                {"clave": clave, "ancho": ancho, "alto": alto}
            )
            return []

        m2_por_pieza = area_vidrio(ancho, alto)
        # CORRECCIÓN: Multiplicar por piezas
        m2_totales = m2_por_pieza * piezas * cantidad_cxc

        self._registrar_info(
            "CALCULO_M2_VIDRIO",
            f"Clave {clave}: {m2_totales:.2f} m²",
            {"clave": clave, "m2_totales": m2_totales}
        )

        # IMPORTANTE: NO calcular hojas todavía
        # La cantidad inicial es m² (para consolidación)
        # Las hojas se calcularán después de consolidar m²
        material_concentrado = MaterialConcentrado(
            clave=clave,
            descripcion=material.get("descripcion", ""),
            almacen="VIDRIO",
            cantidad=m2_totales,  # ← M², NO hojas
            unidad="MetrosCuadrados",  # ← Unidad base para consolidación
            presupuesto_id=item.get("presupuesto_id", 0),
            partida_id=item.get("partida_id", 0),
            cxc_id=item.get("cxc_id", 0),
            tipo_original=item.get("tipo", "VIDRIO"),
            origen=OrigenMaterial.DIRECTO,
            cantidad_cxc_original=cantidad_cxc,
            m2_totales=m2_totales,  # ← Para recálculo
            ancho_original=ancho,
            alto_original=alto
        )

        return [material_concentrado]