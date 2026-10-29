# -*- coding: utf-8 -*-
"""
Explosor de materiales plásticos.
Reglas:
- Unidades simples (cantidad = cantidad_cxc × piezas)
- Sin conversiones especiales
"""
from typing import List, Dict, Any, Optional
from concentrador_materiales.services.explosor_base import ExplosorBase
from concentrador_materiales.models.concentrado import MaterialConcentrado
from concentrador_materiales.models.tipos import OrigenMaterial


from common.logger_config import get_logger
logger = get_logger('concentrador.services.explosor_plasticos')

class ExplosorPlasticos(ExplosorBase):
    """
    Explosor para materiales plásticos.
    """

    def explotar(
            self,
            item: Dict[str, Any],
            cantidad_cxc: float,
            context: Optional[Dict[str, Any]] = None
    ) -> List[MaterialConcentrado]:
        """
        Explota un material plástico.

        Args:
            item: Datos de items_partida
            cantidad_cxc: Cantidad desde CXC
            context: Contexto adicional (no usado)

        Returns:
            Lista de MaterialConcentrado
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
        material = self.materiales_repo.obtener_material_plastico(clave)

        if material is None:
            self._registrar_advertencia(
                "CLAVE_HUERFANA",
                f"Clave {clave} no encontrada en catálogo de plásticos",
                {"clave": clave, "partida_id": item.get("partida_id")}
            )
            return []

        # CORRECCIÓN: Obtener piezas y multiplicar
        piezas = int(item.get("piezas", 1))
        cantidad_total = piezas * cantidad_cxc

        material_concentrado = MaterialConcentrado(
            clave=clave,
            descripcion=material.get("descripcion", ""),
            almacen="PLASTICOS",
            cantidad=cantidad_total,
            unidad="Piezas",
            presupuesto_id=item.get("presupuesto_id", 0),
            partida_id=item.get("partida_id", 0),
            cxc_id=item.get("cxc_id", 0),
            tipo_original=item.get("tipo", "PLASTICOS"),
            origen=OrigenMaterial.DIRECTO,
            cantidad_cxc_original=cantidad_cxc
        )

        return [material_concentrado]