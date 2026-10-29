# -*- coding: utf-8 -*-
"""
Clases de datos para el concentrador de materiales
MaterialConcentrado: Almacena información de un material ya concentrado
ReporteConcentrado: Almacena resumen ejecutivo del proceso
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any

@dataclass
class MaterialConcentrado:
    """
    Representa un material concentrado listo para reporte.
    REGLAS DE CONSOLIDACIÓN:
    - ALUMINIO: Consolidar metros_totales, luego recalcular tramos
    - VIDRIO: Consolidar m2_totales, luego recalcular hojas
    - HERRERIA: Consolidar metros_totales, luego recalcular tramos (6m)
    - HERRAJES/PLASTICOS/OTROS: Consolidar cantidad directamente
    """

    # Campos obligatorios
    clave: str
    descripcion: str
    almacen: str
    presupuesto_id: int
    partida_id: int
    cxc_id: int
    tipo_original: str
    origen: str
    cantidad_cxc_original: float

    # Campos de cantidad (cambian durante el proceso)
    cantidad: float
    unidad: str

    # Campos base para consolidación
    metros_totales: Optional[float] = None
    m2_totales: Optional[float] = None
    kilogramos_totales: Optional[float] = None

    # Campos calculados post-consolidación
    tramos_calculados: Optional[int] = None
    hojas_calculadas: Optional[int] = None
    piezas_calculadas: Optional[int] = None  # ← AGREGADO: Para HERRAJES/PLASTICOS/OTROS

    # Datos originales del item
    ancho_original: Optional[float] = None
    alto_original: Optional[float] = None
    ca_original: Optional[float] = None
    ch_original: Optional[float] = None
    kg_por_metro: Optional[float] = None
    largo_tramo: Optional[float] = None  # Para ALUMINIO

    def __hash__(self):
        return hash((self.clave, self.almacen))

    def __eq__(self, other):
        if not isinstance(other, MaterialConcentrado):
            return False
        return self.clave == other.clave and self.almacen == other.almacen

@dataclass
class ReporteConcentrado:
    """Resumen ejecutivo del proceso de concentración."""
    fecha_generacion: datetime
    total_presupuestos: int
    total_partidas: int
    total_materiales: int
    materiales_por_almacen: Dict[str, List[MaterialConcentrado]]
    advertencias: List[Dict[str, Any]] = field(default_factory=list)
    errores: List[Dict[str, Any]] = field(default_factory=list)
    resumen_por_almacen: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        self.resumen_por_almacen = {
            almacen: len(materiales)
            for almacen, materiales in self.materiales_por_almacen.items()
        }

    def tiene_materiales(self) -> bool:
        return self.total_materiales > 0

    def tiene_advertencias(self) -> bool:
        return len(self.advertencias) > 0

    def tiene_errores(self) -> bool:
        return len(self.errores) > 0