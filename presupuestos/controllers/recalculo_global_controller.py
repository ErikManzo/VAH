# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/controllers/recalculo_global_controller.py
SUBRUTINA ÚNICA de recálculo global del presupuesto (F5 y disparadores automáticos).
REGLAS DE NEGOCIO APLICADAS (definidas por el usuario):
- Ciclo For/Next de 1 a X (X = mayor número de partida del presupuesto actual).
- Cada partida conserva SUS PROPIOS: ancho, alto, piezas, M.O., accesorios y color.
- Entran con valor de pantalla: $/KG, DESPERDICIO y F.V.
- Regla de color: color_global != VARIOS -> aplica a todo; VARIOS -> color_partida.
- dispatch_calculo es la única fuente de verdad de precios (incluye herrería).
- Resumen: A=Σimportes; +MO+Acc; ×(1+desp); ×(1+FV); ×piezas (propia de la partida).
- Persistencia: guardar_items_partida + UPDATE dirigido del resumen.
- Al final refresca la UI de la partida visible desde BD (UI == BD).
NO duplica fórmulas: reutiliza dispatch_calculo, compute_herreria y
_recalcular_y_persistir_resumen_partida del PresupuestoController.
"""
from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtWidgets import QMessageBox
from common.logger_config import get_logger, setup_logger

setup_logger("presupuestos.controllers.recalculo_global_controller")
logger = get_logger("presupuestos.controllers.recalculo_global_controller")


class RecalculoGlobalController(QObject):
    """
    Punto de entrada único: ejecutar(mostrar_mensaje).
    Disparadores: F5 manual, automático diferido (programar_auto) y post-menú.
    """

    def __init__(self, ventana, svc, presupuesto_ctrl):
        super().__init__(ventana)
        self.ventana = ventana
        self.svc = svc
        self.pctrl = presupuesto_ctrl
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.ejecutar_silencioso)

    # ------------------------------------------------------------------
    # Disparador automático diferido (debounce) para eventos de cálculo
    # ------------------------------------------------------------------
    def programar_auto(self, *args) -> None:
        if getattr(self.ventana, "_prog", False):
            return
        if self.pctrl._cargando:
            return
        if not self.pctrl.presupuesto_id:
            return
        self._timer.start()

    def cancelar_auto(self) -> None:
        self._timer.stop()

    def ejecutar_silencioso(self) -> None:
        self._timer.stop()
        try:
            self.ejecutar(mostrar_mensaje=False)
        except Exception as e:
            logger.error(f"recalculo automatico: {e}")

    # ------------------------------------------------------------------
    # Entrada única del recálculo global
    # ------------------------------------------------------------------
    def ejecutar(self, mostrar_mensaje: bool = True) -> bool:
        v = self.ventana
        if getattr(v, "_prog", False) or self.pctrl._cargando:
            return False
        if not self.pctrl.presupuesto_id:
            self.pctrl.guardar_partida_actual_silencioso()
            if not self.pctrl.presupuesto_id:
                return False
        exito = False
        v._prog = True
        try:
            # 1) Guardar partida actual para que BD refleje la pantalla
            self.pctrl.guardar_partida_actual_silencioso()
            # 2) Valores de pantalla que entran al ciclo
            precio_kg = float(v.sp_precio_kg.value())
            desp = float(v.sb_desperdicio.value())
            fv = float(v.sb_fv_pct.value())
            color_global = (v.cbo_color_global.currentText() or "").strip().upper()
            es_varios = (color_global == "VARIOS")
            # 3) Ciclo For/Next de 1 a X
            partidas = self.svc.obtener_partidas(self.pctrl.presupuesto_id)
            if partidas:
                X = max(int(p.get("partida", 0) or 0) for p in partidas)
                for numero in range(1, X + 1):
                    partida = next(
                        (p for p in partidas if int(p.get("partida", 0) or 0) == numero),
                        None,
                    )
                    if partida is None:
                        continue
                    self._recalcular_partida(partida, precio_kg, desp, fv, color_global, es_varios)
                # 4) Refrescar UI de la partida visible desde BD (UI == BD)
                fresca = next(
                    (p for p in self.svc.obtener_partidas(self.pctrl.presupuesto_id)
                     if p["id"] == self.pctrl.partida_id),
                    None,
                )
                if fresca is not None:
                    self.pctrl._cargar_partida_especifica(fresca)
                exito = True
        except Exception as e:
            logger.error(f"recalculo global: {e}")
        finally:
            v._prog = False
        if mostrar_mensaje:
            if exito:
                QMessageBox.information(
                    v, "Recalcular Todo",
                    "Todos los valores han sido recalculados y guardados."
                )
            else:
                QMessageBox.warning(
                    v, "Recalcular Todo",
                    "No fue posible completar el recálculo global."
                )
        return exito

    # ------------------------------------------------------------------
    # Recálculo de UNA partida en BD (misma fórmula que la UI)
    # ------------------------------------------------------------------
    def _recalcular_partida(self, partida, precio_kg, desp, fv, color_global, es_varios):
        from presupuestos.calculators import EspecificacionesCtx, dispatch_calculo
        from presupuestos.calculators.herreria import compute_herreria, _ceil_step

        partida_id = partida["id"]
        color_partida = (partida.get("color_partida") or "").strip().upper()
        color_resuelto = color_partida if es_varios else color_global

        # Desperdicio y F.V. entran con valor de pantalla (UPDATE dirigido)
        try:
            with self.svc.cursor() as cur:
                cur.execute(
                    "UPDATE [presupuestos].dbo.partidas SET desperdicio = ?, fv_porcentaje = ? WHERE id = ?",
                    (desp, fv, partida_id),
                )
                cur.commit()
        except Exception as e:
            logger.error(f"recalculo global: desp/fv partida {partida_id}: {e}")

        # Regla de color global (no VARIOS -> sobrescribe color_partida)
        if not es_varios:
            self.svc.presupuesto_repo.actualizar_color_partida(partida_id, color_global, False)

        items = self.svc.obtener_items_partida(partida_id)
        for item in items:
            tipo = (item.get("tipo") or "").strip().upper()
            clave = item.get("clave") or ""
            ancho = float(item.get("ancho") or 0)
            alto = float(item.get("alto") or 0)
            ca = float(item.get("ca") or 1)
            ch = float(item.get("ch") or 1)
            piezas = int(item.get("piezas") or 1)
            try:
                if tipo in ("HERRERIA", "HERRERÍA"):
                    pu, imp, kgs = compute_herreria(
                        svc=self.svc, clave=clave, piezas=piezas,
                        ancho=ancho, alto=alto,
                        extra={"precio_kg": precio_kg, "ca": ca, "ch": ch},
                    )
                    item["pu"] = pu
                    item["importe"] = imp
                    item["kgs"] = kgs
                    item["kg_m"] = self.svc.herreria_kg_por_m(clave) or 0.0
                    item["metros"] = (ca * _ceil_step(ancho, 0.05)) + (ch * _ceil_step(alto, 0.05))
                    item["precio_kg"] = precio_kg
                else:
                    ctx = EspecificacionesCtx(
                        svc=self.svc, tipo=tipo, clave=clave, color=color_resuelto,
                        ancho=ancho, alto=alto, piezas=piezas, ca=ca, ch=ch,
                        extra={"precio_kg": precio_kg},
                    )
                    pu, imp = dispatch_calculo(ctx)
                    item["pu"] = pu
                    item["importe"] = imp
                    item["color"] = color_resuelto
            except Exception as e:
                logger.error(f"recalculo global: item {clave}: {e}")

        if items:
            self.svc.guardar_items_partida(partida_id, items)

        # Resumen con valores propios de la partida (MO/Acc/piezas) y desp/fv de pantalla
        partida["desperdicio"] = desp
        partida["fv_porcentaje"] = fv
        self.pctrl._recalcular_y_persistir_resumen_partida(partida, items)