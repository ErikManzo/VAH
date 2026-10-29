# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/controllers/paquetes_controller.py
Controlador de paquetes - VERSIÓN FINAL ARQUITECTÓNICA
PRINCIPIOS:
Separación de multiplicadores: piezas_paquete ≠ piezas_globales
Consolidación ÚNICA: solo al agregar paquete o modificar sus piezas/ancho/alto
Tabla anidada INFORMATIVA: no participa en cálculos ni guardado
PH se expanden recursivamente con multiplicador_ph
NUEVO (P3): reconstrucción perezosa del mapa paquete -> filas de materiales
(asegurar_mapeo / reconstruir_mapeo_carga) para presupuestos cargados de BD.
Elimina la duplicidad de componentes al editar un paquete recién cargado y
habilita la regla de dimensiones "sigue / se respeta" (P4).
"""
from typing import Optional, List, Dict, Any, Set
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QMessageBox
from ..models.paquete import Paquete
from ..models.componente_base import ComponenteBase
from ..core.utils import to_float as _f, to_int as _i
from ..core.constants import (
    C_TIPO, C_COLOR, C_CLAVE, C_DESC, C_CA, C_ANCHO, C_CH, C_ALTO, C_PZAS, C_PU, C_IMP,
)


def consolidar_componentes(componentes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Agrupa componentes idénticos (mismo tipo, clave, ancho, alto, ca, ch)
    sumando sus cantidades.
    """
    consolidados = {}
    for comp in componentes:
        key = (
            comp["tipo"],
            comp["clave"],
            comp["ancho"],
            comp["alto"],
            comp["ca"],
            comp["ch"]
        )
        if key in consolidados:
            consolidados[key]["piezas"] += comp["piezas"]
        else:
            consolidados[key] = comp.copy()
    return list(consolidados.values())


