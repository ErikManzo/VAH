# -*- coding: utf-8 -*-
"""
Explosor de materiales de herrajes.
Maneja:
- Materiales directos (tipo HERRAJES)
- Paquetes de herrajes (tipo PAQUETE HERRAJES)

Fórmula oficial para paquetes:
cantidad_total = cantidad_componente × cantidad_paquetes × piezas × cantidad_cxc
"""
from typing import List, Dict, Any, Optional
from concentrador_materiales.services.explosor_base import ExplosorBase
from concentrador_materiales.models.concentrado import MaterialConcentrado
from concentrador_materiales.models.tipos import OrigenMaterial


from common.logger_config import get_logger
logger = get_logger('concentrador.services.explosor_herrajes')

class ExplosorHerrajes(ExplosorBase):
    """
    Explosor para materiales de herrajes.
    """

    def explotar(
            self,
            item: Dict[str, Any],
            cantidad_cxc: float,
            context: Optional[Dict[str, Any]] = None
    ) -> List[MaterialConcentrado]:
        """
        Explota un item de herrajes.

        Args:
            item: Datos de items_partida
            cantidad_cxc: Cantidad desde CXC
            context: Contexto con cantidad_paquetes para paquetes

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

        tipo = item.get("tipo", "").strip().upper()

        # Detectar si es paquete o material directo
        if tipo in ("PAQUETE HERRAJES", "PAQUETE HERRAJE"):
            return self._explotar_paquete(item, cantidad_cxc, context)
        else:
            return self._explotar_material_directo(item, cantidad_cxc)

    def _explotar_material_directo(
            self,
            item: Dict[str, Any],
            cantidad_cxc: float
    ) -> List[MaterialConcentrado]:
        """
        Explota un herraje directo (no paquete).
        """
        clave = item.get("clave", "")
        if not clave:
            self._registrar_advertencia(
                "CLAVE_VACIA",
                "Item sin clave, omitido",
                {"partida_id": item.get("partida_id")}
            )
            return []

        # Obtener datos del catálogo
        material = self.materiales_repo.obtener_material_herraje(clave)

        if material is None:
            self._registrar_advertencia(
                "CLAVE_HUERFANA",
                f"Clave {clave} no encontrada en catálogo de herrajes",
                {"clave": clave, "partida_id": item.get("partida_id")}
            )
            return []

        # CORRECCIÓN: Obtener piezas y multiplicar
        piezas = int(item.get("piezas", 1))
        cantidad_total = piezas * cantidad_cxc

        material_concentrado = MaterialConcentrado(
            clave=clave,
            descripcion=material.get("descripcion", ""),
            almacen="HERRAJES",
            cantidad=cantidad_total,
            unidad="Piezas",
            presupuesto_id=item.get("presupuesto_id", 0),
            partida_id=item.get("partida_id", 0),
            cxc_id=item.get("cxc_id", 0),
            tipo_original=item.get("tipo", "HERRAJES"),
            origen=OrigenMaterial.DIRECTO,
            cantidad_cxc_original=cantidad_cxc
        )

        return [material_concentrado]

    def _explotar_paquete(
            self,
            item: Dict[str, Any],
            cantidad_cxc: float,
            context: Optional[Dict[str, Any]] = None
    ) -> List[MaterialConcentrado]:
        """
        Explota un paquete de herrajes en sus componentes.

        Fórmula oficial:
        cantidad_total = cantidad_componente × cantidad_paquetes × piezas × cantidad_cxc
        """
        clave_paquete = item.get("clave", "")
        if not clave_paquete:
            self._registrar_advertencia(
                "PAQUETE_SIN_CLAVE",
                "Paquete sin clave, omitido",
                {"partida_id": item.get("partida_id")}
            )
            return []

        # Obtener cantidad de paquetes desde partida_paquetes
        cantidad_paquetes = 1
        if context and "cantidad_paquetes" in context:
            cantidad_paquetes = context["cantidad_paquetes"]

        # CORRECCIÓN: Obtener piezas del item
        piezas = int(item.get("piezas", 1))

        # Obtener componentes del paquete
        paquete_completo = getattr(self.materiales_repo, 'obtener_paquete_herrajes_completo', None)
        if paquete_completo is None:
            self._registrar_error(
                "METODO_NO_DISPONIBLE",
                "obtener_paquete_herrajes_completo no disponible en repositorio",
                {}
            )
            return []

        paquete = paquete_completo(clave_paquete)

        if paquete is None:
            self._registrar_advertencia(
                "PAQUETE_NO_ENCONTRADO",
                f"Paquete {clave_paquete} no encontrado",
                {"clave_paquete": clave_paquete}
            )
            return []

        resultados = []
        for componente in paquete.get("componentes", []):
            clave_herraje = componente.get("clave_herraje")
            cantidad_componente = componente.get("cantidad", 1)

            if not clave_herraje:
                continue

            # Obtener datos del herraje componente
            material = self.materiales_repo.obtener_material_herraje(clave_herraje)

            if material is None:
                self._registrar_advertencia(
                    "COMPONENTE_HUERFANO",
                    f"Componente {clave_herraje} del paquete {clave_paquete} no encontrado",
                    {"clave_paquete": clave_paquete, "clave_herraje": clave_herraje}
                )
                continue

            # Fórmula oficial CORREGIDA: incluir piezas
            cantidad_total = cantidad_componente * cantidad_paquetes * piezas * cantidad_cxc

            material_concentrado = MaterialConcentrado(
                clave=clave_herraje,
                descripcion=material.get("descripcion", ""),
                almacen="HERRAJES",
                cantidad=float(cantidad_total),
                unidad="Piezas",
                presupuesto_id=item.get("presupuesto_id", 0),
                partida_id=item.get("partida_id", 0),
                cxc_id=item.get("cxc_id", 0),
                tipo_original=item.get("tipo", "PAQUETE HERRAJES"),
                origen=OrigenMaterial.PAQUETE,
                cantidad_cxc_original=cantidad_cxc
            )
            resultados.append(material_concentrado)

        return resultados