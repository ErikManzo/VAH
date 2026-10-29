# -*- coding: utf-8 -*-
"""
Explosor de materiales de aluminio.
Maneja:
- Materiales directos (tipo AL o ALUMINIO)
- Paquetes de aluminio (tipo PAQUETE ALUMINIO)

REGLAS DE CONSOLIDACIÓN:
- NO calcular tramos todavía
- Consolidar metros_totales
- Los tramos se calcularán después en concentrador_service
"""
from typing import List, Dict, Any, Optional
from concentrador_materiales.services.explosor_base import ExplosorBase
from concentrador_materiales.services.calculos import (

    metros_lineales_aluminio,
    metros_lineales_paquete_aluminio,
    calcular_tramos
)
from concentrador_materiales.models.concentrado import MaterialConcentrado
from concentrador_materiales.models.tipos import OrigenMaterial


from common.logger_config import get_logger
logger = get_logger('concentrador.services.explosor_aluminio')

class ExplosorAluminio(ExplosorBase):
    """
    Explosor para materiales de aluminio.
    IMPORTANTE: Este explosor NO calcula tramos todavía.
    Solo calcula metros_totales para que el concentrador
    pueda consolidar metros y luego recalcular tramos.
    """

    def explotar(
            self,
            item: Dict[str, Any],
            cantidad_cxc: float,
            context: Optional[Dict[str, Any]] = None
    ) -> List[MaterialConcentrado]:
        """
        Explota un item de aluminio.
        Retorna MaterialConcentrado con metros_totales (NO tramos).
        """
        if cantidad_cxc <= 0:
            self._registrar_advertencia(
                "CANTIDAD_CERO",
                f"Cantidad CXC = 0, material omitido",
                {"clave": item.get("clave"), "partida_id": item.get("partida_id")}
            )
            return []

        tipo = item.get("tipo", "").strip().upper()

        if tipo in ("PAQUETE ALUMINIO", "PAQUETE ALUMINIUM"):
            return self._explotar_paquete(item, cantidad_cxc, context)
        else:
            return self._explotar_material_directo(item, cantidad_cxc)

    def _explotar_material_directo(
            self,
            item: Dict[str, Any],
            cantidad_cxc: float
    ) -> List[MaterialConcentrado]:
        """
        Explota un material de aluminio directo.
        Calcula metros_totales, NO tramos.
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
        material = self.materiales_repo.obtener_material_aluminio(clave)

        if material is None:
            self._registrar_advertencia(
                "CLAVE_HUERFANA",
                f"Clave {clave} no encontrada en catálogo de aluminio",
                {"clave": clave, "partida_id": item.get("partida_id")}
            )
            return []

        # Validar largo (necesario para cálculo final de tramos)
        largo_tramo = material.get("largo")
        if largo_tramo is None or largo_tramo <= 0:
            self._registrar_advertencia(
                "LARGO_NULO",
                f"Perfil {clave} sin largo definido. Material excluido.",
                {"clave": clave, "largo": largo_tramo, "partida_id": item.get("partida_id")}
            )
            return []

        # Calcular metros lineales por pieza
        ca = float(item.get("ca", 1.0))
        ancho = float(item.get("ancho", 0.0))
        ch = float(item.get("ch", 1.0))
        alto = float(item.get("alto", 0.0))
        piezas = int(item.get("piezas", 1))  # ← CORRECCIÓN: Obtener piezas

        metros_por_pieza = metros_lineales_aluminio(ca, ancho, ch, alto)
        # CORRECCIÓN: Multiplicar por piezas
        metros_totales = metros_por_pieza * piezas * cantidad_cxc

        # Guardar largo_tramo para recálculo posterior
        self._registrar_info(
            "CALCULO_METROS_ALUMINIO",
            f"Clave {clave}: {metros_totales:.2f} metros",
            {"clave": clave, "metros_totales": metros_totales, "largo_tramo": largo_tramo}
        )

        # IMPORTANTE: NO calcular tramos todavía
        # La cantidad inicial es metros (para consolidación)
        # Los tramos se calcularán después de consolidar metros
        material_concentrado = MaterialConcentrado(
            clave=clave,
            descripcion=material.get("descripcion", ""),
            almacen="ALUMINIO",
            cantidad=metros_totales,  # ← METROS, NO tramos
            unidad="Metros",  # ← Unidad base para consolidación
            presupuesto_id=item.get("presupuesto_id", 0),
            partida_id=item.get("partida_id", 0),
            cxc_id=item.get("cxc_id", 0),
            tipo_original=item.get("tipo", "AL"),
            origen=OrigenMaterial.DIRECTO,
            cantidad_cxc_original=cantidad_cxc,
            metros_totales=metros_totales,  # ← Para recálculo
            ancho_original=ancho,
            alto_original=alto
        )

        return [material_concentrado]

    def _explotar_paquete(
            self,
            item: Dict[str, Any],
            cantidad_cxc: float,
            context: Optional[Dict[str, Any]] = None
    ) -> List[MaterialConcentrado]:
        """
        Explota un paquete de aluminio.
        Calcula metros_totales por componente, NO tramos.
        """
        clave_paquete = item.get("clave", "")
        if not clave_paquete:
            self._registrar_advertencia(
                "PAQUETE_SIN_CLAVE",
                "Paquete sin clave, omitido",
                {"partida_id": item.get("partida_id")}
            )
            return []

        # Obtener componentes del paquete
        paquete_completo = getattr(self.materiales_repo, 'obtener_paquete_aluminio_completo', None)
        if paquete_completo is None:
            self._registrar_error(
                "METODO_NO_DISPONIBLE",
                "obtener_paquete_aluminio_completo no disponible en repositorio",
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

        cantidad_paquetes = 1
        if context and "cantidad_paquetes" in context:
            cantidad_paquetes = context["cantidad_paquetes"]

        ancho_paquete = 0.0
        alto_paquete = 0.0
        if context:
            ancho_paquete = context.get("ancho", 0.0)
            alto_paquete = context.get("alto", 0.0)

        resultados = []
        for componente in paquete.get("componentes", []):
            clave_item = componente.get("clave_item")
            if not clave_item:
                continue

            material = self.materiales_repo.obtener_material_aluminio(clave_item)

            if material is None:
                self._registrar_advertencia(
                    "COMPONENTE_HUERFANO",
                    f"Componente {clave_item} del paquete {clave_paquete} no encontrado",
                    {"clave_paquete": clave_paquete, "clave_item": clave_item}
                )
                continue

            largo_tramo = material.get("largo")
            if largo_tramo is None or largo_tramo <= 0:
                self._registrar_advertencia(
                    "COMPONENTE_SIN_LARGO",
                    f"Componente {clave_item} sin largo definido",
                    {"clave_item": clave_item, "clave_paquete": clave_paquete}
                )
                continue

            horizontal = componente.get("horizontal", 0)
            vertical = componente.get("vertical", 0)
            cantidad_componente = componente.get("cantidad", 1)

            metros_por_paquete = metros_lineales_paquete_aluminio(
                horizontal, vertical, ancho_paquete, alto_paquete
            )

            metros_totales = (
                metros_por_paquete *
                cantidad_componente *
                cantidad_paquetes *
                cantidad_cxc
            )

            # IMPORTANTE: NO calcular tramos todavía
            material_concentrado = MaterialConcentrado(
                clave=clave_item,
                descripcion=material.get("descripcion", ""),
                almacen="ALUMINIO",
                cantidad=metros_totales,  # ← METROS
                unidad="Metros",  # ← Unidad base
                presupuesto_id=item.get("presupuesto_id", 0),
                partida_id=item.get("partida_id", 0),
                cxc_id=item.get("cxc_id", 0),
                tipo_original=item.get("tipo", "PAQUETE ALUMINIO"),
                origen=OrigenMaterial.PAQUETE,
                cantidad_cxc_original=cantidad_cxc,
                metros_totales=metros_totales
            )
            resultados.append(material_concentrado)

        return resultados