# -*- coding: utf-8 -*-
"""
Explosor de materiales de herrería.
REGLAS DE NEGOCIO CORREGIDAS:
- La unidad principal es METROS, NO kilogramos
- Los kilogramos son solo para costeo interno
- Consolidar metros, luego recalcular tramos de 6m
"""
from typing import List, Dict, Any, Optional
from concentrador_materiales.services.explosor_base import ExplosorBase
from concentrador_materiales.services.calculos import (

    metros_lineales_aluminio,
    metros_totales_herreria,
    calcular_piezas_herreria
)
from concentrador_materiales.models.concentrado import MaterialConcentrado
from concentrador_materiales.models.tipos import OrigenMaterial


from common.logger_config import get_logger
logger = get_logger('concentrador.services.explosor_herreria')

class ExplosorHerreria(ExplosorBase):
    """
    Explosor para materiales de herrería.
    IMPORTANTE:
    - La cantidad principal son METROS (no kilogramos)
    - Los tramos se calculan después de consolidar metros
    - Kilogramos se guardan solo para referencia de costeo
    """

    LONGITUD_PERFIL_METROS = 6.00

    def explotar(
            self,
            item: Dict[str, Any],
            cantidad_cxc: float,
            context: Optional[Dict[str, Any]] = None
    ) -> List[MaterialConcentrado]:
        """
        Explota un material de herrería.
        Retorna MaterialConcentrado con metros_totales (unidad base).
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

        # Obtener datos del catálogo
        material = self.materiales_repo.obtener_material_herreria(clave)

        if material is None:
            self._registrar_advertencia(
                "CLAVE_HUERFANA",
                f"Clave {clave} no encontrada en catálogo de herrería",
                {"clave": clave, "partida_id": item.get("partida_id")}
            )
            return []

        # Obtener kg por metro (solo para costeo interno)
        kg_por_metro = material.get("kilogramos_por_metro", 0.0)

        # Obtener piezas del item
        piezas = int(item.get("piezas", 1))  # ← CORRECCIÓN: Obtener piezas

        # Calcular metros totales (UNIDAD BASE)
        metros_por_pieza, usado_metros_campo = metros_totales_herreria(item)
        # CORRECCIÓN: Multiplicar por piezas
        metros_totales = metros_por_pieza * piezas * cantidad_cxc

        # Calcular kilogramos (SOLO PARA COSTEO INTERNO)
        kilogramos_totales = metros_totales * kg_por_metro

        # Calcular tramos informativos (se recalcularán después de consolidar)
        tramos_informativos = calcular_piezas_herreria(metros_totales, self.LONGITUD_PERFIL_METROS)

        self._registrar_info(
            "CALCULO_HERRERIA",
            f"Clave {clave}: {metros_totales:.2f}m, {kilogramos_totales:.2f}kg (costeo)",
            {"clave": clave, "metros": metros_totales, "kg": kilogramos_totales}
        )

        # IMPORTANTE: cantidad = METROS (unidad base para consolidación)
        material_concentrado = MaterialConcentrado(
            clave=clave,
            descripcion=material.get("descripcion", ""),
            almacen="HERRERIA",
            cantidad=metros_totales,  # ← METROS como unidad base
            unidad="Metros",  # ← Unidad base para consolidación
            presupuesto_id=item.get("presupuesto_id", 0),
            partida_id=item.get("partida_id", 0),
            cxc_id=item.get("cxc_id", 0),
            tipo_original=item.get("tipo", "HERRERIA"),
            origen=OrigenMaterial.DIRECTO,
            cantidad_cxc_original=cantidad_cxc,
            metros_totales=metros_totales,
            kilogramos_totales=kilogramos_totales,  # Solo costeo
            tramos_calculados=tramos_informativos,  # Informativo, se recalculará
            ancho_original=item.get("ancho", 0.0),
            alto_original=item.get("alto", 0.0),
            ca_original=item.get("ca", 1.0),
            ch_original=item.get("ch", 1.0),
            kg_por_metro=kg_por_metro
        )

        return [material_concentrado]