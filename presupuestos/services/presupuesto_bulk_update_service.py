# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import QMessageBox

from common.logger_config import setup_logger


LOGGER = setup_logger("presupuestos.bulk_update")


def obtener_presupuesto_id_edicion_global(window):
    presupuesto_id = None
    if hasattr(window, "presupuesto_ctrl") and window.presupuesto_ctrl:
        presupuesto_id = getattr(window.presupuesto_ctrl, "presupuesto_id", None)
    if presupuesto_id:
        return presupuesto_id
    return window._obtener_presupuesto_id_actual()


# Lista blanca de campos permitidos para actualización global (Seguridad)
CAMPOS_PERMITIDOS_UPDATE = {
    "desperdicio",
    "fv_porcentaje",
    "mano_obra",
    "accesorios",
    "piezas",
}

def actualizar_valor_global_partidas(window, campo: str, valor: float) -> bool:
    # Validación de seguridad contra inyección SQL
    if campo not in CAMPOS_PERMITIDOS_UPDATE:
        QMessageBox.critical(
            window,
            "Error de seguridad",
            f"El campo '{campo}' no está permitido para actualización global."
        )
        return False

    print(f"[DEBUG] === actualizar_valor_global_partidas: campo={campo}, valor={valor} ===")
    LOGGER.debug("=== actualizar_valor_global_partidas: campo=%s, valor=%s ===", campo, valor)

    # Obtener presupuesto_id
    presupuesto_id = window._obtener_presupuesto_id_edicion_global()
    print(f"[DEBUG] presupuesto_id obtenido: {presupuesto_id}")
    LOGGER.debug("presupuesto_id obtenido: %s", presupuesto_id)

    if not presupuesto_id:
        print("[DEBUG] ERROR: No se obtuvo presupuesto_id")
        LOGGER.error("No se obtuvo presupuesto_id para la actualizacion global")
        QMessageBox.warning(
            window,
            "Presupuesto no disponible",
            "Debe guardar o abrir un presupuesto antes de aplicar el cambio global.",
        )
        return False

    # Guardar partida actual (silencioso)
    if hasattr(window, "presupuesto_ctrl") and window.presupuesto_ctrl:
        print("[DEBUG] Guardando partida actual silenciosamente...")
        LOGGER.debug("Guardando partida actual silenciosamente antes del UPDATE global")
        if not window.presupuesto_ctrl.guardar_partida_actual_silencioso():
            print("[DEBUG] Falló guardar_partida_actual_silencioso")
            LOGGER.error("guardar_partida_actual_silencioso retorno False antes del UPDATE global")
            return False
        print("[DEBUG] Partida actual guardada")
        LOGGER.debug("Partida actual guardada correctamente")

    try:
        print(f"[DEBUG] Ejecutando UPDATE: SET {campo} = {valor} WHERE presupuesto_id = {presupuesto_id}")
        LOGGER.debug(
            "Ejecutando UPDATE global: campo=%s valor=%s presupuesto_id=%s",
            campo,
            valor,
            presupuesto_id,
        )
        with window.svc.cursor() as cur:
            cur.execute(
                f"UPDATE [presupuestos].dbo.partidas SET {campo} = ? WHERE presupuesto_id = ?",
                (valor, presupuesto_id),
            )
            affected = cur.rowcount
            cur.commit()
        print(f"[DEBUG] UPDATE ejecutado. Filas afectadas: {affected}")
        LOGGER.info("UPDATE global ejecutado. Filas afectadas: %s", affected)
        if affected == 0:
            print("[DEBUG] ADVERTENCIA: Ninguna fila actualizada (el presupuesto no tiene partidas)")
            LOGGER.warning("Ninguna fila actualizada para presupuesto_id=%s y campo=%s", presupuesto_id, campo)
            # No es un error fatal, pero informamos
            QMessageBox.warning(window, "Sin partidas", "El presupuesto actual no tiene partidas. No se actualizó ningún registro.")
            return False
    except Exception as e:
        print(f"[DEBUG] EXCEPCIÓN en UPDATE: {e}")
        LOGGER.exception("Excepcion en UPDATE global de partidas")
        QMessageBox.critical(
            window,
            "Error",
            f"No se pudo actualizar el valor global en las partidas:\n{str(e)}",
        )
        return False

    # Actualizar caché de partidas
    if hasattr(window, "presupuesto_ctrl") and window.presupuesto_ctrl:
        print("[DEBUG] Actualizando caché de partidas...")
        LOGGER.debug("Actualizando cache de partidas despues del UPDATE global")
        window.presupuesto_ctrl._actualizar_cache_partidas()

    print("[DEBUG] actualizar_valor_global_partidas finalizado exitosamente")
    LOGGER.info("actualizar_valor_global_partidas finalizado exitosamente")
    return True


