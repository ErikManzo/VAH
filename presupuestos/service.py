# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/service.py
Servicio unificado (Fachada) del módulo de presupuestos.
Delega todas las operaciones a los servicios especializados.
ARQUITECTURA: Service Layer Pattern
Última actualización: 2026
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Iterable, Tuple
from presupuestos.services.database_service import DatabaseService
from presupuestos.services.pricing_service import PricingService
from presupuestos.services.material_service import MaterialService
from presupuestos.services.cliente_service import ClienteService
from presupuestos.services.presupuesto_repository import PresupuestoRepository
from presupuestos.services.partida_repository import PartidaRepository
from presupuestos.services.paquete_service import PaqueteService
from presupuestos.services.email_service import EmailService
from presupuestos.services.config_service import ConfigService
from presupuestos.core.search.search_ui_builder import SearchUIBuilder


class Service:
    def __init__(self) -> None:
        # Instanciación de la nueva arquitectura modular
        self.db_service = DatabaseService()
        self.pricing_service = PricingService(self.db_service)
        self.material_service = MaterialService(self.db_service)
        self.cliente_service = ClienteService(self.db_service)
        self.presupuesto_repo = PresupuestoRepository(self.db_service)
        self.partida_repo = PartidaRepository(self.db_service)
        self.paquete_service = PaqueteService(self.db_service, self.material_service)
        self.email_service = EmailService(self.db_service)
        self.config_service = ConfigService(self.db_service)
        self.ui_builder = SearchUIBuilder()

    # ------------------------------------------------------------------------
    # - Conexión y Helpers (Delegados a db_service) -
    # ------------------------------------------------------------------------
    def connect(self):
        return self.db_service.connect()

    def cursor(self):
        return self.db_service.cursor()

    def _fetchone(self, sql: str, params: Iterable[Any]) -> Optional[tuple]:
        return self.db_service.fetchone(sql, list(params))

    def _fetchall(self, sql: str, params: Iterable[Any]) -> List[tuple]:
        return self.db_service.fetchall(sql, list(params))

    # ------------------------------------------------------------------------
    # - Búsqueda (Delegados a material_service y cliente_service) -
    # ------------------------------------------------------------------------
    def buscar_por_tabla(self, **kwargs):
        return self.material_service.buscar_por_tabla(**kwargs)

    def buscar_por_tipo(self, tipo: str, buscar_por: str, filtro: str):
        return self.material_service.buscar_por_tipo(tipo, buscar_por, filtro)

    def clientes_buscar(self, filtro: str):
        return self.cliente_service.clientes_buscar(filtro)

    # ------------------------------------------------------------------------
    # - Precios (Delegados a pricing_service) -
    # ------------------------------------------------------------------------
    def aluminio_largo(self, clave: str):
        return self.pricing_service.aluminio_largo(clave)

    def aluminio_precio(self, clave: str, color: Optional[str]):
        return self.pricing_service.aluminio_precio(clave, color)

    def vidrio_precio(self, clave: str):
        return self.pricing_service.vidrio_precio(clave)

    def herreria_kg_por_m(self, clave: str):
        return self.pricing_service.herreria_kg_por_m(clave)

    def plasticos_precio(self, clave: str):
        return self.pricing_service.plasticos_precio(clave)

    def otros_precio(self, clave: str):
        return self.pricing_service.otros_precio(clave)

    def herrajes_precio(self, clave: str):
        return self.pricing_service.herrajes_precio(clave)

    def paquete_aluminio_precio_total(self, clave_paquete: str) -> float:
        return self.pricing_service.paquete_aluminio_precio_total(clave_paquete)

    def paquete_herrajes_precio_total(self, clave_paquete: str) -> float:
        return self.pricing_service.paquete_herrajes_precio_total(clave_paquete)

    def try_precio_generico(self, tipo: str, clave: str):
        return self.pricing_service.try_precio_generico(tipo, clave)

    # ------------------------------------------------------------------------
    # - Descripción de materiales (Delegado a material_service) -
    # ------------------------------------------------------------------------
    def obtener_descripcion_material(self, tipo: str, clave: str):
        return self.material_service.obtener_descripcion_material(tipo, clave)

    # ------------------------------------------------------------------------
    # - Presupuestos (Delegados a presupuesto_repo) -
    # ------------------------------------------------------------------------
    def guardar_presupuesto(self, datos: dict):
        return self.presupuesto_repo.guardar_presupuesto(datos)

    def listar_presupuestos(self):
        return self.presupuesto_repo.listar_presupuestos()

    def obtener_presupuesto(self, presupuesto_id: int):
        return self.presupuesto_repo.obtener_presupuesto(presupuesto_id)

    def obtener_ultimo_numero_presupuesto(self):
        return self.presupuesto_repo.obtener_ultimo_numero()

    def buscar_presupuestos(self, filtros: Dict[str, Any]):
        return self.presupuesto_repo.buscar_presupuestos(filtros)

    def actualizar_color_global_presupuesto(self, presupuesto_id: int, nuevo_color: str) -> bool:
        """
        NUEVO (corrección color_global): Delegado del UPDATE dirigido de
        color_global en la tabla presupuestos.
        """
        return self.presupuesto_repo.actualizar_color_global(presupuesto_id, nuevo_color)

    # ------------------------------------------------------------------------
    # - Partidas (Delegados a partida_repo) -
    # ------------------------------------------------------------------------
    def guardar_partida(self, datos: dict):
        return self.partida_repo.guardar_partida(datos)

    def guardar_items_partida(self, partida_id: int, items: List[Dict[str, Any]]):
        return self.partida_repo.guardar_items(partida_id, items)

    def obtener_partidas(self, presupuesto_id: int):
        return self.partida_repo.obtener_partidas(presupuesto_id)

    def obtener_items_partida(self, partida_id: int):
        return self.partida_repo.obtener_items_partida(partida_id)

    # ------------------------------------------------------------------------
    # - Paquetes (Delegados a paquete_service) -
    # ------------------------------------------------------------------------
    def paquete_aluminio_items(self, clave_paquete: str):
        return self.paquete_service.paquete_aluminio_items(clave_paquete)

    def paquete_herrajes_items(self, clave_paquete: str):
        return self.paquete_service.paquete_herrajes_items(clave_paquete)

    def guardar_paquetes_partida(self, partida_id: int, paquetes: List[Dict[str, Any]]):
        return self.paquete_service.guardar_paquetes_partida(partida_id, paquetes)

    def obtener_paquetes_partida(self, partida_id: int):
        return self.paquete_service.obtener_paquetes_partida(partida_id)

    # ------------------------------------------------------------------------
    # - Configuración (Delegados a config_service) -
    # ------------------------------------------------------------------------
    def obtener_parametros_sistema(self):
        return self.config_service.obtener_parametros_sistema()

    def guardar_parametros_sistema(self, p: Dict[str, Any]):
        return self.config_service.guardar_parametros_sistema(p)

    def verificar_clave_admin(self, clave: str) -> bool:
        return self.config_service.verificar_clave_admin(clave)

    def cambiar_clave_admin(self, nueva_clave: str):
        return self.config_service.cambiar_clave_admin(nueva_clave)

    def obtener_clave_admin(self) -> Optional[str]:
        """Obtiene la clave de administrador desde config.json (delegado)."""
        return self.config_service.obtener_clave_admin()

    def obtener_numero_presupuesto_inicial(self):
        return self.config_service.obtener_numero_presupuesto_inicial()

    def cambiar_numero_presupuesto_inicial(self, nuevo_numero: int):
        return self.config_service.cambiar_numero_presupuesto_inicial(nuevo_numero)

    def obtener_configuracion_correo(self):
        return self.config_service.obtener_configuracion_correo()

    def guardar_configuracion_correo(self, config_correo: Dict[str, Any]):
        return self.config_service.guardar_configuracion_correo(config_correo)

    def obtener_configuracion_presupuesto(self, presupuesto_id: int) -> Dict[str, Any]:
        """Notas, forma de pago, plazo de entrega y descuento_porcentaje."""
        return self.config_service.obtener_configuracion_presupuesto(presupuesto_id)

    def guardar_configuracion_presupuesto(self, presupuesto_id: int, notas: str,
                                          forma_pago: str, plazo_entrega: str,
                                          descuento: Optional[float] = None) -> bool:
        """
        NUEVO: acepta 'descuento' opcional; si es None no toca la columna
        descuento_porcentaje.
        """
        return self.config_service.guardar_configuracion_presupuesto(
            presupuesto_id, notas, forma_pago, plazo_entrega, descuento)

    # ------------------------------------------------------------------------
    # - Email (Delegados a email_service) -
    # ------------------------------------------------------------------------
    def enviar_correo_presupuesto(self, para: str, asunto: str, mensaje: str, ruta_pdf: str, parametros: Dict[str, Any]):
        return self.email_service.enviar_correo_presupuesto(para, asunto, mensaje, ruta_pdf, parametros)