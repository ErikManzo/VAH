# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/controllers/presupuesto_controller.py
Controlador para la gestión de presupuestos y partidas.
VERSIÓN FINAL:
- recalcular_por_color() maneja VARIOS y color específico correctamente
- Actualiza TODAS las partidas del presupuesto en BD
- Usa dispatch_calculo para consistencia BD/UI (misma fórmula que F5)
- duplicar_presupuesto_actual() respeta color_global = "VARIOS"
- recalcular_por_color() persiste color_global en el encabezado del presupuesto
- vista_previa_pdf() para vista previa con QPdfView
- enviar_por_email() para envío automático por Outlook
- NUEVO: Los métodos exportar_pdf(), vista_previa_pdf() y enviar_por_email()
  ahora abren el diálogo de configuración (notas, forma de pago, descuento, plazo)
  antes de generar el PDF
- NUEVO: vista_previa_pdf() pasa correctamente presupuesto_num y cliente al diálogo
Última actualización: 2026
"""
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Any, List, Optional
from datetime import datetime
from common.logger_config import get_logger, setup_logger
from ..core.utils import to_float as _f, to_int as _i

setup_logger("presupuestos.controllers.presupuesto_controller")
logger = get_logger("presupuestos.controllers.presupuesto_controller")


class PresupuestoController(QObject):
    presupuestoGuardado = pyqtSignal(int)
    partidaGuardada = pyqtSignal(int)
    partidaCambiada = pyqtSignal(int, int)
    listaPartidasActualizada = pyqtSignal(list)

    def __init__(self, ventana, svc):
        super().__init__(ventana)
        self.ventana = ventana
        self.svc = svc
        self.presupuesto_id: Optional[int] = None
        self.partida_id: Optional[int] = None
        self.presupuesto_numero: Optional[int] = None
        self._cargando = False
        self._partidas_cache: List[Dict[str, Any]] = []
        self._indice_partida_actual: int = -1

    def _to_int(self, val):
        if val is None:
            return 0
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    def _to_float(self, val):
        if val is None:
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    def _actualizar_cache_partidas(self):
        if not self.presupuesto_id:
            self._partidas_cache = []
            self._indice_partida_actual = -1
            self.listaPartidasActualizada.emit([])
            return
        self._partidas_cache = self.svc.obtener_partidas(self.presupuesto_id)
        self._partidas_cache.sort(key=lambda p: self._to_int(p.get('partida', 0)))
        lista_nombres = []
        for p in self._partidas_cache:
            num = self._to_int(p.get('partida', 0))
            titulo = p.get('titulo', '') or 'Sin título'
            if len(titulo) > 40:
                titulo = titulo[:37] + '...'
            lista_nombres.append(f"{num} - {titulo}")
        self.listaPartidasActualizada.emit(lista_nombres)
        self._indice_partida_actual = -1
        for i, p in enumerate(self._partidas_cache):
            if p['id'] == self.partida_id:
                self._indice_partida_actual = i
                break
        self._actualizar_botones_navegacion()

    def _actualizar_botones_navegacion(self):
        if hasattr(self.ventana, 'btn_partida_anterior'):
            self.ventana.btn_partida_anterior.setEnabled(self._indice_partida_actual > 0)
        if hasattr(self.ventana, 'btn_partida_siguiente'):
            self.ventana.btn_partida_siguiente.setEnabled(
                self._indice_partida_actual >= 0 and self._indice_partida_actual < len(self._partidas_cache) - 1
            )

    def guardar_partida_actual_silencioso(self) -> bool:
        if not self._hay_datos_en_partida() and self.partida_id is not None:
            return True
        try:
            self._cargando = True
            datos_presupuesto = self._recolectar_datos_presupuesto()
            if not datos_presupuesto:
                if self.presupuesto_id is None:
                    return False
            else:
                if self.presupuesto_id is None:
                    self.presupuesto_id = self.svc.guardar_presupuesto(datos_presupuesto)
                    if not self.presupuesto_id:
                        return False
            datos_partida = self._recolectar_datos_partida()
            if not datos_partida:
                return True
            datos_partida['presupuesto_id'] = self.presupuesto_id
            self.partida_id = self.svc.guardar_partida(datos_partida)
            if not self.partida_id:
                return False
            items = self._recolectar_items_partida()
            self.svc.guardar_items_partida(self.partida_id, items)
            paquetes = self._recolectar_paquetes_partida()
            self.svc.guardar_paquetes_partida(self.partida_id, paquetes)
            self.presupuestoGuardado.emit(self.presupuesto_id)
            self.partidaGuardada.emit(self.partida_id)
            self._actualizar_cache_partidas()
            return True
        except Exception as e:
            logger.exception("guardar_partida_actual_silencioso: Excepcion")
            return False
        finally:
            self._cargando = False

    def _hay_datos_en_partida(self) -> bool:
        if self.ventana.le_titulo.text().strip():
            return True
        if self.ventana.te_desc.toPlainText().strip():
            return True
        if self.ventana.cbo_color.currentText().strip():
            return True
        if self.ventana.tbl.rowCount() > 0:
            return True
        if self.ventana.tbl_he.rowCount() > 0:
            return True
        if self.ventana.tbl_paquetes.rowCount() > 0:
            return True
        if self.ventana.sb_desperdicio.value() != 2:
            return True
        if self.ventana.sb_fv_pct.value() != 25:
            return True
        if self.ventana.sp_ancho.value() != 0.0:
            return True
        if self.ventana.sp_alto.value() != 0.0:
            return True
        if self.ventana.sp_mo.value() != 0.0:
            return True
        if self.ventana.sp_acc.value() != 0.0:
            return True
        if self.ventana.sb_pzas_global.value() != 1:
            return True
        return False

    def partida_anterior(self):
        if self._indice_partida_actual <= 0:
            return
        self.guardar_partida_actual_silencioso()
        partida = self._partidas_cache[self._indice_partida_actual - 1]
        self._cargar_partida_especifica(partida)
        self.partida_id = partida['id']
        self.ventana.sp_partida.setValue(self._to_int(partida['partida']))
        self._actualizar_cache_partidas()
        self.partidaCambiada.emit(self._indice_partida_actual - 1, self.partida_id)

    def partida_siguiente(self):
        if self._indice_partida_actual < 0 or self._indice_partida_actual >= len(self._partidas_cache) - 1:
            return
        self.guardar_partida_actual_silencioso()
        partida = self._partidas_cache[self._indice_partida_actual + 1]
        self._cargar_partida_especifica(partida)
        self.partida_id = partida['id']
        self.ventana.sp_partida.setValue(self._to_int(partida['partida']))
        self._actualizar_cache_partidas()
        self.partidaCambiada.emit(self._indice_partida_actual + 1, self.partida_id)

    def cargar_partida_por_indice(self, indice: int):
        if indice < 0 or indice >= len(self._partidas_cache):
            return
        if indice == self._indice_partida_actual:
            return
        self.guardar_partida_actual_silencioso()
        partida = self._partidas_cache[indice]
        self._cargar_partida_especifica(partida)
        self.partida_id = partida['id']
        self.ventana.sp_partida.setValue(self._to_int(partida['partida']))
        self._indice_partida_actual = indice
        self._actualizar_botones_navegacion()
        self.partidaCambiada.emit(indice, self.partida_id)

    def obtener_indice_actual(self) -> int:
        return self._indice_partida_actual

    def obtener_total_partidas(self) -> int:
        return len(self._partidas_cache)

    def _cargar_partida_especifica(self, partida: Dict[str, Any]):
        self.ventana._prog = True
        try:
            self.ventana.sp_partida.setValue(self._to_int(partida['partida']))
            self.ventana.le_titulo.setText(partida['titulo'] or '')
            self.ventana.te_desc.setPlainText(partida['descripcion'] or '')
            self.ventana.cbo_color.setCurrentText(partida['color_partida'] or '')
            self.ventana.sb_desperdicio.setValue(self._to_int(partida['desperdicio']))
            self.ventana.sb_fv_pct.setValue(self._to_int(partida['fv_porcentaje']))
            self.ventana.sp_kg.setValue(self._to_float(partida['kg']))
            self.ventana.sp_ancho.setValue(self._to_float(partida['ancho']))
            self.ventana.sp_alto.setValue(self._to_float(partida['alto']))
            self.ventana.sp_mo.setValue(self._to_float(partida['mano_obra']))
            self.ventana.sp_acc.setValue(self._to_float(partida['accesorios']))
            self.ventana.sb_pzas_global.setValue(self._to_int(partida['piezas']))
            self.ventana.sp_pu_partida.setValue(self._to_float(partida['precio_unitario']))
            self.ventana.sp_total_partida.setValue(self._to_float(partida['total_partida']))
            self.ventana.tbl.setRowCount(0)
            self.ventana.tbl_he.setRowCount(0)
            self.ventana.tbl_paquetes.setRowCount(0)
            self.ventana.tbl_anidada.limpiar()
            self.ventana.gb_tabla_anidada.setVisible(False)
            self.ventana._tabla_anidada_activa = False
            self.ventana._paquete_anidado_actual = None
            self.ventana.paquetes_ctrl.set_cargando(True)
            try:
                items = self.svc.obtener_items_partida(partida['id'])
                for item in items:
                    tipo = item['tipo'].upper()
                    if tipo in ['HERRERIA', 'HERRERÍA']:
                        self._agregar_item_herreria(item)
                    else:
                        self._agregar_item_material(item)
                paquetes = self.svc.obtener_paquetes_partida(partida['id'])
                for p in paquetes:
                    fila = self.ventana.tbl_paquetes.agregar_paquete(
                        p['tipo'], p['clave'], p['descripcion'],
                        p['ancho'], p['alto']
                    )
                    self.ventana.tbl_paquetes.set_piezas_sin_senal(fila, p['piezas'])
                    self.ventana.tbl_paquetes.set_ancho_sin_senal(fila, p['ancho'])
                    self.ventana.tbl_paquetes.set_alto_sin_senal(fila, p['alto'])
            finally:
                self.ventana.paquetes_ctrl.set_cargando(False)
            self.ventana.paquetes_ctrl.limpiar_estado()
            self.ventana._recalc_summary()
        finally:
            self.ventana._prog = False

    def guardar_partida_actual(self) -> bool:
        if self.guardar_partida_actual_silencioso():
            QMessageBox.information(
                self.ventana,
                "Guardar",
                "Presupuesto guardado correctamente."
            )
            return True
        return False

    def _recolectar_datos_presupuesto(self) -> Dict[str, Any]:
        cliente_id = self._obtener_cliente_id()
        if cliente_id is None:
            return {}
        fecha_str = self.ventana.le_fecha.text().strip()
        try:
            fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
            fecha_sql = fecha_obj.strftime("%Y-%m-%d")
        except ValueError:
            fecha_sql = datetime.now().strftime("%Y-%m-%d")
        return {
            'id': self.presupuesto_id,
            'cliente_id': cliente_id,
            'obra': self.ventana.le_obra.text().strip(),
            'presupuesto': self.ventana.sp_presupuesto.value(),
            'fecha': fecha_sql,
            'color_global': self.ventana.cbo_color_global.currentText().strip()
        }

    def _obtener_cliente_id(self) -> Optional[int]:
        if hasattr(self.ventana, 'cliente_actual_id') and self.ventana.cliente_actual_id:
            return self.ventana.cliente_actual_id
        nombre = self.ventana.le_cliente.text().strip()
        if not nombre:
            return None
        nombre_normalizado = " ".join(nombre.split()).upper()
        clientes = self.svc.clientes_buscar(nombre)
        for cli in clientes:
            display = cli.get('display', '').upper()
            if display == nombre_normalizado:
                self.ventana.cliente_actual_id = cli['id']
                return cli['id']
        return None

    def _recolectar_datos_partida(self) -> Dict[str, Any]:
        return {
            'id': self.partida_id,
            'presupuesto_id': None,
            'partida': self.ventana.sp_partida.value(),
            'titulo': self.ventana.le_titulo.text().strip(),
            'descripcion': self.ventana.te_desc.toPlainText().strip(),
            'color_partida': self.ventana.cbo_color.currentText().strip(),
            'desperdicio': self.ventana.sb_desperdicio.value(),
            'fv_porcentaje': self.ventana.sb_fv_pct.value(),
            'kg': self.ventana.sp_kg.value(),
            'ancho': self.ventana.sp_ancho.value(),
            'alto': self.ventana.sp_alto.value(),
            'mano_obra': self.ventana.sp_mo.value(),
            'accesorios': self.ventana.sp_acc.value(),
            'piezas': self.ventana.sb_pzas_global.value(),
            'precio_unitario': self.ventana.sp_pu_partida.value(),
            'total_partida': self.ventana.sp_total_partida.value(),
        }

    def _recolectar_items_partida(self) -> List[Dict[str, Any]]:
        items = []
        for r in range(self.ventana.tbl.rowCount()):
            items.append({
                'tipo': self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_TIPO),
                'color': self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_COLOR),
                'clave': self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_CLAVE),
                'descripcion': self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_DESC),
                'ca': _f(self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_CA), 1.0),
                'ancho': _f(self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_ANCHO), 0.0),
                'ch': _f(self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_CH), 1.0),
                'alto': _f(self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_ALTO), 0.0),
                'piezas': _i(self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_PZAS), 1),
                'pu': _f(self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_PU), 0.0),
                'importe': _f(self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_IMP), 0.0),
                'metros': None,
                'kg_m': None,
                'kgs': None,
                'precio_kg': None,
            })
        for r in range(self.ventana.tbl_he.rowCount()):
            items.append({
                'tipo': self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_TIPO),
                'color': None,
                'clave': self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_CLAVE),
                'descripcion': self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_DESC),
                'ca': _f(self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_CA), 1.0),
                'ancho': _f(self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_ANCHO), 0.0),
                'ch': _f(self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_CH), 1.0),
                'alto': _f(self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_ALTO), 0.0),
                'piezas': _i(self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_PZAS), 1),
                'pu': _f(self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_PU), 0.0),
                'importe': _f(self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_IMP), 0.0),
                'metros': _f(self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_METROS), 0.0),
                'kg_m': _f(self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_KG_M), 0.0),
                'kgs': _f(self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_KGS), 0.0),
                'precio_kg': _f(self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_PKG), 0.0),
            })
        return items

    def _recolectar_paquetes_partida(self) -> List[Dict[str, Any]]:
        paquetes = []
        for r in range(self.ventana.tbl_paquetes.rowCount()):
            datos = self.ventana.tbl_paquetes.obtener_datos_paquete(r)
            if not datos.get("es_anidado", False):
                paquetes.append({
                    'tipo': datos['tipo'],
                    'clave': datos['clave'],
                    'descripcion': datos['descripcion'],
                    'ancho': datos['ancho'],
                    'alto': datos['alto'],
                    'piezas': datos['piezas']
                })
        return paquetes

    def cargar_presupuesto(self, presupuesto_id: int) -> bool:
        self._cargando = True
        try:
            presupuesto = self.svc.obtener_presupuesto(presupuesto_id)
            if not presupuesto:
                return False
            self.presupuesto_id = presupuesto["id"]
            self.ventana.le_cliente.setText(presupuesto["cliente_nombre"])
            self.ventana.le_obra.setText(presupuesto["obra"])
            self.ventana.sp_presupuesto.setValue(self._to_int(presupuesto["presupuesto"]))
            fecha = presupuesto["fecha"]
            if isinstance(fecha, str):
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
            else:
                fecha_obj = fecha
            self.ventana.le_fecha.setText(fecha_obj.strftime("%d/%m/%Y"))
            self.ventana.cbo_color_global.setCurrentText(presupuesto["color_global"])
            partidas = self.svc.obtener_partidas(presupuesto_id)
            if not partidas:
                QMessageBox.warning(self.ventana, "Sin partidas", "Este presupuesto no tiene partidas.")
                return False
            partida = partidas[0]
            self.partida_id = partida["id"]
            self.ventana.sp_partida.setValue(self._to_int(partida["partida"]))
            self._cargar_partida_especifica(partida)
            self._actualizar_cache_partidas()
            return True
        except Exception as e:
            QMessageBox.critical(self.ventana, "Error", f"No se pudo cargar el presupuesto:\n{str(e)}")
            return False
        finally:
            self._cargando = False

    def obtener_siguiente_numero_partida(self, presupuesto_id: int) -> int:
        if not presupuesto_id:
            return 1
        try:
            partidas = self.svc.obtener_partidas(presupuesto_id)
            if not partidas:
                return 1
            max_num = max(self._to_int(p.get("partida", 0)) for p in partidas)
            return max_num + 1
        except Exception:
            return 1

    def limpiar_partida(self, solo_interfaz=False):
        self.ventana.le_titulo.clear()
        self.ventana.te_desc.clear()
        self.ventana.cbo_color.setCurrentText(self.ventana.cbo_color_global.currentText().strip())
        self.ventana.sb_desperdicio.setValue(2)
        self.ventana.sb_fv_pct.setValue(25)
        self.ventana.sp_kg.setValue(0.0)
        self.ventana.sp_ancho.setValue(0.0)
        self.ventana.sp_alto.setValue(0.0)
        self.ventana.sp_mo.setValue(0.0)
        self.ventana.sp_acc.setValue(0.0)
        self.ventana.sb_pzas_global.setValue(1)
        self.ventana.tbl.setRowCount(0)
        self.ventana.tbl_he.setRowCount(0)
        self.ventana.tbl_paquetes.setRowCount(0)
        self.ventana.tbl_anidada.limpiar()
        self.ventana.gb_tabla_anidada.setVisible(False)
        self.ventana.sp_pu_partida.setValue(0.0)
        self.ventana.sp_total_partida.setValue(0.0)
        if not solo_interfaz:
            self.partida_id = None
        self.ventana.le_titulo.setFocus()

    def limpiar_todo(self):
        self.presupuesto_id = None
        self.partida_id = None
        self.ventana.cliente_actual_id = None
        self.ventana.le_cliente.clear()
        self.ventana.le_obra.clear()
        self.ventana.le_fecha.setText(datetime.now().strftime("%d/%m/%Y"))
        params = self.svc.obtener_parametros_sistema()
        self.ventana.cbo_color_global.setCurrentText(params.get('color_global_defecto', 'VARIOS'))
        self.ventana.sb_desperdicio.setValue(int(params.get('desperdicio_defecto', 2)))
        self.ventana.sb_fv_pct.setValue(int(params.get('fv_defecto', 25)))
        self.limpiar_partida(solo_interfaz=True)
        self.ventana.lst_clientes.clear()
        self.ventana.lst_clientes.setVisible(False)
        self.ventana.lst_result.clear()
        self.ventana.lst_result.setVisible(False)
        self.ventana.le_cliente.setFocus()
        self._partidas_cache = []
        self.listaPartidasActualizada.emit([])

    def crear_nueva_partida(self) -> bool:
        if not self.presupuesto_id:
            if not self.guardar_partida_actual_silencioso():
                QMessageBox.warning(
                    self.ventana,
                    "Nueva partida no disponible",
                    "Debe guardar el presupuesto actual antes de crear una nueva partida."
                )
                return False
        if self.partida_id is not None or self._hay_datos_en_partida():
            if not self.guardar_partida_actual_silencioso():
                return False
        nuevo_numero = self.obtener_siguiente_numero_partida(self.presupuesto_id)
        params = self.svc.obtener_parametros_sistema()
        datos_nueva = {
            'presupuesto_id': self.presupuesto_id,
            'partida': nuevo_numero,
            'titulo': '',
            'descripcion': '',
            'color_partida': '',
            'desperdicio': params.get('desperdicio_defecto', 2.0),
            'fv_porcentaje': params.get('fv_defecto', 25.0),
            'kg': 0.0,
            'ancho': 0.0,
            'alto': 0.0,
            'mano_obra': 0.0,
            'accesorios': 0.0,
            'piezas': 1,
            'precio_unitario': 0.0,
            'total_partida': 0.0,
        }
        try:
            nueva_id = self.svc.guardar_partida(datos_nueva)
            self.partida_id = nueva_id
        except Exception as e:
            QMessageBox.critical(self.ventana, "Error", f"No se pudo crear la nueva partida:\n{str(e)}")
            return False
        self.limpiar_partida(solo_interfaz=False)
        self.partida_id = nueva_id
        self.ventana.sp_partida.setValue(nuevo_numero)
        self.ventana.sp_partida.setReadOnly(True)
        self._actualizar_cache_partidas()
        return True

    def duplicar_partida_actual(self) -> bool:
        if self._hay_datos_en_partida():
            if not self.guardar_partida_actual_silencioso():
                return False
        if not self.partida_id:
            QMessageBox.warning(self.ventana, "Duplicar partida", "No hay partida actual para duplicar.")
            return False
        partida_actual = None
        for p in self._partidas_cache:
            if p['id'] == self.partida_id:
                partida_actual = p
                break
        if not partida_actual:
            QMessageBox.warning(self.ventana, "Duplicar partida", "No se encontraron los datos de la partida actual.")
            return False
        nuevo_numero = self.obtener_siguiente_numero_partida(self.presupuesto_id)
        datos_nueva = {
            'presupuesto_id': self.presupuesto_id,
            'partida': nuevo_numero,
            'titulo': partida_actual['titulo'],
            'descripcion': partida_actual['descripcion'],
            'color_partida': partida_actual['color_partida'],
            'desperdicio': partida_actual['desperdicio'],
            'fv_porcentaje': partida_actual['fv_porcentaje'],
            'kg': partida_actual['kg'],
            'ancho': partida_actual['ancho'],
            'alto': partida_actual['alto'],
            'mano_obra': partida_actual['mano_obra'],
            'accesorios': partida_actual['accesorios'],
            'piezas': partida_actual['piezas'],
            'precio_unitario': partida_actual['precio_unitario'],
            'total_partida': partida_actual['total_partida'],
        }
        try:
            nueva_id = self.svc.guardar_partida(datos_nueva)
        except Exception as e:
            QMessageBox.critical(self.ventana, "Error", f"No se pudo duplicar la partida:\n{str(e)}")
            return False
        items = self.svc.obtener_items_partida(self.partida_id)
        if items:
            self.svc.guardar_items_partida(nueva_id, items)
        paquetes = self.svc.obtener_paquetes_partida(self.partida_id)
        if paquetes:
            with self.svc.cursor() as cur:
                for p in paquetes:
                    cur.execute("""
                        INSERT INTO [presupuestos].dbo.partida_paquetes
                        (partida_id, tipo_paquete, clave_paquete, descripcion, ancho, alto, piezas)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        nueva_id,
                        p['tipo'],
                        p['clave'],
                        p['descripcion'],
                        p['ancho'],
                        p['alto'],
                        p['piezas']
                    ))
                cur.commit()
        self.partida_id = nueva_id
        nueva_partida = self.svc.obtener_partidas(self.presupuesto_id)
        for p in nueva_partida:
            if p['id'] == nueva_id:
                self._cargar_partida_especifica(p)
                break
        self._actualizar_cache_partidas()
        QMessageBox.information(self.ventana, "Duplicar partida", f"Partida duplicada como número {nuevo_numero}.")
        return True

    def eliminar_partida_actual(self) -> bool:
        if not self.partida_id:
            QMessageBox.warning(self.ventana, "Eliminar partida", "No hay partida actual para eliminar.")
            return False
        if not self.guardar_partida_actual_silencioso():
            QMessageBox.warning(
                self.ventana,
                "Eliminar Partida",
                "No se pudo guardar el presupuesto actual antes de eliminar."
            )
            return False
        resp = QMessageBox.question(
            self.ventana,
            "Eliminar partida",
            f"¿Está seguro de eliminar la partida {self.ventana.sp_partida.value()}?\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp != QMessageBox.StandardButton.Yes:
            return False
        try:
            with self.svc.cursor() as cur:
                cur.execute("DELETE FROM [presupuestos].dbo.items_partida WHERE partida_id = ?", (self.partida_id,))
                cur.execute("DELETE FROM [presupuestos].dbo.partida_paquetes WHERE partida_id = ?", (self.partida_id,))
                cur.execute("DELETE FROM [presupuestos].dbo.partidas WHERE id = ?", (self.partida_id,))
                cur.commit()
        except Exception as e:
            QMessageBox.critical(self.ventana, "Error", f"No se pudo eliminar la partida:\n{str(e)}")
            return False
        try:
            with self.svc.cursor() as cur:
                cur.execute("""
                    SELECT id, partida FROM [presupuestos].dbo.partidas
                    WHERE presupuesto_id = ?
                    ORDER BY partida
                """, (self.presupuesto_id,))
                partidas_restantes = cur.fetchall()
                for idx, (pid, old_num) in enumerate(partidas_restantes, start=1):
                    if old_num != idx:
                        cur.execute("UPDATE [presupuestos].dbo.partidas SET partida = ? WHERE id = ?", (idx, pid))
                cur.commit()
        except Exception as e:
            QMessageBox.warning(self.ventana, "Renumeración", f"No se pudo renumerar las partidas:\n{str(e)}")
        partidas = self.svc.obtener_partidas(self.presupuesto_id)
        if not partidas:
            self.partida_id = None
            self.limpiar_partida(solo_interfaz=False)
            self.ventana.sp_partida.setValue(1)
            self.ventana.sp_partida.setReadOnly(True)
            self._actualizar_cache_partidas()
            QMessageBox.information(self.ventana, "Eliminar partida",
                                    "Se ha eliminado la última partida. El presupuesto queda vacío.")
            return True
        if self._indice_partida_actual > 0:
            nueva_partida = partidas[self._indice_partida_actual - 1]
        else:
            nueva_partida = partidas[0]
        self._cargar_partida_especifica(nueva_partida)
        self.partida_id = nueva_partida['id']
        self._actualizar_cache_partidas()
        return True

    def recalcular_por_color(self):
        if self._cargando:
            return
        if not self.presupuesto_id:
            self.guardar_partida_actual_silencioso()
            if not self.presupuesto_id:
                self._actualizar_ui_partida_actual()
                return
        nuevo_color = self.ventana._get_color_partida_o_global()
        es_varios = (nuevo_color.upper() == "VARIOS")
        try:
            self.svc.actualizar_color_global_presupuesto(self.presupuesto_id, nuevo_color)
        except Exception as e:
            logger.error(f"Error persistiendo color_global: {e}")
        try:
            from presupuestos.calculators import EspecificacionesCtx, dispatch_calculo
        except ImportError:
            try:
                from calculators import EspecificacionesCtx, dispatch_calculo
            except ImportError:
                logger.error("No se pudo importar dispatch_calculo")
                return
        try:
            partidas = self.svc.obtener_partidas(self.presupuesto_id)
            for partida in partidas:
                partida_id = partida['id']
                color_partida_actual = partida.get('color_partida', '')
                self.svc.presupuesto_repo.actualizar_color_partida(partida_id, nuevo_color, es_varios)
                self.svc.presupuesto_repo.actualizar_color_items_partida(partida_id, nuevo_color, es_varios)
                items = self.svc.obtener_items_partida(partida_id)
                items_actualizados = []
                for item in items:
                    tipo = item['tipo'].upper()
                    clave = item['clave']
                    if tipo in ['HERRERIA', 'HERRERÍA']:
                        color_item = None
                        pu = item['pu']
                        importe = item['importe']
                    else:
                        if es_varios:
                            color_item = item.get('color') or color_partida_actual or ''
                        else:
                            color_item = nuevo_color
                        try:
                            ctx = EspecificacionesCtx(
                                svc=self.svc,
                                tipo=tipo,
                                clave=clave,
                                color=color_item,
                                ancho=float(item.get('ancho', 0)),
                                alto=float(item.get('alto', 0)),
                                piezas=int(item.get('piezas', 1)),
                                ca=float(item.get('ca', 1)),
                                ch=float(item.get('ch', 1)),
                                extra={"precio_kg": float(self.ventana.sp_precio_kg.value())}
                            )
                            pu, importe = dispatch_calculo(ctx)
                        except Exception:
                            pu = item['pu']
                            importe = item['importe']
                    item['color'] = color_item
                    item['pu'] = pu
                    item['importe'] = importe
                    items_actualizados.append(item)
                if items_actualizados:
                    self.svc.guardar_items_partida(partida_id, items_actualizados)
                self._recalcular_y_persistir_resumen_partida(partida, items_actualizados)
        except Exception as e:
            logger.error(f"Error recalculando partidas en BD por cambio de color: {e}")
            QMessageBox.warning(
                self.ventana,
                "Error en recálculo",
                f"Ocurrió un error al recalcular los precios:\n{str(e)}"
            )
        self._actualizar_ui_partida_actual()

    def _recalcular_y_persistir_resumen_partida(self, partida, items):
        A = 0.0
        for item in items:
            A += self._to_float(item.get('importe', 0))
        B = self._to_float(partida.get('mano_obra', 0)) + self._to_float(partida.get('accesorios', 0))
        C = A + B
        desp = self._to_float(partida.get('desperdicio', 0))
        fv = self._to_float(partida.get('fv_porcentaje', 0))
        D = C + (C * (desp / 100.0))
        E = D + (D * (fv / 100.0))
        piezas = max(1, self._to_int(partida.get('piezas', 1)))
        total_partida = E * piezas
        try:
            with self.svc.cursor() as cur:
                cur.execute("""
                    UPDATE [presupuestos].dbo.partidas
                    SET precio_unitario = ?, total_partida = ?
                    WHERE id = ?
                """, (E, total_partida, partida['id']))
                cur.commit()
        except Exception as e:
            logger.error(f"Error persistiendo resumen de partida {partida.get('id')}: {e}")

    def _actualizar_ui_partida_actual(self):
        if not self.partida_id:
            return
        self.ventana._prog = True
        try:
            if hasattr(self.ventana, '_actualizar_color_en_tabla_materiales'):
                self.ventana._actualizar_color_en_tabla_materiales()
            if hasattr(self.ventana, '_actualizar_color_en_tabla_anidada'):
                self.ventana._actualizar_color_en_tabla_anidada()
            for r in range(self.ventana.tbl.rowCount()):
                self.ventana._calc_std_row(r)
            for r in range(self.ventana.tbl_he.rowCount()):
                self.ventana._calc_he_row(r)
            if hasattr(self.ventana, 'tbl_anidada') and self.ventana._tabla_anidada_activa:
                for r in range(self.ventana.tbl_anidada.rowCount()):
                    self.ventana._calc_anidada_row(r)
            self.ventana._recalc_summary()
        except Exception as e:
            logger.error(f"Error actualizando UI después de recálculo por color: {e}")
        finally:
            self.ventana._prog = False

    def propagar_desperdicio_fv(self, desperdicio, fv):
        if not self.presupuesto_id:
            return
        try:
            with self.svc.cursor() as cur:
                cur.execute("""
                    UPDATE [presupuestos].dbo.partidas
                    SET desperdicio = ?, fv_porcentaje = ?
                    WHERE presupuesto_id = ?
                """, (desperdicio, fv, self.presupuesto_id))
                cur.commit()
            partidas = self.svc.obtener_partidas(self.presupuesto_id)
            for partida in partidas:
                items = self.svc.obtener_items_partida(partida['id'])
                self._recalcular_y_persistir_resumen_partida(partida, items)
        except Exception as e:
            logger.error(f"Error propagando desperdicio/F.V.: {e}")

    def aplicar_dimensiones_globales(self):
        if self._cargando:
            return
        nuevo_ancho = self.ventana.sp_ancho.value()
        nuevo_alto = self.ventana.sp_alto.value()
        self.ventana._prog = True
        try:
            for r in range(self.ventana.tbl.rowCount()):
                item_ancho = self.ventana.tbl.item(r, self.ventana.C_ANCHO)
                item_alto = self.ventana.tbl.item(r, self.ventana.C_ALTO)
                if item_ancho:
                    item_ancho.setText(f"{nuevo_ancho:.2f}")
                if item_alto:
                    item_alto.setText(f"{nuevo_alto:.2f}")
                self.ventana._calc_std_row(r)
            for r in range(self.ventana.tbl_he.rowCount()):
                item_ancho = self.ventana.tbl_he.item(r, self.ventana.H_ANCHO)
                item_alto = self.ventana.tbl_he.item(r, self.ventana.H_ALTO)
                if item_ancho:
                    item_ancho.setText(f"{nuevo_ancho:.2f}")
                if item_alto:
                    item_alto.setText(f"{nuevo_alto:.2f}")
                self.ventana._calc_he_row(r)
            self.ventana._recalc_summary()
            QMessageBox.information(self.ventana, "Dimensiones aplicadas",
                                    "Las dimensiones globales se han aplicado a todos los materiales.")
        finally:
            self.ventana._prog = False

    def nuevo_presupuesto(self):
        try:
            num_inicial = self.obtener_numero_inicial_presupuesto()
            ultimo = self.svc.obtener_ultimo_numero_presupuesto()
            nuevo_numero = max(num_inicial, ultimo + 1) if ultimo else num_inicial
        except Exception:
            ultimo = self.svc.obtener_ultimo_numero_presupuesto()
            nuevo_numero = ultimo + 1 if ultimo else 1
        self.ventana.sp_presupuesto.setValue(nuevo_numero)

    def duplicar_presupuesto_actual(self) -> bool:
        if not self.presupuesto_id:
            QMessageBox.warning(self.ventana, "Duplicar presupuesto", "No hay presupuesto cargado para duplicar.")
            return False
        presupuesto_original = self.svc.obtener_presupuesto(self.presupuesto_id)
        if not presupuesto_original:
            QMessageBox.warning(self.ventana, "Duplicar presupuesto", "No se pudo obtener el presupuesto original.")
            return False
        ultimo = self.svc.obtener_ultimo_numero_presupuesto()
        nuevo_numero = ultimo + 1
        datos_nuevo = {
            'cliente_id': presupuesto_original['cliente_id'],
            'obra': presupuesto_original['obra'],
            'presupuesto': nuevo_numero,
            'fecha': datetime.now().strftime("%Y-%m-%d"),
            'color_global': presupuesto_original['color_global'],
        }
        try:
            nuevo_id = self.svc.guardar_presupuesto(datos_nuevo)
        except Exception as e:
            QMessageBox.critical(self.ventana, "Error", f"No se pudo crear el nuevo presupuesto:\n{str(e)}")
            return False
        partidas_originales = self.svc.obtener_partidas(self.presupuesto_id)
        for partida_orig in partidas_originales:
            color_partida = partida_orig.get('color_partida', '')
            if presupuesto_original['color_global'].upper() == 'VARIOS':
                color_partida_final = color_partida
            else:
                color_partida_final = presupuesto_original['color_global']
            datos_partida = {
                'presupuesto_id': nuevo_id,
                'partida': partida_orig['partida'],
                'titulo': partida_orig['titulo'],
                'descripcion': partida_orig['descripcion'],
                'color_partida': color_partida_final,
                'desperdicio': partida_orig['desperdicio'],
                'fv_porcentaje': partida_orig['fv_porcentaje'],
                'kg': partida_orig['kg'],
                'ancho': partida_orig['ancho'],
                'alto': partida_orig['alto'],
                'mano_obra': partida_orig['mano_obra'],
                'accesorios': partida_orig['accesorios'],
                'piezas': partida_orig['piezas'],
                'precio_unitario': partida_orig['precio_unitario'],
                'total_partida': partida_orig['total_partida'],
            }
            try:
                nueva_partida_id = self.svc.guardar_partida(datos_partida)
            except Exception as e:
                QMessageBox.critical(self.ventana, "Error",
                                     f"No se pudo copiar la partida {partida_orig['partida']}:\n{str(e)}")
                continue
            items_originales = self.svc.obtener_items_partida(partida_orig['id'])
            nuevos_items = []
            for item in items_originales:
                nuevos_items.append({
                    'tipo': item['tipo'],
                    'color': item['color'],
                    'clave': item['clave'],
                    'descripcion': item['descripcion'],
                    'ca': item['ca'],
                    'ancho': item['ancho'],
                    'ch': item['ch'],
                    'alto': item['alto'],
                    'piezas': item['piezas'],
                    'pu': item['pu'],
                    'importe': item['importe'],
                    'metros': item['metros'],
                    'kg_m': item['kg_m'],
                    'kgs': item['kgs'],
                    'precio_kg': item['precio_kg'],
                })
            self.svc.guardar_items_partida(nueva_partida_id, nuevos_items)
            paquetes_originales = self.svc.obtener_paquetes_partida(partida_orig['id'])
            with self.svc.cursor() as cur:
                for p in paquetes_originales:
                    cur.execute("""
                        INSERT INTO [presupuestos].dbo.partida_paquetes
                        (partida_id, tipo_paquete, clave_paquete, descripcion, ancho, alto, piezas)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        nueva_partida_id,
                        p['tipo'],
                        p['clave'],
                        p['descripcion'],
                        p['ancho'],
                        p['alto'],
                        p['piezas']
                    ))
                cur.commit()
        QMessageBox.information(self.ventana, "Éxito",
                                f"Presupuesto duplicado correctamente como número {nuevo_numero}.")
        self.cargar_presupuesto(nuevo_id)
        return True

    def exportar_csv(self):
        if not self.partida_id:
            resp = QMessageBox.question(
                self.ventana,
                "Exportar CSV",
                "La partida actual no está guardada. ¿Desea exportar los datos actuales?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resp != QMessageBox.StandardButton.Yes:
                return
        nombre_base = f"presupuesto_{self.ventana.sp_presupuesto.value()}_partida_{self.ventana.sp_partida.value()}"
        archivo, _ = QFileDialog.getSaveFileName(
            self.ventana,
            "Guardar archivo CSV",
            nombre_base + ".csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        if not archivo:
            return
        try:
            import csv
            with open(archivo, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["Tipo", "Color", "Clave", "Descripción", "Cant. Ancho", "Ancho", "Cant. Alto", "Alto", "Piezas",
                     "P.U.", "Importe"])
                for r in range(self.ventana.tbl.rowCount()):
                    row = [
                        self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_TIPO),
                        self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_COLOR),
                        self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_CLAVE),
                        self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_DESC),
                        self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_CA),
                        self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_ANCHO),
                        self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_CH),
                        self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_ALTO),
                        self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_PZAS),
                        self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_PU),
                        self.ventana._safe_text(self.ventana.tbl, r, self.ventana.C_IMP),
                    ]
                    writer.writerow(row)
                writer.writerow([])
                writer.writerow(["--- HERRERÍA ---"])
                writer.writerow(
                    ["Tipo", "Clave", "Descripción", "Cant. Ancho", "Ancho", "Cant. Alto", "Alto", "Metros", "Kg/m",
                     "Kgs.", "$/kg", "Piezas", "P.U.", "Importe"])
                for r in range(self.ventana.tbl_he.rowCount()):
                    row = [
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_TIPO),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_CLAVE),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_DESC),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_CA),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_ANCHO),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_CH),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_ALTO),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_METROS),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_KG_M),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_KGS),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_PKG),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_PZAS),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_PU),
                        self.ventana._safe_text(self.ventana.tbl_he, r, self.ventana.H_IMP),
                    ]
                    writer.writerow(row)
                writer.writerow([])
                writer.writerow(["--- PAQUETES ---"])
                writer.writerow(["Tipo", "Clave", "Descripción", "Ancho", "Alto", "Piezas"])
                for r in range(self.ventana.tbl_paquetes.rowCount()):
                    datos = self.ventana.tbl_paquetes.obtener_datos_paquete(r)
                    if not datos.get("es_anidado", False):
                        row = [
                            datos['tipo'],
                            datos['clave'],
                            datos['descripcion'],
                            f"{datos['ancho']:.2f}",
                            f"{datos['alto']:.2f}",
                            str(datos['piezas'])
                        ]
                        writer.writerow(row)
            QMessageBox.information(self.ventana, "Exportar CSV", f"Archivo guardado correctamente en:\n{archivo}")
        except Exception as e:
            QMessageBox.critical(self.ventana, "Error", f"No se pudo exportar:\n{str(e)}")

    def _abrir_configuracion_presupuesto(self) -> bool:
        """
        NUEVO: Abre el diálogo de configuración del presupuesto
        (notas, forma de pago, descuento, plazo de entrega).
        Guarda los valores en la BD si el usuario acepta.
        Retorna True si se guardó o si no hay presupuesto, False si el usuario canceló.
        """
        if not self.presupuesto_id:
            return True  # No hay presupuesto, no hay nada que configurar

        try:
            # Obtener valores actuales de la BD
            presupuesto = self.svc.obtener_presupuesto(self.presupuesto_id)
            if not presupuesto:
                return True

            notas_actual = presupuesto.get('notas', '') or ''
            forma_pago_actual = presupuesto.get('forma_pago', '') or ''
            plazo_entrega_actual = presupuesto.get('plazo_entrega', '') or ''
            descuento_actual = float(presupuesto.get('descuento_porcentaje', 0.0) or 0.0)

            # Abrir diálogo de configuración
            from ..ui.dialogs.notas_presupuesto_dialog import NotasPresupuestoDialog
            dlg = NotasPresupuestoDialog(
                parent=self.ventana,
                notas_actual=notas_actual,
                forma_pago_actual=forma_pago_actual,
                plazo_entrega_actual=plazo_entrega_actual,
                descuento_actual=descuento_actual
            )

            if dlg.exec():
                # El usuario aceptó, guardar los valores
                nuevas_notas = dlg.obtener_notas()
                nueva_forma_pago = dlg.obtener_forma_pago()
                nuevo_plazo = dlg.obtener_plazo_entrega()
                nuevo_descuento = dlg.obtener_descuento()

                try:
                    with self.svc.cursor() as cur:
                        cur.execute("""
                            UPDATE [presupuestos].dbo.presupuestos
                            SET notas = ?, forma_pago = ?, plazo_entrega = ?, descuento_porcentaje = ?
                            WHERE id = ?
                        """, (nuevas_notas, nueva_forma_pago, nuevo_plazo, nuevo_descuento, self.presupuesto_id))
                        cur.commit()
                    return True
                except Exception as e:
                    logger.error(f"Error guardando configuración del presupuesto: {e}")
                    QMessageBox.warning(
                        self.ventana,
                        "Error",
                        f"No se pudieron guardar los cambios:\n{str(e)}"
                    )
                    return False
            else:
                # El usuario canceló
                return False

        except Exception as e:
            logger.error(f"Error abriendo configuración del presupuesto: {e}")
            return True  # Si hay error, continuar sin configurar

    def exportar_pdf(self):
        """
        CORREGIDO: Ahora abre el diálogo de configuración antes de generar el PDF.
        """
        if not self.presupuesto_id:
            QMessageBox.warning(
                self.ventana,
                "Exportar PDF",
                "No hay un presupuesto guardado para exportar. Guarde el presupuesto primero."
            )
            return

        if not self.guardar_partida_actual_silencioso():
            QMessageBox.warning(
                self.ventana,
                "Exportar PDF",
                "No se pudo guardar la partida actual antes de exportar."
            )
            return

        # NUEVO: Abrir diálogo de configuración
        if not self._abrir_configuracion_presupuesto():
            return  # El usuario canceló

        try:
            from ..reports.presupuesto_pdf_service import PresupuestoPDFService
            pdf_service = PresupuestoPDFService(self.svc)
            ruta_pdf = pdf_service.generar_pdf_desde_id(self.presupuesto_id, parent=self.ventana)
            if ruta_pdf:
                QMessageBox.information(
                    self.ventana,
                    "Exportar PDF",
                    f"PDF generado correctamente en:\n{ruta_pdf}"
                )
            else:
                QMessageBox.critical(
                    self.ventana,
                    "Exportar PDF",
                    "No se pudo generar el PDF. Verifique que el presupuesto tenga partidas."
                )
        except Exception as e:
            QMessageBox.critical(
                self.ventana,
                "Error al exportar PDF",
                f"Ocurrió un error al generar el PDF:\n{str(e)}"
            )
            import traceback
            traceback.print_exc()

    def vista_previa_pdf(self) -> bool:
        """
        CORREGIDO: Ahora abre el diálogo de configuración antes de generar el PDF.
        También obtiene el número de presupuesto y nombre del cliente.
        """
        if not self.presupuesto_id:
            QMessageBox.warning(
                self.ventana,
                "Vista Previa",
                "No hay un presupuesto guardado para previsualizar. Guarde el presupuesto primero."
            )
            return False

        if not self.guardar_partida_actual_silencioso():
            QMessageBox.warning(
                self.ventana,
                "Vista Previa",
                "No se pudo guardar la partida actual antes de previsualizar."
            )
            return False

        # NUEVO: Abrir diálogo de configuración
        if not self._abrir_configuracion_presupuesto():
            return False  # El usuario canceló

        try:
            from ..reports.presupuesto_pdf_service import PresupuestoPDFService
            pdf_service = PresupuestoPDFService(self.svc)
            ruta_pdf = pdf_service.generar_pdf_desde_id(
                self.presupuesto_id,
                parent=None,
                modo_vista_previa=True
            )
            if ruta_pdf:
                # OBTENER DATOS DEL PRESUPUESTO Y CLIENTE
                presupuesto = self.svc.obtener_presupuesto(self.presupuesto_id)
                presupuesto_num = presupuesto.get('presupuesto', 0) if presupuesto else 0
                cliente_nombre = ""

                if presupuesto and presupuesto.get('cliente_id'):
                    try:
                        with self.svc.cursor() as cur:
                            cur.execute("""
                                SELECT Nombre FROM [clientes].dbo.Clientes WHERE id = ?
                            """, (presupuesto.get('cliente_id'),))
                            row = cur.fetchone()
                            if row:
                                cliente_nombre = row[0] or ""
                    except Exception as e:
                        logger.error(f"Error obteniendo nombre del cliente: {e}")

                # CREAR DIÁLOGO CON LOS DATOS CORRECTOS
                from ..ui.dialogs.vista_previa_pdf_dialog import VistaPreviaPDFDialog
                dlg = VistaPreviaPDFDialog(
                    ruta_pdf=ruta_pdf,
                    parent=self.ventana,
                    service=self.svc,
                    presupuesto_num=presupuesto_num,  # ← CORREGIDO: Número real del presupuesto
                    cliente=cliente_nombre,  # ← CORREGIDO: Nombre del cliente
                    presupuesto_id=self.presupuesto_id
                )
                dlg.exec()
                return True
            else:
                QMessageBox.critical(
                    self.ventana,
                    "Vista Previa",
                    "No se pudo generar el PDF. Verifique que el presupuesto tenga partidas."
                )
                return False
        except Exception as e:
            QMessageBox.critical(
                self.ventana,
                "Error en Vista Previa",
                f"Ocurrió un error al generar la vista previa:\n{str(e)}"
            )
            import traceback
            traceback.print_exc()
            return False

    def enviar_por_email(self):
        """
        CORREGIDO: Ahora abre el diálogo de configuración antes de generar el PDF.
        """
        if not self.presupuesto_id:
            QMessageBox.warning(
                self.ventana,
                "Enviar por Email",
                "No hay un presupuesto guardado. Guarde el presupuesto primero."
            )
            return

        if not self.guardar_partida_actual_silencioso():
            QMessageBox.warning(
                self.ventana,
                "Enviar por Email",
                "No se pudo guardar la partida actual."
            )
            return

        # NUEVO: Abrir diálogo de configuración
        if not self._abrir_configuracion_presupuesto():
            return  # El usuario canceló

        try:
            # Obtener datos del presupuesto
            presupuesto = self.svc.obtener_presupuesto(self.presupuesto_id)
            if not presupuesto:
                QMessageBox.critical(
                    self.ventana,
                    "Error",
                    "No se pudieron obtener los datos del presupuesto."
                )
                return

            # Obtener email del cliente
            cliente_id = presupuesto.get('cliente_id')
            cliente_nombre = ""
            cliente_email = ""
            if cliente_id:
                try:
                    # Buscar cliente por ID en la BD
                    with self.svc.cursor() as cur:
                        cur.execute("""
                            SELECT Nombre, Email FROM [clientes].dbo.Clientes WHERE id = ?
                        """, (cliente_id,))
                        row = cur.fetchone()
                        if row:
                            cliente_nombre = row[0] or ""
                            cliente_email = row[1] or ""
                except Exception as e:
                    logger.error(f"Error obteniendo email del cliente: {e}")

            # Generar PDF
            from ..reports.presupuesto_pdf_service import PresupuestoPDFService
            pdf_service = PresupuestoPDFService(self.svc)
            ruta_pdf = pdf_service.generar_pdf_desde_id(
                self.presupuesto_id,
                parent=None,
                modo_vista_previa=True
            )
            if not ruta_pdf:
                QMessageBox.critical(
                    self.ventana,
                    "Error",
                    "No se pudo generar el PDF."
                )
                return

            # Abrir diálogo de envío
            from ..ui.dialogs.enviar_correo_dialog import EnviarCorreoDialog
            dlg = EnviarCorreoDialog(
                parent=self.ventana,
                service=self.svc,
                destinatario=cliente_email,
                presupuesto_num=presupuesto.get('presupuesto', 0),
                cliente=cliente_nombre,
                cliente_id=cliente_id,
                ruta_pdf=ruta_pdf
            )
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(
                self.ventana,
                "Error al enviar por email",
                f"Ocurrió un error:\n{str(e)}"
            )
            import traceback
            traceback.print_exc()

    def obtener_numero_inicial_presupuesto(self) -> int:
        try:
            params = self.svc.obtener_parametros_sistema()
            num_inicial = params.get('numero_inicial_presupuesto', None)
            if num_inicial is not None:
                return int(num_inicial)
        except Exception as e:
            print(f"[DEBUG] Error obteniendo número inicial: {e}")
        try:
            ultimo = self.svc.obtener_ultimo_numero_presupuesto()
            return (ultimo + 1) if ultimo else 1
        except Exception:
            return 1

    def guardar_numero_inicial_presupuesto(self, nuevo_numero: int) -> bool:
        try:
            with self.svc.cursor() as cur:
                cur.execute("""
                    IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'parametros_sistema')
                    BEGIN
                        IF EXISTS (SELECT 1 FROM parametros_sistema WHERE clave = 'numero_inicial_presupuesto')
                            UPDATE parametros_sistema SET valor = ? WHERE clave = 'numero_inicial_presupuesto'
                        ELSE
                            INSERT INTO parametros_sistema (clave, valor) VALUES ('numero_inicial_presupuesto', ?)
                    END
                """, (str(nuevo_numero), str(nuevo_numero)))
                cur.commit()
            return True
        except Exception as e:
            print(f"[DEBUG] Error guardando número inicial: {e}")
            return False

    def _agregar_item_material(self, item: Dict[str, Any]):
        r = self.ventana.tbl.rowCount()
        self.ventana.tbl.insertRow(r)
        self.ventana._set_or_update_item(self.ventana.tbl, r, self.ventana.C_TIPO, item["tipo"], editable=False)
        self.ventana._set_or_update_item(self.ventana.tbl, r, self.ventana.C_COLOR, item["color"] or "", editable=False)
        self.ventana._set_or_update_item(self.ventana.tbl, r, self.ventana.C_CLAVE, item["clave"], editable=False)
        self.ventana._set_or_update_item(self.ventana.tbl, r, self.ventana.C_DESC, item["descripcion"], editable=False)
        self.ventana._set_or_update_item(self.ventana.tbl, r, self.ventana.C_CA, f"{self._to_float(item['ca']):.2f}",
                                         editable=True)
        self.ventana._set_or_update_item(self.ventana.tbl, r, self.ventana.C_ANCHO,
                                         f"{self._to_float(item['ancho']):.2f}", editable=True)
        self.ventana._set_or_update_item(self.ventana.tbl, r, self.ventana.C_CH, f"{self._to_float(item['ch']):.2f}",
                                         editable=True)
        self.ventana._set_or_update_item(self.ventana.tbl, r, self.ventana.C_ALTO,
                                         f"{self._to_float(item['alto']):.2f}", editable=True)
        self.ventana._set_or_update_item(self.ventana.tbl, r, self.ventana.C_PZAS, f"{self._to_int(item['piezas'])}",
                                         editable=True)
        self.ventana._set_or_update_item(self.ventana.tbl, r, self.ventana.C_PU, f"{self._to_float(item['pu']):.2f}",
                                         editable=False)
        self.ventana._set_or_update_item(self.ventana.tbl, r, self.ventana.C_IMP,
                                         f"{self._to_float(item['importe']):.2f}", editable=False)
        self.ventana._apply_editabilidad_std(r)

    def _agregar_item_herreria(self, item: Dict[str, Any]):
        r = self.ventana.tbl_he.rowCount()
        self.ventana.tbl_he.insertRow(r)
        self.ventana._set_or_update_item(self.ventana.tbl_he, r, self.ventana.H_TIPO, item["tipo"], editable=False)
        self.ventana._set_or_update_item(self.ventana.tbl_he, r, self.ventana.H_CLAVE, item["clave"], editable=False)
        self.ventana._set_or_update_item(self.ventana.tbl_he, r, self.ventana.H_DESC, item["descripcion"],
                                         editable=False)
        self.ventana._set_or_update_item(self.ventana.tbl_he, r, self.ventana.H_CA, f"{self._to_float(item['ca']):.2f}",
                                         editable=True)
        self.ventana._set_or_update_item(self.ventana.tbl_he, r, self.ventana.H_ANCHO,
                                         f"{self._to_float(item['ancho']):.2f}", editable=True)
        self.ventana._set_or_update_item(self.ventana.tbl_he, r, self.ventana.H_CH, f"{self._to_float(item['ch']):.2f}",
                                         editable=True)
        self.ventana._set_or_update_item(self.ventana.tbl_he, r, self.ventana.H_ALTO,
                                         f"{self._to_float(item['alto']):.2f}", editable=True)
        self.ventana._set_or_update_item(self.ventana.tbl_he, r, self.ventana.H_METROS,
                                         f"{self._to_float(item['metros']):.3f}", editable=False)
        self.ventana._set_or_update_item(self.ventana.tbl_he, r, self.ventana.H_KG_M,
                                         f"{self._to_float(item['kg_m']):.3f}", editable=False)
        self.ventana._set_or_update_item(self.ventana.tbl_he, r, self.ventana.H_KGS,
                                         f"{self._to_float(item['kgs']):.3f}", editable=False)
        self.ventana._set_or_update_item(self.ventana.tbl_he, r, self.ventana.H_PKG,
                                         f"{self._to_float(item['precio_kg']):.2f}", editable=False)
        self.ventana._set_or_update_item(self.ventana.tbl_he, r, self.ventana.H_PZAS, f"{self._to_int(item['piezas'])}",
                                         editable=True)
        self.ventana._set_money(self.ventana.tbl_he, r, self.ventana.H_PU, self._to_float(item['pu']))
        self.ventana._set_money(self.ventana.tbl_he, r, self.ventana.H_IMP, self._to_float(item['importe']))