def recalcular_y_persistir_totales_presupuesto_actual(window) -> bool:
    """
    Recalcula y persiste precio_unitario y total_partida de TODAS las partidas
    del presupuesto actual usando exactamente la misma fórmula de _recalc_summary().
    """
    presupuesto_id = window._obtener_presupuesto_id_edicion_global()
    if not presupuesto_id:
        QMessageBox.warning(
            window,
            "Presupuesto no disponible",
            "Debe guardar o abrir un presupuesto antes de recalcular totales globales.",
        )
        return False

    if hasattr(window, "presupuesto_ctrl") and window.presupuesto_ctrl:
        if not window.presupuesto_ctrl.guardar_partida_actual_silencioso():
            return False

    try:
        partidas = window.svc.obtener_partidas(presupuesto_id)
        updates = []

        for partida in partidas:
            partida_id = partida["id"]
            items = window.svc.obtener_items_partida(partida_id)

            A = sum(float((it.get("importe") or 0.0)) for it in items)

            mano_obra = float(partida.get("mano_obra") or 0.0)
            accesorios = float(partida.get("accesorios") or 0.0)
            desperdicio = float(partida.get("desperdicio") or 0.0)
            fv_porcentaje = float(partida.get("fv_porcentaje") or 0.0)
            piezas = max(1, int(float(partida.get("piezas") or 1)))

            B = mano_obra + accesorios
            C = A + B
            D = C + (C * (desperdicio / 100.0))
            E = D + (D * (fv_porcentaje / 100.0))
            total_partida = E * piezas

            updates.append((round(E, 2), round(total_partida, 2), partida_id))

        with window.svc.cursor() as cur:
            for precio_unitario, total_partida, partida_id in updates:
                cur.execute(
                    """
                    UPDATE [presupuestos].dbo.partidas
                    SET precio_unitario = ?, total_partida = ?
                    WHERE id = ?
                    """,
                    (precio_unitario, total_partida, partida_id),
                )
            cur.commit()

    except Exception as e:
        QMessageBox.critical(
            window,
            "Error",
            f"No se pudieron recalcular y persistir los totales globales:\n{str(e)}",
        )
        return False

    if hasattr(window, "presupuesto_ctrl") and window.presupuesto_ctrl:
        window.presupuesto_ctrl._actualizar_cache_partidas()

    # Después de actualizar la BD y antes de cualquier operación visual,
    # guardar el estado original de _prog y forzarlo a False para evitar bloqueos.
    original_prog = getattr(window, "_prog", False)
    window._prog = False

    try:
        # Los spinboxes ya deben venir actualizados desde el diálogo/handler.
        # Aquí solo forzamos el recálculo visual completo de la UI.
        if hasattr(window, "_on_recalcular_todo"):
            window._on_recalcular_todo()
        if hasattr(window, "_recalc_summary"):
            window._recalc_summary()
    finally:
        # Restaurar el estado original de _prog.
        window._prog = original_prog
    return True
