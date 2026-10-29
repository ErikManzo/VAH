# -*- coding: utf-8 -*-
"""
Servicio Concentrador - Orquestador principal del módulo.
REGLAS DE CONSOLIDACIÓN:
ALUMINIO: Consolidar metros_totales, luego recalcular tramos = CEIL(metros / largo)
VIDRIO: Consolidar m2_totales, luego recalcular hojas = CEIL(m2 / 9.36)
HERRERIA: Consolidar kilogramos_totales directamente
HERRAJES/PLASTICOS/OTROS: Consolidar cantidad directamente
SOPORTE PARA CXC ESPECÍFICO:
Si se proporciona cxc_id, solo se explota ese CXC específico
Si no se proporciona, se comportará como antes (todos los CXC aceptados)
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from collections import defaultdict
import math
from concentrador_materiales.repositories.cxc_repository import CXCRepository
from concentrador_materiales.repositories.materiales_repository import MaterialesRepository
from concentrador_materiales.repositories.paquetes_repository import PaquetesRepository
from concentrador_materiales.repositories.concentrador_repository import ConcentradorRepository
from concentrador_materiales.services.mapeador_tipos import MapeadorTipos
from concentrador_materiales.services.diagnostico_paquetes import DiagnosticoPaquetes
from concentrador_materiales.services.explosor_aluminio import ExplosorAluminio
from concentrador_materiales.services.explosor_herreria import ExplosorHerreria
from concentrador_materiales.services.explosor_herrajes import ExplosorHerrajes
from concentrador_materiales.services.explosor_vidrio import ExplosorVidrio
from concentrador_materiales.services.explosor_plasticos import ExplosorPlasticos
from concentrador_materiales.services.explosor_otros import ExplosorOtros
from concentrador_materiales.models.concentrado import MaterialConcentrado, ReporteConcentrado
from concentrador_materiales.models.tipos import TipoMaterial
from concentrador_materiales.services.logger_config import (

    configurar_logger,
    registrar_info,
    registrar_error,
    registrar_advertencia
)


from common.logger_config import get_logger
logger = get_logger('concentrador.services.concentrador_service')

class ConcentradorService:
    """
    Servicio orquestador principal del concentrador de materiales.
    """
    HOJA_VIDRIO_AREA = 9.36  # 3.60 × 2.60 metros

    def __init__(
            self,
            cxc_repo: Optional[CXCRepository] = None,
            materiales_repo: Optional[MaterialesRepository] = None,
            paquetes_repo: Optional[PaquetesRepository] = None,
            concentrador_repo: Optional[ConcentradorRepository] = None
    ):
        self.cxc_repo = cxc_repo or CXCRepository()
        self.materiales_repo = materiales_repo or MaterialesRepository()
        self.paquetes_repo = paquetes_repo or PaquetesRepository()
        self.concentrador_repo = concentrador_repo or ConcentradorRepository()

        self.mapeador = MapeadorTipos()

        self.explosor_aluminio = ExplosorAluminio(self.materiales_repo)
        self.explosor_herreria = ExplosorHerreria(self.materiales_repo)
        self.explosor_herrajes = ExplosorHerrajes(self.materiales_repo)
        self.explosor_vidrio = ExplosorVidrio(self.materiales_repo)
        self.explosor_plasticos = ExplosorPlasticos(self.materiales_repo)
        self.explosor_otros = ExplosorOtros(self.materiales_repo)

        self.diagnostico_ejecutado = False
        self.tipos_paquete_conocidos: List[str] = []

        self.logger = configurar_logger()

        self._todas_advertencias: List[Dict] = []
        self._todos_errores: List[Dict] = []

    def ejecutar_concentracion(
            self,
            fecha_desde: Optional[date] = None,
            fecha_hasta: Optional[date] = None,
            almacenes_filtro: Optional[List[str]] = None,
            cxc_id: Optional[int] = None  # ← NUEVO PARÁMETRO
    ) -> ReporteConcentrado:
        """
        Ejecuta el proceso completo de concentración de materiales.

        Args:
            fecha_desde: Fecha desde para filtrar (opcional)
            fecha_hasta: Fecha hasta para filtrar (opcional)
            almacenes_filtro: Lista de almacenes a incluir (opcional)
            cxc_id: ID específico de CXC a explotar (opcional).
                   Si se proporciona, SOLO se explota ese CXC específico,
                   ignorando los filtros de fecha.

        Returns:
            ReporteConcentrado con los resultados de la concentración
        """
        registrar_info("INICIO_PROCESO", "Iniciando proceso de concentración de materiales")

        if not self.diagnostico_ejecutado:
            self._ejecutar_diagnostico_inicial()

        # ====================================================================
        # DETERMINAR QUÉ CXC PROCESAR
        # ====================================================================
        if cxc_id is not None:
            # MODO: Explosión de un CXC específico
            presupuestos = [{
                "cxc_id": cxc_id,
                "presupuesto_id": 0,
                "folio": "",
                "fecha_aceptacion": None
            }]
            registrar_info(
                "MODO_CXC_ESPECIFICO",
                f"Explosión de CXC específico: {cxc_id}",
                {"cxc_id": cxc_id}
            )
        else:
            # MODO: Todos los CXC aceptados (comportamiento original)
            try:
                presupuestos = self._obtener_presupuestos_filtrados(fecha_desde, fecha_hasta)
            except Exception as e:
                error_msg = f"Error crítico al obtener presupuestos aceptados: {str(e)}"
                registrar_error("ERROR_CRITICO", error_msg, {})
                return self._crear_reporte_vacio(error_msg)

        if not presupuestos:
            registrar_info("SIN_PRESUPUESTOS", "No se encontraron presupuestos aceptados")
            return self._crear_reporte_vacio("No hay presupuestos aceptados para procesar")

        registrar_info(
            "PRESUPUESTOS_ENCONTRADOS",
            f"Se encontraron {len(presupuestos)} presupuestos aceptados",
            {"total": len(presupuestos)}
        )

        # ====================================================================
        # PROCESAR CADA CXC
        # ====================================================================
        todos_materiales: List[MaterialConcentrado] = []
        total_partidas = 0

        for presupuesto in presupuestos:
            cxc_id_actual = presupuesto["cxc_id"]
            presupuesto_id = presupuesto["presupuesto_id"]

            try:
                partidas = self.cxc_repo.obtener_cantidades_por_cxc(cxc_id_actual)
            except Exception as e:
                self._registrar_error_con_texto(
                    "ERROR_PARTIDAS_CXC",
                    f"Error al obtener partidas para CXC {cxc_id_actual}: {str(e)}",
                    {"cxc_id": cxc_id_actual, "presupuesto_id": presupuesto_id}
                )
                continue

            for partida in partidas:
                partida_id = partida["partida_id"]
                cantidad_cxc = partida["cantidad_cxc"]

                if cantidad_cxc <= 0:
                    self._registrar_advertencia_con_texto(
                        "CANTIDAD_CXC_CERO",
                        f"Partida {partida_id} con cantidad CXC = 0, omitida",
                        {"partida_id": partida_id, "cxc_id": cxc_id_actual}
                    )
                    continue

                materiales_partida = self._procesar_partida(
                    partida_id, cantidad_cxc, cxc_id_actual, presupuesto_id
                )
                todos_materiales.extend(materiales_partida)
                total_partidas += 1

        # ====================================================================
        # CONSOLIDACIÓN
        # ====================================================================
        concentrado_por_almacen = self._concentrar_y_recalcular(todos_materiales)

        if almacenes_filtro:
            concentrado_por_almacen = self._aplicar_filtro_almacenes(
                concentrado_por_almacen, almacenes_filtro
            )

        total_materiales = sum(len(mats) for mats in concentrado_por_almacen.values())

        reporte = ReporteConcentrado(
            fecha_generacion=datetime.now(),
            total_presupuestos=len(presupuestos),
            total_partidas=total_partidas,
            total_materiales=total_materiales,
            materiales_por_almacen=concentrado_por_almacen,
            advertencias=self._todas_advertencias,
            errores=self._todos_errores
        )

        registrar_info(
            "FIN_PROCESO",
            f"Proceso completado. {total_materiales} materiales concentrados",
            {
                "presupuestos": len(presupuestos),
                "partidas": total_partidas,
                "materiales": total_materiales,
                "advertencias": len(self._todas_advertencias),
                "errores": len(self._todos_errores)
            }
        )

        return reporte

    def _concentrar_y_recalcular(self, materiales: List[MaterialConcentrado]) -> Dict[str, List[MaterialConcentrado]]:
        """
        Concentra materiales y recalcula unidades según reglas de negocio.
        REGLAS:
        - ALUMINIO: Suma metros_totales, luego recalcula tramos = CEIL(metros / largo)
        - VIDRIO: Suma m2_totales, luego recalcula hojas = CEIL(m2 / 9.36)
        - HERRERIA: Suma kilogramos_totales directamente
        - OTROS: Suma cantidad directamente
        """
        # PASO 1: Consolidar por (clave, almacen)
        consolidado_dict: Dict[Tuple[str, str], MaterialConcentrado] = {}

        for material in materiales:
            key = (material.clave, material.almacen)

            if key in consolidado_dict:
                existente = consolidado_dict[key]

                # Sumar según tipo de almacén
                if material.almacen == "ALUMINIO":
                    if material.metros_totales:
                        existente.metros_totales = (existente.metros_totales or 0) + material.metros_totales
                        existente.cantidad = existente.metros_totales

                elif material.almacen == "VIDRIO":
                    if material.m2_totales:
                        existente.m2_totales = (existente.m2_totales or 0) + material.m2_totales
                        existente.cantidad = existente.m2_totales

                elif material.almacen == "HERRERIA":
                    if material.kilogramos_totales:
                        existente.kilogramos_totales = (existente.kilogramos_totales or 0) + material.kilogramos_totales
                        existente.cantidad = existente.kilogramos_totales

                else:
                    # HERRAJES, PLASTICOS, OTROS - sumar cantidad directa
                    existente.cantidad += material.cantidad

                # Sumar métricas auxiliares
                if material.tramos_calculados:
                    existente.tramos_calculados = (existente.tramos_calculados or 0) + material.tramos_calculados
                if material.hojas_calculadas:
                    existente.hojas_calculadas = (existente.hojas_calculadas or 0) + material.hojas_calculadas
                if material.piezas_calculadas:
                    existente.piezas_calculadas = (existente.piezas_calculadas or 0) + material.piezas_calculadas

            else:
                consolidado_dict[key] = material

        # PASO 2: Recalcular unidades finales
        resultado_final: List[MaterialConcentrado] = []

        for material in consolidado_dict.values():
            if material.almacen == "ALUMINIO":
                if material.metros_totales and material.metros_totales > 0:
                    perfil = self.materiales_repo.obtener_material_aluminio(material.clave)
                    if perfil and perfil.get("largo"):
                        largo_tramo = perfil["largo"]
                        tramos = math.ceil(material.metros_totales / largo_tramo)
                        material.cantidad = float(tramos)
                        material.unidad = "Tramos"
                        material.tramos_calculados = tramos
                        registrar_info(
                            "RECALCULO_ALUMINIO",
                            f"Clave {material.clave}: {material.metros_totales:.2f}m → {tramos} tramos",
                            {"clave": material.clave, "metros": material.metros_totales, "tramos": tramos}
                        )
                    else:
                        self._registrar_advertencia_con_texto(
                            "LARGO_NO_DISPONIBLE",
                            f"No se pudo obtener largo para perfil {material.clave}",
                            {"clave": material.clave}
                        )

            elif material.almacen == "VIDRIO":
                if material.m2_totales and material.m2_totales > 0:
                    hojas = math.ceil(material.m2_totales / self.HOJA_VIDRIO_AREA)
                    material.cantidad = float(hojas)
                    material.unidad = "Hojas"
                    material.hojas_calculadas = hojas
                    registrar_info(
                        "RECALCULO_VIDRIO",
                        f"Clave {material.clave}: {material.m2_totales:.2f}m² → {hojas} hojas",
                        {"clave": material.clave, "m2": material.m2_totales, "hojas": hojas}
                    )

            elif material.almacen == "HERRERIA":
                material.unidad = "Kilogramos"

            elif material.almacen == "HERRAJES":
                # ← AGREGADO: Calcular piezas_calculadas para HERRAJES
                material.piezas_calculadas = int(material.cantidad)
                material.unidad = "Piezas"

            elif material.almacen in ["PLASTICOS", "OTROS"]:
                # ← AGREGADO: Calcular piezas_calculadas para PLASTICOS y OTROS
                material.piezas_calculadas = int(material.cantidad)
                material.unidad = "Piezas"

            resultado_final.append(material)

        # Agrupar por almacén
        resultado_por_almacen: Dict[str, List[MaterialConcentrado]] = defaultdict(list)
        for material in resultado_final:
            resultado_por_almacen[material.almacen].append(material)

        # Ordenar cada lista por clave
        for almacen in resultado_por_almacen:
            resultado_por_almacen[almacen].sort(key=lambda x: x.clave)

        return dict(resultado_por_almacen)

    def _ejecutar_diagnostico_inicial(self):
        """Ejecuta diagnóstico de paquetes una sola vez."""
        try:
            diagnostico = DiagnosticoPaquetes(self.concentrador_repo)
            resultados = diagnostico.ejecutar_diagnostico()
            self.tipos_paquete_conocidos = resultados.get("tipos_encontrados", [])

            for adv in resultados.get("advertencias", []):
                self._registrar_advertencia_con_texto("DIAGNOSTICO_PAQUETES", adv, {})

            registrar_info(
                "DIAGNOSTICO_COMPLETADO",
                f"Diagnóstico completado. Tipos encontrados: {self.tipos_paquete_conocidos}"
            )
        except Exception as e:
            self._registrar_error_con_texto("DIAGNOSTICO_FALLIDO", f"Error en diagnóstico: {str(e)}", {})

        self.diagnostico_ejecutado = True

    def _obtener_presupuestos_filtrados(self, fecha_desde: Optional[date], fecha_hasta: Optional[date]) -> List[Dict]:
        """Obtiene presupuestos aceptados con filtros opcionales."""
        presupuestos = self.cxc_repo.obtener_presupuestos_aceptados()

        if not presupuestos:
            return []

        if fecha_desde is None and fecha_hasta is None:
            return presupuestos

        resultados = []
        for p in presupuestos:
            fecha_aceptacion = p.get("fecha_aceptacion")
            if fecha_aceptacion is None:
                continue

            if hasattr(fecha_aceptacion, 'date'):
                fecha_aceptacion = fecha_aceptacion.date()

            if fecha_desde and fecha_aceptacion < fecha_desde:
                continue
            if fecha_hasta and fecha_aceptacion > fecha_hasta:
                continue

            resultados.append(p)

        return resultados

    def _procesar_partida(self, partida_id: int, cantidad_cxc: float, cxc_id: int, presupuesto_id: int) -> List[
        MaterialConcentrado]:
        """Procesa una partida completa."""
        materiales = []

        partida_completa = self.concentrador_repo.obtener_partida_completa(partida_id)

        for item in partida_completa.get("items", []):
            item["partida_id"] = partida_id
            item["cxc_id"] = cxc_id
            item["presupuesto_id"] = presupuesto_id
            materiales.extend(self._procesar_item(item, cantidad_cxc))

        for paquete in partida_completa.get("paquetes", []):
            paquete["partida_id"] = partida_id
            paquete["cxc_id"] = cxc_id
            paquete["presupuesto_id"] = presupuesto_id
            materiales.extend(self._procesar_paquete(paquete, cantidad_cxc))

        return materiales

    def _procesar_item(self, item: Dict[str, Any], cantidad_cxc: float) -> List[MaterialConcentrado]:
        """Procesa un item individual."""
        tipo_original = item.get("tipo", "")
        almacen_normalizado = self.mapeador.obtener_almacen_normalizado(tipo_original)

        if almacen_normalizado == "ALUMINIO":
            return self.explosor_aluminio.explotar(item, cantidad_cxc)
        elif almacen_normalizado == "HERRERIA":
            return self.explosor_herreria.explotar(item, cantidad_cxc)
        elif almacen_normalizado == "HERRAJES":
            return self.explosor_herrajes.explotar(item, cantidad_cxc)
        elif almacen_normalizado == "VIDRIO":
            return self.explosor_vidrio.explotar(item, cantidad_cxc)
        elif almacen_normalizado == "PLASTICOS":
            return self.explosor_plasticos.explotar(item, cantidad_cxc)
        else:
            return self.explosor_otros.explotar(item, cantidad_cxc)

    def _procesar_paquete(self, paquete: Dict[str, Any], cantidad_cxc: float) -> List[MaterialConcentrado]:
        """Procesa un paquete."""
        tipo_paquete = paquete.get("tipo_paquete", "")
        clave_paquete = paquete.get("clave_paquete", "")
        cantidad_paquetes = paquete.get("cantidad_paquetes", 1)
        ancho_paquete = paquete.get("ancho", 0.0)
        alto_paquete = paquete.get("alto", 0.0)

        tipo_normalizado = self.mapeador.normalizar_tipo_paquete(tipo_paquete)

        if tipo_normalizado.value == "DESCONOCIDO":
            self._registrar_advertencia_con_texto(
                "TIPO_PAQUETE_DESCONOCIDO",
                f"Tipo de paquete '{tipo_paquete}' no reconocido, omitido",
                {"tipo_paquete": tipo_paquete, "clave_paquete": clave_paquete}
            )
            return []

        item_fake = {
            "tipo": f"PAQUETE {tipo_normalizado.value}",
            "clave": clave_paquete,
            "partida_id": paquete.get("partida_id", 0),
            "cxc_id": paquete.get("cxc_id", 0),
            "presupuesto_id": paquete.get("presupuesto_id", 0)
        }

        context = {
            "cantidad_paquetes": cantidad_paquetes,
            "ancho": ancho_paquete,
            "alto": alto_paquete
        }

        if tipo_normalizado.value == "ALUMINIO":
            return self.explosor_aluminio.explotar(item_fake, cantidad_cxc, context)
        elif tipo_normalizado.value == "HERRAJES":
            return self.explosor_herrajes.explotar(item_fake, cantidad_cxc, context)

        return []

    def _aplicar_filtro_almacenes(self, concentrado: Dict, almacenes_filtro: List[str]) -> Dict:
        """Filtra el concentrado por lista de almacenes."""
        almacenes_set = set(a.upper() for a in almacenes_filtro)
        return {
            almacen: materiales
            for almacen, materiales in concentrado.items()
            if almacen.upper() in almacenes_set
        }

    def _crear_reporte_vacio(self, mensaje: str) -> ReporteConcentrado:
        """Crea un reporte vacío."""
        return ReporteConcentrado(
            fecha_generacion=datetime.now(),
            total_presupuestos=0,
            total_partidas=0,
            total_materiales=0,
            materiales_por_almacen={},
            advertencias=[{"mensaje": mensaje}],
            errores=[{"mensaje": mensaje}]
        )

    def _registrar_advertencia_con_texto(self, codigo: str, mensaje: str, datos: Dict):
        self._todas_advertencias.append({"codigo": codigo, "mensaje": mensaje, "datos": datos})
        registrar_advertencia(codigo, mensaje, datos)

    def _registrar_error_con_texto(self, codigo: str, mensaje: str, datos: Dict):
        self._todos_errores.append({"codigo": codigo, "mensaje": mensaje, "datos": datos})
        registrar_error(codigo, mensaje, datos)