class PaquetesController(QObject):
    """
    Controlador que maneja la lógica de paquetes:
    - Carga de componentes en tabla anidada (INFORMATIVA)
    - Actualización por cambio de piezas, ancho, alto
    - Consolidación a tabla de materiales (donde ocurre el cálculo real)
    - Eliminación de materiales asociados al eliminar un paquete
    - Reconstrucción del mapa paquete->filas tras cargar de BD (P3)
    """
    paqueteCargado = pyqtSignal(str)  # clave del paquete cargado
    componentesConsolidados = pyqtSignal()  # cuando se consolidan a materiales

    def __init__(self, ventana, svc):
        super().__init__(ventana)
        self.ventana = ventana
        self.svc = svc
        # Estado del paquete activo (el que se muestra en anidada)
        self.paquete_activo_fila: int = -1
        self.paquete_activo_clave: str = ""
        self.paquete_activo_tipo: str = ""
        self.paquete_activo_ancho: float = 0.0
        self.paquete_activo_alto: float = 0.0
        self.paquete_activo_piezas: int = 1
        # Componentes base (SIN multiplicadores aplicados)
        self.componentes_base: List[ComponenteBase] = []
        # Mapa: fila del paquete -> lista de filas de materiales generadas
        self._materiales_generados: Dict[int, List[int]] = {}
        # Banderas de control
        self._consolidando: bool = False
        self._cargando: bool = False
        self._recalculando_color: bool = False
        # Conectar señales de las tablas personalizadas
        self.ventana.tbl_paquetes.paqueteAgregado.connect(self._on_paquete_agregado)
        self.ventana.tbl_paquetes.piezasCambiadas.connect(self._on_piezas_cambiadas)
        self.ventana.tbl_paquetes.anchoCambiado.connect(self._on_ancho_cambiado)
        self.ventana.tbl_paquetes.altoCambiado.connect(self._on_alto_cambiado)
        self.ventana.tbl_paquetes.paqueteEliminado.connect(self._on_paquete_eliminado)

    # ========================================================================
    # MÉTODOS PÚBLICOS (BANDERAS DE CONTROL)
    # ========================================================================
    def set_cargando(self, valor: bool) -> None:
        """Establece la bandera de carga de presupuesto."""
        self._cargando = valor

    def set_recalculando_color(self, valor: bool) -> None:
        """Establece la bandera de recálculo por color."""
        self._recalculando_color = valor

    def limpiar_estado(self) -> None:
        """Limpia el estado interno del controlador."""
        self.paquete_activo_fila = -1
        self.paquete_activo_clave = ""
        self.componentes_base.clear()
        # CORREGIDO (P3): el mapa de filas corresponde a la carga anterior;
        # se limpia en cada carga para evitar borrar filas equivocadas.
        self._materiales_generados.clear()

    # ========================================================================
    # NUEVO (P3): MAPA PAQUETE -> FILAS DE MATERIALES TRAS CARGA DE BD
    # ========================================================================
    def asegurar_mapeo(self) -> None:
        """
        Garantiza que _materiales_generados esté construido para la carga
        actual. Si el mapa ya tiene datos (sesión en vivo), no hace nada.
        Si está vacío y hay paquetes en tabla, lo reconstruye por coincidencia
        exacta con la definición de cada paquete.
        """
        if self._materiales_generados:
            return
        if self._consolidando or self._cargando:
            return
        if self.ventana.tbl_paquetes.rowCount() == 0:
            return
        self.reconstruir_mapeo_carga()

    def reconstruir_mapeo_carga(self) -> None:
        """
        Reconstruye _materiales_generados después de cargar un presupuesto
        desde BD, replicando la misma consolidación que se usó al guardar:
        cantidad_final = cantidad_base × multiplicador_ph × piezas_paquete,
        ca = horizontal, ch = vertical, ancho/alto = los del paquete.
        Las filas ya reclamadas por un paquete anterior se excluyen para no
        duplicar reclamos cuando dos paquetes comparten componentes.
        """
        if self._consolidando or self._cargando:
            return
        v = self.ventana
        if v.tbl_paquetes.rowCount() == 0:
            return
        reclamadas: Set[int] = set()
        for fila in range(v.tbl_paquetes.rowCount()):
            datos = v.tbl_paquetes.obtener_datos_paquete(fila)
            if datos.get("es_anidado"):
                continue
            tipo = datos.get("tipo", "")
            clave = datos.get("clave", "")
            ancho = float(datos.get("ancho", 0.0))
            alto = float(datos.get("alto", 0.0))
            piezas = int(datos.get("piezas", 1))
            self._cargar_componentes_base(clave, tipo)
            if not self.componentes_base:
                continue
            componentes_finales = []
            for comp in self.componentes_base:
                if comp.es_ph:
                    continue
                cantidad_final = comp.cantidad_base * comp.multiplicador_ph * piezas
                ca = comp.horizontal if comp.horizontal > 0 else 1.0
                ch = comp.vertical if comp.vertical > 0 else 1.0
                componentes_finales.append({
                    "tipo": comp.tipo,
                    "clave": comp.clave,
                    "ancho": ancho,
                    "alto": alto,
                    "ca": float(ca),
                    "ch": float(ch),
                    "piezas": int(cantidad_final),
                })
            consolidados = consolidar_componentes(componentes_finales)
            filas = []
            for comp in consolidados:
                r = self._buscar_componente_existente(comp, excluir=reclamadas)
                if r >= 0:
                    reclamadas.add(r)
                    filas.append(r)
            if filas:
                self._materiales_generados[fila] = filas
        self.componentes_base.clear()

    def filas_de_paquetes(self) -> Set[int]:
        """Devuelve el conjunto de filas de tbl generadas por paquetes."""
        self.asegurar_mapeo()
        out: Set[int] = set()
        for filas in self._materiales_generados.values():
            out.update(filas)
        return out

    def aplicar_dimensiones_paquete(self, fila: int, ancho: float, alto: float) -> None:
        """
        NUEVO (soporte P4): actualiza ancho/alto de un paquete en tbl_paquetes
        (sin señales) y re-consolida sus componentes con las nuevas dimensiones.
        """
        if self._consolidando or self._cargando:
            return
        self.asegurar_mapeo()
        v = self.ventana
        datos = v.tbl_paquetes.obtener_datos_paquete(fila)
        if datos.get("es_anidado"):
            return
        v.tbl_paquetes.set_ancho_sin_senal(fila, ancho)
        v.tbl_paquetes.set_alto_sin_senal(fila, alto)
        if self.paquete_activo_fila == fila:
            self.paquete_activo_ancho = ancho
            self.paquete_activo_alto = alto
        if not self.componentes_base or self.paquete_activo_fila != fila:
            self._cargar_componentes_base(datos["clave"], datos["tipo"])
            self.paquete_activo_fila = fila
            self.paquete_activo_clave = datos["clave"]
            self.paquete_activo_tipo = datos["tipo"]
            self.paquete_activo_piezas = datos["piezas"]
        self._consolidar_a_materiales(fila, datos["piezas"], ancho, alto)

    # ========================================================================
    # MANEJADORES DE SEÑALES
    # ========================================================================
    def _on_paquete_agregado(self, datos: dict) -> None:
        """Se ejecuta cuando el usuario agrega un paquete (desde la búsqueda)."""
        if self._consolidando or self._cargando or self._recalculando_color:
            return
        fila = datos.get("fila", self.ventana.tbl_paquetes.rowCount() - 1)
        clave = datos.get("clave", "")
        tipo = datos.get("tipo", "")
        ancho = datos.get("ancho", 0.0)
        alto = datos.get("alto", 0.0)
        piezas = datos.get("piezas", 1)
        descripcion = datos.get("descripcion", "")
        # Guardar estado del paquete activo
        self.paquete_activo_fila = fila
        self.paquete_activo_clave = clave
        self.paquete_activo_tipo = tipo
        self.paquete_activo_ancho = ancho
        self.paquete_activo_alto = alto
        self.paquete_activo_piezas = piezas
        # Cargar componentes base desde BD (con expansión recursiva de PH)
        self._cargar_componentes_base(clave, tipo)
        # Mostrar en tabla anidada (INFORMATIVO)
        self._mostrar_en_anidada(ancho, alto)
        # Activar visualización de tabla anidada
        self.ventana.gb_tabla_anidada.setVisible(True)
        self.ventana._tabla_anidada_activa = True
        self.ventana._paquete_anidado_actual = clave
        # Consolidar a materiales (ÚNICA VEZ)
        self._consolidar_a_materiales(fila, piezas, ancho, alto)
        self.paqueteCargado.emit(clave)

    def _on_piezas_cambiadas(self, fila: int, nuevas_piezas: int) -> None:
        """Cuando cambian las piezas del paquete madre."""
        if self._consolidando or self._cargando or self._recalculando_color:
            return
        self.asegurar_mapeo()
        datos = self.ventana.tbl_paquetes.obtener_datos_paquete(fila)
        if datos.get("es_anidado"):
            return
        # Actualizar estado
        if self.paquete_activo_fila == fila:
            self.paquete_activo_piezas = nuevas_piezas
        # Cargar componentes base si no están cargados
        if not self.componentes_base or self.paquete_activo_fila != fila:
            self._cargar_componentes_base(datos["clave"], datos["tipo"])
            self.paquete_activo_fila = fila
            self.paquete_activo_clave = datos["clave"]
            self.paquete_activo_tipo = datos["tipo"]
            self.paquete_activo_ancho = datos["ancho"]
            self.paquete_activo_alto = datos["alto"]
        # Re-consolidar con nuevas piezas
        self._consolidar_a_materiales(fila, nuevas_piezas, datos["ancho"], datos["alto"])
        # Actualizar tabla anidada
        if self.ventana._tabla_anidada_activa:
            self._mostrar_en_anidada(datos["ancho"], datos["alto"])

    def _on_ancho_cambiado(self, fila: int, nuevo_ancho: float) -> None:
        """Cuando cambia el ancho del paquete madre."""
        if self._consolidando or self._cargando or self._recalculando_color:
            return
        self.asegurar_mapeo()
        datos = self.ventana.tbl_paquetes.obtener_datos_paquete(fila)
        if datos.get("es_anidado"):
            return
        # Actualizar estado
        if self.paquete_activo_fila == fila:
            self.paquete_activo_ancho = nuevo_ancho
        # Cargar componentes base si no están cargados
        if not self.componentes_base or self.paquete_activo_fila != fila:
            self._cargar_componentes_base(datos["clave"], datos["tipo"])
            self.paquete_activo_fila = fila
            self.paquete_activo_clave = datos["clave"]
            self.paquete_activo_tipo = datos["tipo"]
            self.paquete_activo_piezas = datos["piezas"]
            self.paquete_activo_alto = datos["alto"]
        # Re-consolidar con nuevo ancho
        self._consolidar_a_materiales(fila, datos["piezas"], nuevo_ancho, datos["alto"])
        # Actualizar tabla anidada
        if self.ventana._tabla_anidada_activa:
            self._mostrar_en_anidada(nuevo_ancho, datos["alto"])

    def _on_alto_cambiado(self, fila: int, nuevo_alto: float) -> None:
        """Cuando cambia el alto del paquete madre."""
        if self._consolidando or self._cargando or self._recalculando_color:
            return
        self.asegurar_mapeo()
        datos = self.ventana.tbl_paquetes.obtener_datos_paquete(fila)
        if datos.get("es_anidado"):
            return
        # Actualizar estado
        if self.paquete_activo_fila == fila:
            self.paquete_activo_alto = nuevo_alto
        # Cargar componentes base si no están cargados
        if not self.componentes_base or self.paquete_activo_fila != fila:
            self._cargar_componentes_base(datos["clave"], datos["tipo"])
            self.paquete_activo_fila = fila
            self.paquete_activo_clave = datos["clave"]
            self.paquete_activo_tipo = datos["tipo"]
            self.paquete_activo_piezas = datos["piezas"]
            self.paquete_activo_ancho = datos["ancho"]
        # Re-consolidar con nuevo alto
        self._consolidar_a_materiales(fila, datos["piezas"], datos["ancho"], nuevo_alto)
        # Actualizar tabla anidada
        if self.ventana._tabla_anidada_activa:
            self._mostrar_en_anidada(datos["ancho"], nuevo_alto)

    def _on_paquete_eliminado(self, fila_paquete: int) -> None:
        """Manejador para cuando se elimina un paquete desde la tabla de paquetes."""
        self.asegurar_mapeo()
        self._eliminar_materiales_por_paquete(fila_paquete)
        if self.paquete_activo_fila == fila_paquete:
            self.ventana.tbl_anidada.limpiar()
            self.ventana.gb_tabla_anidada.setVisible(False)
            self.ventana._tabla_anidada_activa = False
            self.ventana._paquete_anidado_actual = None
            self.paquete_activo_fila = -1
            self.paquete_activo_clave = ""
            self.componentes_base.clear()
        self.ventana._recalc_summary()

    # ========================================================================
    # MÉTODOS PRIVADOS - CARGA DE COMPONENTES
    # ========================================================================
    def _cargar_componentes_base(self, clave_paquete: str, tipo_paquete: str) -> None:
        """
        Carga los componentes base del paquete desde la BD.
        Expande recursivamente los PH con su multiplicador correspondiente.
        """
        self.componentes_base.clear()
        # Obtener items desde BD
        if tipo_paquete.startswith("PAQUETE ALUMINIO"):
            items = self.svc.paquete_aluminio_items(clave_paquete)
        elif tipo_paquete.startswith("PAQUETE HERRAJES"):
            items = self.svc.paquete_herrajes_items(clave_paquete)
        else:
            return
        for item in items:
            tipo = item.get("tipo", "").strip().upper()
            clave = item.get("clave", "").strip()
            cantidad = float(item.get("cantidad", 1))
            horizontal = float(item.get("horizontal", 0))
            vertical = float(item.get("vertical", 0))
            if tipo == "PH":
                # Es un paquete anidado de herrajes
                comp_ph = ComponenteBase(
                    tipo="PH",
                    clave=clave,
                    descripcion=item.get("descripcion", "").strip(),
                    cantidad_base=1,
                    horizontal=horizontal,
                    vertical=vertical,
                    multiplicador_ph=1,
                    es_ph=True,
                    datos_originales=item
                )
                self.componentes_base.append(comp_ph)
                # Expandir recursivamente los componentes del PH
                self._expandir_componentes_ph(clave, cantidad, horizontal, vertical)
            else:
                # Componente normal
                self.componentes_base.append(ComponenteBase(
                    tipo=tipo,
                    clave=clave,
                    descripcion=item.get("descripcion", "").strip(),
                    cantidad_base=cantidad,
                    horizontal=horizontal,
                    vertical=vertical,
                    multiplicador_ph=1,
                    es_ph=False,
                    datos_originales=item
                ))

    def _expandir_componentes_ph(self, clave_ph: str, multiplicador: float,
                                 horizontal: float, vertical: float) -> None:
        """
        Expande recursivamente los componentes de un paquete PH.
        Aplica el multiplicador a todos los componentes hijos.
        """
        try:
            items_ph = self.svc.paquete_herrajes_items(clave_ph)
            for item in items_ph:
                tipo = item.get("tipo", "").strip().upper()
                clave = item.get("clave", "").strip()
                cantidad = float(item.get("cantidad", 1))
                # Si el PH contiene otro PH, expandir recursivamente
                if tipo == "PH":
                    comp_ph = ComponenteBase(
                        tipo="PH",
                        clave=clave,
                        descripcion=item.get("descripcion", "").strip(),
                        cantidad_base=1,
                        horizontal=horizontal,
                        vertical=vertical,
                        multiplicador_ph=multiplicador,
                        es_ph=True,
                        datos_originales=item
                    )
                    self.componentes_base.append(comp_ph)
                    self._expandir_componentes_ph(clave, cantidad * multiplicador, horizontal, vertical)
                else:
                    # Componente normal con multiplicador del PH padre
                    self.componentes_base.append(ComponenteBase(
                        tipo=tipo,
                        clave=clave,
                        descripcion=item.get("descripcion", "").strip(),
                        cantidad_base=cantidad,
                        horizontal=horizontal,
                        vertical=vertical,
                        multiplicador_ph=multiplicador,
                        es_ph=False,
                        datos_originales=item
                    ))
        except Exception as e:
            print(f"Error expandiendo PH {clave_ph}: {e}")

    def _mostrar_en_anidada(self, ancho: float, alto: float) -> None:
        """Muestra los componentes base en la tabla anidada (SOLO INFORMATIVO)."""
        self.ventana.tbl_anidada.limpiar()
        color = self.ventana._get_color_partida_o_global()
        for comp in self.componentes_base:
            if comp.es_ph:
                # Los PH se muestran como referencia (no se calculan en anidada)
                self.ventana.tbl_anidada.agregar_componente(
                    {
                        "tipo": comp.tipo,
                        "clave": comp.clave,
                        "descripcion": comp.descripcion,
                        "cantidad_base": int(comp.multiplicador_ph),
                        "horizontal": comp.horizontal,
                        "vertical": comp.vertical,
                    },
                    ancho, alto, color
                )
            else:
                # Componentes normales: mostrar cantidad_base × multiplicador_ph
                cantidad_mostrar = int(comp.cantidad_base * comp.multiplicador_ph)
                self.ventana.tbl_anidada.agregar_componente(
                    {
                        "tipo": comp.tipo,
                        "clave": comp.clave,
                        "descripcion": comp.descripcion,
                        "cantidad_base": cantidad_mostrar,
                        "horizontal": comp.horizontal,
                        "vertical": comp.vertical,
                    },
                    ancho, alto, color
                )
        # Recalcular P.U. en tabla anidada
        for r in range(self.ventana.tbl_anidada.rowCount()):
            self.ventana._calc_anidada_row(r)

    # ========================================================================
    # MÉTODOS PRIVADOS - CONSOLIDACIÓN A MATERIALES
    # ========================================================================
    def recalcular_fila(self, fila: int) -> None:
        """Alias para _consolidar_a_materiales (retrocompatibilidad)."""
        self._consolidar_a_materiales(fila)

    def _consolidar_a_materiales(self, fila_paquete: int, piezas_paquete: int = None,
                                 ancho_paquete: float = None, alto_paquete: float = None) -> None:
        """
        Toma los componentes base, aplica multiplicadores y los consolida en tbl.
        FÓRMULA: cantidad_final = cantidad_base × multiplicador_ph × piezas_paquete
        """
        if self._consolidando or self._cargando or self._recalculando_color:
            return
        # Si no se pasan dimensiones, obtenerlas de la tabla
        if piezas_paquete is None or ancho_paquete is None or alto_paquete is None:
            datos = self.ventana.tbl_paquetes.obtener_datos_paquete(fila_paquete)
            piezas_paquete = piezas_paquete if piezas_paquete is not None else datos.get("piezas", 1)
            ancho_paquete = ancho_paquete if ancho_paquete is not None else datos.get("ancho", 0.0)
            alto_paquete = alto_paquete if alto_paquete is not None else datos.get("alto", 0.0)
        if not self.componentes_base:
            return
        self._consolidando = True
        try:
            componentes_finales = []
            color = self.ventana._get_color_partida_o_global()
            for comp in self.componentes_base:
                if comp.es_ph:
                    # Los PH no se insertan en materiales (solo sus hijos ya expandidos)
                    continue
                # FÓRMULA CORRECTA
                cantidad_final = comp.cantidad_base * comp.multiplicador_ph * piezas_paquete
                ca = comp.horizontal if comp.horizontal > 0 else 1.0
                ch = comp.vertical if comp.vertical > 0 else 1.0
                comp_final = {
                    "tipo": comp.tipo,
                    "color": color,
                    "clave": comp.clave,
                    "descripcion": comp.descripcion,
                    "ca": float(ca),
                    "ancho": float(ancho_paquete),
                    "ch": float(ch),
                    "alto": float(alto_paquete),
                    "piezas": int(cantidad_final),
                }
                componentes_finales.append(comp_final)
            # Consolidar componentes idénticos
            consolidados = consolidar_componentes(componentes_finales)
            # Eliminar materiales previos de este paquete
            self._eliminar_materiales_por_paquete(fila_paquete)
            # Insertar en tabla de materiales
            nuevas_filas = []
            for comp in consolidados:
                fila_existente = self._buscar_componente_existente(comp)
                if fila_existente >= 0:
                    item = self.ventana.tbl.item(fila_existente, C_PZAS)
                    if item:
                        actual = _f(item.text(), 0)
                        item.setText(f"{int(actual + comp['piezas'])}")
                        self.ventana._calc_std_row(fila_existente)
                    nuevas_filas.append(fila_existente)
                else:
                    r = self.ventana.tbl.rowCount()
                    self.ventana.tbl.insertRow(r)
                    self.ventana._set_or_update_item(self.ventana.tbl, r, C_TIPO, comp["tipo"], editable=False)
                    self.ventana._set_or_update_item(self.ventana.tbl, r, C_COLOR, comp["color"], editable=False)
                    self.ventana._set_or_update_item(self.ventana.tbl, r, C_CLAVE, comp["clave"], editable=False)
                    self.ventana._set_or_update_item(self.ventana.tbl, r, C_DESC, comp["descripcion"], editable=False)
                    self.ventana._set_or_update_item(self.ventana.tbl, r, C_CA, f"{comp['ca']:.0f}", editable=True)
                    self.ventana._set_or_update_item(self.ventana.tbl, r, C_ANCHO, f"{comp['ancho']:.2f}",
                                                     editable=True)
                    self.ventana._set_or_update_item(self.ventana.tbl, r, C_CH, f"{comp['ch']:.0f}", editable=True)
                    self.ventana._set_or_update_item(self.ventana.tbl, r, C_ALTO, f"{comp['alto']:.2f}", editable=True)
                    self.ventana._set_or_update_item(self.ventana.tbl, r, C_PZAS, f"{int(comp['piezas'])}",
                                                     editable=True)
                    self.ventana._set_or_update_item(self.ventana.tbl, r, C_PU, "0.00", editable=False)
                    self.ventana._set_or_update_item(self.ventana.tbl, r, C_IMP, "0.00", editable=False)
                    self.ventana._apply_editabilidad_std(r)
                    self.ventana._calc_std_row(r)
                    nuevas_filas.append(r)
            self._materiales_generados[fila_paquete] = nuevas_filas
        finally:
            self._consolidando = False
        self.ventana._recalc_summary()
        self.componentesConsolidados.emit()

    def _buscar_componente_existente(self, comp: Dict[str, Any], excluir: Optional[Set[int]] = None) -> int:
        """Busca un componente idéntico en la tabla de materiales."""
        ancho_comp = float(comp["ancho"])
        alto_comp = float(comp["alto"])
        ca_comp = float(comp["ca"])
        ch_comp = float(comp["ch"])
        for r in range(self.ventana.tbl.rowCount()):
            if excluir is not None and r in excluir:
                continue
            if (self.ventana._safe_text(self.ventana.tbl, r, C_TIPO) == comp["tipo"] and
                    self.ventana._safe_text(self.ventana.tbl, r, C_CLAVE) == comp["clave"] and
                    abs(_f(self.ventana._safe_text(self.ventana.tbl, r, C_ANCHO)) - ancho_comp) < 0.001 and
                    abs(_f(self.ventana._safe_text(self.ventana.tbl, r, C_ALTO)) - alto_comp) < 0.001 and
                    abs(_f(self.ventana._safe_text(self.ventana.tbl, r, C_CA)) - ca_comp) < 0.001 and
                    abs(_f(self.ventana._safe_text(self.ventana.tbl, r, C_CH)) - ch_comp) < 0.001):
                return r
        return -1

    def _eliminar_materiales_por_paquete(self, fila_paquete: int) -> None:
        """Elimina de la tabla de materiales todas las filas generadas por un paquete."""
        filas_a_eliminar = self._materiales_generados.pop(fila_paquete, [])
        for r in sorted(filas_a_eliminar, reverse=True):
            if r < self.ventana.tbl.rowCount():
                self.ventana.tbl.removeRow(r)